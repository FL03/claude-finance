# /myfi:analyze report -- "should I refinance this year?"

## Current position

- Existing mortgage: $312,000 balance, 30-year fixed at 6.75%, originated 22 months ago, 328
  months remaining. Monthly P&I: $2,024.
- `mcp__plugin_myfi_myfi-toolkit__quote` pulled today's par 30-year conforming rate proxy
  (`MBS30Y`): 5.95%. Client's self-reported 760 FICO / 32% DTI qualifies within roughly 0.15pp of
  that par quote.
- Estimated closing costs for a refinance at this balance: $6,800 (title, origination, appraisal),
  from the standard closing-cost model applied to the current balance.

## Recommendation

1. Refinance now into a 30-year fixed at ~6.10% (par proxy + 0.15pp spread). New payment:
   $1,893/month -- a $131/month reduction. Breakeven on the $6,800 closing cost is 52 months
   (4.3 years); a 10+ year hold clears that easily.
2. Pay closing costs from cash on hand rather than rolling them into the new balance, so the
   breakeven math above does not erode.
3. Re-quote in 90 days if the planned hold period shortens -- the breakeven flips unfavorable
   below a ~5-year hold.

## Risks and uncertainty

The 760 FICO / 32% DTI figures are self-reported and unverified by a lender pull, so the actual
quoted rate could differ from the 6.10% par-proxy estimate by more than the assumed 0.15pp spread.
Rates could also fall further in the next few months, in which case waiting captures a better rate
at the cost of the $131/month foregone in the meantime -- a real trade-off, not a reason to delay
indefinitely.

## Next concrete step

Get a formal rate-lock quote from at least two lenders this week to confirm the 6.10% estimate
before committing.
