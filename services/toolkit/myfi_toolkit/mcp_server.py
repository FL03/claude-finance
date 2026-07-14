"""myfi_toolkit.mcp_server — stdio MCP server exposing the myfi toolkit's tools.

Registers the toolkit's capability-description tool with FastMCP and serves it
over stdio (discovery-packaging finding: official `mcp` SDK, FastMCP, stdio
transport — `.mcp.json` at the plugin root points `bin/myfi-mcp` at `main()`
below). Business logic lives in `myfi_toolkit.tools`; this module only wires it
to the MCP protocol, so it is not a fast-gate module (the `mcp` import here is
expected and fine — only `myfi_toolkit.cli` is required to stay import-light).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from myfi_toolkit import tools as _tools

mcp = FastMCP("myfi-toolkit")


@mcp.tool()
def describe_toolkit() -> dict[str, object]:
    """Describe the myfi toolkit: name, version, and the CLI/MCP capabilities it exposes."""
    return _tools.describe_toolkit()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
