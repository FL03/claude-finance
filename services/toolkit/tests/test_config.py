"""tests/test_config.py -- gate tests for myfi_toolkit.config, the
`.claude/myfi.toml` loader + typed getters, and its wiring into
`myctx.db.resolve_db_path()` / `marketdata.registry.default_source()`.

Every test isolates cwd + PWD to a fresh `tmp_path` (never the repo's own
`.claude/myfi.toml` or `.myfi/`), per CLAUDE.md's config unit: precedence is
explicit arg > env var > myfi.toml value > hardcoded default; a missing or
malformed file must degrade to defaults, never raise. Stdlib + pytest only,
no network, <2s.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myfi_toolkit import config
from myfi_toolkit.marketdata import registry
from myfi_toolkit.myctx import db


@pytest.fixture
def isolated_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Chdir + PWD both pointed at a fresh tmp_path -- config.find_config_path
    (and myctx.db._logical_cwd, which it mirrors) prefer PWD, so both must be
    set to keep a test hermetic against the real repo's own .claude/myfi.toml.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PWD", str(tmp_path))
    return tmp_path


def _write_toml(root: Path, content: str) -> Path:
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    path = claude_dir / "myfi.toml"
    path.write_text(content)
    return path


# -- find_config_path / load_config ------------------------------------------


def test_find_config_path_returns_none_when_absent(isolated_cwd: Path) -> None:
    assert config.find_config_path() is None
    assert config.load_config() == {}


def test_find_config_path_finds_file_at_cwd(isolated_cwd: Path) -> None:
    written = _write_toml(isolated_cwd, "[llm]\nmodel = 'x'\n")
    assert config.find_config_path() == written


def test_find_config_path_walks_up_from_a_nested_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A caller running a subcommand from a subdirectory of the project still
    finds the project's one `.claude/myfi.toml`, not just the immediate cwd.
    """
    written = _write_toml(tmp_path, "[llm]\nmodel = 'x'\n")
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.setenv("PWD", str(nested))

    assert config.find_config_path() == written


def test_load_config_missing_file_returns_empty_dict_never_raises(
    isolated_cwd: Path,
) -> None:
    assert config.load_config() == {}


def test_load_config_malformed_toml_returns_empty_dict_never_raises(
    isolated_cwd: Path,
) -> None:
    _write_toml(isolated_cwd, "= invalid =\n")
    assert config.load_config() == {}


def test_load_config_unreadable_section_type_is_ignored_not_crashed(
    isolated_cwd: Path,
) -> None:
    """`[toolkit]` etc. must be TOML tables; a myfi.toml where a section name
    is reused as a plain string is malformed input, not a crash.
    """
    _write_toml(isolated_cwd, 'toolkit = "oops, not a table"\n')
    assert config.toolkit_db() == config.DEFAULT_TOOLKIT_DB


# -- toolkit_db / toolkit_global_db ------------------------------------------


def test_toolkit_db_default_when_no_config(isolated_cwd: Path) -> None:
    assert config.toolkit_db() == ".myfi/myfi.db" == config.DEFAULT_TOOLKIT_DB


