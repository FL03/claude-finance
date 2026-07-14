---
name: compliance
description: Local-law and regulatory knowledge for the myfi flock's adversarial reviewer. Covers the US-federal baseline an @auditor pass checks (suitability vs fiduciary duty, Reg BI, disclosure, KYC/AML basics, insider trading/MNPI, marketing rules, recordkeeping) and the jurisdiction-honesty discipline that keeps every verdict inside its actual authority. Load before any @auditor compliance pass, and before /myfi:taxes or /myfi:trade run through their compliance gate.
---

# COMPLIANCE: regulatory knowledge for the adversarial reviewer

This skill exists for `@auditor`. It does not replace a licensed compliance officer or attorney;
it gives the auditor a concrete, checkable baseline to run a Hypothesis+Falsification+Confidence
pass against, and the discipline to say "outside my jurisdiction" instead of guessing.

## Scope: what this skill actually knows

The working baseline is **US-federal, retail-investing-adjacent**: the rules that show up most
often when a flock agent produces advice, a trade thesis, or a tax-adjacent report for an
individual client. It is explicitly not a substitute for state-level securities law (blue-sky
rules vary by state), ERISA plan-specific rules, cross-border tax treaties, or any non-US
jurisdiction. When a report's client, account, or transaction touches a jurisdiction this skill
does not cover, the correct `@auditor` verdict is a LOW-confidence `## Open questions` note, never
a silent PASS.

## The checklist an @auditor pass runs

1. **Standard of care.** Does the output claim or imply a fiduciary standard (SEC/DOL fiduciary
   rule, RIA duty of loyalty and care) when it is only offering suitability-level guidance
   (broker-dealer Regulation Best Interest, Reg BI)? Mixing the two is a common and material error;
   flag any recommendation that does not name which standard it is operating under.
2. **Disclosure.** Are fees, conflicts of interest, and the basis for a recommendation (for
   example, "this fund pays a higher commission") stated, not buried or omitted? Reg BI's Care,
   Disclosure, Conflict of Interest, and Compliance obligations are the four buckets to check
   against.
3. **Suitability grounding.** Does the recommendation tie back to the client's actual stated goal,
   time horizon, and risk tolerance (captured earlier in the flock's dispatch), or is it generic
   "markets go up" boilerplate that would suit any client identically? Generic boilerplate fails
   suitability even when every individual fact in it is technically true.
4. **KYC/AML basics.** Any account-opening or money-movement language names the standard baseline
   (identity verification, source-of-funds awareness) rather than skipping straight to execution.
5. **Insider trading / MNPI.** No output may use or imply the use of material non-public
   information. If a data source's provenance is unclear, that is itself a finding, not something
   to wave past.
6. **Market manipulation.** No output may recommend or describe wash trading, spoofing, layering,
   or pump-style coordinated promotion. This applies with extra weight to anything `@trader`
   touches, given its scaffold-only, no-live-execution doctrine (`agents/trader.md`,
   `commands/trade.md`).
7. **Marketing / communications rules.** Performance claims ("this strategy returns X%") need a
   basis and a disclaimer that past performance does not guarantee future results, the
   Investment Adviser Marketing Rule baseline. Unqualified "your financial future is looking
   bright" framing is exactly the pattern to reject.
8. **Recordkeeping.** Does the output leave an evidence trail (data source cited, assumptions
   stated) an actual compliance review could reconstruct, or is the reasoning opaque?

## Actionable for the auditor

Every item above maps to a concrete PASS/REDO check, not a vibe: cite the specific claim in the
subject text, name which numbered item it fails, and state the falsification condition (what
evidence would change the verdict) per the Hypothesis+Falsification+Confidence triple
(`skills/shepherd/references/flock.md §@auditor` for the shepherd precedent this ports). A finding
with no falsification condition is not a finding. It is an opinion, and it does not belong in an
`audit_findings` row.

## Jurisdiction-honesty: the non-negotiable discipline

This skill's authority ends at "flags a US-federal-baseline concern for human review." It never
issues a definitive legal verdict, never asserts a state's blue-sky rule without being told the
state, and never treats "I didn't find a violation" as "this is compliant"; absence of a finding
is absence of evidence, not proof of clearance. Any output that claims legal certainty
("this is 100% compliant") is itself a finding against this skill's own discipline. The correct
closing line on every compliance pass is a plain statement of scope: what was checked, what
jurisdiction was assumed, and that a licensed professional should review before the client acts on
it.

## Wiring

`@auditor` loads this skill for its adversarial pass over `@advisor`/`@quant`/`@worker`/`@trader`
output; `/myfi:taxes` and `/myfi:trade` route through the auditor's compliance gate before either
command's final report ships. Findings this skill's checklist surfaces feed the `IMPROVE` loop
(`skills/improve/SKILL.md`) exactly like any other `@auditor` finding: a recurring compliance
concern graduates from a one-off finding to a stored prior the same way any other pattern does.

## Orienting cold

Landed here with nothing else loaded? You now know: this is a US-federal, retail-adjacent
baseline, not a law license; the eight-item checklist above (standard of care, disclosure,
suitability, KYC/AML, MNPI, manipulation, marketing, recordkeeping) is what an `@auditor` pass
actually runs; every finding needs a falsification condition; and "outside my jurisdiction" is
always a correct, honest answer. A confident wrong verdict is worse than a flagged unknown.
