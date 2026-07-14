"""myfi_toolkit — core lib backing the myfi CLI and stdio MCP server.

Stays import-light at package scope: this module sits on the fast gate's hot
path (``bin/myfi-toolkit --version``, CLI/MCP import smoke), so importing
``myfi_toolkit`` MUST NOT pull in numpy/pandas/scipy/matplotlib/mcp. Every
module that needs the heavy data stack imports it lazily inside the function
that needs it — see ``myfi_toolkit.tools`` and ``myfi_toolkit.cli``.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
