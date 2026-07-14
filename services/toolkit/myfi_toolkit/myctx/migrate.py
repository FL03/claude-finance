"""myfi_toolkit.myctx.migrate -- gap-fill schema migration runner.

Applies every versioned `.sql` file under the packaged `schema/` directory
(and its `schema/migrations/` subdirectory) whose integer version is absent
from the `schema_versions` table -- not merely those greater than the current
max version. This repairs a database that skipped an out-of-place migration,
mirroring shepherd's `skills/context/scripts/cmd_migrate.sh` gap-fill logic
(v6.0.3: "repairs DBs that skipped an out-of-place migration").

Each migration file is a self-contained `.sql` script (its own `BEGIN`/
`COMMIT`, `PRAGMA`s as needed -- see `schema/0001_init.sql`). The runner
records every applied version in `schema_versions` via `INSERT OR IGNORE`, so
a migration file that already inserts its own baseline row is never double-
counted, and future migration files don't need to repeat that insert
themselves.

Stdlib-only (sqlite3, pathlib, hashlib) -- no ORM, per CLAUDE.md "vanilla by
default".
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from pathlib import Path

# The packaged schema root: `myfi_toolkit/myctx/schema/`. Callers (mainly
# tests) may override this via the `schema_root` parameter to point at a
# synthetic migration set instead.
_SCHEMA_ROOT = Path(__file__).resolve().parent / "schema"

_VERSION_RE = re.compile(r"^(\d{4})_")


def _discover(schema_root: Path) -> list[tuple[int, Path]]:
    """Find every `NNNN_*.sql` file under `schema_root` and
    `schema_root/migrations/`, sorted by integer version.

    A version number appearing in both locations is a packaging bug -- fail
    loudly rather than silently pick one.
    """
    found: dict[int, Path] = {}
    for directory in (schema_root, schema_root / "migrations"):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.sql")):
            match = _VERSION_RE.match(path.name)
            if not match:
                continue
            version = int(match.group(1))
            if version in found:
                raise ValueError(
                    f"duplicate migration version {version}: {found[version]} vs {path}"
                )
            found[version] = path
    return sorted(found.items())


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def applied_versions(conn: sqlite3.Connection) -> set[int]:
    """Versions already recorded in `schema_versions`.

    Returns the empty set for a pre-bootstrap database (no `schema_versions`
    table yet) rather than raising -- that is the normal state of a brand new
    `.myfi/myfi.db` before `db init` runs.
    """
    if not _has_table(conn, "schema_versions"):
        return set()
    rows = conn.execute("SELECT version FROM schema_versions").fetchall()
    return {row[0] for row in rows}


def current_version(conn: sqlite3.Connection) -> int:
    """Highest applied version, or 0 for a schema_versions-less database."""
    versions = applied_versions(conn)
    return max(versions) if versions else 0


def run(conn: sqlite3.Connection, schema_root: Path | None = None) -> int:
    """Apply every pending migration (gap-fill semantics). Returns the count
    of migrations applied in this call (0 means already fully current)."""
    schema_root = schema_root if schema_root is not None else _SCHEMA_ROOT
    already = applied_versions(conn)
    pending = [(v, p) for v, p in _discover(schema_root) if v not in already]

    applied = 0
    for version, path in pending:
        sql_text = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql_text.encode("utf-8")).hexdigest()
        conn.executescript(sql_text)
        conn.execute(
            "INSERT OR IGNORE INTO schema_versions (version, applied_at, checksum) "
            "VALUES (?, ?, ?)",
            (version, int(time.time()), checksum),
        )
        conn.commit()
        applied += 1
    return applied
