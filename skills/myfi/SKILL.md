---
name: myfi
description: Core orientation scaffold for every myfi session and subagent -- points to the toolkit (CLI + MCP + per-project DB), the six-agent flock, the four entry-point commands, and the LLM-routing law. Load this first; deep domain knowledge lives in the finance, compliance, taxes, and improve skills.
---

# MYFI -- core scaffold

Read this first, every session and every subagent. It orients you to where things live in this
plugin; it is not a manual. Domain depth lives in the `finance`, `compliance`, `taxes`, and
`improve` skills -- load those when the task actually needs them.

## The toolkit

`services/toolkit/` is a poetry project (package `myfi_toolkit`) exposed two ways:

- **CLI** -- `bin/myfi-toolkit <verb>`. Verbs: `--version` (fast, no heavy imports), `quote <symbol>
  [--json]` (market data via the `MarketDataSource` contract, degrades to `research` with no
  provider env set), `db init` / `db migrate` / `db version` (per-project SQLite lifecycle).
- **MCP** -- `bin/myfi-mcp`, a stdio server registered in `.mcp.json` under the key `myfi-toolkit`.
  Its tools surface to agents as `mcp__plugin_myfi_myfi-toolkit__<tool>` (e.g.
  `mcp__plugin_myfi_myfi-toolkit__quote`). Prefer the MCP tool over shelling out to the CLI from
  inside an agent turn.
- **Database** -- a per-project `.myfi/myfi.db` (git-ignored, WAL, `foreign_keys=ON`), plus an
  optional global `~/.myfi/global.db` via `--global`. Both are gap-fill migrated from
  `myfi_toolkit/myctx/schema/*.sql`.

Heavy imports (numpy/pandas/scipy/matplotlib/mcp) are lazy -- never top-level in `cli.py` -- so
`bin/myfi-toolkit --version` stays fast (<2s fast-gate rule).

## The flock

Six agents, one adversarial pair, one dispatcher:

| Agent | Reach for it when |
|---|---|
| `@advisor` (opus) | the client's goal needs decomposing, the flock needs dispatching, and a final report needs assembling |
| `@quant` | you need research-grade modeling -- numpy/pandas/scipy analysis that cites its data |
| `@auditor` | any actor's output needs a compliance/local-law adversarial pass -- Hypothesis+Falsification+Confidence, PASS/REDO, cap 3 |
| `@designer` | a live artifact needs its final edit pass -- matplotlib (Agg) charts, HTML reports, data exports |
| `@worker` | a routine, bounded finance task -- form-fill, aggregation -- doesn't need a specialist |
| `@trader` | scaffold-only in v0.0.0 -- documents the agentic cycle + authorization gate; wires **no** order/exchange tool and never executes live |

`@advisor` dispatches; `@quant` and `@worker` produce; `@auditor` adversarially reviews;
`@designer` finalizes the artifact. `@trader` never trades in this version -- it exists to document
the doctrine, not to act on it.

## Entry-point commands

- `/myfi:analyze` -- single-shot financial report for one goal.
- `/myfi:plan` -- `@advisor`-led planning pipeline that dispatches the flock.
- `/myfi:taxes` -- tax-workflow pipeline.
- `/myfi:trade` -- authorization-gated scaffold; halts before any live action.

## The LLM law

Every model call in this plugin routes through `services/llm` (`services/llm/llm.py`), which
shells out to **local Claude Code**. Never a hosted inference API -- not Anthropic's, not OpenAI's,
not any provider's -- anywhere in this plugin, no exceptions. `services/eval` scores latent outputs
(agent reports, this skill's own orientation) against a rubric through that same
local-Claude-Code seam.

## TOOLKIT reference

CLI verbs (`bin/myfi-toolkit`):

- `--version` -- fast smoke check, no heavy imports.
- `quote <symbol> [--json]` -- `default_source().quote(symbol)`.
- `db init` / `db migrate` / `db version` -- `.myfi/myfi.db` lifecycle.

MCP tools (`bin/myfi-mcp`, server key `myfi-toolkit` in `.mcp.json`):

- `mcp__plugin_myfi_myfi-toolkit__quote`
- `mcp__plugin_myfi_myfi-toolkit__db_init`
- `mcp__plugin_myfi_myfi-toolkit__db_migrate`
- `mcp__plugin_myfi_myfi-toolkit__db_version`

## Orienting cold

Landed here with nothing else loaded? You now know: where the toolkit lives and how to call it
(CLI or MCP), which of the six flock agents to dispatch for a given need, the four commands a user
can invoke, and that every model call goes through `services/llm` -- never a hosted API. Load a
domain skill (`finance`, `compliance`, `taxes`, `improve`) for depth; this scaffold only orients.
