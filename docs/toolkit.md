# The toolkit

`services/toolkit/` is a single poetry project (package `myfi_toolkit`) exposed two ways: a CLI
and a stdio MCP server, both backed by the same tool implementations in `myfi_toolkit/tools.py` so
an agent gets identical results whichever surface it calls.

## CLI: `bin/myfi-toolkit`

| Verb | What it does |
| :--- | :--- |
| `--version` / `-V` | Prints `myfi_toolkit.__version__` and exits. No heavy import, this is the fast-gate path. |
| `version` | Same info, through the normal subcommand dispatch. |
| `db init \| migrate \| version [--global]` | `.myfi/myfi.db` lifecycle. `init`/`migrate` apply any pending schema migrations (idempotent, gap-fill). `version` reports the current schema version without writing. `--global` targets the optional `~/.myfi/global.db` instead of the per-project db. |
| `quote <symbol>` | Fetches a market quote via the `MarketDataSource` contract (see [`marketdata.md`](marketdata.md)) and prints it as a JSON object. Always JSON, there is no separate `--json` flag. |
| `stats` | A numpy/pandas/scipy version summary of the current environment, useful for confirming the data stack resolved correctly. |

```bash
bin/myfi-toolkit --version
bin/myfi-toolkit db init
bin/myfi-toolkit quote AAPL
bin/myfi-toolkit stats
```

## MCP: `bin/myfi-mcp`

Registered in `.mcp.json` under the server key `myfi-toolkit`. Its tools surface to agents as
`mcp__plugin_myfi_myfi-toolkit__<tool>`:

| Tool | Mirrors | Notes |
| :--- | :--- | :--- |
| `describe_toolkit` | (no CLI equivalent) | Returns the toolkit's name, version, and the capability payload the CLI is built from, useful for a cold agent to confirm the toolkit is reachable. |
| `quote(symbol)` | `quote <symbol>` | Same `MarketDataSource` call as the CLI, returned as a structured object rather than a printed line. |
| `db_init(use_global=False)` | `db init` | Creates the registry and applies pending migrations. Idempotent. |
| `db_migrate(use_global=False)` | `db migrate` | Applies pending migrations. Idempotent, same underlying call as `db_init`. |
| `db_version(use_global=False)` | `db version` | Reports the current schema version without applying migrations. |

Every flock agent's `tools:` frontmatter wires the subset of these it needs, `@advisor` and
`@quant` get all four (`quote`, `db_init`, `db_migrate`, `db_version`), `@auditor` and `@trader`
only need `quote`. Prefer the MCP tool over shelling out to the CLI from inside an agent turn, it
avoids a subprocess and returns a typed object instead of a string to parse.

## The database

A per-project registry at `.myfi/myfi.db` (git-ignored, WAL journal mode, foreign keys on), plus an
optional global `~/.myfi/global.db` for state you want to share across projects. Both are gap-fill
migrated from `myfi_toolkit/myctx/schema/*.sql`, `0001_init.sql` is the v0.0.0 baseline:
`projects`, `sessions`, `mem_entries` (doctrine/notes/decisions/priors, with a `prior` kind baked in
from the start), `discovery_findings`, and `audit_findings`, plus a `v_mem_recent_7d` view. This is
what backs the `improve` skill's harvest/store/inject/cite loop, see [`flock.md`](flock.md#the-four-skills).

`skills/improve/SKILL.md` reads and writes this database directly through `myfi_toolkit.myctx`,
there is no separate client library, the schema module is the client.

## Fast-gate discipline

`myfi_toolkit.cli` never imports numpy, pandas, scipy, matplotlib, or the `mcp` SDK at module
scope, those imports sit on the hot path of `bin/myfi-toolkit --version` and the plugin's fast
gate tests, both of which must stay under two seconds. Every subcommand handler that needs the
heavy data stack (or the `myctx`/`marketdata` subpackages) imports it lazily, inside the function
that needs it, never at the top of the file. Any code that touches matplotlib calls
`matplotlib.use("Agg")` before importing `pyplot`, headless-safe, no display backend assumed.

## The LLM law

Nothing under `services/toolkit/` calls a hosted inference API. Any latent-quality scoring of this
toolkit's own output (`services/eval/rubrics/toolkit.rubric.json`) routes through
`services/llm/llm.py`, which shells out to your local Claude Code, see
[`configuration.md`](configuration.md#llm) for the full LLM law.

## Development

```sh
poetry -C services/toolkit install
poetry -C services/toolkit run pytest -q
poetry -C services/toolkit run ruff check myfi_toolkit tests
```

`poetry -C <dir>` changes the working directory the command resolves before it looks at any
trailing path arguments, so paths passed to `pytest`/`ruff` above are already relative to
`services/toolkit/`, do not re-prefix them with `services/toolkit/` or poetry looks for a
nested `services/toolkit/services/toolkit/...` path and fails.
