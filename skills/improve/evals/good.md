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

**Recurrence.** Nine sprints later -- well outside any 7-day window since `mem_9f21` was first
stored -- `@auditor` flags the SAME ungrounded-price-citation concern again, this time on a
`@trader-doc` unit. The harvest step finds the existing `mem_entries` row titled `"prior:
ungrounded price citation"` rather than inserting a duplicate, so it refreshes that row's
`updated_at` to now; `created_at` stays at its original value from nine sprints back. The next
dispatch's Phase-0 mesh reads `v_mem_recent_7d` and `mem_9f21` is still in the result set, because
the view filters and orders on `updated_at` ("touched in the last 7 days"), not `created_at` -- a
prior that keeps recurring keeps re-surfacing no matter how long ago it was first stored. That is
the dedup-refresh-then-reinject cycle working as designed: harvest finds the existing row, store
refreshes `updated_at` instead of growing a duplicate, and inject re-surfaces it on the next read.
