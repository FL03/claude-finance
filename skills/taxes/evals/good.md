# Tax-workflow summary: good

Tax-year summary for client's taxable brokerage account, generated under `/myfi:taxes`.

**Gathered.** Pulled 1099-B (three sales), 1099-DIV (one fund position) via the account snapshot;
current-price context confirmed against `bin/myfi-toolkit quote`.

**Classified.**
- AAPL, 40 shares, bought 2024-11-02, sold 2026-03-14: holding period 16 months, so **long-term**.
- NVDA, 15 shares, bought 2025-12-01, sold 2026-01-08: holding period 38 days, so **short-term**.
- A $1,240 ordinary dividend from the index fund position.

**Routed to forms.** The AAPL and NVDA sales route to **Form 8949**, rolling to **Schedule D**
(split long-term/short-term per the holding periods above); no wash-sale code applies since
neither position was repurchased within 30 days. The dividend routes to **Schedule B** (exceeds
the $1,500 threshold when combined with interest income) sourced from **Form 1099-DIV**.

**Computed.** Estimated long-term gain: $2,150 (AAPL). Estimated short-term loss: -$480 (NVDA);
short-term losses net against short-term gains first, then against long-term. Net taxable gain
picture: **$1,670**, well under the $3,000/year loss-carryforward threshold so no carryforward
applies this year.

**Optimization.** The NVDA short-term loss already offsets part of the AAPL gain; no further
tax-loss harvesting is recommended this year since there is no remaining short-term gain to shelter
and realizing an additional loss would not change the marginal bracket.

**Filing deadline.** Standard individual deadline: **April 15**. No estimated-tax quarterly
payment is triggered since total under-withheld liability is below the safe-harbor threshold.

**Caveat.** This is a structured estimate for filing preparation, not a filed return. A CPA or
enrolled agent should confirm before submission, and any multi-state or foreign-account exposure is
out of scope for this summary.
