"""tests/test_myctx.py -- gate tests for myfi_toolkit.myctx (per-project +
optional global SQLite context registry).

Stdlib `sqlite3` + `tmp_path` only -- no live `.myfi/myfi.db` ever touched,
<2s total, per the v0.0.0 plan's W3-toolkit-db unit. `test_migration_golden`
is this unit's eval per CLAUDE.md's latent/deterministic split: a SQL
migration has no latent surface, so the eval IS the round-trip golden, not a
rubric (stated explicitly in the plan, not skipped).
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pytest

from myfi_toolkit.myctx import db, migrate


def _connect(tmp_path: Path, name: str = "myfi.db") -> sqlite3.Connection:
    conn = sqlite3.connect(tmp_path / name)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def test_migrate_run_creates_schema_versions(tmp_path: Path) -> None:
    """`migrate.run()` on an empty file creates `schema_versions` with >= 1 row."""
    conn = _connect(tmp_path)
    try:
        applied = migrate.run(conn)
        assert applied >= 1
        count = conn.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0]
        assert count >= 1
    finally:
        conn.close()


def test_migrate_run_is_idempotent(tmp_path: Path) -> None:
    """A second `migrate.run()` call applies 0 migrations and adds 0 rows."""
    conn = _connect(tmp_path)
    try:
        first_applied = migrate.run(conn)
        assert first_applied >= 1
        before = conn.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0]

        second_applied = migrate.run(conn)
        after = conn.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0]

        assert second_applied == 0
        assert after == before
    finally:
        conn.close()


def test_migrate_gap_fills_missing_intermediate_version(tmp_path: Path) -> None:
    """A missing intermediate version is gap-filled, not skipped as "> MAX".

    Seeds `schema_versions` with rows for v1 and v3 (as if v2 were an
    out-of-place migration that never ran -- shepherd cmd_migrate.sh v6.0.3's
    exact motivating bug) while a real v1/v2/v3 migration set exists on disk,
    then confirms `migrate.run()` applies only v2.
    """
    schema_root = tmp_path / "schema"
    schema_root.mkdir()
    (schema_root / "0001_base.sql").write_text(
        "CREATE TABLE schema_versions ("
        "  version INTEGER PRIMARY KEY,"
        "  applied_at INTEGER NOT NULL,"
        "  checksum TEXT NOT NULL"
        ");\n"
        "CREATE TABLE t1 (id INTEGER PRIMARY KEY);\n"
    )
    (schema_root / "0002_middle.sql").write_text("CREATE TABLE t2 (id INTEGER PRIMARY KEY);\n")
    (schema_root / "0003_last.sql").write_text("CREATE TABLE t3 (id INTEGER PRIMARY KEY);\n")

    conn = _connect(tmp_path, "gapfill.db")
    try:
        conn.execute(
            "CREATE TABLE schema_versions ("
            "  version INTEGER PRIMARY KEY,"
            "  applied_at INTEGER NOT NULL,"
            "  checksum TEXT NOT NULL"
            ")"
        )
        conn.execute("INSERT INTO schema_versions VALUES (1, 0, 'seed-v1')")
        conn.execute("INSERT INTO schema_versions VALUES (3, 0, 'seed-v3')")
        conn.commit()

        applied = migrate.run(conn, schema_root=schema_root)

        assert applied == 1
        versions = {row[0] for row in conn.execute("SELECT version FROM schema_versions")}
        assert versions == {1, 2, 3}

        # v2's DDL actually ran (the gap was filled)...
        conn.execute("SELECT 1 FROM t2 LIMIT 1")
        # ...but v1/v3's DDL was NOT re-run -- they were already recorded as
        # applied, so their tables were never created by this test.
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("SELECT 1 FROM t1 LIMIT 1")
    finally:
        conn.close()


def test_foreign_keys_pragma_on(tmp_path: Path) -> None:
    """`db.connect()` enables `PRAGMA foreign_keys` (OFF by default in sqlite3)."""
    conn = db.connect(tmp_path / ".myfi" / "myfi.db")
    try:
        value = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert value == 1
    finally:
        conn.close()


def test_migration_golden_is_byte_stable(tmp_path: Path) -> None:
    """Migration round-trip golden -- this unit's eval.

    Applies the packaged `0001_init.sql` to a fresh DB, dumps
    `schema_versions` + `sqlite_master`, and asserts the dump is byte-stable
    across two independent fresh databases. A schema change that breaks
    gap-fill determinism (e.g. a migration that isn't safely re-appliable, or
    one whose DDL output varies run to run) fails this golden -- the
    generalization proof for a unit with no latent surface (CLAUDE.md
    latent/deterministic split), so no LLM-judged rubric is shipped here.
    """

    def snapshot(db_name: str) -> str:
        conn = sqlite3.connect(tmp_path / db_name)
        try:
            migrate.run(conn)
            versions = conn.execute(
                "SELECT version, checksum FROM schema_versions ORDER BY version"
            ).fetchall()
            objects = conn.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            ).fetchall()
        finally:
            conn.close()
        return repr((versions, objects))

    first = snapshot("golden_a.db")
    second = snapshot("golden_b.db")

    assert first == second
    assert "schema_versions" in first
    assert "mem_entries" in first
    assert "audit_findings" in first
    assert "discovery_findings" in first


def test_baseline_checksum_is_sha256_of_the_sql(tmp_path: Path) -> None:
    """Regression: the baseline's schema_versions.checksum MUST be the real
    sha256 of 0001_init.sql, not a literal placeholder. 0001_init.sql must not
    self-insert its version row (a literal would shadow the real hash and
    migrate.py's INSERT OR IGNORE would silently no-op). This is the tamper/
    drift signal migrate.py records uniformly for every applied migration.
    """
    import hashlib

    sql_path = migrate._SCHEMA_ROOT / "0001_init.sql"
    expected = hashlib.sha256(sql_path.read_bytes()).hexdigest()

    conn = sqlite3.connect(tmp_path / "checksum.db")
    try:
        migrate.run(conn)
        stored = conn.execute(
            "SELECT checksum FROM schema_versions WHERE version = 1"
        ).fetchone()[0]
    finally:
        conn.close()

    assert stored == expected, f"baseline checksum {stored!r} != sha256(0001_init.sql) {expected!r}"


def test_current_version_reports_zero_pre_bootstrap(tmp_path: Path) -> None:
    conn = _connect(tmp_path, "fresh.db")
    try:
        assert migrate.current_version(conn) == 0
        migrate.run(conn)
        assert migrate.current_version(conn) == 1
    finally:
        conn.close()


def test_resolve_db_path_per_project_and_global(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PWD", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    project_path = db.resolve_db_path(use_global=False)
    assert project_path == tmp_path / ".myfi" / "myfi.db"

    global_path = db.resolve_db_path(use_global=True)
    assert global_path == tmp_path / "home" / ".myfi" / "global.db"


def test_resolve_db_path_prefers_pwd_over_os_getcwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: `bin/myfi-toolkit` runs the CLI via `poetry -C
    services/toolkit run myfi-toolkit ...`, and `poetry -C <dir>` chdirs the
    real OS process into `<dir>` before running the command -- so
    `Path.cwd()` alone always resolves to `services/toolkit/`, never the
    caller's actual project root. Simulates that divergence directly: chdir
    the process one place, set `PWD` to a different (real) directory, and
    confirm `resolve_db_path` follows `PWD`, not `os.getcwd()`.
    """
    real_cwd = tmp_path / "process-cwd-after-poetry-C-chdir"
    real_cwd.mkdir()
    caller_dir = tmp_path / "callers-actual-project-root"
    caller_dir.mkdir()

    monkeypatch.chdir(real_cwd)
    monkeypatch.setenv("PWD", str(caller_dir))

    assert Path.cwd() == real_cwd
    assert db.resolve_db_path(use_global=False) == caller_dir / ".myfi" / "myfi.db"


def test_db_init_end_to_end_creates_db_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mirrors the [ACCEPTANCE] predicate: `db init` creates `.myfi/myfi.db`
    with >= 1 `schema_versions` row, and a second `db init` is idempotent."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PWD", str(tmp_path))
    args = argparse.Namespace(sub="init", use_global=False)

    assert db.dispatch(args) == 0
    db_path = tmp_path / ".myfi" / "myfi.db"
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0]
        assert count >= 1
    finally:
        conn.close()

    assert db.dispatch(args) == 0
    conn = sqlite3.connect(db_path)
    try:
        count_again = conn.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0]
        assert count_again == count
    finally:
        conn.close()


def test_db_version_subcommand(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PWD", str(tmp_path))
    db.dispatch(argparse.Namespace(sub="init", use_global=False))
    capsys.readouterr()

    exit_code = db.dispatch(argparse.Namespace(sub="version", use_global=False))
    out = capsys.readouterr().out.strip()

    assert exit_code == 0
    assert out == "1"
