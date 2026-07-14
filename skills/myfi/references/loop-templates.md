---
description: Ready-to-use per-role loop templates for the myfi six-agent flock. Read this before dispatching any bounded loop (a REDO ladder, a convergence pass, or a repeated fan-out) so the cap and the termination predicate are declared before the loop starts, never assembled after the fact.
---

# Loop Template Catalog (myfi)

Ported from shepherd's loop discipline (`skills/harness/references/loop-templates.md` in the
shepherd repo) and re-shaped for myfi's closed six-agent finance flock: `@advisor` (dispatcher),
`@quant` and `@worker` (actors), `@auditor` (adversary), `@designer` (final artifact editor), and
`@trader` (scaffold-only, no loop surface at all). Every template below specializes one of two
composites, both carried over unchanged from shepherd:

- **CONVERGENCE-LOOP** - an iterator fixes something and re-checks a gate expression until it
  passes.
- **Loop-Until-Done** - an iterator sweeps until it finds nothing new to fix.

Two invariants bind every template in this file, no exceptions:

1. **A bounded `--max` MUST be declared before the first iteration.** A loop with no cap is a
   framework violation, not a convenience. Every template below states its default `--max`.
2. **Every iterator MUST emit a structured `new_findings: true|false` field on every tick.**
   Unstructured prose ("looks clean now") is not a valid termination signal. `true` means the loop
   keeps going; `false` means the gate passed, the deliverable matched, or the sweep found nothing
   left to fix.

## The flock-wide REDO cap

`@auditor` gates every actor's draft PASS or REDO before `@designer` performs the final artifact
edit (`agents/auditor.md §Modes`). **REDO cap 3** is the one hard ceiling every template in this
file respects: a draft gets at most 3 REDO cycles through the same specialist before the finding
escalates to `@advisor` instead of looping a fourth time. A REDO cap that does not match this
document, or a REDO loop with no matching `--max`/`new_findings` predicate here, is a process bug,
not a policy choice (`agents/auditor.md` states this explicitly).

## Skeleton (stated once, not repeated per template)

Every template below follows this 7-part shape; only the parts that differ (agent, predicate,
default `--max`, anti-patterns) appear in its own entry:

1. **Intent** - one-line purpose.
2. **Composite** - CONVERGENCE-LOOP or Loop-Until-Done, specialized.
3. **Flock agent binding** - iterator and gate roles.
4. **Loop body** - Act, then Check, then Branch.
5. **Termination predicate** - the exact condition for `new_findings: false`.
6. **Default `--max`** - a numeral, plus what exceeding it means.
7. **Anti-patterns** - the top violations to watch for on this role.

## Quick-selection table

| Role | Template | Composite | Default `--max` | Terminates on |
|---|---|---|---|---|
| `@advisor` | ADVISOR-DISPATCH-CONVERGE | CONVERGENCE-LOOP | 3 | `@auditor` PASS reaches the assembled report (`new_findings: false`) |
| `@quant` | QUANT-MODEL-CONVERGE | CONVERGENCE-LOOP | 3 | every figure traces to a toolkit call, Assumptions/Methodology/Results/Caveats complete |
| `@worker` | WORKER-DELIVERABLE-CONVERGE | CONVERGENCE-LOOP | 3 | deliverable matches the brief's `[FORMAT]` exactly, within budget |
| `@auditor` | AUDITOR-GATE-REDO | Loop-Until-Done | 3 (REDO cap, hard) | verdict is PASS, or REDO attempt 3 escalates instead of looping again |
| `@designer` | DESIGNER-CHECKLIST-CONVERGE | CONVERGENCE-LOOP | 3 | all 5 final-edit checklist items read `ok` |
| `@trader` | none | n/a | n/a | never loops; every dispatch halts once at the Authorization Gate |

## ADVISOR-DISPATCH-CONVERGE

Drive the assembled client report to a state where every dispatched unit has cleared `@auditor`.

- **Intent.** `@advisor` re-dispatches a specialist whose output `@auditor` REDO'd, until the
  report's every section carries a PASS.
