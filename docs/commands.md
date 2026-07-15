# Commands

Four entry points. Two report pipelines (`analyze`, `plan`), one domain workflow (`taxes`), and
one permanently-closed scaffold (`trade`).

| Command | What it does | Reach for it when |
| :--- | :--- | :--- |
| `/myfi:analyze <subject>` | Single-shot report: one toolkit pull, one flock agent pass, one artifact. | A cheap one-off question, no adversarial gate, no live-artifact finish needed. |
| `/myfi:plan <goal>` | The full `@advisor`-led pipeline: decompose, dispatch `@quant`/`@worker`, gate through `@auditor` (PASS/REDO cap 3), finalize via `@designer`. | The goal spans multiple units of work, needs the compliance pass, or needs a finished live artifact. |
| `/myfi:taxes [tax_year]` | Gathers account activity, classifies income/gains, routes each item to its IRS form, estimates, flags the filing deadline, clears the `@auditor` gate. | Any tax-adjacent question for a given tax year. |
| `/myfi:trade <symbol-or-thesis>` | SCAFFOLD. Documents the agentic trade cycle and halts at a permanently-closed authorization gate. | A trade idea, a risk-scoped thesis, or a walkthrough of the doctrine, never an executed order. |

## `/myfi:analyze`

```text
/myfi:analyze <subject> [--agent=quant|worker] [--out=<path>] [--json]
```

- `<subject>` (required, free text) : the question or lookup.
- `--agent` (default `quant`) : which single flock agent runs the pass. `quant` for a
  modeling-heavy lookup, `worker` for a routine aggregation that needs no judgment. `@advisor` is
  never valid here -- it is the flock's sole dispatcher, reach for `/myfi:plan` instead.
- `--out` (default `.myfi/reports/<slug>-<timestamp>.md`) : where the report lands.
- `--json` : also emit a machine-readable `<out>.json` sidecar.

Pulls real data via the toolkit first (a quote, a `db_*` lookup), dispatches exactly one agent
pass, writes the report artifact, and stops. No `@auditor` gate, no `@designer` finalization, that
distinction is the entire reason to reach for `/myfi:plan` instead.

## `/myfi:plan`

```text
/myfi:plan <goal> [--horizon=<duration>] [--out=<path>] [--redo-cap=3]
```

- `<goal>` (required, free text) : the client's stated goal.
- `--horizon` (optional, e.g. `10y`, `18mo`) : the planning horizon, passed through to `@advisor`'s
  decomposition.
- `--out` (default `.myfi/reports/plan-<slug>-<timestamp>.md`).
- `--redo-cap` (default `3`, hard ceiling `3`) : the `@auditor` REDO count for this run. A value
  above `3` clamps down to `3`, there is no operator override past the hard cap. A run that exhausts
  the cap halts rather than shipping an unaudited plan.

`@advisor` decomposes the goal, dispatches `@quant`/`@worker` to produce, `@auditor` adversarially
gates every draft (Hypothesis + Falsification + Confidence, PASS/REDO), and `@designer` performs
the final artifact pass once the gate clears. See [`flock.md`](flock.md#dispatch-order) for the
full dispatch diagram.

## `/myfi:taxes`

```text
/myfi:taxes [tax_year] [--account taxable|ira|401k|hsa] [--dry-run]
```

- `[tax_year]` (default: the current calendar year).
- `--account` (optional) : scope the run to one account type.
- `--dry-run` : walk the pipeline without writing the filing-actionable summary artifact.

Loads `skills/taxes/SKILL.md` first, the form map and workflow this command implements, then walks
gather, classify, route-to-form, estimate, flag-deadline, and the `@auditor` compliance gate before
anything ships. Never improvises a tax rule the skill does not name.

## `/myfi:trade`

```text
/myfi:trade <symbol-or-thesis> [--dry-run]
```

SCAFFOLD, read that literally. `<allowed-tools>` names only read/research tools plus the toolkit's
read-only `quote`, no order, exchange, or execution tool is wired into this command in this
release, anywhere. It walks a documented seven-step cycle (assess, discover, rank, gate-check,
**halt at the authorization gate**, report, idle) and always stops at step 5, there is no "open"
state this version can reach. Opening that gate in a future release is an explicit operator
decision, not something this command can grow into on its own. See
[`flock.md`](flock.md#trader-read-literally) for the agent-side twin of this same boundary.

## Report artifacts

`analyze` and `plan` both write to `.myfi/reports/` (created on first write), a slug from the
subject/goal plus a UTC timestamp (`date -u +%Y%m%dT%H%M%SZ`) keeps every run's artifact unique and
sortable. `taxes` writes its filing-actionable summary the same way unless `--dry-run` is passed.
`trade` never writes an order, only its documented report.
