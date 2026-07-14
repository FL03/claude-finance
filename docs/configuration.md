# Configuration

myfi reads a per-project `myfi.toml` at `.claude/myfi.toml`. A template lives at
[`examples/minimal/myfi.toml`](../examples/minimal/myfi.toml), copy it in and edit:

```bash
mkdir -p .claude
cp /path/to/myfi/examples/minimal/myfi.toml .claude/myfi.toml
```

No section is required. Every key below has a working default, so an empty or missing
`.claude/myfi.toml` still runs, market data degrades to the self-contained research path and the
LLM defaults to `opus`.

## `[toolkit]`

```toml
[toolkit]
db = ".myfi/myfi.db"
# global_db = "~/.myfi/global.db"   # optional, opt-in
```

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `db` | `.myfi/myfi.db` | Path to the per-project SQLite registry (git-ignored). Created lazily by the first `db init`/`db migrate`/`db_init`/`db_migrate` call. |
| `global_db` | unset | An optional second registry shared across projects. Leave it commented out to stay project-local. |

The registry itself is not configured through `myfi.toml` beyond the path: schema and migrations
live at `services/toolkit/myfi_toolkit/myctx/schema/`, see [`toolkit.md`](toolkit.md).

## `[llm]`

```toml
[llm]
model = "claude-opus-4-8"
```

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `model` | `opus` (`services/llm`'s own default) | The model alias every `services/llm` call requests when a caller does not pass `--model` explicitly. Best available model by default, see [CLAUDE.md](../CLAUDE.md) §LLM access, never a silent downgrade for cost. |

Every LLM call in this plugin routes through `services/llm/llm.py`, which shells out to your
**local Claude Code** (`claude -p`). Nothing here, or anywhere else in this plugin, calls a hosted
inference API directly, not Anthropic's, not OpenAI's, not any provider's.

Two env vars override `[llm]` at the process level (useful for tests and CI, see
[`services/llm/README.md`](../services/llm/README.md)):

```bash
MYFI_LLM_MOCK=<file>       # services/llm complete returns the file contents verbatim
MYFI_LLM_MOCK_TEXT=<str>   # ...or this inline string
```

## `[marketdata]`

```toml
[marketdata]
provider = "research"
```

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `provider` | `research` | Which `MarketDataSource` implementation `default_source()` resolves. `research` is the self-contained default, needs no API key. `finnhub`/`yfinance`/`fred` are registered but each raises `NotImplementedError` until a follow-up release wires the concrete HTTP client. |

The equivalent runtime override is the `MYFI_MARKETDATA_PROVIDER` env var, which `default_source()`
reads directly (env wins over `myfi.toml` for this key today, the toolkit does not yet parse
`.claude/myfi.toml` itself, see [`marketdata.md`](marketdata.md) for the full contract).

## Verifying a config

```bash
python3 -c "import tomllib; tomllib.load(open('.claude/myfi.toml','rb')); print('ok')"
```

Any valid TOML file parses. There is no schema validator beyond that in v0.0.0, an unrecognized key
is ignored rather than rejected.