- **Composite.** CONVERGENCE-LOOP. Iterator: `@advisor` (re-dispatch), gate: `@auditor` verdict.
- **Loop body.** Act: re-dispatch the specialist with the auditor's findings attached (never
  silently patch the output itself, per `agents/advisor.md §The dispatch cycle` step 3). Check:
  read the new `@auditor` verdict. Branch: PASS moves the section to `@designer`; REDO loops again
  up to the cap.
- **Termination predicate.** `new_findings: false` once every dispatched section carries a PASS
  verdict and no open `@auditor` finding remains CRITICAL or HIGH.
- **Default `--max`: 3.** This is the same ceiling as the flock-wide REDO cap 3, because each
  iteration of this loop IS one REDO cycle by construction; a 4th attempt is never re-dispatched,
  it escalates.
- **Anti-patterns.** Patching a specialist's output directly instead of re-dispatching it (that is
  `@advisor` overstepping into `@quant`/`@worker`'s lane); assembling the final report before every
  section shows PASS; treating a LOW-confidence `@auditor` open question as a REDO trigger (only
  CRITICAL/HIGH findings force a loop).

## QUANT-MODEL-CONVERGE

Drive a model or figure to fully grounded, before it ever reaches `@auditor`.

- **Intent.** `@quant` re-pulls data or re-derives a figure until every number in the report traces
  to a toolkit call, per the grounding rule in `agents/quant.md §Grounding rule`.
- **Composite.** CONVERGENCE-LOOP. Iterator: `@quant` (pull data, build model), gate: a
  self-check against `agents/quant.md`'s Assumptions/Methodology/Results/Caveats contract.
- **Loop body.** Act: call `mcp__plugin_myfi_myfi-toolkit__quote` or a `db_*` tool for the missing
  input. Check: does every reported figure now cite a toolkit call or a named model input? Branch:
  yes closes the loop; no re-pulls the missing input.
- **Termination predicate.** `new_findings: false` when zero figures in the draft lack a toolkit
  citation or a named, checkable model input, AND the four-part report (Assumptions, Methodology,
  Results, Caveats) is complete.
- **Default `--max`: 3.** Exceeding it without a resolved gap means the underlying data source is
  genuinely absent, not that another attempt will help; report the gap explicitly instead
  (`agents/quant.md §Hard prohibitions` forbids inventing a plausible-looking number to close the
  loop artificially).
- **Anti-patterns.** Filling a missing figure with a plausible guess to make the loop terminate;
  looping past `--max` instead of reporting the data gap; skipping the uncertainty band to declare
  convergence early.

## WORKER-DELIVERABLE-CONVERGE

Drive a bounded deliverable to exactly match its brief.

- **Intent.** `@worker` iterates a mechanical task (form-fill, aggregation, a toolkit lookup) until
  the output matches the brief's `[FORMAT]` field exactly, within its stated `[BUDGET]`.
- **Composite.** CONVERGENCE-LOOP. Iterator: `@worker`, gate: the brief's own `[FORMAT]` field
  (`agents/worker.md §Brief contract`).
- **Loop body.** Act: produce or reshape the deliverable. Check: does it match `[FORMAT]` and stay
  inside `[BUDGET]`? Branch: yes closes the loop; no adjusts and retries.
- **Termination predicate.** `new_findings: false` when the deliverable matches `[FORMAT]` exactly
  and every reported figure traces to a toolkit call, per `agents/worker.md §The toolkit, not
  guesswork`.
- **Default `--max`: 3.** At 80% of the tool-call or time budget with no match yet, `@worker` cuts
  scope and returns a partial result labeled as such rather than spending the remaining 20% of
  budget on more iterations (`agents/worker.md §Hard constraints`).
- **Anti-patterns.** Looping on a deliverable that turns out to need advisory judgment or modeling
  instead of halting with `BRIEF-AMENDMENT REQUEST: deliverable requires <agent> lane`; exceeding
  the stated `[BUDGET]` to force one more iteration; silently widening `[FORMAT]` instead of
  matching what was asked.

## AUDITOR-GATE-REDO

