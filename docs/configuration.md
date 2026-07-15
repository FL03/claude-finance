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

## How it's parsed -- and where

`myfi_toolkit.config` (`services/toolkit/myfi_toolkit/config.py`) is the one loader: stdlib-only
(`tomllib`, Python 3.11+), it walks up from the caller's working directory looking for
`.claude/myfi.toml` -- the same PWD-preferring cwd resolution `myctx.db` uses, so a subcommand run
from a nested directory still finds the project's one config file -- parses it, and exposes a typed
getter per key. A missing file, an unreadable one, or one with invalid TOML all degrade to the
hardcoded defaults below; the loader never crashes and never partially applies a broken file.

Precedence is the same for every key, in order:

1. **Explicit argument** -- a caller passes a value directly (reserved for a future CLI flag; no
   subcommand does this today).
2. **Environment variable** -- only `[llm].model` (`MYFI_LLM_MODEL`) and `[marketdata].provider`
   (`MYFI_MARKETDATA_PROVIDER`) have one. `[toolkit].db` and `[toolkit].global_db` have no env
   override.
3. **`.claude/myfi.toml` value** -- read through `myfi_toolkit.config`.
4. **Hardcoded default** -- documented per key below.

Three call sites consult it today: `myctx.db.resolve_db_path()` (`[toolkit].db` /
`[toolkit].global_db`), `marketdata.registry.default_source()` (`[marketdata].provider`), and
`services/llm/llm.py`'s `--model` default (`[llm].model`, best-effort -- see the `[llm]` section
below for the one caveat that section applies).

## `[toolkit]`

```toml
[toolkit]
db = ".myfi/myfi.db"
# global_db = "~/.myfi/global.db"   # optional, opt-in
```

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `db` | `.myfi/myfi.db` | Path to the per-project SQLite registry (git-ignored). Relative to the resolved project root unless it is absolute. Created lazily by the first `db init`/`db migrate`/`db_init`/`db_migrate` call. No environment-variable override. |
| `global_db` | `~/.myfi/global.db` | An optional second registry shared across projects, used only with `--global`. Relative to `$HOME` unless it is already absolute (or `~`-prefixed). Leave it commented out to stay project-local -- `myctx.db.resolve_db_path()` still consults this key, it's just unset in the template. No environment-variable override. |

Both keys are read by `myctx.db.resolve_db_path()` through `myfi_toolkit.config.toolkit_db()` /
`toolkit_global_db()`. The registry's schema itself is not configured through `myfi.toml` beyond
the path: schema and migrations live at `services/toolkit/myfi_toolkit/myctx/schema/`, see
[`toolkit.md`](toolkit.md).

## `[llm]`

```toml
[llm]
model = "claude-opus-4-8"
```

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `model` | `opus` (`services/llm/llm.py`'s own `DEFAULT_MODEL`) | The model alias `services/llm` requests when a caller does not pass `--model` explicitly. Best available model by default, see [CLAUDE.md](../CLAUDE.md) §LLM access, never a silent downgrade for cost. |

Every LLM call in this plugin routes through `services/llm/llm.py`, which shells out to your
**local Claude Code** (`claude -p`). Nothing here, or anywhere else in this plugin, calls a hosted
inference API directly, not Anthropic's, not OpenAI's, not any provider's. Wiring `[llm].model` into
that call never changes that routing -- it only picks which alias the same `claude -p` invocation
requests.

Precedence: `MYFI_LLM_MODEL` env > `[llm].model` > `opus`. `MYFI_LLM_MODEL` wins outright and, when
set, `services/llm/llm.py` never even attempts the lookup below. One caveat, unique to this key:
`services/llm` is designed to run standalone (no `poetry` env required, stdlib only, works with a
bare `python3` and no other service's package installed). Reading `[llm].model` means it optionally
imports `myfi_toolkit.config` from the sibling `services/toolkit/` checkout at runtime -- if that
import fails for any reason (no sibling checkout, a stripped-down deployment, anything), it silently
falls back to the env-var-or-`opus` behavior this service has always had. `.claude/myfi.toml` is
never a hard dependency for this service.

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
| `provider` | `research` | Which `MarketDataSource` implementation `default_source()` resolves. `research` is the self-contained default, needs no API key. `finnhub`/`yfinance`/`fred` are registered -- `provider` selects which adapter class gets constructed -- but each one's `.quote()` still raises `NotImplementedError` until a follow-up release wires the concrete HTTP client + API key handling. Setting `provider` to one of them today does not make it work, it only proves the selection surface picks the right (still-stubbed) adapter. |

Precedence: `MYFI_MARKETDATA_PROVIDER` env > `[marketdata].provider` > `research`.
`marketdata.registry.default_source()` reads this through
`myfi_toolkit.config.marketdata_provider()`, so both the env var and `.claude/myfi.toml` are live
today (env wins when both are set). See [`marketdata.md`](marketdata.md) for the full
`MarketDataSource` contract and the per-provider status.

## Verifying a config

```bash
python3 -c "import tomllib; tomllib.load(open('.claude/myfi.toml','rb')); print('ok')"
```

Any valid TOML file parses. There is no schema validator beyond that currently, an unrecognized key
is ignored rather than rejected.
