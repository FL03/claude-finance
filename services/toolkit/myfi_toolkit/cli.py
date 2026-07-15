"""myfi_toolkit.cli -- stdlib argparse dispatcher for the myfi toolkit.

Stays import-light on purpose: this module is on the hot path of the plugin's
fast gate (`bin/myfi-toolkit --version`, CLI import/smoke tests), so the heavy
data stack (numpy, pandas, scipy, matplotlib) and the `mcp` SDK MUST stay out
of module scope entirely. Every subcommand that needs them (or the Wave-3
`myctx`/`marketdata` subpackages) imports lazily inside its own handler
function, never at module scope.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from myfi_toolkit import __version__

Handler = Callable[[argparse.Namespace], int]


def _cmd_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def _cmd_db(args: argparse.Namespace) -> int:
    # Lazy -- the myctx subpackage (schema, migrations, connection factory)
    # lands in Wave 3; the scaffold never imports it at module scope so this
    # unit builds and tests green without it.
    from myfi_toolkit import myctx

    return myctx.dispatch(args)


def _cmd_quote(args: argparse.Namespace) -> int:
    # Lazy -- the marketdata adapter package lands in Wave 3.
    from myfi_toolkit import marketdata

    return marketdata.quote(args.symbol)


def _cmd_stats(_args: argparse.Namespace) -> int:
    # Lazy -- pulls in numpy/pandas/scipy only when this subcommand runs.
    from myfi_toolkit.tools import describe_stats

    print(describe_stats())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myfi-toolkit",
        description="myfi finance-plugin toolkit -- CLI over the myfi_toolkit core lib.",
    )
    # Top-level `--version`/`-V` short-circuits before subcommand dispatch
    # (argparse's built-in version action prints + exits 0), matching the
    # `bin/myfi-toolkit --version` acceptance predicate. The `version`
    # subcommand below covers the same info through the normal dispatch path.
    parser.add_argument("--version", "-V", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_version = sub.add_parser("version", help="print the toolkit's semantic version")
    p_version.set_defaults(handler=_cmd_version)

    p_db = sub.add_parser("db", help="per-project / global SQLite registry (myctx)")
    p_db.add_argument("sub", choices=["init", "migrate", "version"], help="db subcommand")
    p_db.add_argument(
        "--global",
        dest="use_global",
        action="store_true",
        help="operate on the optional ~/.myfi/global.db instead of the per-project db",
    )
    p_db.set_defaults(handler=_cmd_db)

    p_quote = sub.add_parser("quote", help="fetch a market quote via the market-data adapter")
    p_quote.add_argument("symbol", help="ticker symbol, e.g. AAPL")
    p_quote.set_defaults(handler=_cmd_quote)

    p_stats = sub.add_parser("stats", help="numpy/pandas/scipy version summary of this environment")
    p_stats.set_defaults(handler=_cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Handler = args.handler
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
