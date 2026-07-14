---
name: finance
description: Quantitative-modeling knowledge for the myfi flock's analyst -- stochastic calculus and risk theory (QUANT.md), the pricing/risk/portfolio model zoo of Black-Scholes, Heston, Merton, term-structure, factor models, Monte Carlo, and backtesting discipline (MODELS.md), binary-contract and prediction-market probability arithmetic (PREDICTION.md), and market microstructure/execution cost (MICROSTRUCTURE.md). Load QUANT.md and MODELS.md for any modeling task; add PREDICTION.md and MICROSTRUCTURE.md whenever the goal touches a binary contract, a prediction market, or fill/execution mechanics. Mandatory before @quant builds or reports any model.
---

# FINANCE -- quantitative modeling knowledge

This skill exists for `@quant` (`agents/quant.md`), and for any agent producing a modeled number.
It is a scaffold, not a manual: it orients you to four reference files and the mindset that ties
them together, and the depth lives in those files, not here.

> A quant does not predict. A quant prices risk. Every output is a distribution with a mean,
> variance, and tail -- a point estimate with no confidence interval is a guess, not analysis.

## The four references

| File | Load when | Covers |
|---|---|---|
| `references/QUANT.md` | Always, for any modeling task | Distribution-over-point-estimate discipline, stochastic calculus (Brownian motion, Ito's lemma, GBM, risk-neutral vs physical measure), risk theory (volatility, VaR vs Expected Shortfall, Greeks, fat tails), and how to attach an uncertainty band to any result |
| `references/MODELS.md` | Always, for any modeling task | The model zoo -- Black-Scholes, Heston, Merton (jump-diffusion and structural credit), term-structure (Vasicek, CIR, Nelson-Siegel), factor models (CAPM, Fama-French, APT), Monte Carlo methods, backtesting discipline -- each with assumptions and failure modes |
| `references/PREDICTION.md` | In addition, when the goal touches a binary contract or prediction market | Price-as-probability arithmetic, calibration, Brier/log score, favorite-longshot bias, forecast aggregation |
| `references/MICROSTRUCTURE.md` | In addition, when the goal touches fill/execution mechanics | Order types, the limit order book, bid-ask spread, slippage, market impact, adverse selection |

`QUANT.md` and `MODELS.md` load together and always -- foundations without the model zoo is theory
with nothing to apply it to, and the model zoo without the foundations is formulas plugged in by
someone who does not know what they assume. `PREDICTION.md` and `MICROSTRUCTURE.md` are additive:
load them alongside the always-on pair, never instead of it, whenever the unit of work is a binary
contract, a prediction-market probability, or anything touching how an order actually fills.

## The core mindset

1. **Distribution, not point estimate.** Every number carries a mean, a dispersion, and a stated
   view of its tail (`QUANT.md §The discipline`). "The position is worth $X" with nothing else is
   not a finished thought.
2. **Price the risk, not just the level.** A model's job is to say what could go wrong and by how
   much -- VaR/Expected Shortfall for a portfolio, Greeks for an option, the spread/impact/slippage
   band for anything about to touch a real book (`MICROSTRUCTURE.md`). The level is the least
   interesting part of the output.
3. **Every number is sourced and traceable.** A figure either comes from a toolkit call
   (`mcp__plugin_myfi_myfi-toolkit__quote`, the `db_*` verbs) with the raw value cited, or from a
   named model input an `@auditor` pass could go check. An unsourced number is fiction with decimal
   points, not analysis (`agents/quant.md §Grounding rule`).
4. **Name the model, defend the choice.** Black-Scholes and Heston are not interchangeable, and
   neither is Vasicek and Nelson-Siegel. State which model was used and why it fits the question
   over its alternatives -- a reader should be able to tell which assumptions are in play without
   asking.

## Building the model

Do the actual computation in `numpy`/`pandas`/`scipy` via `Bash`, lazy-imported the way
`myfi_toolkit.cli` does (`skills/myfi/SKILL.md §The toolkit`) so a trivial lookup never pays a
heavy import cost. Pull every input through the toolkit (`quote`, the `db_*` verbs) rather than
inventing a price, a rate, or a historical series -- the toolkit is the only legitimate data source
this skill's models are allowed to run on.

## Wiring

`agents/quant.md` loads this skill for every modeling unit `@advisor` dispatches to it; the four
references above are what let `@quant`'s Assumptions/Methodology/Results/Caveats report
(`agents/quant.md §The modeling cycle`) name a real model instead of describing a vibe. `@auditor`
(`skills/compliance/SKILL.md`) checks the output this skill informs for a sourced number and a
stated uncertainty exactly as it checks for a disclosed conflict -- a missing confidence interval
is a finding, not a style preference.

## Orienting cold

Landed here with nothing else loaded? You now know: load `QUANT.md` + `MODELS.md` always, add
`PREDICTION.md` + `MICROSTRUCTURE.md` for binary/prediction-market/execution work; the mindset is
distribution over point estimate, price the risk not the level, and every number traces to a
toolkit call or a named model input; and a model is not reported until its assumptions, its
uncertainty band, and its failure modes are all stated alongside the number itself.
