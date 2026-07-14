# Compliance review: good

`@auditor` pass over `@advisor`'s recommendation to move a client from a target-date fund into an
actively managed sector fund the advisor's own firm receives a distribution fee from.

**Scope assumed.** US-federal baseline (Reg BI / SEC fiduciary standard), retail brokerage
account, single-state client (California). State-specific blue-sky rules beyond the federal
baseline are out of scope for this pass and are flagged below, not silently cleared.

**Finding 1, standard-of-care mismatch (HIGH).** Hypothesis: the report reads as fiduciary-level
advice ("this is in your best interest") but the advisor is compensated as a broker-dealer, which
is governed by Reg BI's suitability-plus-Care-Obligation standard, not a fiduciary duty of loyalty.
Falsification: if the advisor is dually registered as an RIA for this account, the fiduciary framing
is correct and this finding is withdrawn. Confidence: medium, pending account-registration
confirmation.

**Finding 2, undisclosed conflict (HIGH).** Hypothesis: the report never states that the firm
receives a distribution fee from the recommended fund, which Reg BI's Disclosure and Conflict-of-
Interest obligations both require. Falsification: if the fee disclosure appears in an attached
document referenced but not shown here, this finding is withdrawn. Confidence: high, since the
report text itself contains no fee disclosure of any kind.

**Out of scope, flagged not cleared.** This pass does not evaluate California-specific investment
adviser rules or ERISA status if this account is plan-linked; a licensed compliance officer should
confirm both before the recommendation proceeds. Verdict: REDO. Finding 2 must be resolved before
this report ships to the client.
