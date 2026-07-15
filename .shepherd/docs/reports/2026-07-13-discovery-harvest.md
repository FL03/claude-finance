---
title: Discovery -- shepherd-to-myfi port map
date: 2026-07-13
discovery_id: D-HARVEST
sprint: v0.0.0
sources_consulted: 21
tool_calls_used: 24
time_used_minutes: 13
---

## Sources

`/Users/jo3/src/fl03/shepherd/services/llm/{README.md,llm.sh}` · `services/eval/{README.md,eval.sh}` ·
`skills/context/references/{schema.md,toolkit.md}` · `skills/context/scripts/cmd_migrate.sh` ·
`skills/context/schema/0001_init.sql` · `skills/adaptation/SKILL.md` · `skills/motivation/SKILL.md` ·
`hooks/hooks.json` · `hooks/scripts/{dispatch_guard.sh,dedup_write_guard.sh,coordinate_drive_guard.sh}` ·
`agents/{critic.md,auditor.md}` · `skills/shepherd/references/pipeline.md` (grep, `§Wave review + REDO`) ·
`skills/context/scripts/cmd_discovery.sh` (own contract) · myfi `.shepherd/project.json`, `src/agents/*.md`, `src/skills/*/SKILL.md` (analogue-mapping context).

## Findings

| shepherd path | what it does | myfi analogue |
|---|---|---|
| `services/llm/llm.sh` | Shells to `claude -p --output-format text --model <alias> [--append-system-prompt F]`, stdin=prompt file; bg watchdog kills after timeout (macOS has no `timeout`); mock seam `SHEPHERD_LLM_MOCK`/`_MOCK_TEXT`; exit 0/2/3/4; tested via `tests/{test_llm_mock,test_llm_contract}.sh`, mock-only, <2s | `services/llm/llm.py`, same contract (`complete`/`ping`), same mock env vars, same exit codes |
| `services/eval/eval.sh` | Deterministically builds a judge prompt from `rubrics/*.rubric.json` (`kind/subject/scale/threshold/dimensions[key,weight,desc]/guidance`) → calls `llm.sh complete` → `overall=round(100·Σ(score·weight)/(scale·Σweight))`, `passed=overall≥threshold`; gate lane mocked vs live lane `SHEPHERD_EVAL_LIVE=1` (golden-good/bad margin) | `services/eval/eval.py` + `rubrics/{advisory,plan,trade}.rubric.json`, identical two-lane split |
| `schema/0001_init.sql` + `schema/migrations/0002…0018_*.sql` | Per-project SQLite: `projects(id UUIDv7)` root, every table `project_id FK CASCADE`, WAL+FK on, `schema_versions(version,checksum)`; `cmd_migrate.sh` gap-fills any version absent from `schema_versions` (not just `>MAX`) | `myctx/schema/0001_init.sql` + `migrations/`, Python stdlib `sqlite3`, identical gap-fill migration runner |
| `scripts/shctx` + ~45 `scripts/cmd_*.sh` | Bash CLI dispatcher, one file per verb, `tests/*.sh` one gate test per verb | `myctx` poetry package, `typer`/`click` subcommands, pytest one-per-verb |
| `skills/adaptation/SKILL.md` | harvest (`adapt roll` @ close, HIGH/CRITICAL `audit_findings`→dedup `mem_entries(kind='prior')`) → store (3 tables+1 view) → inject (`shctx inject <role>`) → cite (`prior:<id>`); 6-kind `## INSIGHTS` taxonomy | myfi IMPROVE skill, same 3-table+1-view shape |
| `skills/motivation/SKILL.md` | focus record (`(sprint,lane)` PK) + FOCUS-HEARTBEAT drift guard; `/goal` templates; bounded loop discipline (`--max`, `new_findings` predicate, `LOOP-CAP`); REDO cap 3; SOAK/SENTINEL | myfi redo-loops, same bounded-loop + REDO-cap-3 mechanics |
| `hooks/scripts/dispatch_guard.sh` | `PreToolUse(Agent\|Task)` closed-flock + tier enforcement, denies off-flock/missing subagent_type | guard myfi's advisor/auditor/quant/worker dispatch |
| `hooks/scripts/dedup_write_guard.sh` | `PreToolUse(Write\|Edit)` blocks new public symbols duplicating an existing one, for the coder-equivalent role only | myfi's worker/quant write guard |
| `hooks/scripts/coordinate_drive_guard.sh` | `Stop` backstop vs. passive-wait with idle teammates/unread mail, 2-nudge fail-open cap | only relevant once myfi has a teammate/conductor tier |
| `agents/critic.md` | pre-hoc adversarial gate: `PROCEED/PROCEED WITH CHANGES/RECONSIDER/REJECT` | myfi advisor↔auditor pre-hoc pairing |
| `agents/auditor.md` | post-hoc grading (A–F) + wave-review `PASS/REDO`; every finding = Hypothesis+Falsification+Confidence triple | myfi's existing `src/agents/auditor.md` -- port the triple contract + grade rubric (currently thin) |
| `pipeline.md §Wave review + REDO` | `REDO` re-dispatches the **named** author on the **named** scope only, cap 3, then `REDO-CAP-EXCEEDED`→HARD-STOP | myfi advisor↔auditor REDO loop |

Full 6 rows also written as `discovery_findings` rows (`shctx discovery insert --run=D-HARVEST`, ids 7-12, section=`port-map`).

## Open questions

- myfi's `shctx` binary on `PATH` is shared with shepherd's install (not yet a vendored/forked copy) -- whether myfi ports its own `myctx` package or continues depending on the shepherd-authored `shctx` long-term is an architecture decision for `@engineer`, not resolved by this read.
- No `services/llm/tests/run.sh` equivalent exists yet in myfi -- confirm the pytest gate lane before the eval harness lands (would block CLAUDE.md's "tests+evals every commit" rule).

## Confidence

HIGH -- every row above is a direct file read (paths cited), not inference.

## Suggested follow-ups (optional)

- A dedicated discovery on `skills/shepherd/references/spawn-flags.md` + `commands/spawn.md` once myfi actually adds a teammate/conductor tier (not needed for v0.0.0).

## PORT PRIORITY

**Must-port for v0.0.0 foundation:**
1. `services/llm/` + `services/eval/` -- CLAUDE.md hard-requires local-Claude-Code-only + tests+evals every commit; nothing else can ship without this.
2. `skills/context/` schema+migrations+scripts core (registry, dedup-check, adapt/audit tables) -- everything else (adaptation, hooks, REDO) reads/writes this DB.
3. `agents/auditor.md` triple-contract + `pipeline.md §Wave review + REDO` -- myfi's advisor↔auditor pairing is dead weight without a real gate + bounded REDO loop.

**Can wait:** `coordinate_drive_guard.sh` and teammate-coordination hooks (myfi has no teammate/conductor tier yet); SOAK/SENTINEL (post-deploy remediation, premature pre-v1); full `## INSIGHTS` taxonomy capture hook (nice-to-have once adaptation's core 3-table loop is stable).
