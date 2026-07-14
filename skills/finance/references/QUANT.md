---
description: Quantitative foundations for any myfi modeling task -- the distribution-over-point-estimate discipline, the stochastic calculus a pricing model rests on (Brownian motion, Ito's lemma, GBM, risk-neutral vs physical measure), risk theory (volatility, VaR vs Expected Shortfall, Greeks, fat tails), and how to attach an uncertainty band to a result. Load always, alongside MODELS.md, for any modeling task.
---

# QUANT -- foundations

This file is the load-bearing floor under every model in `MODELS.md`. Skip it and a Black-Scholes
number or a factor-model beta is just a formula plugged in without knowing what it assumes or
what it costs to be wrong.

## The discipline: distribution, not point estimate

A quant does not predict a number. A quant prices a distribution -- mean, variance, and tail -- and
reports the point estimate as one summary of that distribution, never as the whole answer. "AAPL
options imply 28% annualized volatility" is a fact about a market input. "The position has 3%
expected return" with nothing else is a guess wearing a number's clothes.

The concrete rule: every quantitative output this skill informs states three things or it is not
done --

1. **The central estimate.** The number itself: a price, a probability, an expected return.
2. **A dispersion measure.** Standard deviation, a confidence/credible interval, or a quantile
   range around the central estimate -- not "roughly," an actual number derived from the model or
   the data.
3. **The tail.** What happens in the bad 1-in-20 or 1-in-100 case, and whether the model's own
   assumptions hold up there (most don't -- see Fat tails below).

If a step in the modeling cycle (`agents/quant.md §The modeling cycle`) cannot produce all three,
the honest move is to say so explicitly, not to round up to a false precision.

## Stochastic calculus essentials

### Brownian motion (Wiener process)

A standard Brownian motion `W_t` satisfies: `W_0 = 0`, independent increments, `W_t - W_s ~
N(0, t-s)` for `t > s`, and continuous (but nowhere differentiable) paths. It is the noise source
every diffusion model in `MODELS.md` builds on. Its defining, non-intuitive property: quadratic
variation is deterministic, `(dW_t)^2 = dt`. That single identity is why calculus on `W_t` needs
its own chain rule.

### Ito's lemma

For a process `dX_t = a(X_t, t) dt + b(X_t, t) dW_t` and a twice-differentiable function `f(X_t,
t)`, Ito's lemma gives:

```
df = ( df/dt + a * df/dx + (1/2) b^2 * d^2f/dx^2 ) dt + b * df/dx * dW_t
```

The `(1/2) b^2 * d^2f/dx^2` term is the entire point: it is the correction ordinary calculus
misses because `(dW_t)^2 = dt` rather than `0`. Every closed-form diffusion result in this skill
(GBM's log, Black-Scholes' PDE, Vasicek/CIR's bond-price ODEs) is Ito's lemma applied once to the
right function of the state variable.

### Geometric Brownian motion (GBM)

`dS_t = mu * S_t dt + sigma * S_t dW_t`. Apply Ito's lemma to `f(S) = ln(S)`:

```
d(ln S_t) = (mu - sigma^2 / 2) dt + sigma dW_t
```

so `ln S_t` is normal and:

```
S_t = S_0 * exp( (mu - sigma^2/2) * t + sigma * W_t )
```

The `- sigma^2/2` drift adjustment (the "Ito correction") is a direct consequence of the lemma
above, not an approximation -- forgetting it is a common, checkable error (`@auditor` should
falsify any GBM derivation that drops it).

### Risk-neutral vs physical measure

The physical (real-world, `P`) measure describes what actually happens -- the `mu` an analyst
estimates from historical returns. Pricing does not use `mu`. Under no-arbitrage, there exists an
equivalent martingale measure `Q` under which every discounted tradable asset price is a
martingale; Girsanov's theorem states the change of measure shifts the Brownian motion by the
market price of risk `(mu - r) / sigma`:

```
dW^Q_t = dW^P_t + ( (mu - r) / sigma ) dt
```

so under `Q` the drift on a traded asset becomes the risk-free rate `r`, regardless of the asset's
real-world expected return. This is why Black-Scholes prices a call with `r`, never with an
analyst's view of `mu` -- the model prices what a *replicating portfolio* costs, not what the
stock is expected to return. Conflating `P` and `Q` (using a real-world return forecast inside a
pricing formula) is one of the most common quant errors and an automatic `@auditor` finding.

## Risk theory

### Volatility

Annualized volatility from daily returns: `sigma_annual = sigma_daily * sqrt(252)` (252 trading
days is the standard convention; use the venue's actual trading-day count if it differs).
**Realized volatility** is computed from historical returns; **implied volatility** is backed out
of an observed option price by inverting a pricing model (Black-Scholes by market convention, even
where the model's own assumptions are known to be wrong -- implied vol is a market-quoting
convention as much as a forecast). The two disagreeing is not a bug, it is the volatility risk
premium.

### VaR vs Expected Shortfall (CVaR)

**Value at Risk** at confidence level `alpha` is the loss quantile:

```
VaR_alpha(L) = inf { l : P(L > l) <= 1 - alpha }
```

i.e. "the loss you will not exceed with probability `alpha`." VaR says nothing about *how bad* the
tail beyond that quantile is, and it is **not a coherent risk measure** -- it fails subadditivity
in general (a portfolio's VaR can exceed the sum of its parts' VaR), which breaks the
diversification argument a risk measure is supposed to support.

**Expected Shortfall** (a.k.a. CVaR, Conditional VaR) fixes this by averaging the tail instead of
picking one quantile:

```
ES_alpha(L) = E[ L | L >= VaR_alpha(L) ]
```

ES is coherent (monotone, subadditive, positively homogeneous, translation-invariant) and is the
Basel-III-era standard for regulatory market-risk capital precisely because VaR's
non-subadditivity let institutions understate diversified risk. Default to reporting ES alongside
or instead of VaR whenever the toolkit's return sample supports it.

### Greeks as risk sensitivities

Greeks are partial derivatives of a derivative's value `V` with respect to a pricing input --
each one is a risk exposure, not a curiosity:

| Greek | Definition | Risk it measures |
|---|---|---|
| Delta | `dV/dS` | Exposure to a small move in the underlying |
| Gamma | `d^2V/dS^2` | How fast delta itself changes -- convexity/re-hedging risk |
| Vega | `dV/d(sigma)` | Exposure to implied volatility changing |
| Theta | `-dV/dt` | Value lost to time decay per unit time, hedge held fixed |
| Rho | `dV/dr` | Exposure to the risk-free rate changing |

A reported option price with no delta/gamma/vega alongside it tells `@advisor` the price but
hides the risk that price carries -- report the Greeks whenever an options position is in scope.

### Moments, tails, fat tails

Beyond mean and variance: **skewness** (third standardized moment) measures asymmetry -- equity
index returns are typically left-skewed (crashes are sharper than rallies). **Kurtosis** (fourth
standardized moment) measures tail weight; a normal distribution has kurtosis 3, and **excess
kurtosis** (`kurtosis - 3`) above zero means fatter-than-normal tails (leptokurtic).

Financial return series are reliably leptokurtic -- large moves happen far more often than a
Gaussian model predicts. A Student-t distribution (finite degrees of freedom) or an
extreme-value/power-law tail fits realized return tails better than the normal that GBM assumes.
Practical consequence: **a VaR or Greek computed under a normal/lognormal assumption
systematically understates tail risk**; state this as a caveat whenever the model in use assumes
normality, and prefer a fat-tailed distribution or historical/Monte Carlo simulation (`MODELS.md
§Monte Carlo`) for tail-sensitive risk numbers.

## Attaching an uncertainty band to any output

No number leaves `@quant` without one of the following, chosen by how the number was produced:

- **Analytic/parametric.** If the model has closed-form standard errors (e.g., a regression beta,
  a Black-Scholes price as a function of an estimated `sigma`), propagate the input's standard
  error into an output confidence interval.
- **Bootstrap.** Resample the historical return series (with replacement) many times, recompute
  the statistic each time, and report the empirical spread of the resampled estimates as the
  interval. Cheap, assumption-light, and directly usable with `numpy`/`pandas`.
- **Monte Carlo standard error.** For a simulated price or risk metric, report the simulation
  standard error (`sigma_sim / sqrt(N)`) alongside the estimate -- more paths shrinks the band,
  and the band is exactly how a reader knows whether `N` was large enough.
- **Bayesian credible interval.** Where a prior is available (e.g., a Beta-Binomial posterior for
  a hit-rate estimate), report the posterior interval directly -- this is the natural fit for
  `PREDICTION.md`'s calibration work.

Whichever method, name it. "95% CI: [x, y] via 10,000-path Monte Carlo, SE = z" is traceable and
falsifiable by `@auditor`; "roughly x to y" is not.
