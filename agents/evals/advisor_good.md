# Advisory report — client goal: "should I refinance my mortgage this year?"

## Current position

- Existing mortgage: $312,000 balance, 30-year fixed at 6.75%, originated 22 months ago, 328
  months remaining. Monthly P&I: $2,024.
- `mcp__plugin_myfi_myfi-toolkit__quote` pulled today's par 30-year conforming rate proxy
  (`MBS30Y`): 5.95%. Client's credit profile (self-reported 760 FICO, 32% DTI) qualifies for
  rates within ~0.15pp of that par quote per `@quant`'s dispatched analysis.
- Estimated closing costs for a refinance at this balance: $6,800 (title, origination, appraisal),
  per `@quant`'s toolkit-grounded cost model.

## Recommendation

1. Refinance now into a 30-year fixed at ~6.10% (par proxy + 0.15pp spread). New payment:
   $1,893/month — a $131/month reduction. Breakeven on the $6,800 closing cost is 52 months
   (4.3 years); the client's stated horizon (staying in the home 10+ years) clears that easily.
2. Do not roll the closing costs into the loan balance — pay them from the existing $22,000 cash
   reserve identified in the client's account snapshot, so the new balance doesn't grow and the
   breakeven math above holds without erosion.
3. Re-quote in 90 days if the client's timeline shortens (job relocation, planned sale) — the
   breakeven math flips unfavorable below a ~5-year hold, and that is the single assumption this
   entire recommendation rests on.

## Risks and uncertainty

`@auditor` verified the rate quote against the toolkit source (PASS, no findings). Two risks
remain outside the toolkit's reach: (1) rates could fall further in the next few months, in which
case waiting captures a better rate at the cost of ~$131/month foregone savings while waiting —
this is a real trade-off, not a reason to delay indefinitely; (2) the 760 FICO and 32% DTI are
self-reported and unverified by a lender pull, so the actual quoted rate could differ from the
par-proxy estimate by more than the assumed 0.15pp spread.

## Next concrete step

Get a formal rate lock quote from at least two lenders this week to confirm the 6.10% estimate
before committing; revisit this recommendation if the client's expected hold period changes.
