---
name: taxes
description: Tax-workflow knowledge for /myfi:taxes, the document-grounded pipeline from raw account activity to a filing-actionable summary. Covers income/gain classification, the specific IRS forms and publications each classification routes to, cost-basis and holding-period mechanics, common optimization moves (tax-loss harvesting, asset location, retirement-contribution timing), and the filing-deadline discipline. Load before running /myfi:taxes or before @worker/@quant produce any tax-adjacent output.
---

# TAXES: tax-workflow knowledge

This skill exists for `/myfi:taxes` and any agent producing tax-adjacent output. It is a workflow
and a form map, not a substitute for a CPA or enrolled agent. Every output this skill informs
closes with that caveat, and every claim traces to a specific IRS form or publication rather than a
vague "consult your tax situation."

## The workflow, end to end

1. **Gather.** Pull the client's account activity for the tax year via the toolkit
   (`bin/myfi-toolkit quote` for current pricing context, plus whatever position/transaction data
   the account snapshot carries; see `skills/myfi/SKILL.md` for the toolkit surface). Identify
   every account type touched: taxable brokerage, traditional/Roth IRA, 401(k), HSA. Each has a
   different tax treatment for the same underlying transaction.
2. **Classify.** Sort activity into the categories that drive different forms: realized capital
   gains/losses (short-term vs long-term, by holding period, more or less than one year),
   ordinary dividends vs qualified dividends, interest income, wash sales, and any retirement
   account contributions or distributions.
3. **Route to forms.** Each classification has a specific documented home:
   - Realized capital gains/losses route to **Form 8949** (transaction detail) rolling up to
     **Schedule D** (summary), informed by broker **Form 1099-B**.
   - Dividend and interest income route to **Schedule B** when it exceeds the reporting threshold,
     sourced from **Form 1099-DIV** / **1099-INT**.
   - Wash-sale adjustments and cost-basis mechanics reference **IRS Publication 550** (Investment
     Income and Expenses); the wash-sale disallowed-loss adjustment is reported on Form 8949 with
     code "W".
   - Traditional IRA / 401(k) contributions and deduction limits reference **IRS Publication
     590-A**; distributions reference **Publication 590-B** and **Form 1099-R**.
   - Qualified small business stock, straddles, and other less-common instruments are flagged as
     out-of-scope for this skill's baseline and routed to a human preparer rather than guessed.
4. **Compute.** Net short-term and long-term gains/losses separately (different rates apply); apply
   the $3,000/year capital-loss deduction limit against ordinary income with the remainder carried
   forward; sum the picture into an estimated taxable-income delta, not a final filed number. This
   skill informs a workflow; it does not replace filing software or a preparer's sign-off.
5. **Identify optimization opportunities**, each grounded in the specific mechanism it relies on:
   - **Tax-loss harvesting**: realizing a loss to offset a gain, while respecting the 30-day
     wash-sale window (buying a "substantially identical" security within 30 days before or after
     the sale disallows the loss).
   - **Asset location**: holding tax-inefficient assets (high-turnover funds, taxable bonds) in
     tax-advantaged accounts and tax-efficient assets (index funds, municipal bonds) in taxable
     accounts.
   - **Long-term holding-period timing**: a position approaching the one-year mark may be worth
     holding past it to convert a short-term gain (taxed as ordinary income) into a long-term gain
     (preferential capital-gains rate).
   - **Retirement-contribution timing**: traditional account contributions before the filing
     deadline can still reduce the prior tax year's liability, within the applicable limit.
6. **Flag filing deadlines.** The standard individual filing deadline is **April 15** (the next
   business day if it falls on a weekend/holiday); estimated-tax quarterly deadlines fall
   mid-April, mid-June, mid-September, and mid-January of the following year for anyone with
   under-withheld income (for example, realized capital gains or self-employment income). An
   extension (**Form 4868**) moves the *filing* deadline, never the *payment* deadline. This
   distinction is worth stating explicitly since it is a common and costly point of confusion.
7. **Recommend professional review.** The workflow output is a structured summary and checklist for
   a preparer, or filing software, not a substitute for either. Anything outside the baseline above
   (multi-state filings, foreign accounts/FBAR, business income, AMT edge cases) is named
   explicitly as out-of-scope rather than silently omitted.

## Filing-actionable output shape

A `/myfi:taxes` output that follows this workflow should let the client (or their preparer) act
without a second research pass: which forms apply, which 1099s to pull, the estimated
short-term/long-term gain split, one or two concrete optimization moves with their deadline, and
the filing deadline itself stated plainly. "You may owe capital gains tax" is not actionable.
"Schedule D shows an estimated $2,400 long-term gain from the March AAPL sale; Form 8949 code is
not needed since there's no wash sale; filing deadline is April 15" is.

## Document-grounded, not invented

Every numeric threshold or rule cited above (the $3,000 loss-deduction cap, the 30-day wash-sale
window, the one-year long-term holding threshold, the April 15 baseline deadline) is drawn from the
named IRS form or publication, not estimated. When a client's situation raises a question this
skill's baseline does not cover, the correct output names the gap and routes to a preparer. It
does not extrapolate a plausible-sounding number.

## Wiring

`/myfi:taxes` loads this skill for its pipeline; `@auditor` loads `skills/compliance/SKILL.md`
alongside it for the compliance gate before any tax-workflow report ships. A recurring gap this
skill's baseline does not cover (a new form, a new instrument class) is exactly the kind of pattern
the `IMPROVE` loop (`skills/improve/SKILL.md`) harvests into a stored prior for next time.

## Orienting cold

Landed here with nothing else loaded? You now know the seven-step workflow (gather, classify, route
to forms, compute, identify optimizations, flag deadlines, recommend professional review), the
specific forms each classification routes to (8949/Schedule D for gains, Schedule B for dividends/
interest, Publication 550/590-A/590-B for the reference mechanics), the wash-sale and holding-period
rules that drive optimization, and that every output closes with a professional-review caveat and
routes true out-of-scope cases to a human rather than guessing.
