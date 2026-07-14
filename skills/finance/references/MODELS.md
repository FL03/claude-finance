---
description: The pricing, risk, and portfolio model zoo for myfi modeling tasks -- Black-Scholes, Heston, Merton (jump-diffusion and structural credit), term-structure models (Vasicek, CIR, Nelson-Siegel), factor models (CAPM, Fama-French, APT), Monte Carlo methods, and backtesting discipline -- each with when-to-use, assumptions, and named failure modes. Load always, alongside QUANT.md, for any modeling task.
---

# MODELS -- the model zoo

Every entry below follows the same shape: what the model is for, what it assumes, and where it
breaks. State all three when you use one -- naming a model without its assumptions is the same
error as reporting a price without a confidence interval (`QUANT.md §The discipline`).

## Option pricing

### Black-Scholes

**Use for:** European-style option pricing and as the market's quoting convention for implied
volatility, even when its own assumptions are known to be wrong.

**Formula (call):**

```
C = S * N(d1) - K * e^(-rT) * N(d2)
d1 = ( ln(S/K) + (r + sigma^2/2) * T ) / ( sigma * sqrt(T) )
d2 = d1 - sigma * sqrt(T)
```

Put value follows from put-call parity: `P = C - S + K * e^(-rT)`.

**Assumptions:** constant volatility `sigma`, constant risk-free rate `r`, no dividends (or a
known continuous dividend yield folded into `r`), the underlying follows GBM (log-normal returns,
`QUANT.md §GBM`), frictionless markets (no transaction costs, no taxes, unlimited short-selling,
continuous trading), European exercise only.

**Failure modes:**

- **Volatility smile/skew.** Implied volatility varies by strike and maturity in real markets,
  directly contradicting the constant-`sigma` assumption. A single Black-Scholes `sigma` cannot
  simultaneously match an entire options chain -- this is the model telling you it is wrong, not a
  quoting quirk to ignore.
- **Fat-tail mispricing.** Log-normal returns underweight large moves (`QUANT.md §Fat tails`), so
  Black-Scholes underprices deep out-of-the-money options relative to what jump/fat-tail models
  imply.
- **Discrete hedging error.** The model's replication argument assumes continuous rebalancing;
  real hedging is discrete, so realized P&L on a "delta-hedged" book has gamma-driven noise the
  model treats as zero.
- **American exercise / dividends.** Early-exercise value and discrete dividend dates need a
  binomial/trinomial tree or finite-difference PDE solve, not the closed form above.

### Heston (stochastic volatility)

**Use for:** pricing when the volatility smile itself matters (skew-sensitive exotics, anything
priced across a full options chain).

```
dS_t = mu * S_t dt + sqrt(v_t) * S_t dW1_t
dv_t = kappa * (theta - v_t) dt + xi * sqrt(v_t) dW2_t
corr(dW1_t, dW2_t) = rho
```

`v_t` is instantaneous variance, mean-reverting to long-run level `theta` at speed `kappa`; `xi`
is vol-of-vol; `rho` (typically negative for equities -- the "leverage effect": prices down, vol
up) generates skew directly from the model rather than needing a separate ad-hoc adjustment.
Priced via the characteristic function and Fourier inversion (semi-closed-form), not a plain
closed form.

**Assumptions:** still continuous paths (no jumps), correlation and vol-of-vol constant, requires
the **Feller condition** `2 * kappa * theta >= xi^2` for `v_t` to stay strictly positive --
routinely violated by calibrated parameters in practice, which is itself a documented model
weakness.

**Failure modes:** five-plus parameters make calibration ill-posed (many parameter sets fit the
same options chain about equally well -- an underdetermined inverse problem); still cannot fully
capture short-dated skew without adding jumps (see Merton below); Feller-condition violation means
the simulated variance process can be forced to zero and reflected, an artifact of the
discretization scheme rather than the model's economics.

## Jump-diffusion and structural credit

### Merton jump-diffusion

**Use for:** pricing gap/event risk (earnings, binary catalysts) that pure diffusion cannot
represent -- sudden discontinuous moves, not just fast continuous ones.

