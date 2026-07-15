---
title: Planter mesh -- myfi v0.0.0 (first cycle)
date: 2026-07-13
author: planter (opus) @ shepherd:plant
scope: v0.0.0 (brand-new patch arc, N=0)
---

# Planter Mesh -- myfi v0.0.0

Greenfield finance plugin. This is the first cycle: no prior close, no priors, empty GitHub. The
authoritative signal is the operator's overview (this session's opening brief), not a ledger.

## 12-row mesh

| # | Source | Result | Drift risk |
|---|--------|--------|-----------|
| 1 | GH issues `--state all --limit 100` | **0 issues** | none -- deliverables will be filed at Phase 0 |
| 2 | GH PRs `--state all` | **0 PRs** | none |
| 3 | GH milestones | **0 milestones** | must create `v0.0.0` milestone at Phase 0 |
| 4 | git log | 2 commits: `cd7d679 initial commit`, `086732b add .github` | none |
| 5 | Sentry | skipped -- `[mcp].sentry` unset | n/a |
| 6 | Datastore (Supabase) | skipped -- `[mcp].supabase` unset | n/a |
| 7 | Deploy (fly) | skipped -- no `[cli].fly` | n/a |
| 8 | Prior close report | none (first cycle) | n/a |
| 9 | Prior handoff | none (first cycle) | n/a |
| 10 | Project CLAUDE.md | present -- services-first architecture, latent/deterministic split, tests+evals-every-commit, LLM-via-local-Claude-Code, vanilla-tech-by-default, precision-of-language | binding doctrine -- every deliverable must honor it |
| 11 | Carry-forward ledger | none (first cycle) | n/a |
| 12 | ctx/*.md + `shctx adapt priors` | **empty** ("none (first cycle)") | n/a |

## Ground-truth repo state

Current layout is a **`shepherd`→`myfi` find/replace skeleton**, partially adapted:

| Path | State | Verdict |
|---|---|---|
| `.claude-plugin/plugin.json` | name/desc/version set (`0.0.0`) | keep, refine |
| `.claude-plugin/marketplace.json` | `fl03` marketplace, `myfi` plugin registered | keep |
| `src/agents/{advisor,auditor,quant,worker}.md` | frontmatter-only stubs; **missing `designer`, `trader`** | flesh out; **relocate `src/agents`→`agents/`** (plugin auto-discovery requires root-level dirs -- `src/` is inert) |
| `src/skills/{advise,myfi,plan,trade}/SKILL.md` | mostly empty; `myfi` has a 2-line frontmatter | replace with real skills; **relocate `src/skills`→`skills/`**; names don't match the target skill set (IMPROVE/COMPLIANCE/TAXES/MYFI) |
| `README.md` | **shepherd engineering-sprint README, not myfi's finance vision** | full rewrite |
| `.github/workflows/release.yml` | shepherd patch-release pipeline (v*.*.* → main → tag → next-patch) | keep -- confirms patch-by-patch cadence |
| `CLAUDE.md` | myfi doctrine (services-first, latent/deterministic, tests+evals) | authoritative |
| `.shepherd/shepherd.db` | bootstrapped, schema v18 | ready |
| `.claude/shepherd.toml` | fixed this session: `language=python`, poetry gates, `sprints_per_patch=3`, python/shell/markdown detection | ready |

**Critical finding (Row 10 + layout):** components under `src/` are NOT auto-discovered by Claude
Code plugin loading -- plugin dirs (`agents/`, `skills/`, `commands/`, `hooks/`) must sit at the
plugin root next to `.claude-plugin/`. The current `src/*` scaffold is effectively inert. The
foundation sprint MUST relocate to root-level component dirs (shepherd's own layout).

## Operator intent (primary source -- from the overview)

- **6 agents** (closed flock): `@advisor` (opus dispatcher / planner), `@auditor` (adversary +
  compliance), `@designer` (live artifacts + data-formatting), `@quant` (research-grade analysis),
  `@trader` (agentic loop + authorization surface), `@worker` (catch-all).
- **Skills:** `IMPROVE` (loop self-improvement), `COMPLIANCE` (local law/regulatory), `TAXES`
  (tax workflow knowledge), `MYFI` (core scaffold) -- the last owns **TOOLKIT** (Python3/poetry
  CLI, optionally an MCP, with numpy/pandas/scipy/matplotlib; per-project + optional global SQLite DB).
- **Entry points:** `/myfi:analyze` (single-shot report), `/myfi:plan` (advisor pipeline),
  `/myfi:taxes` (tax workflow), `/myfi:trade` (authorized agentic trading loop).
- **Harness themes to port from shepherd:** adversarial actor/critic pairs + REDO loops, focus
  loops/goals, dynamic workflows, agent teams, per-project + global memory DB, self-improvement.
- **Cadence:** patch-by-patch, publish frequently -- NOT the big multi-dev-branch fan-out.

## Reference patterns available to cite (shepherd source at `~/src/fl03/shepherd`)

- `services/{llm,eval}/` -- self-contained local-Claude-Code LLM service + eval harness (the
  CLAUDE.md-mandated pattern). myfi's `services/toolkit/` and `services/llm/` mirror this.
- `skills/context/` (the `shctx` bash toolkit: schema/migrations, views, queries, scripts, tests)
  -- the structural template myfi's **Python** toolkit ports (Joe's explicit lesson: Python over bash).
- `skills/{adaptation,motivation,harness,thinking}/` -- lesson memory, focus/drive, platform
  mechanics. myfi's `IMPROVE` skill is the adaptation-loop analogue.
- `agents/` closed-flock contracts + `skills/shepherd/references/*` -- dispatch law, pipeline,
  seed template, flock briefs.

## Tension flagged for operator (drives the batched question)

Joe's own directives pull two ways: **"patch by patch, publish frequently"** (small, incremental
ships) vs. **"boil the ocean, do the whole thing, best initial sprint of all time"** (ship the
whole vision at once). The v0.0.0 scope cut is a genuine architectural fork -- resolved via one
batched operator question before seed authorship, not guessed.

## Priors / lessons

none (first cycle).