def test_toolkit_db_from_toml(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[toolkit]\ndb = 'custom/registry.db'\n")
    assert config.toolkit_db() == "custom/registry.db"


def test_toolkit_db_explicit_arg_wins_over_toml(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[toolkit]\ndb = 'custom/registry.db'\n")
    assert config.toolkit_db(explicit="explicit/registry.db") == "explicit/registry.db"


def test_toolkit_global_db_default_when_no_config(isolated_cwd: Path) -> None:
    assert config.toolkit_global_db() == "~/.myfi/global.db" == config.DEFAULT_TOOLKIT_GLOBAL_DB


def test_toolkit_global_db_from_toml(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[toolkit]\nglobal_db = '/opt/shared/global.db'\n")
    assert config.toolkit_global_db() == "/opt/shared/global.db"


def test_toolkit_global_db_explicit_arg_wins_over_toml(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[toolkit]\nglobal_db = '/opt/shared/global.db'\n")
    assert config.toolkit_global_db(explicit="/explicit/global.db") == "/explicit/global.db"


# -- llm_model ----------------------------------------------------------------


def test_llm_model_default_when_no_config(isolated_cwd: Path) -> None:
    assert config.llm_model() == "opus" == config.DEFAULT_LLM_MODEL


def test_llm_model_from_toml(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[llm]\nmodel = 'claude-opus-4-8'\n")
    assert config.llm_model() == "claude-opus-4-8"


def test_llm_model_env_wins_over_toml(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_toml(isolated_cwd, "[llm]\nmodel = 'claude-opus-4-8'\n")
    monkeypatch.setenv(config.LLM_MODEL_ENV, "claude-haiku-x")
    assert config.llm_model() == "claude-haiku-x"


def test_llm_model_explicit_arg_wins_over_env_and_toml(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_toml(isolated_cwd, "[llm]\nmodel = 'claude-opus-4-8'\n")
    monkeypatch.setenv(config.LLM_MODEL_ENV, "claude-haiku-x")
    assert config.llm_model(explicit="claude-explicit-y") == "claude-explicit-y"


# -- marketdata_provider --------------------------------------------------------


def test_marketdata_provider_default_when_no_config(isolated_cwd: Path) -> None:
    assert config.marketdata_provider() == "research" == config.DEFAULT_MARKETDATA_PROVIDER


def test_marketdata_provider_from_toml(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[marketdata]\nprovider = 'finnhub'\n")
    assert config.marketdata_provider() == "finnhub"


def test_marketdata_provider_env_wins_over_toml(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_toml(isolated_cwd, "[marketdata]\nprovider = 'finnhub'\n")
    monkeypatch.setenv(config.MARKETDATA_PROVIDER_ENV, "yfinance")
    assert config.marketdata_provider() == "yfinance"


def test_marketdata_provider_explicit_arg_wins_over_env_and_toml(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_toml(isolated_cwd, "[marketdata]\nprovider = 'finnhub'\n")
    monkeypatch.setenv(config.MARKETDATA_PROVIDER_ENV, "yfinance")
    assert config.marketdata_provider(explicit="fred") == "fred"


# -- cross-module drift guards --------------------------------------------------
# config.py can't import myctx/marketdata back (it would be a circular import,
# since those modules import config), so its defaults are hand-kept in sync
# with the modules that owned these values before this loader existed. These
# guards fail loudly the moment one side drifts without the other.


def test_marketdata_default_and_env_constants_match_registry() -> None:
    assert config.DEFAULT_MARKETDATA_PROVIDER == registry.DEFAULT_PROVIDER
    assert config.MARKETDATA_PROVIDER_ENV == registry.PROVIDER_ENV


# -- integration: myctx.db.resolve_db_path() consults config -------------------


def test_resolve_db_path_default_matches_hardcoded_default_with_no_config(
    isolated_cwd: Path,
) -> None:
    assert db.resolve_db_path(use_global=False) == isolated_cwd / ".myfi" / "myfi.db"


def test_resolve_db_path_project_honors_toml_db_key(
    isolated_cwd: Path,
) -> None:
    _write_toml(isolated_cwd, "[toolkit]\ndb = 'custom/registry.db'\n")
    assert db.resolve_db_path(use_global=False) == isolated_cwd / "custom" / "registry.db"


def test_resolve_db_path_global_honors_toml_global_db_key(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = isolated_cwd / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    _write_toml(isolated_cwd, "[toolkit]\nglobal_db = '~/shared/global.db'\n")

    assert db.resolve_db_path(use_global=True) == home / "shared" / "global.db"


def test_resolve_db_path_absolute_toml_db_ignores_project_root(
    isolated_cwd: Path,
) -> None:
    absolute = isolated_cwd / "elsewhere" / "abs.db"
    _write_toml(isolated_cwd, f"[toolkit]\ndb = '{absolute.as_posix()}'\n")

    assert db.resolve_db_path(use_global=False) == absolute


# -- integration: marketdata.registry.default_source() consults config ---------


def test_default_source_honors_toml_provider_key(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(registry.PROVIDER_ENV, raising=False)
    _write_toml(isolated_cwd, "[marketdata]\nprovider = 'finnhub'\n")

    with pytest.raises(NotImplementedError):
        registry.default_source().quote("AAPL")


def test_default_source_env_still_wins_over_toml_provider(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_toml(isolated_cwd, "[marketdata]\nprovider = 'finnhub'\n")
    monkeypatch.setenv(registry.PROVIDER_ENV, "research")

    result = registry.default_source().quote("AAPL")
    assert result.source == "research"


def test_default_source_still_defaults_to_research_with_no_config(
    isolated_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(registry.PROVIDER_ENV, raising=False)
    result = registry.default_source().quote("AAPL")
    assert result.source == "research"


# -- flock dispatch roster ----------------------------------------------------
# The machine-readable half of the "agent mapping table": config exposes the
# per-agent model roster and the [flock] override surface, and the drift test
# below cross-checks the roster against every agents/<name>.md frontmatter so an
# accidental all-opus wave is un-mergeable, not merely discouraged.


def test_flock_default_is_sonnet_with_no_config(isolated_cwd: Path) -> None:
    assert config.flock_default() == "sonnet"
    assert config.DEFAULT_FLOCK_MODEL == "sonnet"


def test_flock_default_reads_toml(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[flock]\ndefault = 'opus'\n")
    assert config.flock_default() == "opus"


def test_flock_default_explicit_arg_wins(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[flock]\ndefault = 'opus'\n")
    assert config.flock_default("haiku") == "haiku"


def test_flock_model_uses_shipped_roster_with_no_config(isolated_cwd: Path) -> None:
    # @advisor is the sole opus seat; everyone else is sonnet, straight from the
    # baked roster when no [flock] section overrides it.
    assert config.flock_model("advisor") == "opus"
    for agent in ("quant", "auditor", "designer", "worker", "trader"):
        assert config.flock_model(agent) == "sonnet"


def test_flock_model_per_agent_key_overrides_roster(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[flock]\ndesigner = 'opus'\n")
    assert config.flock_model("designer") == "opus"
    assert config.flock_model("quant") == "sonnet"  # untouched


def test_flock_model_default_key_moves_every_unpinned_seat(isolated_cwd: Path) -> None:
    # [flock].default beats the shipped roster, so it lifts even @advisor's peers
    # -- the single knob an operator flips to force the whole flock one way.
    _write_toml(isolated_cwd, "[flock]\ndefault = 'opus'\n")
    assert config.flock_model("worker") == "opus"
    assert config.flock_model("advisor") == "opus"


def test_flock_model_per_agent_beats_default(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[flock]\ndefault = 'haiku'\nquant = 'opus'\n")
    assert config.flock_model("quant") == "opus"
    assert config.flock_model("worker") == "haiku"


def test_flock_model_explicit_arg_beats_everything(isolated_cwd: Path) -> None:
    _write_toml(isolated_cwd, "[flock]\ndefault = 'haiku'\nquant = 'haiku'\n")
    assert config.flock_model("quant", "opus") == "opus"


def test_flock_model_unknown_agent_falls_to_sonnet_floor(isolated_cwd: Path) -> None:
    assert config.flock_model("nobody") == "sonnet"


def _read_frontmatter_model(md_path: Path) -> str | None:
    """The `model:` value from an agent .md's YAML frontmatter, or None if the
    file has no closed frontmatter block or no `model:` line inside it.
    """
    import re

    text = md_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter = parts[1]
    match = re.search(r"^model:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    return match.group(1) if match else None


def test_flock_frontmatter_matches_roster() -> None:
    """The load-bearing guard: every `agents/<name>.md` frontmatter must pin a
    `model:` that equals `FLOCK_DEFAULT_MODELS[name]`, and the set of agent files
    must exactly match the roster keys. A new agent with no `model:` line, or an
    agent whose model drifts from the roster (the exact way an accidental
    all-opus wave gets introduced), fails the gate here.
    """
    repo_root = Path(__file__).resolve().parents[3]
    agents_dir = repo_root / "agents"
    assert agents_dir.is_dir(), f"agents/ not found at {agents_dir}"

    on_disk = {p.stem for p in agents_dir.glob("*.md")}
    roster = set(config.FLOCK_DEFAULT_MODELS)
    assert on_disk == roster, (
        f"flock roster and agents/ dir disagree: "
        f"only in roster={roster - on_disk}, only on disk={on_disk - roster}"
    )

    for name, expected in config.FLOCK_DEFAULT_MODELS.items():
        model = _read_frontmatter_model(agents_dir / f"{name}.md")
        assert model is not None, f"agents/{name}.md frontmatter has no explicit model:"
        assert model == expected, (
            f"agents/{name}.md pins model:{model} but roster says {expected} "
            f"-- update the frontmatter or FLOCK_DEFAULT_MODELS so they agree"
        )
