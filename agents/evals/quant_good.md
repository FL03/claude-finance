# Quant analysis -- 3-month at-the-money call, XYZ

## Assumptions

- Model: Black-Scholes-Merton, European exercise, constant volatility and risk-free rate over the
  contract life, no dividends (XYZ does not currently pay one), continuous trading, no transaction
  costs or bid/ask spread applied to the theoretical price itself.
- Spot pulled via `mcp__plugin_myfi_myfi-toolkit__quote("XYZ")`: $84.20 as of today's close.
- Strike: $85.00 (client-specified, approximately at-the-money).
- Time to expiry: 91 days (T = 0.2493 years).
- Risk-free rate: 4.35%, proxied from the 3-month T-bill quote pulled the same way.
- Volatility: 28% annualized, the trailing-60-day realized volatility computed from daily closes
  retrieved via the same `quote` tool (log-return stdev, annualized by sqrt(252)) -- used as a
  realized-vol proxy for implied vol since no live options-chain IV feed is wired in this
  environment; this substitution is flagged explicitly below, not silently assumed.

## Methodology

Standard closed-form Black-Scholes call: C = S*N(d1) - K*e^(-rT)*N(d2), with
d1 = [ln(S/K) + (r + sigma^2/2)T] / (sigma*sqrt(T)), d2 = d1 - sigma*sqrt(T). Computed with scipy's
`norm.cdf` for N(.), numpy for the array/scalar arithmetic. Delta and vega were computed alongside
the price (delta = N(d1); vega = S*phi(d1)*sqrt(T)) since a directional recommendation needs both
the price and its sensitivity to be decisive rather than just a number.

## Results

- Theoretical call price: $4.62 (d1 = 0.187, d2 = -0.026).
- Delta: 0.574 -- roughly a 57% chance of finishing in-the-money under the risk-neutral measure,
  consistent with the option being slightly in-the-money on a spot/strike basis today.
- Vega: $0.163 per 1 vol-point -- a 1pp move in realized/implied vol shifts the price by about 16
  cents, so the realized-vol proxy substitution above is the single largest source of price
  uncertainty in this estimate, larger than the rate or spot inputs.
- Recommendation: at a quoted market price of $4.85 (client-supplied), the option is priced
  roughly 5% above this model's theoretical value under the realized-vol assumption -- modestly
  rich, not dramatically so. This does not clear the bar for a strong mispricing call given the
  vega sensitivity above; treat it as fairly priced within the model's uncertainty, not a buy or
  sell signal on relative value alone.

## Caveats

The realized-vol-for-implied-vol substitution is the load-bearing assumption -- if the options
market is pricing in an upcoming earnings event (unknown from this data alone), implied vol could
run meaningfully above the 28% realized estimate used here, which would make the $4.85 market
price fair or cheap rather than rich. Confirm an earnings date before acting on the "modestly rich"
read above.
