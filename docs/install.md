# Install

myfi is a [Claude Code](https://claude.com/claude-code) plugin. There is no build step and no
server to run: everything ships as markdown (agents, skills, commands), a small Python/poetry
service layer, and a stdio MCP server. Works across CLI, web, and IDE surfaces.

## From the marketplace (recommended)

myfi is published through the `fl03` marketplace, hosted in the dedicated catalog repo
[`FL03/claude`](https://github.com/FL03/claude). That repo is the marketplace (a plain
`marketplace.json` catalog listing every `fl03` plugin); this repo, `FL03/claude-finance`, is the
plugin it points at, installed under the name `myfi`. Add the catalog once, then install any plugin
from it.

```text
/plugin marketplace add FL03/claude
/plugin install myfi@fl03
```

Update later with `/plugin update myfi@fl03`.

### Standalone (this repo as its own catalog)

This repo also ships a small catalog so it can be added on its own, without the dedicated `fl03`
one. Its marketplace name is **`claude-finance`** (the repo name), install name is **`myfi`**:

```text
/plugin marketplace add FL03/claude-finance
/plugin install myfi@claude-finance
```

The marketplace name here is `claude-finance`, **not** `fl03`. That is deliberate: Claude Code
keeps only one marketplace per name, so a second catalog also named `fl03` would silently replace
the dedicated `FL03/claude` one (and with it every other plugin that catalog lists, like
`shepherd`). Keeping the names distinct lets both coexist. Prefer the `FL03/claude` catalog above
when you can -- it lists every `fl03` plugin in one place; reach for the standalone path only when
you want myfi alone.

## Personal symlink or per-project pin

```bash
git clone https://github.com/FL03/claude-finance.git ~/src/FL03/claude-finance
ln -s ~/src/FL03/claude-finance ~/.claude/plugins/myfi      # personal, every project
ln -s /path/to/FL03/claude-finance .claude-plugin/myfi      # per-project pin (mkdir -p .claude-plugin first)
```

## Runtime requirements

| Requirement | Why |
| :--- | :--- |
| `git`, `bash` | Repo checkout, hooks, structural tests. |
| Python 3.12+ | Required by `services/toolkit` (its `pyproject.toml` floor, set by numpy/scipy). `services/llm` and `services/eval` are stdlib-only and run on older Python, but 3.12+ is the supported baseline. |
| `poetry` (2.3.2+) | Manages the `services/toolkit` venv (`myfi_toolkit`: numpy, pandas, scipy, matplotlib, the `mcp` SDK). Not required at runtime: `bin/myfi-toolkit`/`bin/myfi-mcp` fall back to `python3 -m myfi_toolkit.<module>` on `PYTHONPATH` if `poetry` is absent from `PATH`. |
| `claude` on `PATH` | Every model call in this plugin shells out to your local Claude Code (`claude -p`, see [`toolkit.md`](toolkit.md#the-llm-law)). No hosted inference API is ever called. |

No API key is required to get started. The market-data adapter (see
[`marketdata.md`](marketdata.md)) defaults to a self-contained research path with no provider
configured.

## What happens on first session start

A `SessionStart` hook (`hooks/scripts/session_venv.sh`) calls `bin/myfi-venv-ensure`, which
installs or refreshes the `services/toolkit` poetry venv under `${CLAUDE_PLUGIN_DATA}` (a location
that survives a plugin update, unlike `${CLAUDE_PLUGIN_ROOT}`). This is idempotent: it diffs
`services/toolkit/pyproject.toml` against a stamp file from the previous run and no-ops when
nothing changed. If `poetry` is not on `PATH`, the hook logs that and skips the install, the
CLI/MCP wrappers still work via the `PYTHONPATH` fallback.

## Per-project database

myfi keeps a per-project SQLite registry at `.myfi/myfi.db` (git-ignored, WAL mode, foreign keys
on). It is created lazily the first time any toolkit `db` verb or MCP `db_*` tool runs, or you can
create it explicitly:

```bash
bin/myfi-toolkit db init
```

See [`toolkit.md`](toolkit.md) for the full CLI/MCP surface.

## Verify the install

```bash
bin/myfi-toolkit --version   # fast smoke check, no heavy imports
bin/myfi-toolkit db init     # creates .myfi/myfi.db
bin/myfi-toolkit quote AAPL  # research-degrade quote (always JSON), no API key needed
```

Then, in Claude Code, try `/myfi:analyze "should I refinance this year?"` for a first report. See
[`commands.md`](commands.md) for the full command reference and
[`configuration.md`](configuration.md) for `myfi.toml`.
