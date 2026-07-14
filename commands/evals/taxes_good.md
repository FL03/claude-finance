## TAX-YEAR SUMMARY -- 2025 (taxable brokerage + Roth IRA)

**Gather.** Pulled 2025 activity across the client's taxable brokerage and Roth IRA. One
still-open position (NVDA) priced via the toolkit `quote` verb for context; no live position data
was fetched for closed lots, per client-supplied statements only.

**Classify.** Two realized sales: 40 shares AAPL held 14 months (long-term), 15 shares TSLA held 3
months (short-term). $180 in ordinary (non-qualified) dividends from a bond fund. No wash sales
detected -- no repurchase within 30 days of either sale.

**Route to forms.** AAPL and TSLA sales route to Form 8949 (transaction detail), rolling up to
Schedule D. The $180 in ordinary dividends is below the Schedule B reporting threshold, so it
reports directly on Form 1040 line 3b, sourced from the broker's Form 1099-DIV. Roth IRA activity
(one $6,500 contribution) is not taxable and needs no gain/loss form, but is tracked against the
annual contribution limit per Publication 590-A.

**Compute.** AAPL: $2,340 long-term gain. TSLA: -$410 short-term loss. Net: $2,340 LT gain, -$410
ST loss, netting to an estimated $1,930 taxable capital gain at the long-term rate (no carryforward
needed since losses don't exceed gains).

**Optimization.** With the LT/ST split already favorable, the one live opportunity is the NVDA
position: it is 11 months into the holding period. Holding it 4 more weeks past the one-year mark
would convert any gain from ordinary-rate short-term to preferential-rate long-term -- actionable
before the position is closed, not after.

**Filing deadline.** April 15, 2026 for the 2025 tax year (no weekend/holiday shift). No
estimated-tax quarterly payments are owed this cycle since withholding covers ordinary income and
the realized gain is modest relative to the safe-harbor threshold.

**Compliance gate -- cleared.** @auditor reviewed the form citations (8949/Schedule D, 1099-DIV
threshold) and the numeric claims (holding periods, gain/loss math) against the source statements
and skills/taxes/SKILL.md's baseline; no jurisdiction beyond US-federal retail is touched, no
scope-creep beyond the documented baseline, PASS on first pass.

**Professional-review caveat.** This is a structured checklist for filing software or a preparer,
not a filed return. Multi-state filing questions (the client mentioned a Q3 relocation) are flagged
as out-of-scope for this baseline and routed to a preparer rather than estimated here.

Report written to `.myfi/reports/taxes-2025-20260115T090000Z.md`.
