"""myfi_toolkit.myctx -- per-project (`.myfi/myfi.db`) + optional global
(`~/.myfi/global.db`) SQLite context registry.

Stdlib-only (`sqlite3`) -- no ORM, per CLAUDE.md "vanilla by default".
`db.py` is the connection factory + CLI dispatch handler; `migrate.py` is the
gap-fill schema runner; `schema/` holds the versioned `.sql` migration files
(`0001_init.sql` baseline, future `schema/migrations/NNNN_*.sql`).

`myfi_toolkit.cli` imports this package lazily from inside its `db`
subcommand handler -- see `cli.py::_cmd_db` -- so importing `myfi_toolkit`
itself never pays this package's (cheap, stdlib-only) import cost either.
"""

from __future__ import annotations

from myfi_toolkit.myctx.db import connect, dispatch, resolve_db_path
from myfi_toolkit.myctx.migrate import current_version
from myfi_toolkit.myctx.migrate import run as run_migrations

__all__ = [
    "connect",
    "resolve_db_path",
    "dispatch",
    "current_version",
    "run_migrations",
]