The REDO ladder itself, the flock's one mandatory adversarial loop.

- **Intent.** `@auditor` re-reviews a re-dispatched draft after the specialist addressed its
  findings, until the draft reaches PASS or the REDO cap 3 is spent.
- **Composite.** Loop-Until-Done, specialized as a REDO ladder rather than an open sweep: the
  iteration count is the REDO attempt number, capped hard at 3.
- **Loop body.** Act: run the Hypothesis+Falsification+Confidence triple against the new draft.
  Check: zero CRITICAL/HIGH findings outstanding? Branch: yes emits PASS and the loop ends; no
  emits REDO and increments the attempt counter, unless the counter is already at 3.
- **Termination predicate.** `new_findings: false` on a PASS verdict (zero CRITICAL/HIGH findings
  remain). At REDO attempt 3, the loop terminates regardless of `new_findings`, and the open
  finding escalates to `@advisor` instead of a fourth pass (`agents/auditor.md §Modes`).
- **Default `--max`: 3.** This is the flock's REDO cap 3, verbatim, not a separate number that
  happens to agree with it. Any change to this cap MUST land in both `agents/auditor.md` and this
  file in the same change, or the two documents drift out of sync.
- **Anti-patterns.** A 4th silent REDO instead of escalating; grading a finding it cannot falsify
  (an unfalsifiable observation goes to `## Open questions`, never counts toward a REDO verdict);
  editing the artifact directly instead of reporting the finding (`AUDITOR-WRITE-PATH`).

## DESIGNER-CHECKLIST-CONVERGE

Drive the final artifact to a clean pass of its own checklist before calling it done.

- **Intent.** `@designer` iterates formatting, chart placement, and citation wiring until every
  item in the final-edit checklist (`agents/designer.md §Final-edit checklist`) reads `ok`.
- **Composite.** CONVERGENCE-LOOP. Iterator: `@designer`, gate: the 5-item checklist itself
  (format fidelity, chart integrity, no orphaned citation, readability, no reopened finding).
- **Loop body.** Act: fix the failing checklist item. Check: re-run the checklist. Branch: all 5
  read `ok` closes the loop; any `fail` retries.
- **Termination predicate.** `new_findings: false` when `format-fidelity=ok, chart-integrity=ok,
  no-orphaned-citation=ok, readability=ok, no-reopened-finding=ok` all appear in the same pass.
- **Default `--max`: 3.** A checklist that still fails after 3 passes means the source draft itself
  needs another `@auditor` cycle, not a 4th cosmetic pass; halt `DESIGNER-PRE-GATE` and hand the
  draft back rather than polishing around a structural gap.
- **Anti-patterns.** Touching a number, a citation, or a risk disclosure while "fixing" a checklist
  item, that reopens a gate `@auditor` already cleared and is out of scope for this loop entirely;
  finalizing a draft with no recorded `@auditor` PASS just to close the loop faster.

## `@trader`: no loop surface

`@trader` is scaffold-only in v0.0.0 and never loops. Every dispatch runs the documented cycle once
(ASSESS, DISCOVER, RANK, GATE-CHECK) and halts permanently at the Authorization Gate (step 5 of
`agents/trader.md §The trade cycle`) because no live-order or exchange tool is wired to this agent
anywhere in this plugin. There is no `--max` here because there is no iteration: a loop that tried
to retry past the Authorization Gate would be attempting to route around a hard non-goal, not a
bounded convergence. If a future patch ever adds `@trader` a loop template, it inherits this same
REDO cap 3 discipline and the same `--max`/`new_findings` contract as every other role in this file.

## See also

- `skills/myfi/references/workflow-templates.md` - the dynamic-workflow fan-out shape these loops
  nest inside.
- `skills/myfi/references/agent-team-templates.md` - the flock dispatch law and adversarial pairing
  these loops assume.
- `agents/auditor.md §Modes` - the canonical REDO cap 3 statement this file mirrors.
- `agents/advisor.md §The dispatch cycle` - the re-dispatch step ADVISOR-DISPATCH-CONVERGE
  specializes.
