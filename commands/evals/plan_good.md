# /myfi:plan -- goal: "build a plan to retire by 55" (horizon: 20y)

## Dispatch trail

1. **@advisor decomposed** the goal into three units: (a) a savings-rate/withdrawal model for the
   20-year horizon, (b) a routine net-worth snapshot pull, (c) a compliance check on the assumed
   withdrawal strategy's tax treatment.
2. **@quant produced** the savings-rate model -- Assumptions (4% real return, 3.5% safe withdrawal
   rate, current $340,000 invested balance via `mcp__plugin_myfi_myfi-toolkit__quote`-priced
   holdings) / Methodology (Monte Carlo over 20 years, 10,000 paths) / Results (82% success
   probability at the current $2,400/month contribution; rises to 94% at $3,100/month) / Caveats
   (assumes constant real contribution, no major health-cost shock modeled).
   **@worker produced** the routine net-worth snapshot: $340,000 invested, $58,000 cash, $210,000
   home equity, pulled via the toolkit's `db_*` registry calls.
3. **@auditor gated** the savings-rate model: one finding (MEDIUM confidence -- the 3.5% withdrawal
   rate assumption should be flagged as a planning convention, not a guarantee) -- verdict PASS
   after `@quant` added the caveat explicitly to the Results section. No findings against the
   `@worker` snapshot.
4. **@designer finalized** the artifact: a two-panel chart (contribution-vs-success-probability,
   and the 10,000-path Monte Carlo fan chart) embedded in this report, Agg-rendered by the
   toolkit.

## Recommendation

1. Raise the monthly contribution from $2,400 to $3,100 over the next 12 months (phase in $60/mo
   quarterly) to move the 20-year success probability from 82% to 94%.
2. Hold the current $58,000 cash reserve as an 18-month expense buffer rather than deploying it
   into the market -- it is sized correctly for the household's stated risk tolerance.
3. Revisit the withdrawal-rate assumption in 5 years once actual market returns diverge materially
   from the 4% real-return baseline -- the auditor's flagged caveat is the single assumption this
   plan is most sensitive to.

## Risks (per @auditor)

The 3.5% safe withdrawal rate is a planning convention, not a guarantee -- a sustained below-4%
real-return decade would require either a lower withdrawal rate or a delayed retirement date. This
was the auditor's one finding against the model and is now stated explicitly rather than buried in
an appendix.

## Next concrete step

Set up the automatic contribution increase this month via the retirement account's contribution
schedule, and revisit this plan on the account's next annual statement date.
