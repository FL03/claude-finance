# The market-data contract

myfi never hallucinates a price. Every quote the toolkit, an agent, or a command reports comes
through one typed adapter contract, `MarketDataSource`, and every implementation of it is honest
about where its number came from.

## The contract

```python
@dataclass(frozen=True, slots=True)
class Quote:
    symbol: str
    price: float
    currency: str
    asof: datetime
    source: str          # which provider produced this quote

class MarketDataSource(Protocol):
    def quote(self, symbol: str) -> Quote: ...
```

`Quote.source` names the provider that produced it (`"research"`, `"finnhub"`, ...), a caller uses
it to judge trust and freshness rather than assuming every quote came from a live, paid feed. The
contract is a `typing.Protocol`, not an abstract base class, so a provider needs only the method,
no shared base class to inherit from.

## Provider selection

```bash
export MYFI_MARKETDATA_PROVIDER=research   # or: finnhub | yfinance | fred
bin/myfi-toolkit quote AAPL
```

`default_source()` picks a provider by the `MYFI_MARKETDATA_PROVIDER` env var (equivalent to
`[marketdata].provider` in `.claude/myfi.toml`, see [`configuration.md`](configuration.md#marketdata)),
falling back to `research` when unset. An unrecognized provider name raises loudly rather than
silently behaving like the default.

## Default: the research-degrade source

`research` is the default for now and needs no API key, no network credential, no setup at all. It
is a self-contained source that always answers, so a client goal never stalls on missing market
data infrastructure, at the cost of not being a live, tradeable-grade feed.

## Deferred providers

Three concrete providers are registered in the same table as `research` but each currently raises
`NotImplementedError` from `.quote()`, they exist so the provider-selection surface is real and
testable now, ahead of the HTTP client + API key handling that wires them live in a follow-up
release:

| Provider | Status | Why this one |
| :--- | :--- | :--- |
| `finnhub` | Deferred, locked default for the next release | 60 req/min free tier, no daily cap, one API spanning equities/FX/crypto. |
| `yfinance` | Deferred, alternate | Zero-setup and matches the plugin's self-contained philosophy, but unofficial and scrape-fragile. |
| `fred` | Deferred, alternate | Free, unlimited-tier macro/rates series, no equities or crypto coverage. |

Wiring any of these live is a contract-preserving change: implement `MarketDataSource.quote()` for
the class already registered under that provider name in
`myfi_toolkit/marketdata/registry.py`, nothing upstream (CLI, MCP tool, agent) needs to change.

## Calling it

```bash
bin/myfi-toolkit quote AAPL              # CLI, always prints Quote.to_dict() as JSON
```

```text
mcp__plugin_myfi_myfi-toolkit__quote(symbol="AAPL")   # MCP, returns the same shape as a typed object
```

Both paths call the exact same `default_source().quote(symbol)`, see [`toolkit.md`](toolkit.md) for
the rest of the toolkit surface.
