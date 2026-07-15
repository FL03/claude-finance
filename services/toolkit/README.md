# services/toolkit -- myfi_toolkit

The Python3/poetry core lib behind the myfi finance plugin's CLI and stdio MCP
server. One package (`myfi_toolkit`), two console scripts, one shared tool
layer -- carries numpy/pandas/scipy/matplotlib, the per-project + optional
global SQLite registry (`myctx`, Wave 3), and the market-data adapter contract
(`marketdata`, Wave 3).

## Layout

```
services/toolkit/
├── pyproject.toml           poetry project: deps, dev-deps, console scripts
├── myfi_toolkit/
│   ├── __init__.py          __version__ -- single source of truth for semver
│   ├── cli.py                stdlib argparse dispatcher (fast-gate module)
│   ├── mcp_server.py          FastMCP stdio server wiring
│   ├── tools.py               tool implementations shared by cli.py + mcp_server.py
│   ├── myctx/                 per-project/global SQLite registry (Wave 3)
│   └── marketdata/             market-data adapter contract (Wave 3)
└── tests/
    ├── test_cli.py            gate: version/exit-code behavior, <2s
    ├── test_mcp_smoke.py       gate: MCP tool listing + eval mock-lane margin
    └── evals/{good,bad}_tool_output.txt   goldens for the toolkit eval
```

## The two entry points

- `myfi-toolkit` → `myfi_toolkit.cli:main` -- the CLI. Subcommands: `version`,
  `db <init|migrate|version> [--global]` (Wave 3), `quote <symbol>` (Wave 3),
  `stats` (numpy/pandas/scipy version summary).
- `myfi-mcp` → `myfi_toolkit.mcp_server:main` -- the stdio MCP server
  (`FastMCP("myfi-toolkit")`), registered in the plugin root's `.mcp.json`.
  Exposes `describe_toolkit()`, returning the same capability payload the CLI
  is built from.

Root-level wrappers (`bin/myfi-toolkit`, `bin/myfi-mcp`) run `poetry run` when
poetry is on PATH, falling back to `python3 -m myfi_toolkit.<module>` on
`PYTHONPATH` otherwise. `bin/myfi-venv-ensure` installs/refreshes this
project's venv under `${CLAUDE_PLUGIN_DATA}` (idempotent -- diffs
`pyproject.toml` against a stored copy); the plugin's SessionStart hook calls
it on every session start.

## Fast-gate discipline

`myfi_toolkit.cli` MUST NOT top-level-import numpy/pandas/scipy/matplotlib/mcp
-- it is on the hot path of `bin/myfi-toolkit --version` and the CLI import
smoke test, both of which must stay under 2 seconds. Every subcommand handler
that needs the heavy data stack (or the Wave-3 `myctx`/`marketdata`
subpackages) imports it lazily, inside the function that needs it. Any code
that touches matplotlib must call `matplotlib.use("Agg")` before importing
`pyplot` (headless-safe; no display backend assumed).

## Dev workflow

`poetry -C <dir>` changes the working directory the command resolves
*before* it looks at any trailing path arguments (`poetry help run`), so
paths passed to `pytest`/`ruff` below are already relative to
`services/toolkit/` -- do not re-prefix them with `services/toolkit/` or
poetry will look for `services/toolkit/services/toolkit/...` and fail with
exit 4 ("file or directory not found").

```sh
poetry -C services/toolkit install
poetry -C services/toolkit run pytest -q tests/test_cli.py tests/test_mcp_smoke.py
poetry -C services/toolkit run ruff check myfi_toolkit tests
```

Equivalently, from inside `services/toolkit/` itself: `poetry run pytest -q
tests/test_cli.py tests/test_mcp_smoke.py`.

## LLM law

Nothing in this package calls a hosted inference API directly. Any latent-quality
scoring this toolkit's outputs go through (see `services/eval/rubrics/toolkit.rubric.json`)
routes through `services/llm/llm.py`, which shells out to the local Claude
Code CLI -- never a hosted vendor endpoint (CLAUDE.md §LLM access).
