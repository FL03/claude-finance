# myfi (golden: good)

An all-in-one financial plugin: a wall-street grade financial planner, a custom research toolkit,
and a set of skills aiming for a QUANT-level understanding of market conditions.

myfi is a Claude Code plugin that turns a session into a small financial firm: a dispatcher that
assembles client-ready reports, a research-grade quant, a compliance adversary, a final-artifact
editor, a bounded catch-all worker, and a trade-idea scaffold with no live execution surface.

## The flock

Six agents, closed at six:

| Agent | Job |
| :--- | :--- |
| `@advisor` | Decomposes a client goal, dispatches the rest of the flock, assembles the final report. |
| `@quant` | Research-grade modeling: pricing, risk, portfolio, factor analysis, grounded in toolkit data. |
| `@auditor` | Compliance/local-law adversarial review, Hypothesis + Falsification + Confidence, PASS/REDO cap 3. |
| `@designer` | Final artifact editor: live-HTML reports, matplotlib charts, data exports. |
| `@worker` | Bounded catch-all for routine, well-defined chores. |
| `@trader` | Scaffold-only trade-cycle doctrine, zero live-execution surface in this release. |

`@advisor` dispatches `@quant`/`@worker` to produce, `@auditor` adversarially gates every draft,
and `@designer` performs the final artifact pass once the gate clears.

## Install

```text
/plugin marketplace add FL03/myfi
/plugin install myfi@fl03
```

Runtime needs: `git`, `bash`, Python 3.14+, and `poetry` for the toolkit venv. No API key required.

## Quickstart

```bash
bin/myfi-toolkit --version
bin/myfi-toolkit db init
```

```text
/myfi:analyze "should I refinance this year?"
```

## The toolkit

`services/toolkit` is a poetry project exposing `bin/myfi-toolkit` (CLI: `--version`, `db
init|migrate|version`, `quote <symbol>`, `stats`) and `bin/myfi-mcp` (stdio MCP server, tools
`describe_toolkit`, `quote`, `db_init`, `db_migrate`, `db_version`). It fronts a per-project SQLite
registry (`.myfi/myfi.db`) and the `MarketDataSource` adapter contract, which degrades to a
self-contained research provider when no API key is configured.

## Commands

`/myfi:analyze` (single-shot report), `/myfi:plan` (full advisor-led pipeline with the compliance
gate), `/myfi:taxes` (tax-year workflow), `/myfi:trade` (SCAFFOLD, permanently-closed authorization
gate, never places a live order).
