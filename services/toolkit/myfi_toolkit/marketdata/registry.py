"""myfi_toolkit.marketdata.registry — provider selection by env.

``default_source()`` picks a ``MarketDataSource`` by the ``MYFI_MARKETDATA_PROVIDER``
env var, falling back to the research-degrade default (``research.py``) when
unset. Concrete providers are DEFERRED behind the contract per the v0.0.0
plan's non-goals ("No concrete market-data provider integrations — the
adapter contract only; providers wire in behind it later") and
`discovery-marketdata.md`'s LOCKED RECOMMENDATIONS (Finnhub default, yfinance
+ FRED alternates): they are registered here so the provider-selection
surface is real and testable now, but each stub raises ``NotImplementedError``
until a follow-up unit wires the concrete HTTP client + API key handling.
"""

from __future__ import annotations

import os

from myfi_toolkit.marketdata.contract import MarketDataSource, Quote
from myfi_toolkit.marketdata.research import ResearchSource

__all__ = ["PROVIDER_ENV", "DEFAULT_PROVIDER", "PROVIDERS", "default_source"]

PROVIDER_ENV = "MYFI_MARKETDATA_PROVIDER"
DEFAULT_PROVIDER = "research"

_DEFERRED_DOC = (
    "market-data provider is deferred behind the MarketDataSource contract "
    "(see .shepherd/docs/reports/2026-07-13-discovery-marketdata.md); set "
    f"{PROVIDER_ENV}=research, or leave it unset, to use the default."
)


class _FinnhubSource:
    """DEFERRED — discovery-marketdata's LOCKED default recommendation: 60
    req/min free tier, no daily cap, one API spanning equities/FX/crypto.
    Contract-only in v0.0.0: no HTTP client, no API key handling, no network
    I/O ships with this unit.
    """

    def quote(self, symbol: str) -> Quote:
        raise NotImplementedError(f"the 'finnhub' {_DEFERRED_DOC}")


class _YfinanceSource:
    """DEFERRED — discovery-marketdata's ALTERNATE 1: zero-setup, matches this
    plugin's self-contained/degrade-to-research philosophy, but unofficial and
    scrape-fragile. Contract-only; see ``_FinnhubSource``.
    """

    def quote(self, symbol: str) -> Quote:
        raise NotImplementedError(f"the 'yfinance' {_DEFERRED_DOC}")


class _FredSource:
    """DEFERRED — discovery-marketdata's ALTERNATE 2: free, unlimited-tier
    macro/rates series (no equities/crypto coverage). Contract-only; see
    ``_FinnhubSource``.
    """

    def quote(self, symbol: str) -> Quote:
        raise NotImplementedError(f"the 'fred' {_DEFERRED_DOC}")


# Registered by provider name (`MYFI_MARKETDATA_PROVIDER`). Every entry is
# constructible today; only ``research`` is actually callable — the rest raise
# NotImplementedError from `.quote()` until a follow-up unit wires them.
PROVIDERS: dict[str, type[MarketDataSource]] = {
    "research": ResearchSource,
    "finnhub": _FinnhubSource,
    "yfinance": _YfinanceSource,
    "fred": _FredSource,
}


def default_source() -> MarketDataSource:
    """Select a ``MarketDataSource`` by env, falling back to ``research``.

    Raises ``ValueError`` for an unrecognized ``MYFI_MARKETDATA_PROVIDER``
    value — a typo'd provider name fails loudly here rather than silently
    behaving like the default.
    """
    name = (os.environ.get(PROVIDER_ENV) or DEFAULT_PROVIDER).strip().lower()
    try:
        provider_cls = PROVIDERS[name]
    except KeyError as exc:
        known = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"unknown {PROVIDER_ENV}={name!r} (known providers: {known})") from exc
    return provider_cls()
