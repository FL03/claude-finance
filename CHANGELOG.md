# Changelog

All notable changes to myfi are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/).

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

[0.0.0]: https://github.com/FL03/myfi/releases/tag/v0.0.0
