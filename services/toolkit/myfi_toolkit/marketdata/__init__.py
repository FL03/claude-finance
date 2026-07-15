"""myfi_toolkit.marketdata -- MarketDataSource contract + research-degrade default.

Public surface:

- ``Quote`` / ``MarketDataSource`` (``contract.py``) -- the typed shape every
  provider returns / implements.
- ``default_source()`` (``registry.py``) -- provider selection by
  ``MYFI_MARKETDATA_PROVIDER``, falling back to the research-degrade default.
- ``quote(symbol)`` below -- the handler behind ``myfi_toolkit.cli``'s ``quote``
  subcommand (``bin/myfi-toolkit quote <symbol>``); prints a JSON ``Quote`` to
  stdout and returns the process exit code, matching every other structured
  toolkit response (see ``myfi_toolkit.tools.describe_toolkit``).

Import-light at package scope on purpose: ``myfi_toolkit.cli`` only imports
this package lazily inside its ``quote`` handler (never at module scope), and
this package itself needs nothing beyond the stdlib, so importing it never
pays a heavy-import cost.
"""

from __future__ import annotations

import json

from myfi_toolkit.marketdata.contract import MarketDataSource, Quote
from myfi_toolkit.marketdata.registry import default_source

__all__ = ["MarketDataSource", "Quote", "default_source", "quote"]


def quote(symbol: str) -> int:
    """Fetch a quote via the default (env-selected) source and print it as JSON.

    Behind ``myfi_toolkit.cli._cmd_quote``: ``marketdata.quote(args.symbol)``.
    Output is always the ``Quote.to_dict()`` JSON shape -- structured,
    agent-parseable output, per the toolkit's response convention.
    """
    resolved = default_source().quote(symbol)
    print(json.dumps(resolved.to_dict()))
    return 0
