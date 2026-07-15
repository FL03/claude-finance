# The flock

myfi runs six agents, closed at six on purpose. Each has one job and a fixed place in the
dispatch order. `@advisor` is the only one that dispatches the others.

| Agent | Model | Job | Reach for it when |
| :--- | :--- | :--- | :--- |
| `@advisor` | opus | Decomposes a client goal, dispatches the rest of the flock, adversarially reviews their output, assembles the final report. | A client goal needs decomposing across more than one specialist, or you need the finished, synthesized report. |
| `@quant` | sonnet | Research-grade modeling: pricing, risk, portfolio, factor, or prediction-market analysis, grounded in toolkit data, reported as Assumptions / Methodology / Results / Caveats. | The unit of work needs real numerical modeling, not routine aggregation. |
| `@auditor` | sonnet | Compliance and local-law adversarial review. Runs the Hypothesis + Falsification + Confidence triple against a draft, verdicts PASS or REDO (cap 3). | Any draft cites a number, a jurisdiction, a regulation, or a risk claim that has not yet been checked. |
| `@designer` | sonnet | Final artifact editor. Owns every live output surface: the live-HTML report, matplotlib (Agg) charts, CSV/JSON exports. Performs the last edit pass once `@auditor` gates a draft PASS. | A PASS'd draft needs to become the artifact a client or command actually reads. |
| `@worker` | sonnet | Bounded catch-all for routine, well-defined chores: form-fill, data aggregation, toolkit lookups, report-skeleton formatting. | The task is mechanical and bounded, and does not need advisory judgment, modeling, compliance review, or a final artifact pass. |
| `@trader` | sonnet | Scaffold-only. Documents the shape of an agentic trade cycle (discover, rank, gate-check, halt-and-report) and the authorization-gate doctrine a future live step would need to clear. | A client's plan calls for a trade idea, a risk-scoped thesis, or a walkthrough of the doctrine, never to place, confirm, cancel, or monitor a live order. |

## Model policy

The `Model` column is the shipped roster: one opus seat (`@advisor`, the sole orchestrator) and five
sonnet specialists. It is not advisory prose -- it is enforced in three places that must agree, or
the gate goes red:

- **Each `agents/<name>.md` frontmatter** pins `model:` explicitly. No agent inherits the session's
  model, so a session running on opus can never silently fan the whole flock out on opus.
- **`myfi_toolkit.config.FLOCK_DEFAULT_MODELS`** (`services/toolkit/myfi_toolkit/config.py`) mirrors
  the same roster for any caller or test that needs to ask "which model for `@<agent>`" in code.
- **`test_config.py::test_flock_frontmatter_matches_roster`** reads every agent's frontmatter and
  fails if one lacks a `model:` line or disagrees with the roster. That test is what makes an
  accidental all-opus wave un-mergeable rather than merely discouraged.

An operator retargets the flock in `.claude/myfi.toml` without touching any of the above.
`myfi_toolkit.config.flock_model(agent)` resolves, highest precedence first:

1. an explicit per-run model a dispatcher passes for that call;
2. `[flock].<agent>` -- a per-agent pin (e.g. `designer = "opus"` to put final-artifact polish on
   opus);
3. `[flock].default` -- a flock-wide floor (set it to `sonnet` to force every seat cheap, or to
   `opus` to lift them all at once);
4. the shipped `FLOCK_DEFAULT_MODELS` roster above;
5. `sonnet`, the hardcoded floor for an unknown agent name.

The default is the roster, the override is one line, and nothing an operator sets can leave an agent
with no model at all.

## Dispatch order

`@advisor` dispatches `@quant` and `@worker` to produce, sends their output to `@auditor` for the
adversarial gate, and once `@auditor` verdicts PASS, hands the draft to `@designer` for the final
artifact pass. `@trader` sits outside this main line: it is dispatched directly for a trade-idea
walkthrough and never touches the exchange-side of anything, no order tool is wired into it, in
this or any current-release command.

```text
client goal
     |
  @advisor  ---dispatch--->  @quant / @worker   (produce)
     |                              |
     |<-----------------------------
     |
  @auditor    (adversarial gate, PASS / REDO x3)
     |
  @designer   (final live artifact)
     |
final report
```

## `@trader`, read literally

`@trader` is scaffold-only in this release. No order-placement, order-submission, confirmation, or
cancellation tool is wired into its `tools:` list, anywhere. It exists to document the doctrine a
future gated execution path would need to clear, not to act on it. `/myfi:trade` is the
command-tier twin of this same boundary, see [`commands.md`](commands.md#myfitrade).

## Adversarial pairing

`@advisor`/`@quant` (and `@worker`'s output, when it flows through a pipeline) are the actors;
`@auditor` is the adversary. Every PASS/REDO verdict is capped at 3 REDOs, an actor that cannot
clear the gate in three passes stops instead of looping forever. `skills/compliance/SKILL.md` gives
`@auditor` its regulatory baseline (suitability vs fiduciary duty, Reg BI, disclosure, KYC/AML
basics, insider trading/MNPI, marketing rules, recordkeeping), scoped to US-federal,
retail-investing-adjacent rules, and the discipline to flag "outside my jurisdiction" instead of
guessing when a report crosses into territory it does not cover.

## The five skills

| Skill | Loaded by | What it adds |
| :--- | :--- | :--- |
| `skills/myfi/SKILL.md` | Every agent, first, every session. | Orientation: where the toolkit lives, which agent to dispatch, the four commands, the LLM-routing law. Not a manual, a map. |
| `skills/finance/SKILL.md` | `@quant`, mandatory for every modeling unit; `@advisor`, `@auditor`, `@designer`, `@worker`, and `@trader` load it to whatever depth their own task needs. | The quant reference set: stochastic calculus and risk theory (`QUANT.md`), the pricing/risk/portfolio model zoo (`MODELS.md`), prediction-market probability (`PREDICTION.md`), and execution microstructure (`MICROSTRUCTURE.md`) -- so a modeled number names a real model instead of a vibe. |
| `skills/compliance/SKILL.md` | `@auditor`, and `/myfi:taxes`/`/myfi:trade` before their compliance gate. | The regulatory checklist an audit pass runs. |
| `skills/taxes/SKILL.md` | `/myfi:taxes`, and any agent producing tax-adjacent output. | The gather-classify-route-estimate-flag-gate-summarize workflow and the IRS form map behind it. |
| `skills/improve/SKILL.md` | Before a close, a fresh dispatch, or a REDO that feels familiar. | The harvest/store/inject/cite loop: turns `@auditor` findings and discovery notes into durable per-project priors in `myctx`, so the flock does not relearn the same failure twice. |

See [`toolkit.md`](toolkit.md) for the CLI/MCP surface every agent shares, and
[`commands.md`](commands.md) for how a command threads the flock together end to end.
