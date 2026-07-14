---
description: The dynamic-workflow fan-out shape for the myfi six-agent flock, a compile-down projection of a small pattern library onto the native Dynamic Workflow tool when it is present, and an in-context walk of the same graph when it is not. Read before authoring any dispatch sequence that spans more than one flock agent.
---

# Workflow Templates (myfi)

Ported from shepherd's pattern library (`skills/harness/references/workflow-templates.md` in the
shepherd repo) and trimmed to the four patterns myfi's closed six-agent flock actually uses. Every
dispatch sequence below is a projection of one graph: `@advisor` classifies and routes, `@quant` /
`@worker` / `@trader` produce in parallel where their units are independent, `@auditor`
adversarially gates the result, and `@designer` performs the final artifact edit.

## Pattern library (myfi's four)

| # | Pattern | Select when | Flock binding |
|---|---|---|---|
| 1 | Classify-And-Act | The client's goal spans more than one specialist and needs decomposing first | `@advisor` decomposes, then routes each unit |
| 2 | Fanout-And-Synthesize | Two or more units are independent and non-overlapping (a `@quant` model and a `@worker` aggregation, say) | parallel `@quant`/`@worker`/`@trader`-doc, then `@advisor` synthesizes |
| 3 | Adversarial Verification | Any draft that will reach a client needs an independent challenge before it is finalized | producer (`@advisor`/`@quant`/`@worker`/`@trader`) then `@auditor`, cap 3 REDO |
| 6 | Loop-Until-Done | Completion means "no CRITICAL/HIGH finding remains," not a fixed step count | `@auditor` REDO ladder, see `skills/myfi/references/loop-templates.md` |

Patterns 4 (Generate-And-Filter) and 5 (Tournament) from the shepherd source do not apply here:
myfi's flock has no `@critic`-equivalent absolute-rubric gate and no comparative-ranking use case
in v0.0.0. If a later patch adds one (a multi-strategy `@quant` bake-off, say), port those two
patterns then, not speculatively now.

1. **Classify-And-Act.** `@advisor` reads the client's goal and emits a decomposition: which units
   need `@quant`, which need `@worker`, whether `@trader`'s scaffold-only cycle documentation is
   even in scope (`agents/advisor.md §The dispatch cycle` step 1). A goal with no matching
   specialist surfaces to the operator rather than getting force-fit into the nearest agent.
2. **Fanout-And-Synthesize.** Independent units dispatch in parallel: a `@quant` model and a
   `@worker` aggregation that do not depend on each other's output run concurrently, then
   `@advisor` synthesizes both into the assembled report. `@worker` never dispatches a fanout of
   its own (it is a bounded catch-all, not a sub-dispatcher); only `@advisor` fans out.
3. **Adversarial Verification.** Every actor's output, `@advisor`'s own composition included, goes
   through `@auditor` before `@designer` ever sees it. Concern split is mandatory when more than
   one dimension needs checking (a compliance concern and a data-integrity concern on the same
   draft are two separate `@auditor` passes, not one blended finding list). The producer never
   verifies its own artifact.
4. **Loop-Until-Done (the REDO ladder).** `@auditor`'s PASS/REDO cycle, capped at REDO cap 3, is
   the flock's only Loop-Until-Done instance. Full mechanics: `skills/myfi/references/
   loop-templates.md §AUDITOR-GATE-REDO`.

## The named composite: MYFI-DISPATCH-WAVE

The one composite every `/myfi:analyze` and `/myfi:plan` invocation runs, stated once here so no
command or agent re-derives it from scratch:

```
CLASSIFY (@advisor decomposes the goal)
  -> FANOUT (parallel @quant / @worker / @trader-doc units, only where independent)
  -> SYNTHESIZE (@advisor composes the draft)
  -> VERIFY (@auditor gate, REDO cap 3 -> skills/myfi/references/loop-templates.md)
  -> FINALIZE (@designer final-edit pass -> skills/myfi/references/loop-templates.md
     §DESIGNER-CHECKLIST-CONVERGE)
  -> ASSEMBLE (@advisor emits the client-facing report)
```

`@trader` participates only as a documentation-producing leaf inside FANOUT (a trade thesis, never
a live order) and is never itself a classify, synthesize, verify, or finalize step. A dispatch that
skips VERIFY to save a round-trip is not a smaller version of MYFI-DISPATCH-WAVE, it is a different,
unaudited path and must not ship a client-facing artifact (`agents/advisor.md §Hard prohibitions`).

## Compile-down, or the in-context fallback

When the native Dynamic Workflow tool is present, `@advisor`'s FANOUT step compiles to a bounded
parallel dispatch (the independent `@quant`/`@worker`/`@trader` units run concurrently, results
land in script variables, `@advisor` stays responsive while they run). When the tool is confirmed
absent, the same graph walks in-context instead: `@advisor` dispatches each unit sequentially with
`Agent`, same flock, same briefs, same VERIFY/FINALIZE order, just without the parallel win. Record
which mode ran once per session; never retry the presence check mid-dispatch and never report the
feature broken when the honest answer is "absent, degraded cleanly."

**Faithfulness, minimal version for a six-agent flock.** Whichever mode runs, three things MUST
hold: (1) soundness, every dispatch in the run maps to a node in MYFI-DISPATCH-WAVE, nothing
invented; (2) completeness, VERIFY always runs before FINALIZE, never skipped or reordered; (3)
determinism, the same classification from `@advisor` always produces the same dispatch sequence.

## Anti-patterns

- Running FINALIZE before VERIFY returns PASS (`@designer` halts `DESIGNER-PRE-GATE` if asked to).
- `@worker` or `@quant` dispatching a sub-unit of its own; only `@advisor` fans out in this flock.
- Skipping the parallel fanout when the tool is present and hand-rolling a sequential dispatch
  instead, for units that are genuinely independent, that wastes the wall-clock win for no reason.
- Treating `@trader`'s documentation output as if it were a live execution branch inside FANOUT; it
  is a leaf that always halts at its own Authorization Gate
  (`skills/myfi/references/loop-templates.md §@trader: no loop surface`).
- Assembling the final report on partial completion; MYFI-DISPATCH-WAVE's ASSEMBLE step is
  all-or-nothing across every dispatched unit, never a synthesis of whatever happened to finish.

## See also

- `skills/myfi/references/loop-templates.md` - the REDO ladder and per-role convergence loops that
  VERIFY and FINALIZE specialize.
- `skills/myfi/references/agent-team-templates.md` - the flock dispatch law (who may dispatch
  whom) and the adversarial pairing this composite assumes.
- `agents/advisor.md §The dispatch cycle` - the canonical five-step cycle this file names as a
  reusable composite.
- `commands/analyze.md`, `commands/plan.md` - the two entry points that run MYFI-DISPATCH-WAVE.
