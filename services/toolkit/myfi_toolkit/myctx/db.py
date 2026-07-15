"""myfi_toolkit.myctx.db -- SQLite connection factory for the myctx registry.

Resolves and opens the per-project `.myfi/myfi.db` (default) or the optional
global `~/.myfi/global.db` (`--global`), tuned with WAL journaling and
foreign-key enforcement -- both OFF by default in stdlib `sqlite3` and easy
to forget. Also carries `dispatch()`, the handler the CLI's lazy `db`
subcommand imports (`myfi_toolkit.cli._cmd_db` -> `myctx.dispatch(args)`).

Stdlib-only (sqlite3, argparse, pathlib) -- no ORM, per CLAUDE.md "vanilla by
default". The db path itself comes from `myfi_toolkit.config` (`[toolkit].db`
/ `[toolkit].global_db` in `.claude/myfi.toml`, hardcoded defaults otherwise)
-- see `resolve_db_path()`.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

from myfi_toolkit import config


def _logical_cwd() -> Path:
    """The caller's logical working directory.

    Prefers the `PWD` environment variable over `Path.cwd()` (`os.getcwd()`).
    `bin/myfi-toolkit` invokes this CLI via `poetry -C services/toolkit run
    myfi-toolkit ...`, and `poetry -C <dir>` chdirs the actual OS process
    into `<dir>` (the poetry-managed project) before running the command --
    so `Path.cwd()` alone would resolve every `db init` to
    `services/toolkit/.myfi/myfi.db` regardless of where the caller actually
    ran the command from. The shell keeps `PWD` pointing at the caller's real
    directory across that chdir, so preferring it here is what makes `db
    init` create `.myfi/myfi.db` in the CALLER's project root -- the
    ACCEPTANCE predicate ("in a scratch dir: bin/myfi-toolkit db init
    creates .myfi/myfi.db").
    """
    pwd = os.environ.get("PWD")
    if pwd:
        candidate = Path(pwd)
        if candidate.is_dir():
            return candidate
    return Path.cwd()


def resolve_db_path(use_global: bool = False, project_root: Path | None = None) -> Path:
    """Resolve the sqlite db path.

    Per-project (default): `<project_root>/<[toolkit].db>`, where
    `project_root` defaults to the caller's logical working directory (see
    `_logical_cwd`) -- the caller's project checkout -- and `[toolkit].db`
    comes from `myfi_toolkit.config.toolkit_db()` (`.claude/myfi.toml`,
    default `.myfi/myfi.db`). An absolute `[toolkit].db` value is used as-is,
    ignoring `project_root`.

    Global (`use_global=True`): `[toolkit].global_db` (default
    `~/.myfi/global.db`) via `myfi_toolkit.config.toolkit_global_db()`,
    resolved relative to `$HOME` unless it is already absolute (or
    `~`-prefixed, which `expanduser()` makes absolute); ignores
    `project_root`.
    """
    if use_global:
        global_path = Path(config.toolkit_global_db()).expanduser()
        if global_path.is_absolute():
            return global_path
        return Path.home() / global_path
    root = project_root if project_root is not None else _logical_cwd()
    db_path = Path(config.toolkit_db()).expanduser()
    if db_path.is_absolute():
        return db_path
    return root / db_path


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection tuned for the myctx registry.

    Creates the parent directory (and the db file itself, via sqlite3's
    connect-time file creation) if absent, enables WAL journaling and
    foreign-key enforcement (both per-connection settings sqlite3 defaults to
    OFF), and returns rows addressable by column name.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def dispatch(args: argparse.Namespace) -> int:
    """CLI entry point for `myfi-toolkit db <init|migrate|version> [--global]`.

    `init` and `migrate` both gap-fill (`migrate.run`) -- `init` is simply the
    first call against a database that has no `schema_versions` table yet, so
    both subcommands share one code path and re-running either is idempotent
    by construction (gap-fill applies nothing once the db is current).
    """
    from myfi_toolkit.myctx import migrate

    use_global = bool(getattr(args, "use_global", False))
    label = "global" if use_global else "project"
    db_path = resolve_db_path(use_global=use_global)
    conn = connect(db_path)
    try:
        sub = args.sub
        if sub in ("init", "migrate"):
            applied = migrate.run(conn)
            if applied:
                print(f"myctx: applied {applied} migration(s) to {label} db at {db_path}")
            else:
                print(f"myctx: {label} db already current at {db_path}")
            return 0
        if sub == "version":
            print(migrate.current_version(conn))
            return 0
        print(f"myctx: unknown db subcommand {sub!r}", file=sys.stderr)
        return 2
    finally:
        conn.close()
