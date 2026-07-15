---
name: improve
description: The myfi self-improvement loop (harvest, store, inject, cite). Turns @auditor findings and discovery notes into durable per-project priors in myctx, then feeds them back into future dispatches so the flock never relearns the same failure twice. Load before a close, a fresh dispatch brief, or any REDO you suspect has happened before.
---

# IMPROVE: the harvest, store, inject, cite loop

The flock must not relearn the same failure twice. This skill is the myfi analogue of shepherd's
adaptation loop: four verbs, in order, closing a durable feedback cycle through the per-project
myctx SQLite database (`.myfi/myfi.db`, gap-fill migrated from
`services/toolkit/myfi_toolkit/myctx/schema/*.sql`; see `skills/myfi/SKILL.md` for the toolkit
surface). Read this before assembling a dispatch brief, before closing a sprint, or any time an
`@auditor` REDO feels familiar.

## The four verbs

**Harvest.** After `@auditor` runs its Hypothesis+Falsification+Confidence pass and writes a row to
`audit_findings` (concern, severity, hypothesis, finding, evidence_refs), and after any discovery
pass writes to `discovery_findings` (section, title, body, sources), the harvest step reads those
rows back and asks: which of these is a *recurring* concern, not a one-off? HIGH/CRITICAL severity
findings and discovery insights that name a durable pattern (not an incidental typo) are harvest
candidates. Info/low/medium findings are never promoted; the loop stays bounded, not a firehose.

**Store.** A harvested candidate becomes one deduped `mem_entries` row with `kind='prior'`: `title`
names the concern (`"prior: <concern>"`), `body` carries the gist plus the severity and the sprint
it came from, `tags` is a JSON array of related concern keywords, `source_path` points at the
`audit_findings`/`discovery_findings` row it was harvested from. Storage is per-project by default
(`.myfi/myfi.db`), with an optional global tier (`~/.myfi/global.db`, `--global`) for lessons that
generalize across every project the toolkit touches. Dedup is by title: a recurring concern
refreshes `updated_at` on its existing row rather than growing a duplicate; `pinned=1` rows are
never pruned. This is the **3-table+1-view memory shape** the loop reads and writes:
`mem_entries` (the store), `audit_findings` and `discovery_findings` (the two harvest sources), and
the `v_mem_recent_7d` view (pinned rows OR anything touched in the last 7 days, the inject step's
default read).

**Inject.** At the start of a fresh dispatch (a new `@advisor` brief, a new `@auditor` pass, a
sprint's Phase-0 mesh), read `v_mem_recent_7d` (or a tag-scoped `mem_entries` query for a narrower
context) and fold the resulting priors into the dispatch's opening context. An empty store is not
an error; it means "no pattern history yet" and the loop proceeds cold. A concern that keeps
recurring across the view is a signal the *next* brief should scope a dedicated lane for it, not
just repeat the same warning silently forever.

**Cite.** Any decision, brief, or report that acted on an injected prior MUST cite its row id
(`prior:<mem_id>`) in its rationale. This is the loop's only measurement signal: if priors get
injected but nothing ever cites one, the injection is being ignored, and that itself is worth a
harvest entry. A report with no citations across several non-empty-store sprints means the inject
step is being skipped, not that the flock stopped making mistakes.

## REDO discipline

`@auditor` verdicts are PASS or REDO, capped at 3 attempts per unit (`skills/shepherd/references/
flock.md §@auditor` in the shepherd repo, the precedent this ports). A REDO on the *same* concern
across two or more units, or across sprints, is exactly the "recurring, not one-off" test the
harvest step applies: it graduates from a one-time finding to a stored prior so the next dispatch
brief for that surface area gets the warning up front, before the mistake repeats a third time.
The cap-3 ceiling and the harvest-on-recurrence rule work together. REDO stops runaway rework
within a unit; IMPROVE stops the same rework from recurring across units.

## Where the mechanism lives

The schema (`mem_entries`, `discovery_findings`, `audit_findings`) ships in Wave 3's
`services/toolkit/myfi_toolkit/myctx/schema/0001_init.sql` and is reachable today via
`myfi_toolkit.myctx.db.connect()` / `resolve_db_path()`. `v_mem_recent_7d` itself is keyed on
`updated_at`, not `created_at` (fixed in
`services/toolkit/myfi_toolkit/myctx/schema/migrations/0002_v_mem_recent_7d_updated_at.sql`):
"touched in the last 7 days" means the row's `updated_at`, so a prior whose `updated_at` gets
refreshed on recurrence -- per the Store step above -- surfaces again no matter how old its
`created_at` is. The harness's dispatch-time hooks (`hooks/scripts/adaptation_capture.sh`, wired in
`hooks/hooks.json`) are the mechanized writer that turns a fresh `audit_findings`/
`discovery_findings` row into a harvested `mem_entries(kind='prior')` row -- on recurrence,
refreshing only `updated_at`, never `created_at` -- without a human doing it by hand. That wiring
is a harness concern, not this skill's; this skill is the loop's contract, not its cron job.

## Bounded, not a firehose

The loop is bounded by construction: dedup-by-title (one prior per recurring concern, never per
occurrence), HIGH/CRITICAL-only promotion (info/low/medium never graduate), and injection scoped to
recent-or-pinned (`v_mem_recent_7d`) rather than the full historical table. It is not an issue
tracker (chronic items still get a GH issue), not auto-applied (a prior is surfaced in context, it
never silently rewrites a plan), and not a log (the full record stays in `audit_findings`/
`discovery_findings`; `mem_entries` holds only the distilled lesson).

## Orienting cold

Landed here with nothing else loaded? You now know: harvest reads `audit_findings` and
`discovery_findings` for recurring HIGH/CRITICAL patterns; store writes one deduped
`mem_entries(kind='prior')` row per pattern in the per-project `.myfi/myfi.db`; inject reads
`v_mem_recent_7d` at the top of a fresh dispatch; cite means naming `prior:<mem_id>` in any
rationale that acted on one. That is the whole loop: harvest, store, inject, cite.
