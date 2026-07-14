"""myfi_toolkit.mcp_server — stdio MCP server exposing the myfi toolkit's tools.

Registers the toolkit's tools with FastMCP and serves them over stdio
(discovery-packaging finding: official `mcp` SDK, FastMCP, stdio transport —
`.mcp.json` at the plugin root points `bin/myfi-mcp` at `main()` below).
Business logic lives in `myfi_toolkit.{tools,marketdata,myctx}`; this module
only wires it to the MCP protocol, so it is not a fast-gate module (the `mcp`
import here is expected and fine — only `myfi_toolkit.cli` stays import-light).

The tool set mirrors the CLI verbs so an agent reaches the SAME logic whether it
calls the MCP tool (`mcp__plugin_myfi_myfi-toolkit__<tool>`) or shells to the CLI.
`skills/myfi/SKILL.md` documents these names as canonical; keep the two in sync.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from myfi_toolkit import tools as _tools

mcp = FastMCP("myfi-toolkit")


@mcp.tool()
def describe_toolkit() -> dict[str, object]:
    """Describe the myfi toolkit: name, version, and the CLI/MCP capabilities it exposes."""
    return _tools.describe_toolkit()


@mcp.tool()
def quote(symbol: str) -> dict[str, object]:
    """Fetch a market quote for a ticker symbol via the MarketDataSource adapter.

    Uses the provider named by MYFI_MARKETDATA_PROVIDER, defaulting to the
    research-degrade source when unset (self-contained, no API key required).
    """
    from dataclasses import asdict, is_dataclass

    from myfi_toolkit import marketdata

    q = marketdata.default_source().quote(symbol)
    if is_dataclass(q):
        return asdict(q)
    return {"symbol": symbol, "value": str(q)}


def _db_state(use_global: bool = False, apply_migrations: bool = True) -> dict[str, object]:
    from myfi_toolkit import myctx
    from myfi_toolkit.myctx import migrate

    db_path = myctx.resolve_db_path(use_global=use_global)
    conn = myctx.connect(db_path)
    try:
        applied = migrate.run(conn) if apply_migrations else 0
        version = migrate.current_version(conn)
    finally:
        conn.close()
    return {
        "db_path": str(db_path),
        "applied": applied,
        "version": version,
        "scope": "global" if use_global else "project",
    }


@mcp.tool()
def db_init(use_global: bool = False) -> dict[str, object]:
    """Create the per-project (or --global) SQLite registry and apply all pending migrations. Idempotent."""
    return _db_state(use_global=use_global, apply_migrations=True)


@mcp.tool()
def db_migrate(use_global: bool = False) -> dict[str, object]:
    """Apply any pending schema migrations to the SQLite registry (gap-fill). Idempotent."""
    return _db_state(use_global=use_global, apply_migrations=True)


@mcp.tool()
def db_version(use_global: bool = False) -> dict[str, object]:
    """Report the current schema version of the SQLite registry without applying migrations."""
    return _db_state(use_global=use_global, apply_migrations=False)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