```
dS_t / S_t = (mu - lambda * k) dt + sigma dW_t + dJ_t
```

`J_t` is a compound Poisson process with intensity `lambda` (expected jumps per year) and
log-jump sizes typically drawn `~ N(mu_J, sigma_J^2)`; `k = E[e^{jump} - 1]` is the compensator
that keeps the drift risk-neutral-consistent. Produces fatter, more realistic tails than
Black-Scholes and prices short-dated skew that pure-diffusion models understate.

**Failure modes:** `lambda`, jump mean, and jump volatility are hard to identify separately from
`sigma` using price history alone -- multiple parameter combinations produce similar historical
fit, so calibration leans on options data more than the return series.

### Merton structural credit model

**Use for:** default-probability and credit-spread estimation from equity-observable inputs
(applies the option-pricing machinery to a firm's balance sheet -- the basis for KMV-style
distance-to-default models).

**Setup:** firm asset value `V_t` follows GBM; equity is modeled as a call option on `V_t` with
strike equal to the face value of debt `D` at debt maturity `T`. Distance-to-default scales with
`ln(V_0/D)` relative to asset volatility and drift; default probability follows from the same
`N(d2)`-style term as Black-Scholes, read as a risk-neutral default probability.

**Assumptions:** single, discrete zero-coupon debt maturity (real firms have layered, staggered
debt), asset value and its volatility are not directly observable and must be inferred from equity
value and equity volatility (an inverse problem, not a direct input).

**Failure modes:** the **credit-spread puzzle** -- Merton's own math implies short-maturity credit
spreads should go to zero as `T -> 0`, but observed short-dated spreads do not, because the model
omits jump risk, liquidity premia, and non-Gaussian asset-value moves. Cite this by name when using
a plain Merton model for near-term credit risk; it is a known, published gap, not a modeling
oversight to paper over.

## Term-structure models

| Model | SDE / form | Positivity | Closed form | Notes |
|---|---|---|---|---|
| Vasicek | `dr = a(b - r)dt + sigma dW` | Can go negative | Yes, affine | Mean-reverting Gaussian short rate; negative rates were long treated as a flaw, less so post-2010s zero/negative-rate regimes |
| CIR | `dr = a(b - r)dt + sigma*sqrt(r) dW` | Non-negative if `2ab >= sigma^2` (Feller) | Yes, affine | Same mean-reversion as Vasicek, `sqrt(r)` diffusion keeps rates non-negative when the Feller condition holds |
| Nelson-Siegel | `y(tau) = b0 + b1*(1-e^(-tau/lam))/(tau/lam) + b2*[(1-e^(-tau/lam))/(tau/lam) - e^(-tau/lam)]` | N/A | Curve-fit, not an SDE | Parametric yield-curve fit (level `b0`, slope `b1`, curvature `b2`); Nelson-Siegel-Svensson adds a second curvature term for more flexible shapes |

**Use Vasicek/CIR** to model the short rate's *dynamics* (simulate forward, price rate
derivatives); **use Nelson-Siegel** to *fit and interpolate* an observed curve at a point in time
(what central banks publish) -- it is not a dynamic risk model unless embedded in a time-varying
framework (Diebold-Li).

**Failure modes:** single-factor Vasicek/CIR cannot fit curves that twist (a steepening short end
with a flattening long end) -- multi-factor extensions exist precisely because one factor
under-fits real curve shapes; Nelson-Siegel is a snapshot least-squares fit with no built-in
no-arbitrage guarantee across maturities or over time.

## Factor models

| Model | Return equation | Factors |
|---|---|---|
| CAPM | `E[R_i] = R_f + beta_i * (E[R_m] - R_f)` | Market only |
| Fama-French 3-factor | adds `SMB` (size) and `HML` (value) to CAPM | Market, size, value |
| Fama-French 5-factor | adds `RMW` (profitability) and `CMA` (investment) | Market, size, value, profitability, investment |
| APT | `E[R_i] = R_f + sum_k( beta_ik * lambda_k )` | Unspecified -- any priced risk factors, derived from no-arbitrage rather than market equilibrium |

