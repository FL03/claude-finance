---
name: plan
description: Advisor-led planning pipeline. Dispatches the full flock in order (@advisor decomposes -> @quant/@worker produce -> @auditor adversarially gates, PASS/REDO cap 3 -> @designer finalizes the artifact) and returns a synthesized, client-ready plan. Use for a multi-step engagement; use /myfi:analyze for a cheap single-shot report.
argument-hint: "<goal> [--horizon=<duration>] [--out=<path>] [--redo-cap=3]"
allowed-tools: Agent, Bash, Read, Grep, Skill, Write, mcp__plugin_myfi_myfi-toolkit__quote, mcp__plugin_myfi_myfi-toolkit__db_init, mcp__plugin_myfi_myfi-toolkit__db_migrate, mcp__plugin_myfi_myfi-toolkit__db_version
---

# /myfi:plan -- advisor-led flock pipeline

The full path. `/myfi:plan "build a plan to retire by 55"` runs the entire myfi flock in a fixed
dispatch order and returns one synthesized, client-ready plan -- not a single agent's raw output.
This command is the harness that drives that pipeline; `@advisor` is the dispatcher inside it, not
a replacement for it. Reach for `/myfi:analyze` instead when the goal is a single cheap lookup that
does not need multi-step decomposition, the adversarial compliance gate, or a finished live
artifact.

## Flags

- `<goal>` (required) -- the client's stated goal, free text. A missing `<goal>` halts with a usage
  message.
- `--horizon=<duration>` (optional) -- the planning horizon (e.g. `10y`, `18mo`); passed through to
  `@advisor`'s decomposition so every dispatched unit is scoped to the same timeline.
- `--out=<path>` (default `.myfi/reports/plan-<slug>-<timestamp>.md`) -- where the final plan
  artifact lands, same slug/timestamp convention as `/myfi:analyze`.
- `--redo-cap=3` (default `3`) -- the `@auditor` REDO ceiling for this run. Never raise this past
  the flock-wide cap without an explicit operator override; a run that exhausts the cap halts
  rather than shipping an unaudited plan.

## Step 0 -- Preflight

Parse `<goal>` and flags. Read `skills/myfi/SKILL.md` first -- orient to the toolkit, the flock
table, the command list, and the LLM-routing law before dispatching anything. `db init` via
`mcp__plugin_myfi_myfi-toolkit__db_init` if `.myfi/myfi.db` does not yet exist, so the pipeline has
a per-project registry to persist dispatch state and audit findings into.

## Step 1 -- Dispatch @advisor to decompose

Dispatch `@advisor` (`Agent`, `model: opus`) with the goal and horizon. `@advisor` is the flock's
only dispatcher: it breaks the goal into concrete units, decides which of `@quant`/`@worker` (and,
only if the goal is explicitly about scaffold-only trade-cycle documentation, `@trader`) owns each
unit, and routes work to them -- this command does not hand-pick specialists itself; that
decomposition is `@advisor`'s job per `agents/advisor.md §The dispatch cycle`.

## Step 2 -- @advisor dispatches @quant / @worker

`@advisor` sends each decomposed unit to its owning specialist. `@quant` returns
Assumptions/Methodology/Results/Caveats grounded in toolkit calls (`agents/quant.md`); `@worker`
returns a bounded task result. This command does not dispatch these agents directly -- it observes
`@advisor`'s dispatch trail so the final plan can cite who produced what.

## Step 3 -- @auditor adversarial gate (PASS / REDO, cap `--redo-cap`)

Every specialist's output, and `@advisor`'s own draft synthesis, goes through `@auditor` before
anything is finalized. `@auditor` returns a Hypothesis+Falsification+Confidence triple per finding
and a PASS/REDO verdict. On REDO, this command re-dispatches the SAME specialist with the
auditor's findings attached (never patches the output itself) and loops back to Step 2/3, capped
at `--redo-cap` cycles. Exhausting the cap without a PASS halts the pipeline -- a plan that never
clears the adversarial gate does not ship.

## Step 4 -- @designer finalizes the artifact

Once `@auditor` returns PASS on every unit, hand the audited content to `@designer` for the final
live-artifact pass: chart rendering placement, HTML/data-format finalization
(`agents/designer.md`). `@designer` owns the last edit on the artifact; this command does not
re-word its output.

## Step 5 -- Synthesize and write the plan artifact

`@advisor` assembles the finished plan from every stage's output, in dispatch order: the client's
goal restated, the current position grounded in toolkit data, the recommendation as ordered
concrete steps traceable to `@quant`/`@worker`'s cited figures, the risks `@auditor` verified (and
any it flagged), and the next action to take this week. `Write` the assembled plan to the resolved
`--out` path (default `.myfi/reports/plan-<slug>-<timestamp>.md`), creating `.myfi/reports/` if it
does not exist. A plan that skips a stage of this pipeline, or that presents a specialist's raw
output unsynthesized, is not ready to leave the flock.

## Step 6 -- Print the artifact path

The last line of output is always the resolved plan artifact path:

```
[PLAN] plan artifact: .myfi/reports/plan-retire-by-55-20260713T190500Z.md
```

## Halt codes

- `PLAN-NO-GOAL` -- `<goal>` missing or empty.
- `PLAN-REDO-CAP-EXCEEDED` -- `@auditor` returned REDO `--redo-cap` times without a PASS; the
  pipeline halts rather than shipping an unaudited plan.
- `PLAN-WRITE-FAILED` -- the plan artifact could not be written to `--out`.

## Grounding + LLM law

Every figure in the assembled plan traces to a toolkit call or a specialist's cited output -- never
an invented number (`agents/advisor.md §Grounding rule`). Every model call any dispatched agent
makes routes through `services/llm` to local Claude Code, never a hosted inference API
(`skills/myfi/SKILL.md §The LLM law`).

## Eval

Scored against `services/eval/rubrics/plan_pipeline.rubric.json` (correct-dispatch-order,
synthesis-quality); goldens at `commands/evals/plan_good.md` / `commands/evals/plan_bad.md`.
