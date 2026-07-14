---
description: Binary-contract and prediction-market probability arithmetic -- converting odds/prices to implied probability, calibration and proper scoring rules (Brier, log score), favorite-longshot bias, forecast aggregation, and how to state a probability with its uncertainty. Load in addition to QUANT.md + MODELS.md whenever the goal touches a binary contract, a prediction market, or a probability forecast.
---

# PREDICTION -- binary contracts and forecast quality

Everything in `QUANT.md §The discipline` applies to a probability exactly as it applies to a
price: a bare "62%" with no source and no uncertainty is a guess. This file is the arithmetic and
the scoring discipline for treating a probability as a real quantitative output.

## Price-as-probability arithmetic

A binary contract paying $1 if an event occurs and $0 otherwise has a no-arbitrage price equal to
its risk-neutral probability of occurring (discounting is usually negligible for short-dated
contracts and should be applied explicitly, not silently ignored, for longer-dated ones):

```
p = price / payout   (e.g., a $0.62 contract paying $1 implies p = 0.62)
```

**Converting odds formats to implied probability:**

- **Decimal odds `d`** (total payout per unit staked, e.g. `1.60`): `p = 1 / d`.
- **American odds:** if positive (`+150`, profit per $100 staked): `p = 100 / (100 + 150)`. If
  negative (`-150`, stake needed to win $100): `p = 150 / (150 + 100)`.
- **Prediction-market price** quoted in cents (0-100) or as a decimal (0-1): `p = price / 100` or
  `p = price` directly, respectively.

**Removing the vig/overround.** Bookmaker odds on a mutually exclusive, collectively exhaustive
set of outcomes sum to more than 100% -- the excess is the vig. To recover a fair probability,
normalize: `p_i_fair = p_i_implied / sum_j(p_j_implied)`. Skipping this step and quoting a raw
implied probability from a two-sided market overstates every outcome's true probability by the
size of the vig.

## Calibration

A forecaster (or a market) is **well-calibrated** if, among all the times a probability of `x` is
stated, the event happens a fraction `x` of the time -- calibration is a statement about a whole
track record, not any single forecast. Check it with a **reliability diagram**: bin forecasts
(e.g., 0-10%, 10-20%, ...), and for each bin plot the average forecast against the observed event
frequency in that bin. Points on the 45-degree line are calibrated; points below it mean the
forecaster is overconfident in that range, above it means underconfident.

Calibration is necessary but not sufficient: a forecaster who always says "the historical base
rate" is calibrated in aggregate but useless, because they never sharpen the estimate per-event.
The missing half is **resolution/refinement** -- see the Brier decomposition below.

## Proper scoring rules

A scoring rule is **strictly proper** if a forecaster's expected score is uniquely minimized
(or maximized, by convention) by reporting their true belief -- hedging the number away from
one's real estimate can only make the expected score worse. Both rules below are strictly proper,
which is why they, not raw accuracy, are the standard for grading probability forecasts.

**Brier score.** For `N` forecasts with probability `f_i` and binary outcome `o_i in {0, 1}`:

```
BS = (1/N) * sum_i ( f_i - o_i )^2
```

Range `[0, 1]`, lower is better, `0` is a perfect forecast. The Murphy decomposition splits it
into `BS = Reliability - Resolution + Uncertainty`: reliability penalizes miscalibration
(the reliability-diagram gap above), resolution rewards actually discriminating between
high-probability and low-probability cases (sharpening away from the base rate), and uncertainty
is a property of the event base rate itself, not the forecaster.

**Log score (log loss).**

```
LS = -(1/N) * sum_i [ o_i * ln(f_i) + (1 - o_i) * ln(1 - f_i) ]
```

Lower is better, `0` is perfect. Unlike Brier, the log score is unbounded above: a confident wrong
call (`f_i` near 0 or 1 on the wrong side) is punished arbitrarily harshly as `f_i -> 0` or `1`,
which makes it the sharper tool for penalizing overconfidence specifically. Prefer the log score
when the cost of a confident miss is what matters most to the client; prefer Brier when a bounded,
more interpretable scale matters more.

## Favorite-longshot bias

Documented across horse racing, sports betting, and prediction markets: **favorites (high implied
probability) are systematically underpriced** relative to their true win rate, and **longshots
(low implied probability) are systematically overpriced** -- bettors as a population overpay for a
lottery-ticket payoff and underpay for the safe bet. Practical implication: do not read a 2-cent
contract at face value as "2% probability." The correct move is to state the raw market-implied
probability, name the favorite-longshot adjustment as a known bias, and haircut the extreme end of
the range toward the favorite side rather than silently accepting the raw price as calibrated
truth -- especially for prices below roughly 5% or above roughly 95%, where the bias is largest in
the published literature.

## Aggregating multiple forecasts

Simple linear averaging of several forecasters' probabilities is a common default and it is
provably **underconfident** relative to the true aggregate belief when the forecasters share
correlated information, because averaging probabilities pulls every extreme estimate toward 0.5.
Two better defaults:

- **Log-odds (logit) averaging.** Convert each `p_i` to log-odds `ln(p_i / (1-p_i))`, average in
  log-odds space, convert back. Equivalent to a geometric mean of the odds, and preserves more of
  the aggregate's confidence than a linear average.
- **Extremizing aggregation.** Average in logit space as above, then apply a mild extremizing
  exponent (`> 1`) before converting back -- empirically shown (forecasting-tournament literature,
  e.g. Satopaa et al.) to outperform plain linear or logit averaging when forecasters' errors are
  correlated, which they usually are when drawing on the same public information.

Name which aggregation method was used; "the average of three forecasts" without specifying linear
vs logit is not reproducible.

## Stating a probability with its uncertainty

Never report a bare point probability. Attach one of:

- **From a sample of `n` past outcomes:** a Wilson score interval or a Beta-Binomial posterior
  credible interval, not a naive `p +/- 1.96*sqrt(p(1-p)/n)` normal approximation when `n` is
  small or `p` is near 0 or 1 (the normal approximation breaks exactly in the region
  `PREDICTION.md §Favorite-longshot bias` warns about).
- **From a market price:** the bid-ask spread on that price *is* the uncertainty band -- report
  it, and flag thin liquidity/depth explicitly, since a wide spread or a shallow book means the
  quoted mid is a noisier estimate of the true probability than the same price in a deep, tight
  market.
- **From a model-derived probability** (e.g., a Merton default probability, `MODELS.md
  §Merton structural credit model`): propagate the input parameter uncertainty (asset volatility,
  drift estimation error) into the output the same way `QUANT.md §Attaching an uncertainty band`
  requires for any other model output.
