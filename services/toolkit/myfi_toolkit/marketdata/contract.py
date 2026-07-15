"""myfi_toolkit.marketdata.contract -- the MarketDataSource protocol + Quote shape.

Every market-data provider (the research-degrade default in ``research.py``, and
the deferred concrete providers registered in ``registry.py``) implements one
structural contract: ``quote(symbol) -> Quote``. Defined as a
``typing.Protocol`` rather than an ABC so a provider needs no shared base
class -- it only needs the method, which keeps the deferred provider stubs in
``registry.py`` (and any future concrete provider) trivially conformant.

Stdlib only. This module sits behind the CLI's lazy-import boundary
(``myfi_toolkit.cli._cmd_quote`` imports ``myfi_toolkit.marketdata`` only
inside the handler function, never at module scope), but it must stay
import-light itself since every provider module in this subpackage imports it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

__all__ = ["Quote", "MarketDataSource"]


@dataclass(frozen=True, slots=True)
class Quote:
    """A single market quote, typed and provider-agnostic.

    ``source`` names the provider that produced the quote (e.g. ``"research"``,
    ``"finnhub"``) -- callers use it to judge trust and freshness rather than
    assuming every quote came from a live, paid feed.
    """

    symbol: str
    price: float
    currency: str
    asof: datetime
    source: str

    def to_dict(self) -> dict[str, object]:
        """JSON-serializable shape (``asof`` isoformatted) for CLI/MCP output."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "currency": self.currency,
            "asof": self.asof.isoformat(),
            "source": self.source,
        }


@runtime_checkable
class MarketDataSource(Protocol):
    """Structural contract every market-data provider implements."""

    def quote(self, symbol: str) -> Quote:
        """Return a :class:`Quote` for ``symbol``.

        Implementations MAY raise ``NotImplementedError`` for a provider that
        is registered but not yet wired -- see ``registry.py``'s deferred
        provider stubs (Finnhub / yfinance / FRED).
        """
        ...
