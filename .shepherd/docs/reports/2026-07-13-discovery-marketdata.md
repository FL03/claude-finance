---
title: Discovery — market-data options for MarketDataSource adapter contract
date: 2026-07-13
discovery_id: D-MKTDATA
sprint: v0.0.0
sources_consulted: 12
tool_calls_used: 15
time_used_minutes: 14
---

## Sources
- Finnhub rate-limit docs — finnhub.io/docs/api/rate-limit
- Tiingo pricing/ToS — tiingo.com/about/pricing, app.tiingo.com/tos
- Twelve Data ToS — twelvedata.com/terms
- CoinGecko pricing/rate-limit — coingecko.com/en/api/pricing, support.coingecko.com
- FRED pricing summary — apispine.com/fred/pricing
- Alpha Vantage / Polygon comparison — alphalog.ai/blog/alphavantage-api-complete-guide, tildalice.io/yfinance-alpha-vantage-polygon-cost-breakdown
- yfinance repo — github.com/ranaroussi/yfinance
- MCP server rankings — awesomeclaude.ai/mcp/finance-fintech
- Massive.com MCP — github.com/massive-com/mcp_massive
- EODHD MCP — eodhd.com/financial-apis/mcp-server-for-financial-data-by-eodhd, github.com/EodHistoricalData/eodhd-mcp-server

## Findings

**1. Free/freemium API ranking** (breadth / free-tier limit / redistribution ToS / maintenance):
1. **Finnhub** — 60 calls/min, no daily cap; equities+FX+crypto+fundamentals+macro in one API; official licensed data; actively maintained [finnhub.io/docs/api/rate-limit].
2. **yfinance** — unofficial Yahoo scraper, no rate limit, ~24.6k GitHub stars, release June 2026, active issue traffic; ToS-risky, breaks on Yahoo changes [github.com/ranaroussi/yfinance].
3. **CoinGecko** — Demo plan 100/min & 10k/mo free (public no-key tier 5-15/min); crypto-only [coingecko.com/en/api/pricing].
4. **FRED** — free, no tiers, generous limits; authoritative but macro/rates-only, no equities/crypto [apispine.com/fred/pricing].
5. **Tiingo** — free tier exists but redistribution needs special permission + "Data sourced by Tiingo" attribution [tiingo.com/about/pricing; app.tiingo.com/tos].
6. **Twelve Data** — free tier exists; redistribution restricted, contact-sales for expanded rights [twelvedata.com/terms].
7. **Alpha Vantage** — only 25 req/day + 5/min free; most restrictive [alphalog.ai/blog/alphavantage-api-complete-guide].
8. **Polygon.io** — free tier discontinued; paid-only from ~$99/mo after Massive.com rebrand. Not viable as zero-cost default [tildalice.io/yfinance-alpha-vantage-polygon-cost-breakdown].

**2. Financial-market MCP servers** (2026), ranked by GitHub stars [awesomeclaude.ai/mcp/finance-fintech, 116 total listed]: MetaTrader MCP 504★ (forex/commodities), LongPort OpenAPI 437★ (stocks/options), Polygon.io MCP 353★ (stocks/indices/forex/options), Investor Agent 334★, CCXT MCP 139★ (crypto spot/futures), Alpha Vantage MCP 97★, CoinCap MCP 92★ (no auth). Named-not-ranked: **Massive.com MCP** (search/call/query composable tools, full stock/options/forex/crypto/futures via `MASSIVE_API_KEY`, auto-syncs from llms.txt) [github.com/massive-com/mcp_massive]; **EODHD MCP** (72 tools/15 categories incl. Treasury rates, ESG, macro; v1 API-key, v2 OAuth-native for Claude Desktop) [eodhd.com/...mcp-server-for-financial-data-by-eodhd]. All require auth except CoinCap.

**3. Recommendation** — see LOCKED RECOMMENDATIONS below.

## Open questions
- Exact FRED numeric rate-limit ceiling not found in sources consulted (described only as "generous").
- No MCP server found with broad multi-asset coverage AND a genuinely free/no-key tier — CoinCap is the only no-auth MCP but crypto-only.

## Confidence
MEDIUM-HIGH — rate-limit and ToS claims are well-sourced from provider docs; MCP star-counts are a single secondary aggregator (awesomeclaude.ai) not cross-checked against live GitHub API calls due to budget.

## Suggested follow-ups (optional)
- Live-verify Finnhub/CoinGecko/FRED rate limits against provider docs directly (not aggregator pages) before locking the contract's rate-limit constants.
- When wiring the MCP path, evaluate EODHD v2 OAuth vs Massive.com MCP key-auth for lowest operator friction.

## LOCKED RECOMMENDATIONS
- **DEFAULT adapter: Finnhub** — 60 req/min free with no daily cap, single API spans equities/FX/crypto/fundamentals, licensed (not scraped), actively maintained.
- **ALTERNATE 1: yfinance** — zero-setup, matches the plugin's self-contained/degrade-to-WebFetch default; largest community lib but ToS-gray and scrape-fragile.
- **ALTERNATE 2: FRED** — free unlimited-tier macro/rates source to pair with Finnhub, which has no Fed macro-series coverage.
