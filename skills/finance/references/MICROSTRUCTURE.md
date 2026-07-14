---
description: Market microstructure and execution mechanics -- order types, the limit order book, bid-ask spread, slippage, market impact (temporary vs permanent), fill mechanics, and adverse selection -- framed as the frictions a modeled return must survive before it is a realized return. Load in addition to QUANT.md + MODELS.md whenever the goal touches fill/execution mechanics, not just a theoretical price or return.
---

# MICROSTRUCTURE -- execution mechanics

A model that prices a return without pricing what it costs to actually get that return is only
half a model. This file is the other half: the frictions between a theoretical price and a filled
order, and why `@quant` must name them even when `@trader` is the one who would (in a future
version) act on them.

## Order types

- **Market order.** Executes immediately against the best available resting price(s). Guarantees
  execution, not price -- it walks the book (see below) if the order is larger than the top-of-book
  size.
- **Limit order.** Executes only at a specified price or better. Guarantees price, not execution --
  it can sit unfilled indefinitely if the market never trades through it, and it carries adverse-
  selection risk (below) while resting.
- **Marketable limit order.** A limit order priced aggressively enough (at or through the current
  opposite best price) to execute immediately like a market order, while still capping the worst
  price paid.
- **Stop / stop-limit.** A stop order converts to a market (stop) or limit (stop-limit) order once
  a trigger price trades; useful for risk control, but a stop is not a price guarantee -- in a fast
  market it can trigger and then fill far through the trigger price.

## The limit order book (LOB)

The order book is two ranked queues: **bids** (resting buy orders, ranked highest price first) and
**asks/offers** (resting sell orders, ranked lowest price first). The **best bid** and **best ask**
define the top of book; **depth** is the size resting at each price level below the top. Most
venues match on **price-time priority**: at a given price, the order that arrived first fills
first (some venues use pro-rata matching instead, splitting fills proportionally to size at a
price level -- know which regime applies before assuming FIFO).

## Bid-ask spread

```
spread = best_ask - best_bid
```

The spread is a real cost paid by whoever crosses it (a market order or a marketable limit taking
liquidity); the resting side effectively captures it. **Half-spread** (`spread / 2`) is the common
one-way transaction-cost proxy relative to the mid-price. **Quoted spread** is what the book shows;
**effective spread** measures what was actually paid relative to the mid at order entry, and can
be smaller than quoted spread when an order receives price improvement.

## Slippage

Slippage is the gap between the price a strategy or backtest assumed (typically the mid-price at
decision time) and the price actually realized on the fill. It is driven by three additive
sources: the cost of crossing the spread, market impact (below), and the latency between the
decision and the order reaching the venue (during which the market can move). A backtest that
prices fills at the historical mid with zero slippage is, by construction, reporting an
upper bound on the strategy's true return (`MODELS.md §Backtesting discipline`).

## Market impact

- **Temporary impact.** The price concession needed to source liquidity right now -- it pushes the
  price against the trader while the order executes, then **reverts** as the book replenishes.
  Larger for orders that consume more of the available depth at once.
- **Permanent impact.** A price move that does **not** revert, because the trade itself reveals
  information (the market infers something from the fact that a large order arrived) or
  represents a lasting shift in supply/demand. Distinguishing the two matters for anyone splitting
  an order over time: temporary impact resets between child orders, permanent impact does not.
- **Square-root law.** Empirically (and in classic microstructure models, e.g. Kyle's lambda,
  Almgren-Chriss), impact scales roughly with the square root of order size relative to typical
  traded volume, not linearly -- doubling an order size roughly multiplies impact by `sqrt(2)`,
  not `2`. This is why large orders are worked over time rather than sent as one clip.
- **Almgren-Chriss framing.** Optimal execution trades off two costs that move in opposite
  directions with execution speed: impact cost (falls if you trade slower, spreading the order
  thinner) against timing/volatility risk (rises if you trade slower, since the price can move
  against you the whole time you are still exposed). The "right" execution horizon is the point
  that balances the two, not the fastest or the slowest possible fill.

## Fill mechanics

Orders can **partial-fill** -- only part of the requested size executes against available
opposite-side liquidity, with the remainder either resting (limit) or cancelled (immediate-or-
cancel/fill-or-kill variants). **Iceberg/hidden orders** display only part of their true size to
the book, reducing the signal a large order sends but not eliminating impact once enough of it has
traded. Execution can happen on a **lit exchange** (displayed book, price-time or pro-rata
priority as above) or in a **dark pool** (matched off-book, typically at a reference price like
the lit-market midpoint, trading displayed-price certainty for reduced information leakage).

## Adverse selection

A resting limit order is a free option written to the rest of the market: it gets filled
disproportionately often right when the market is about to move against the price it was resting
at, because informed traders selectively pick off stale quotes before the quote-setter can react
(the Glosten-Milgrom / Kyle framing of market-making). This is the economic reason **market makers
widen quoted spreads exactly when information asymmetry is high** (around earnings, macro
releases, or any event where some participants plausibly know more than the quote is priced for) --
the wider spread is compensation for the expected adverse-selection loss, not simple greed.

## Why this matters to a modeled return

A price target, an expected return, or a backtested Sharpe ratio computed with no reference to
spread, slippage, or impact is a **paper return** -- it describes a trade that was never actually
exposed to a real order book. Realized P&L is:

```
realized_return = modeled_return - (spread cost + market impact + slippage)
```

For low-turnover, small-size strategies this gap can be a rounding error; for high-turnover or
large-relative-to-volume strategies it routinely consumes most or all of the theoretical edge.
Every `@quant` output that implies a trade (an option hedge, a portfolio rebalance, a
backtested strategy) states explicitly whether execution costs were modeled and how -- silence on
this point is the same category of omission as a point estimate with no confidence interval
(`QUANT.md §The discipline`): the number looks complete and is not.
