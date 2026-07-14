# IMPROVE loop: good

Close-time harvest note for this sprint's `@auditor` pass:

**Harvest.** Two `audit_findings` rows came back HIGH severity this sprint: (1) a `@quant` trade
thesis cited a price level with no toolkit-sourced quote behind it, (2) a `@worker` tax summary
skipped the wash-sale adjustment on a repurchased position. Both are recurring-pattern candidates,
not one-off typos, so both graduate to harvest.

**Store.** Each becomes one deduped `mem_entries` row with `kind='prior'` in the per-project
`.myfi/myfi.db`: `title="prior: ungrounded price citation"` and `title="prior: missed wash-sale
adjustment"`, `body` carrying the severity and the sprint branch, `tags=["quant","data-grounding"]`
and `tags=["taxes","wash-sale"]` respectively. Neither row already existed under that title, so
this is a fresh insert, not a duplicate.

**Inject.** Next sprint's Phase-0 mesh reads `v_mem_recent_7d` (both rows are within the 7-day
window) and folds both priors into the `@quant` and `@worker` dispatch briefs before either agent
starts work, so the same two mistakes get a warning up front instead of a third occurrence.

**Cite.** This sprint's `@quant` report opens with: "grounding every price to `bin/myfi-toolkit
quote` per `prior:mem_9f21`, last sprint's finding on ungrounded citations." That citation is the
loop's proof the injected lesson was actually read, not just stored inertly.
