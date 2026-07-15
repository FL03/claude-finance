"""myfi_toolkit.config -- the `.claude/myfi.toml` loader + typed getters.

The single place that finds, parses, and reads the project's `.claude/myfi.toml`.
Every caller in this plugin that wants a config value (the toolkit's db paths,
the market-data provider, the LLM's default model) goes through one of the
typed getters below rather than parsing the file itself -- one loader, read
in one place, per CLAUDE.md "vanilla by default".

Stdlib-only (`tomllib`, Python 3.11+) -- no third-party TOML library, no ORM.

-- Root-finding --------------------------------------------------------------
Starts from the caller's logical cwd (`_logical_cwd()` below, mirroring
`myfi_toolkit.myctx.db._logical_cwd()`'s PWD-over-`Path.cwd()` preference --
see that module's docstring for why `PWD` matters when a wrapper script
`poetry -C <dir>`-chdirs the real OS process), then walks UP through parent
directories looking for `.claude/myfi.toml`, returning the first match. This
mirrors how git/npm/etc. find their nearest project marker: a caller running
a subcommand from a nested working directory still finds the project's one
config file, not just the immediate cwd.

-- Precedence -----------------------------------------------------------------
Every typed getter resolves, in order: an explicit `explicit=` argument (a
caller-supplied override, e.g. a future CLI flag) > the key's environment
variable (only `[llm].model` and `[marketdata].provider` have one today) >
the value in `.claude/myfi.toml` > a hardcoded default. A missing config file,
an unreadable one, or one with invalid TOML all degrade to `{}` -- every
getter still returns its documented default. This loader never crashes.

-- Not cached on purpose ------------------------------------------------------
Each getter call re-finds and re-parses the file fresh. The file is tiny (a
handful of keys) so the repeat cost is negligible, and this keeps every call
correct after the file changes underneath a long-lived process (a test that
rewrites `.claude/myfi.toml` mid-run, a CLI invocation right after `myfi.toml`
was hand-edited) -- a process-wide cache would need explicit invalidation to
handle that safely, and this loader is not on any hot path that needs one.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

__all__ = [
    "CONFIG_RELATIVE",
    "DEFAULT_TOOLKIT_DB",
    "DEFAULT_TOOLKIT_GLOBAL_DB",
    "DEFAULT_LLM_MODEL",
    "DEFAULT_MARKETDATA_PROVIDER",
    "DEFAULT_FLOCK_MODEL",
    "FLOCK_DEFAULT_MODELS",
    "LLM_MODEL_ENV",
    "MARKETDATA_PROVIDER_ENV",
    "find_config_path",
    "load_config",
    "toolkit_db",
    "toolkit_global_db",
    "llm_model",
    "marketdata_provider",
    "flock_default",
    "flock_model",
]

# Relative to a resolved project root -- see `find_config_path()`.
CONFIG_RELATIVE = Path(".claude") / "myfi.toml"

# Hardcoded defaults -- kept in sync BY HAND with the modules that owned
# these values before this loader existed (a getter's own module doesn't
# import this one back, to avoid a circular import, so each pair is
# cross-checked by a test instead, see test_config.py):
#   DEFAULT_TOOLKIT_DB / DEFAULT_TOOLKIT_GLOBAL_DB  -- myctx/db.py's old
#     PROJECT_DB_RELATIVE / GLOBAL_DB_RELATIVE.
#   DEFAULT_LLM_MODEL                                -- services/llm/llm.py's
#     DEFAULT_MODEL.
#   DEFAULT_MARKETDATA_PROVIDER                       -- marketdata/registry.py's
#     DEFAULT_PROVIDER.
DEFAULT_TOOLKIT_DB = ".myfi/myfi.db"
DEFAULT_TOOLKIT_GLOBAL_DB = "~/.myfi/global.db"
DEFAULT_LLM_MODEL = "opus"
DEFAULT_MARKETDATA_PROVIDER = "research"

# -- Flock dispatch roster ----------------------------------------------------
# The model each flock agent is dispatched on. This is the machine-readable
# half of the "agent mapping table": `docs/flock.md` and `skills/myfi/SKILL.md`
# document the same roster in prose, and each `agents/<name>.md` frontmatter
# pins the same value in its `model:` line. All three are kept in lockstep BY a
# gate test -- `test_config.py::test_flock_frontmatter_matches_roster` fails if
# any agent's frontmatter lacks an explicit `model:` or drifts from this map.
# That test is what makes an accidental all-opus wave structurally
# un-mergeable: `@advisor` is the sole opus seat (it alone orchestrates the
# flock and assembles the final report); every other agent runs sonnet by
# default, per CLAUDE.md "dispatch subagents on Sonnet, always".
DEFAULT_FLOCK_MODEL = "sonnet"
FLOCK_DEFAULT_MODELS: dict[str, str] = {
    "advisor": "opus",
    "quant": "sonnet",
    "auditor": "sonnet",
    "designer": "sonnet",
    "worker": "sonnet",
    "trader": "sonnet",
}

LLM_MODEL_ENV = "MYFI_LLM_MODEL"
MARKETDATA_PROVIDER_ENV = "MYFI_MARKETDATA_PROVIDER"


def _logical_cwd() -> Path:
    """The caller's logical working directory -- prefers `PWD` over
    `Path.cwd()`, identical reasoning to `myctx.db._logical_cwd()`: a wrapper
    script that `poetry -C <dir>`-chdirs the real OS process would otherwise
    make every lookup resolve relative to that `<dir>`, not the caller's
    actual project root.
    """
    pwd = os.environ.get("PWD")
    if pwd:
        candidate = Path(pwd)
        if candidate.is_dir():
            return candidate
    return Path.cwd()


def find_config_path(start: Path | None = None) -> Path | None:
    """Walk up from `start` (default: `_logical_cwd()`) looking for
    `.claude/myfi.toml`. Returns the first match, or `None` if no directory
    from `start` up to the filesystem root has one.
    """
    current = (start if start is not None else _logical_cwd()).resolve()
    while True:
        candidate = current / CONFIG_RELATIVE
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def load_config(start: Path | None = None) -> dict[str, Any]:
    """Find and parse `.claude/myfi.toml`, or return `{}` if it is missing,
    unreadable, or not valid TOML. Never raises.
    """
    path = find_config_path(start)
    if path is None:
        return {}
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _section(cfg: dict[str, Any], name: str) -> dict[str, Any]:
    """A `[name]` table from a parsed config, or `{}` if absent or malformed
    (e.g. a myfi.toml where `toolkit = "oops"` is a string, not a table) --
    keeps every getter below crash-proof against a hand-edited config.
    """
    value = cfg.get(name)
    return value if isinstance(value, dict) else {}


def _resolve(
    *,
    explicit: str | None,
    env_var: str | None,
    section: str,
    key: str,
    default: str,
    start: Path | None,
) -> str:
    """The one precedence chain every getter below runs: explicit arg > env
    var (if this key has one) > `.claude/myfi.toml` value > hardcoded default.

    An env var set to the empty string counts as unset and falls through to the
    toml/default -- an empty ``MYFI_LLM_MODEL`` should not force an empty model
    string; only a non-empty env value wins.
    """
    if explicit is not None:
        return explicit
    if env_var is not None:
        env_value = os.environ.get(env_var)
        if env_value:
            return env_value
    value = _section(load_config(start), section).get(key)
    if isinstance(value, str) and value:
        return value
    return default


def toolkit_db(explicit: str | None = None, *, start: Path | None = None) -> str:
    """`[toolkit].db` -- the per-project SQLite registry path, relative to the
    resolved project root unless it is absolute. Default `.myfi/myfi.db`. No
    environment-variable override exists for this key.
    """
    return _resolve(
        explicit=explicit,
        env_var=None,
        section="toolkit",
        key="db",
        default=DEFAULT_TOOLKIT_DB,
        start=start,
    )


def toolkit_global_db(explicit: str | None = None, *, start: Path | None = None) -> str:
    """`[toolkit].global_db` -- the optional shared-across-projects SQLite
    registry path, relative to `$HOME` unless it is absolute (or already
    `~`-prefixed). Default `~/.myfi/global.db`. No environment-variable
    override exists for this key.
    """
    return _resolve(
        explicit=explicit,
        env_var=None,
        section="toolkit",
        key="global_db",
        default=DEFAULT_TOOLKIT_GLOBAL_DB,
        start=start,
    )


def llm_model(explicit: str | None = None, *, start: Path | None = None) -> str:
    """`[llm].model` -- the model alias `services/llm` requests when a caller
    does not pass `--model` explicitly. Env override: `MYFI_LLM_MODEL`.
    Default `opus` (matches `services/llm/llm.py`'s `DEFAULT_MODEL`).
    """
    return _resolve(
        explicit=explicit,
        env_var=LLM_MODEL_ENV,
        section="llm",
        key="model",
        default=DEFAULT_LLM_MODEL,
        start=start,
    )


def marketdata_provider(explicit: str | None = None, *, start: Path | None = None) -> str:
    """`[marketdata].provider` -- which `MarketDataSource` `default_source()`
    resolves. Env override: `MYFI_MARKETDATA_PROVIDER`. Default `research`
    (matches `marketdata/registry.py`'s `DEFAULT_PROVIDER`).
    """
    return _resolve(
        explicit=explicit,
        env_var=MARKETDATA_PROVIDER_ENV,
        section="marketdata",
        key="provider",
        default=DEFAULT_MARKETDATA_PROVIDER,
        start=start,
    )


def flock_default(explicit: str | None = None, *, start: Path | None = None) -> str:
    """`[flock].default` -- the model a dispatched flock agent runs on when
    neither a per-run override nor a per-agent `[flock].<agent>` key nor the
    shipped roster (`FLOCK_DEFAULT_MODELS`) names one. Default `sonnet`, the
    cost-safe floor that keeps an accidental all-opus wave impossible. No
    environment-variable override exists for this key.
    """
    return _resolve(
        explicit=explicit,
        env_var=None,
        section="flock",
        key="default",
        default=DEFAULT_FLOCK_MODEL,
        start=start,
    )


def flock_model(agent: str, explicit: str | None = None, *, start: Path | None = None) -> str:
    """The model a given flock `agent` should be dispatched on.

    One resolution chain, highest precedence first:
      1. `explicit` -- a per-run override a dispatcher passes for this call.
      2. `[flock].<agent>` in `.claude/myfi.toml` -- an operator's per-agent pin.
      3. `[flock].default` in `.claude/myfi.toml` -- an operator's flock-wide
         floor (set this to `sonnet` to force the whole flock cheap, or to
         `opus` to lift every seat at once).
      4. `FLOCK_DEFAULT_MODELS[agent]` -- the shipped roster (advisor `opus`,
         every other agent `sonnet`).
      5. `DEFAULT_FLOCK_MODEL` (`sonnet`) -- the floor for an unknown agent name.

    This is the single place a dispatcher (`/myfi:plan`, `@advisor`) or a test
    asks "which model for `@<agent>`", so no agent silently inherits the
    session's model, and one `[flock].default` line reshapes the entire flock.
    """
    if explicit is not None:
        return explicit
    flock = _section(load_config(start), "flock")
    per_agent = flock.get(agent)
    if isinstance(per_agent, str) and per_agent:
        return per_agent
    default = flock.get("default")
    if isinstance(default, str) and default:
        return default
    return FLOCK_DEFAULT_MODELS.get(agent, DEFAULT_FLOCK_MODEL)
