# Changelog

All notable changes to myfi are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

Rigor, precision, and cleanup sprint on the 0.0.2 line: the `.claude/myfi.toml` config is now
actually read, a flock dispatch policy makes agent model selection explicit and enforced, the
`finance` domain skill lands, and a sweep of content/correctness fixes closes doc/spec
contradictions across the flock.

### Added

- `finance` skill (`skills/finance/`): `@quant`'s quantitative-modeling knowledge silo -- stochastic
  calculus and risk theory (`QUANT.md`), the pricing/risk/portfolio model zoo (`MODELS.md`),
  prediction-market probability (`PREDICTION.md`), and execution microstructure (`MICROSTRUCTURE.md`).
- Flock dispatch policy (the agent-to-model mapping table). `myfi_toolkit.config` gains
  `FLOCK_DEFAULT_MODELS` plus `flock_model(agent)` / `flock_default()` getters and a `[flock]`
  override section in `.claude/myfi.toml` (`default` moves every seat, `[flock].<agent>` moves one).
  The shipped roster is one opus seat (`@advisor`) and five sonnet specialists, pinned in each
  `agents/<name>.md` frontmatter and cross-checked by
  `test_config.py::test_flock_frontmatter_matches_roster`, which fails the gate if any agent lacks a
  `model:` line or drifts from the roster -- an accidental all-opus dispatch is now un-mergeable.
  Documented in `skills/myfi/SKILL.md` (Dispatch by the roster) and `docs/flock.md` (Model policy).
- `.claude/myfi.toml` loader (`services/toolkit/myfi_toolkit/config.py`): a stdlib-only reader with
  precedence explicit arg > env var > myfi.toml > default, degrading to defaults on a missing or
  malformed file, never raising.
- Fifth release-gate lane: `bin/myfi-test` now runs `tests/structure/run.sh` (repo-shape gate over
  every `tests/structure/test_*.sh`) alongside the toolkit, services, hooks, and integration lanes.

### Changed

- `.claude/myfi.toml` values now take effect: `myctx.db.resolve_db_path()` reads
  `[toolkit].db`/`global_db`, `marketdata.registry.default_source()` reads `[marketdata].provider`,
  and `services/llm` reads `[llm].model` (best-effort, degrading cleanly when the toolkit package is
  not importable, so `services/llm` still runs standalone).
- Content and correctness pass across the flock: agent, command, skill, and doc prose reconciled
  against the code and against each other (dropped internal "Wave N" codenames, aligned version
  phrasing, fixed cross-references).
- House-style cleanup: purged em-dashes repo-wide, converting every U+2014 to the double-hyphen
  `--` (520 across 76 files: source docstrings and comments, tests, docs, READMEs, rubrics, eval
  goldens, `bin/` scripts, `CLAUDE.md`, and archival `.shepherd/` planning docs). Zero remain; each
  change is character-only, verified against the full gate.

### Fixed

- IMPROVE-loop recurrence bug: `v_mem_recent_7d` now filters and orders by `updated_at`, not
  `created_at`, so a recurring prior older than 7 days re-surfaces instead of silently dropping out
  of the inject window (migration `0002`).
- Doc/spec contradictions: `/myfi:analyze` no longer lists `@advisor` as a valid `--agent`;
  `--redo-cap` is documented as a hard ceiling of 3 with no operator override; the toolkit `quote`
  verb is documented as always-JSON (there is no `--json` flag); schema-migration paths corrected to
  the repo-relative `services/toolkit/...`.

## [0.0.2] - 2026-07-14

### Changed

- Version bump only: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and the
  README version line advanced 0.0.1 → 0.0.2. No functional, agent, toolkit, or contract change.

## [0.0.1] - 2026-07-14

### Changed

- Renamed the GitHub repository `FL03/myfi` → `FL03/claude-finance`, and updated `homepage`,
  `repository`, and `plugins[].source.repo` in `.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` to the new URL. The plugin and every tool keep the `myfi`
  identity (plugin name, `/myfi:*` commands, `bin/myfi-*`, the `myfi-toolkit` MCP server, the
  `myfi_toolkit` package, the `.myfi/` registry) -- only the repository name changed.
- Reworked `.gitignore`.

## [0.0.0] - 2026-07-13

The Foundation, the first complete, installable myfi finance plugin: a six-agent flock, four
skills, four commands, and a Python toolkit exposed as both a CLI and an MCP server.

### Added

- Six-agent flock: `@advisor` (opus dispatcher, decomposes a client goal and assembles the final
  report), `@quant` (research-grade analyst), `@auditor` (compliance/local-law adversarial
  reviewer, Hypothesis + Falsification + Confidence, PASS/REDO cap 3), `@designer` (final live
  artifact editor), `@worker` (bounded catch-all executor), `@trader` (scaffold-only trade-cycle
  doctrine, zero live-execution surface).
- Four entry-point commands: `/myfi:analyze` (single-shot report), `/myfi:plan` (full advisor-led
  pipeline), `/myfi:taxes` (tax-year workflow), `/myfi:trade` (SCAFFOLD, permanently-closed
  authorization gate).
- `services/toolkit`, a poetry project (`myfi_toolkit`) exposing `bin/myfi-toolkit` (CLI) and
  `bin/myfi-mcp` (stdio MCP server), carrying numpy, pandas, scipy, and matplotlib (Agg backend).
- `myctx`, a per-project SQLite registry (`.myfi/myfi.db`, WAL, gap-fill migrations) plus an
  optional global `~/.myfi/global.db`.
- A `MarketDataSource` adapter contract with a self-contained research-degrade default; `finnhub`,
  `yfinance`, and `fred` registered as deferred providers behind the same contract.
- `services/llm`, routing every model call through the local Claude Code (`claude -p`), never a
  hosted inference API, with a deterministic mock seam for gate tests.
- `services/eval`, a rubric-scored eval harness (JSON rubrics, weighted scoring, threshold
  verdicts) for every latent output the plugin produces.
- Four skills: `myfi` (core orientation scaffold, loaded first by every agent), `compliance`
  (regulatory knowledge for the adversarial reviewer), `taxes` (tax-workflow knowledge and the IRS
  form map), `improve` (the harvest/store/inject/cite self-improvement loop).
- Enforcement hooks: `dispatch_guard.sh` (closed-flock dispatch gate), `dedup_write_guard.sh`
  (duplicate-symbol guard), `session_venv.sh` (idempotent toolkit venv bootstrap),
  `adaptation_capture.sh` (self-improvement harvest).
- `docs/` (install, configuration, flock, toolkit, commands, marketdata) and
  `examples/minimal/myfi.toml`.
- `tests/integration/`, an end-to-end suite (plugin auto-discovery, `/myfi:analyze` mock-seam
  walkthrough, toolkit smoke) aggregated by `bin/myfi-test`, the single command the release gate
  calls.

### Non-goals (this release)

- No live trade execution. `@trader` and `/myfi:trade` are scaffold-only, no order or exchange
  tool is wired anywhere in v0.0.0.
- No concrete market-data provider wired live. `finnhub`, `yfinance`, and `fred` are registered
  behind `MarketDataSource` but each raises until a follow-up release adds the HTTP client and API
  key handling.

[Unreleased]: https://github.com/FL03/claude-finance/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/FL03/claude-finance/releases/tag/v0.0.2
[0.0.1]: https://github.com/FL03/claude-finance/releases/tag/v0.0.1
[0.0.0]: https://github.com/FL03/claude-finance/releases/tag/v0.0.0
