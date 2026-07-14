---
name: analyze
description: Single-shot financial report command. Runs the toolkit against a subject, dispatches ONE flock agent pass (default @advisor, or @quant/@worker for a narrower lookup), and writes a report artifact to a path it prints. Use for a cheap one-off report; use /myfi:plan when the goal needs the full advisor-led flock pipeline.
argument-hint: "<subject> [--agent=advisor|quant|worker] [--out=<path>] [--json]"
allowed-tools: Agent, Bash, Read, Grep, Skill, Write, mcp__plugin_myfi_myfi-toolkit__quote, mcp__plugin_myfi_myfi-toolkit__db_init, mcp__plugin_myfi_myfi-toolkit__db_migrate, mcp__plugin_myfi_myfi-toolkit__db_version
---

# /myfi:analyze -- single-shot report

The cheap path. One toolkit pull, one flock agent pass, one report artifact. `/myfi:analyze
"should I refinance this year?"` answers the question and stops -- it does not decompose the goal
into a multi-step engagement, does not run the `@auditor` adversarial gate, and does not hand off
to `@designer` for a live-artifact finish. Reach for `/myfi:plan` instead when the goal spans
multiple units of work, needs the compliance/local-law adversarial pass, or needs a finished
live-HTML/chart artifact rather than a plain markdown report.

## Flags

- `<subject>` (required) -- the question or lookup, free text. Everything after the flags.
- `--agent=advisor|quant|worker` (default `advisor`) -- which single flock agent runs the pass.
  `advisor` for a general recommendation, `quant` for a modeling-heavy lookup (pricing, a risk
  metric), `worker` for a routine aggregation/form-fill that does not need judgment.
- `--out=<path>` (default `.myfi/reports/<slug>-<timestamp>.md`) -- where the report artifact is
  written. `<slug>` is the subject, lowercased and dash-joined; `<timestamp>` is
  `date -u +%Y%m%dT%H%M%SZ`.
- `--json` -- also emit a machine-readable sidecar (`<out>.json`) with `{subject, agent, artifact,
  toolkit_calls, generated_at}` alongside the markdown artifact.

## Step 0 -- Preflight

Parse `<subject>` and flags; a missing `<subject>` halts with a usage message (this command never
guesses a subject). Read `skills/myfi/SKILL.md` first -- every invocation orients to the toolkit
surface, the flock table, and the LLM-routing law before dispatching anything. Resolve `--agent`
to one of `advisor`/`quant`/`worker`; an unrecognized value halts rather than silently defaulting.

## Step 1 -- Ground the subject via the toolkit

Before dispatching the agent, pull whatever real data the subject implies: a market quote via
`mcp__plugin_myfi_myfi-toolkit__quote` for anything price-sensitive, or a `db_*` tool call for
anything already persisted in the per-project `.myfi/myfi.db` registry. This is single-shot, not
zero-shot -- the dispatched agent gets real numbers to ground its report in, not a bare question.
`db init` first if `.myfi/myfi.db` does not yet exist (`mcp__plugin_myfi_myfi-toolkit__db_init`).

## Step 2 -- Dispatch ONE agent pass

Dispatch the resolved `--agent` via `Agent`, carrying the subject and every toolkit result pulled
in Step 1. This is the single-shot boundary: the dispatched agent produces its full report in one
turn -- it does not itself fan out to the rest of the flock, and this command does not run the
`@auditor` gate or the `@designer` finalization pass. That is the entire distinction from
`/myfi:plan`: one pull, one agent, one report, done.

## Step 3 -- Write the report artifact

Assemble the agent's output into the report shape (goal restated, current position grounded in
toolkit data, the recommendation, risks and uncertainty, the next concrete action) and `Write` it
to the resolved `--out` path (default `.myfi/reports/<slug>-<timestamp>.md`), creating
`.myfi/reports/` if it does not exist. This is the report artifact this command exists to produce
-- nothing about `/myfi:analyze` is complete until a real `.md` file lands on disk at a path the
caller can open.

## Step 4 -- Print the artifact path

The last line of output is always the resolved artifact path, on its own line, so a caller (human
or another command) can locate the report without re-parsing the whole transcript:

```
[ANALYZE] report artifact: .myfi/reports/should-i-refinance-this-year-20260713T190500Z.md
```

With `--json`, also print the sidecar path on the following line.

## Halt codes

- `ANALYZE-NO-SUBJECT` -- `<subject>` missing or empty.
- `ANALYZE-BAD-AGENT` -- `--agent` is not one of `advisor`/`quant`/`worker`.
- `ANALYZE-WRITE-FAILED` -- the report artifact could not be written to `--out` (permissions,
  missing parent that could not be created).

## Grounding + LLM law

Every figure in the emitted report traces to a toolkit call from Step 1 or the dispatched agent's
own toolkit calls -- never an invented number. Every model call this command's dispatched agent
makes routes through `services/llm` to local Claude Code (`skills/myfi/SKILL.md §The LLM law`) --
never a hosted inference API.

## Eval

Scored against `services/eval/rubrics/analyze_report.rubric.json` (report-completeness,
data-grounding, actionable-recs); goldens at `commands/evals/analyze_good.md` /
`commands/evals/analyze_bad.md`.