**Use for:** portfolio attribution (how much of a return came from market exposure vs
size/value/profitability tilts) and cost-of-capital estimates.

**Failure modes:** CAPM's single beta empirically explains little of the cross-section of returns
(the "low-beta anomaly" -- low-beta stocks earn more than CAPM predicts); factor loadings drift
over time, so a beta estimated on trailing data is already stale; the published "factor zoo"
(hundreds of claimed return factors) has a real overfitting problem -- data-mined factors that
worked in one sample often fail out-of-sample, so prefer the named, widely-replicated factors
above over an unfamiliar one without independent replication; APT's silence on which factors to
use is a feature (no dependence on CAPM's market-equilibrium assumptions) and a liability (the
factor choice itself becomes a modeling decision to defend).

## Monte Carlo

**Use for pricing:** simulate the underlying's path under the risk-neutral measure (`QUANT.md
§Risk-neutral vs physical measure`), evaluate the payoff on each path, average, and discount --
the general-purpose method when no closed form exists (path-dependent payoffs, multiple
correlated underlyings, Heston/jump-diffusion dynamics).

**Use for risk:** simulate the P&L distribution directly (historical, bootstrapped, or
model-based paths) to get VaR/ES empirically without assuming a parametric return distribution --
the right default when `QUANT.md §Fat tails` makes a normal-distribution VaR suspect.

**Variance reduction** (use before just cranking up path count): antithetic variates (pair each
path with its mirror-image innovations), control variates (net out the simulation error of a
correlated instrument with a known closed-form price), importance sampling (oversample the tail
region for rare-event/VaR estimation, reweight), quasi-Monte Carlo (low-discrepancy sequences,
e.g. Sobol, for faster convergence on smooth low-dimensional integrands).

**Failure modes:** standard Monte Carlo error shrinks only as `O(1/sqrt(N))` -- quadrupling `N`
halves the error, an expensive way to buy precision without variance reduction; naive
Euler-Maruyama time-stepping has `O(sqrt(dt))` weak error for path-dependent products, so
discretization bias needs checking against a finer grid or a better scheme (Milstein) before
trusting a path-dependent price; tail risk metrics (VaR/ES at the 99th percentile and beyond) are
inherently rare-event estimates and need either very large `N` or importance sampling -- a naive
10,000-path VaR at the 99.9th percentile is estimated from about ten tail observations and its own
confidence interval (`QUANT.md §Attaching an uncertainty band`) should say so.

## Backtesting discipline

A backtest is a model like any other -- it needs its own assumptions stated and its own failure
modes checked before its Sharpe ratio is reported as a result.

- **Look-ahead bias.** Using information not actually available at decision time -- point-in-time
  financial-statement data restated later, a same-day close price used to trigger a same-day
  entry, survivor-biased universes (see below). Check every data join for a timestamp that could
  leak the future.
- **Survivorship bias.** Backtesting only currently-listed constituents silently excludes delisted
  and failed names, inflating historical returns. Use a point-in-time constituent list.
- **Overfitting / data snooping.** Too many free parameters or too many strategy variants tested
  against one sample inflates the in-sample Sharpe ratio; correct with an explicit train/test
  split, walk-forward (rolling) validation, and a multiple-testing-adjusted ("deflated") Sharpe
  ratio rather than reporting the single best variant found.
- **Transaction costs.** Omitting spread, slippage, and market impact (`MICROSTRUCTURE.md`)
  overstates returns, most severely for high-turnover strategies -- a backtest without explicit
  cost assumptions is a paper return, not a return.
- **Out-of-sample discipline.** Reserve a true holdout the strategy's parameters never touch;
  reusing the "test" set to re-tune after a disappointing result turns it back into training data.

Report a backtest's Sharpe/return figures the same way any other model output is reported
(`QUANT.md §The discipline`): the central estimate, its dispersion across the walk-forward folds
or bootstrap resamples, and which of the failure modes above were checked and how.
