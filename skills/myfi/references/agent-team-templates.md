---
description: The myfi flock dispatch patterns, the closed six-agent roster, dispatch law (who may dispatch whom), the adversarial pairing, and the halt-code index used across the flock. Read before writing any dispatch brief or reasoning about which agent owns a task.
---

# Agent-Team Templates (myfi)

Ported from shepherd's flock reference (`skills/shepherd/references/flock.md` in the shepherd
repo) and re-shaped for myfi's own six-agent finance flock. Shepherd's flock builds software;
myfi's flock produces client-facing financial analysis. The roles, tool surfaces, and halt codes
below are myfi's own, not shepherd's, ported in shape only.

## The closed roster

Six agents, no more, no fewer, in v0.0.0:

| Agent | Model | Produces or gates | Dispatches others? |
|---|---|---|---|
| `@advisor` | opus | Decomposition, dispatch, adversarial-pass routing, final report assembly | **Yes, the only one** |
| `@quant` | sonnet | Research-grade models, toolkit-grounded figures | No |
| `@auditor` | (inherits) | Hypothesis+Falsification+Confidence findings, PASS/REDO verdicts | No |
| `@designer` | (inherits) | The final live artifact: HTML report, charts, data exports | No |
| `@worker` | sonnet | Bounded mechanical deliverables: form-fill, aggregation, lookups | No |
| `@trader` | sonnet | Documented, unexecuted trade theses; scaffold-only | No |

`skills/myfi/SKILL.md §The flock` is the one-paragraph orientation every subagent reads first; this
file is the deeper dispatch-pattern reference `@advisor` and any dispatching command load when the
task spans more than one agent.

## Dispatch law

- **Only `@advisor` dispatches.** Every other agent is a leaf: `@quant`, `@worker`, `@auditor`,
  `@designer`, and `@trader` never call `Agent` on a sibling. A brief that asks a leaf agent to
  fan out further is a mis-scoped brief, halt with `BRIEF-AMENDMENT REQUEST`, never a mid-lane
  pause and never a silent sub-dispatch.
- **A missing capability is an amendment request, never a silent workaround.** `@worker`
  discovering a deliverable actually needs advisory judgment halts `BRIEF-AMENDMENT REQUEST:
  deliverable requires <agent> lane` (`agents/worker.md §Brief contract`), it does not attempt the
  judgment call itself.
- **The producer never verifies its own artifact.** `@auditor` reviews `@advisor`/`@quant`/
  `@worker`/`@trader` output; it never grades a draft it authored, and no actor grades itself
  before handing off.
- **`@designer` is the last hands, not a co-author.** It performs the final edit pass on a PASS'd
  draft; it does not originate analysis, and it does not re-litigate an `@auditor` finding
  (`agents/designer.md §Hard prohibitions`).
- **`@trader` never dispatches and never executes.** Its `tools:` list wires zero order or
  exchange surface in v0.0.0; opening that surface is a future-patch decision requiring an
  explicit operator sign-off, not something a dispatch brief can grant on the fly
  (`agents/trader.md §Authorization-gate doctrine`).

## The adversarial pairing

`@advisor` and `@quant` (plus `@worker`'s mechanical output when it feeds a client-facing report)
are the **actors**. `@auditor` is the **adversary**: it reads a draft, tries to break it with a
concrete falsification, and returns PASS or REDO. `@designer` is the **final artifact editor**,
positioned after the adversary, never before it. This shape ports shepherd's actor/adversary/
editor triple (`skills/shepherd/references/flock.md §@auditor` in the shepherd repo) directly:

```
ACTOR (@advisor / @quant / @worker / @trader-doc)
  -> ADVERSARY (@auditor: Hypothesis + Falsification + Confidence, PASS | REDO, cap 3)
  -> EDITOR (@designer: final-edit checklist, live artifact)
```

REDO cap 3 governs the ACTOR -> ADVERSARY edge exclusively: 3 attempts through the same specialist,
then escalate to `@advisor` rather than loop a fourth time. Full loop mechanics:
`skills/myfi/references/loop-templates.md §AUDITOR-GATE-REDO`.

## Dispatch pattern selection

| Situation | Pattern | Where defined |
|---|---|---|
| Goal spans more than one specialist, needs decomposing first | Classify-And-Act | `skills/myfi/references/workflow-templates.md` |
| Two or more units are independent | Fanout-And-Synthesize | `skills/myfi/references/workflow-templates.md` |
| Any draft about to reach a client | Adversarial Verification | this file, `§The adversarial pairing` |
| A REDO'd draft needs another pass | AUDITOR-GATE-REDO | `skills/myfi/references/loop-templates.md` |
| A single mechanical deliverable, no decomposition needed | Direct `@worker` dispatch, no fanout | `agents/worker.md §Brief contract` |
| A trade thesis with no live execution in scope | Direct `@trader` dispatch, documentation only | `agents/trader.md §The trade cycle` |

## Halt-code index (cross-flock)

| Code | Owning agent | Trigger |
|---|---|---|
| `BRIEF INVALID` | `@worker`, `@auditor`, `@designer` | missing/empty required brief section |
| `BRIEF-AMENDMENT REQUEST: deliverable requires <agent> lane` | `@worker` | a bounded task turns out to need judgment |
| `AUDITOR-WRITE-PATH` | `@auditor` | a Write outside the auditor's own report path |
| `SKILL-MISSING` | `@auditor` | a concern-specific skill (`compliance`) required and genuinely absent |
| `DESIGNER-PRE-GATE` | `@designer` | asked to finalize a draft with no recorded `@auditor` PASS |
| `DESIGNER-WRITE-PATH` | `@designer` | asked to write outside the artifact output path the dispatcher named |

A dispatcher (`@advisor`, or a command like `/myfi:analyze`/`/myfi:plan`) that receives one of
these halts re-scopes the brief and re-dispatches; it never routes around the halt by doing the
work itself.

## Anti-patterns

- A leaf agent (`@quant`, `@worker`, `@auditor`, `@designer`, `@trader`) calling `Agent` on a
  sibling. Only `@advisor` dispatches, no exceptions.
- `@advisor` patching a specialist's output directly after an `@auditor` REDO instead of
  re-dispatching the specialist (`agents/advisor.md §The dispatch cycle` step 3 forbids this).
- Sending a draft to `@designer` before `@auditor` has recorded a PASS, that is exactly
  `DESIGNER-PRE-GATE` and is never a shortcut worth taking under time pressure.
- Widening `@trader`'s tool surface inside a dispatch brief instead of treating any live-order
  request as a hard non-goal in v0.0.0.
- Two `@auditor` passes grading the same concern on the same draft, that is redundant; split
  concerns instead (compliance vs data-integrity are separate passes, per
  `skills/myfi/references/workflow-templates.md §Adversarial Verification`).

## See also

- `skills/myfi/SKILL.md §The flock` - the one-paragraph orientation every subagent reads first.
- `skills/myfi/references/loop-templates.md` - the per-role bounded loops, REDO cap 3, and the
  `--max`/`new_findings` predicate every convergence template carries.
- `skills/myfi/references/workflow-templates.md` - MYFI-DISPATCH-WAVE, the composite this file's
  dispatch law feeds.
- `agents/advisor.md`, `agents/auditor.md`, `agents/designer.md`, `agents/quant.md`,
  `agents/worker.md`, `agents/trader.md` - the six agent system prompts this file cross-references.
