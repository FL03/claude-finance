"""myfi_toolkit.tools — tool implementations shared by the CLI and the MCP server.

Single source of truth for the toolkit's capability surface, so `myfi_toolkit.cli`
and `myfi_toolkit.mcp_server` never drift from each other. Every function that
touches numpy/pandas/scipy/matplotlib performs the import inside itself (lazy)
so importing this module never pays the heavy-import cost — the fast-gate rule
from the v0.0.0 plan (`<2s`, no top-level numpy/pandas/scipy/matplotlib).
"""

from __future__ import annotations

from myfi_toolkit import __version__

__all__ = ["describe_toolkit", "describe_stats"]

# Kept in one place so `describe_toolkit()` (CLI `stats`/MCP tool output) and
# the CLI's own subparser help strings describe the identical surface.
CAPABILITIES: tuple[str, ...] = (
    "version — print the toolkit's semantic version",
    "db init|migrate|version [--global] — per-project/global SQLite registry (myctx, Wave 3)",
    "quote <symbol> — fetch a market quote via the market-data adapter (Wave 3)",
    "stats — numpy/pandas/scipy version summary of the active toolkit environment",
)


def describe_toolkit() -> dict[str, object]:
    """Return the toolkit's identity + capability list.

    This is the payload behind both the CLI's implicit self-description and
    the MCP `describe_toolkit` tool — structured (JSON-serializable) output an
    agent can parse programmatically rather than free-form prose.
    """
    return {
        "name": "myfi-toolkit",
        "version": __version__,
        "capabilities": list(CAPABILITIES),
    }


def describe_stats() -> str:
    """Summarize the numpy/pandas/scipy versions available to the toolkit.

    Lazy-imports the heavy data stack — only reached from the CLI `stats`
    subcommand or an MCP tool call, never at module import time.
    """
    import numpy as np
    import pandas as pd
    import scipy

    lines = [
        f"numpy  {np.__version__}",
        f"pandas {pd.__version__}",
        f"scipy  {scipy.__version__}",
    ]
    return "\n".join(lines)
