"""myfi_toolkit.marketdata.research — the DEFAULT MarketDataSource.

Per the v0.0.0 plan (`W3-toolkit-marketdata` [NOTES]): this sprint ships the
``MarketDataSource`` *contract* only — no concrete provider, no API keys, no
network I/O. ``ResearchSource`` is the DEFAULT source selected by
``registry.default_source()`` whenever no paid provider is configured (which
is also the offline / CI default): it "degrades" to the research/WebFetch
path an agent would use on its own — asking local Claude Code to look a price
up — rather than calling a metered feed.

That live research call is a genuine latent operation (an LLM turn), which is
exactly why it stays out of this module's *default*, deterministic code path:
this plugin's fast-gate rule (`CLAUDE.md`, the v0.0.0 plan's topology
convention) requires every gate-tested import/call to be fast and offline, and
`services/eval/rubrics/market_quote.rubric.json` is where the research call's
*plausibility* actually gets judged (by the live-lane local Claude Code judge,
mock-lane-asserted on the gate — see ``services/toolkit/tests/test_marketdata.py``).
So ``quote()`` below performs no network I/O and reads no provider env: it
always returns a Quote whose price is the documented ``STUB_PRICE`` sentinel,
paired with a real, current ``asof`` timestamp and ``source="research"`` — a
structurally valid, honestly-labeled placeholder rather than a fabricated
market price. Wiring a live research call through ``services/llm`` (the same
local-Claude-Code seam every other model call in this plugin routes through —
never a hosted inference API) is a natural follow-up, not part of this
contract-only unit.
"""

from __future__ import annotations

from datetime import UTC, datetime

from myfi_toolkit.marketdata.contract import Quote

__all__ = ["ResearchSource", "SOURCE_NAME", "STUB_PRICE"]

SOURCE_NAME = "research"

# Documented placeholder price for the offline / no-provider-configured path.
# Deliberately not a "plausible-looking" fabricated number: 0.0 paired with
# source="research" tells a caller unambiguously "no paid feed resolved this
# — treat it as unresolved," rather than letting a made-up figure masquerade
# as real market data. A live integration replaces this value entirely; it
# never adjusts it.
STUB_PRICE = 0.0

DEFAULT_CURRENCY = "USD"


class ResearchSource:
    """The DEFAULT MarketDataSource — degrades to the research/WebFetch path.

    Structurally valid even fully offline: ``quote()`` performs no network
    I/O and reads no provider env, so it behaves identically in CI, in a
    fresh Claude Code session with no market-data MCP configured, and on a
    laptop with no network at all. Every ``Quote`` field is populated —
    ``price`` is the documented ``STUB_PRICE`` sentinel (never a fabricated
    real quote) and ``asof`` is a real, current timestamp, so a caller can
    tell "resolved just now, no provider configured" apart from a stale
    cache.
    """

    def quote(self, symbol: str) -> Quote:
        if not symbol or not symbol.strip():
            raise ValueError("quote() requires a non-empty symbol")
        return Quote(
            symbol=symbol.strip().upper(),
            price=STUB_PRICE,
            currency=DEFAULT_CURRENCY,
            asof=datetime.now(UTC),
            source=SOURCE_NAME,
        )
