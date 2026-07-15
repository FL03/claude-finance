# myfi

[![GitHub License](https://img.shields.io/github/license/FL03/claude-finance?style=for-the-badge&logo=github)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/FL03/claude-finance?style=for-the-badge&logo=github)](https://github.com/FL03/claude-finance/releases)
[![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-d97757?style=for-the-badge)](https://github.com/FL03/claude-finance)

---

> An all-in-one financial plugin: a wall-street grade financial planner, a custom research toolkit,
> and a set of skills that together aim for a QUANT-level understanding of market conditions.

myfi is a [Claude Code](https://claude.com/claude-code) plugin that turns a session into a small
financial firm: a dispatcher that assembles client-ready reports, a research-grade quant, a
compliance adversary, a final-artifact editor, a bounded catch-all worker, and a trade-idea
scaffold with no live execution surface. Backing them is one Python toolkit (CLI + MCP server), a
per-project database, and a market-data adapter contract that never hallucinates a price.

No build step, no server to run. Everything ships as markdown (agents, skills, commands), one
poetry-managed service layer, and a stdio MCP server wired through `.mcp.json`.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  /myfi:analyze <subject>   Single-shot report, one agent pass            │
│  /myfi:plan <goal>         Full advisor-led flock pipeline               │
│  /myfi:taxes [tax_year]    Tax-workflow pipeline, forms + deadline       │
│  /myfi:trade <thesis>      SCAFFOLD, authorization gate, no live orders  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Contents

- [Why myfi](#why-myfi)
- [How it works in 60 seconds](#how-it-works-in-60-seconds)
- [Install](#install)
- [Quickstart](#quickstart)
- [Commands](#commands)
- [The toolkit](#the-toolkit)
- [Market data](#market-data)
- [Configure](#configure)
- [Troubleshooting and FAQ](#troubleshooting-and-faq)
- [File map](#file-map)
- [Versioning](#versioning)
- [Contributing](#contributing)
- [License](#license)

---

## Why myfi

| What you want | What myfi gives you |
| :--- | :--- |
| A real, client-ready report, not a chat reply | `@advisor` assembles one synthesized artifact from every specialist it dispatches, not a raw agent transcript. |
| Numbers grounded in real data | Every quote routes through the `MarketDataSource` contract, no provider means a self-contained research-degrade default, never a fabricated price. |
| A compliance check before anything ships | `@auditor` runs a Hypothesis + Falsification + Confidence pass on every draft, PASS/REDO, capped at 3 cycles. |
| Confidence that a trade idea stays an idea | `@trader` and `/myfi:trade` ship with zero live-execution surface, no order tool is wired in anywhere in this release. |
| Your data staying yours | Every model call routes through `services/llm` to your **local** Claude Code, never a hosted inference API. |
| A place for the flock to remember what it learned | A per-project SQLite registry (`.myfi/myfi.db`) backs the `improve` skill's harvest/store/inject/cite loop, findings become durable priors instead of being relearned. |

## How it works in 60 seconds

**1. A closed flock of six agents.** Each has one job.

| Agent | Job |
| :--- | :--- |
| `@advisor` | Decomposes a goal, dispatches the flock, assembles the final report. |
| `@quant` | Research-grade modeling: pricing, risk, portfolio, factor analysis. |
| `@auditor` | Compliance/local-law adversarial review, PASS or REDO. |
| `@designer` | Final artifact editor: live-HTML reports, matplotlib charts, data exports. |
| `@worker` | Bounded catch-all for routine, well-defined chores. |
| `@trader` | Scaffold-only trade-cycle doctrine. No live execution, ever, in this release. |

See [`docs/flock.md`](docs/flock.md) for the full dispatch order and each agent's boundary.

**2. One shared toolkit.** `services/toolkit` is a single poetry project exposed as a CLI
(`bin/myfi-toolkit`) and a stdio MCP server (`bin/myfi-mcp`, registered in `.mcp.json`), carrying
numpy, pandas, scipy, and matplotlib (Agg backend). It fronts a per-project SQLite registry and the
market-data adapter contract every quote goes through. See [`docs/toolkit.md`](docs/toolkit.md).

**3. Four commands.** `/myfi:analyze` for a cheap single-shot report, `/myfi:plan` for the full
advisor-led pipeline with the compliance gate, `/myfi:taxes` for the tax-year workflow, and
`/myfi:trade` for a documented, permanently non-executing trade-idea walkthrough. See
[`docs/commands.md`](docs/commands.md).

---

## Install

### From the marketplace (recommended)

```text
/plugin marketplace add FL03/claude-finance
/plugin install myfi@fl03
```

Update later with `/plugin update myfi@fl03`.

### Personal symlink or per-project pin

```bash
git clone https://github.com/FL03/claude-finance.git ~/src/FL03/claude-finance
ln -s ~/src/FL03/claude-finance ~/.claude/plugins/myfi      # personal
ln -s /path/to/FL03/claude-finance .claude-plugin/myfi      # per-project (mkdir -p .claude-plugin first)
```

No build system. Runtime needs: `git`, `bash`, Python 3.12+, `poetry` for the toolkit venv (falls
back to a `PYTHONPATH` install if absent), and `claude` on `PATH` for the LLM law below. No API key
is required to get started. Full detail: [`docs/install.md`](docs/install.md).

---

## Quickstart

From zero to your first report in about a minute, no API key needed.

```bash
# 1. Configure myfi for this repo (optional, every key has a working default).
mkdir -p .claude
cp /path/to/myfi/examples/minimal/myfi.toml .claude/myfi.toml

# 2. Verify the toolkit is reachable.
bin/myfi-toolkit --version
bin/myfi-toolkit db init
bin/myfi-toolkit quote AAPL
```

Then, in Claude Code:

```text
/myfi:analyze "should I refinance this year?"
```

That single-shot pass pulls real data via the toolkit, dispatches one flock agent, and writes a
report to `.myfi/reports/`. Reach for `/myfi:plan` next for a multi-step engagement that clears the
compliance gate; see the [Commands](#commands) table below.

---

## Commands

| Command | What it does |
| :--- | :--- |
| `/myfi:analyze <subject> [--agent=...] [--out=<path>] [--json]` | Single-shot report: one toolkit pull, one flock agent pass, one artifact. |
| `/myfi:plan <goal> [--horizon=<duration>] [--out=<path>] [--redo-cap=3]` | The full `@advisor`-led pipeline: decompose, produce, adversarially gate, finalize. |
| `/myfi:taxes [tax_year] [--account ...] [--dry-run]` | Gather, classify, route to IRS form, estimate, flag the filing deadline, gate, summarize. |
| `/myfi:trade <symbol-or-thesis> [--dry-run]` | SCAFFOLD. Documents the trade cycle, halts at a permanently-closed authorization gate. |

Full flags, examples, and the report-artifact convention: [`docs/commands.md`](docs/commands.md).

---

## The toolkit

One poetry project, two entry points, one shared tool layer:

- **CLI** (`bin/myfi-toolkit`): `--version`, `db init|migrate|version [--global]`, `quote
  <symbol>`, `stats`.
- **MCP** (`bin/myfi-mcp`, server key `myfi-toolkit` in `.mcp.json`): tools surface as
  `mcp__plugin_myfi_myfi-toolkit__<tool>`: `describe_toolkit`, `quote`, `db_init`, `db_migrate`,
  `db_version`.
- **Database**: a per-project `.myfi/myfi.db` (git-ignored, WAL) plus an optional global
  `~/.myfi/global.db`, gap-fill migrated from `myfi_toolkit/myctx/schema/*.sql`.

Heavy imports (numpy/pandas/scipy/matplotlib/mcp) stay lazy inside subcommand handlers, never at
module scope, so `bin/myfi-toolkit --version` stays fast. Full reference:
[`docs/toolkit.md`](docs/toolkit.md).

## Market data

Every quote goes through one typed contract, `MarketDataSource`, and every provider is honest about
where its number came from (`Quote.source`). The v0.0.0 default, `research`, is self-contained and
needs no API key; `finnhub`, `yfinance`, and `fred` are registered behind the same contract but
deferred until a follow-up release wires the concrete HTTP client. Full contract and the provider
table: [`docs/marketdata.md`](docs/marketdata.md).

---

## Configure

Create `.claude/myfi.toml` at the repo root, a template lives at
[`examples/minimal/myfi.toml`](examples/minimal/myfi.toml). No section is required, every key has a
working default. It's parsed by `myfi_toolkit.config` and consulted by the toolkit, market-data
adapter selection, and `services/llm`'s model default -- each key falls back to an env var
(`MYFI_LLM_MODEL`, `MYFI_MARKETDATA_PROVIDER`) then a hardcoded default if unset here.

```toml
[toolkit]
db = ".myfi/myfi.db"

[llm]
model = "claude-opus-4-8"

[marketdata]
provider = "research"
```

Full schema and precedence order: [`docs/configuration.md`](docs/configuration.md).

---

## Troubleshooting and FAQ

| Question | Answer |
| :--- | :--- |
| `bin/myfi-toolkit --version` is slow | It should not be, that path never imports numpy/pandas/scipy/matplotlib. If it is, check for a stale venv, `bin/myfi-venv-ensure` runs on every session start. |
| `poetry: command not found` | Not fatal, `bin/myfi-toolkit`/`bin/myfi-mcp` fall back to `python3 -m myfi_toolkit.<module>` on `PYTHONPATH`. Install `poetry` for the maintained venv path. |
| `.myfi/myfi.db` does not exist yet | Run `bin/myfi-toolkit db init`, or call `mcp__plugin_myfi_myfi-toolkit__db_init` from inside an agent turn, both are idempotent. |
| A quote always returns the same placeholder price | You are on the default `research` provider, it is self-contained and does not hit a live feed. Set `MYFI_MARKETDATA_PROVIDER` once a concrete provider ships. |
| Can `/myfi:trade` place an order? | No. No order, exchange, or execution tool is wired into `/myfi:trade` or `@trader` anywhere in this release, see [`docs/flock.md`](docs/flock.md#trader-read-literally). |
| Anything sent to a third-party LLM API? | No, every model call routes through `services/llm` to your local Claude Code. |
| A report artifact did not appear | Check `.myfi/reports/`, `analyze`/`plan`/`taxes` all write there unless `--dry-run` was passed. |

---

## File map

| Path | Purpose |
| :--- | :--- |
| `.claude-plugin/plugin.json` | Plugin manifest. |
| `agents/{advisor,quant,auditor,designer,worker,trader}.md` | The closed flock. |
| `commands/{analyze,plan,taxes,trade}.md` | The four entry points. |
| `skills/{myfi,compliance,taxes,improve}/` | Core orientation, regulatory knowledge, tax workflow, the self-improvement loop. |
| `services/toolkit/` | The `myfi_toolkit` poetry project: CLI, MCP server, `myctx` database, `marketdata` adapter. |
| `services/{llm,eval}/` | The local-Claude-Code LLM service and the rubric-scored eval harness. |
| `hooks/hooks.json` + `hooks/scripts/` | Lifecycle hooks (dispatch guard, dedup guard, venv bootstrap, self-improve capture). |
| `bin/` | Root wrappers: `myfi-toolkit`, `myfi-mcp`, `myfi-llm`, `myfi-eval`, `myfi-venv-ensure`, `myfi-test`. |
| `docs/{install,configuration,flock,toolkit,commands,marketdata}.md` | This documentation. |
| `examples/minimal/myfi.toml` | Starter config. |
| `tests/` | Structural gates and the end-to-end integration suite. |

---

## Versioning

Semantic versioning. Current version: **0.0.3**. The first complete, installable release was
**0.0.0** (the foundation); 0.0.1 renamed the repository and 0.0.2 is a version bump. See
[`CHANGELOG.md`](CHANGELOG.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). All
main-bound changes flow through a PR; the hook suite (`bash hooks/tests/run.sh`) and
`bin/myfi-test` must stay green.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
