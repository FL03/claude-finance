# Model writeup: good

`@quant` output for a client considering writing a 45-day covered call on a 500-share AAPL
position, dispatched by `@advisor` under `/myfi:analyze`.

**Assumptions.** Pricing via **Black-Scholes** (`skills/finance/references/MODELS.md
§Black-Scholes`): constant volatility over the option's life, continuous frictionless trading, no
early-exercise premium priced in (American calls on a non-dividend-payer are worth the same as
European per put-call-parity arguments; AAPL's next ex-dividend date falls after this option's
44-day expiry per the account snapshot, so the assumption holds for this specific trade).

**Methodology.** Spot `S = $211.40` and the 45-day at-the-money strike `K = $212.50` both pulled
via `mcp__plugin_myfi_myfi-toolkit__quote AAPL`. Risk-free rate `r = 4.3%` (13-week T-bill, same
toolkit call, `--json` field `risk_free_proxy`). Implied volatility `sigma = 27.8%` backed out of
the venue's quoted 45-day AAPL option mid, not a historical estimate -- historical realized vol
over the trailing 60 days was 24.1%, so the market is pricing in a premium above realized, flagged
below.

**Results.** Call value **$6.85** (Black-Scholes closed form). Greeks: delta 0.52, gamma 0.031,
vega 0.25 (per 1-point change in `sigma`), theta -0.041/day. Premium income if exercised/assigned:
$6.85 x 500 = $3,425, a 1.6% income yield over 45 days on the $211,400 position. **Uncertainty
band:** propagating vega against a +/-3-point implied-vol estimation error (typical bid-ask on
this venue's 45-day AAPL option) gives a call-value range of **$6.10 - $7.60** at roughly one
standard deviation -- report the $6.85 center alongside that range, not alone.

**Caveats.** The 27.8% implied vol already prices in more risk than trailing realized vol, meaning
the strategy is selling into elevated implied vol (favorable for the writer) but also means a
vol-crush assumption is doing real work in the expected-value case -- if realized vol comes in
above 27.8% into expiry (an earnings date falls inside this window per the account calendar), the
assigned-away upside cost exceeds this estimate. This is a Black-Scholes point estimate on implied
vol as of quote time, not a forecast of AAPL's actual 45-day move; a genuine tail scenario (a
market-moving AAPL event) is not priced by this model and would require a jump-diffusion overlay
(`MODELS.md §Merton jump-diffusion`) to capture.
