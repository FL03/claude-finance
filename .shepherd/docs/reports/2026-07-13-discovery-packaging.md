---
title: Discovery -- plugin layout, poetry CLI, stdio MCP packaging for myfi
date: 2026-07-13
discovery_id: D-PKG
sprint: v0.0.0
sources_consulted: 6
tool_calls_used: 12
time_used_minutes: 11
---

## Sources
1. Skill `plugin-dev:plugin-structure` (bundled plugin-dev plugin)
2. Skill `plugin-dev:mcp-integration` (bundled plugin-dev plugin)
3. https://code.claude.com/docs/en/plugins-reference (fetched 2026-07-13)
4. https://code.claude.com/docs/en/mcp -- §Option 3: Add a local stdio server (fetched 2026-07-13)
5. https://python-poetry.org/docs/pyproject/#scripts (fetched 2026-07-13)
6. https://pypi.org/project/mcp/ and https://github.com/modelcontextprotocol/python-sdk (fetched 2026-07-13)
7. Repo inspection: `/Users/jo3/src/fl03/myfi/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `src/agents/`, `src/skills/`

## Findings

### 1. Plugin component layout
`.claude-plugin/plugin.json` holds only the manifest [3]. All component dirs -- `agents/`, `skills/`, `commands/`, `hooks/`, `output-styles/`, `themes/`, `monitors/`, `bin/`, `.mcp.json`, `.lsp.json` -- MUST live at plugin root, sibling to `.claude-plugin/`, never nested inside it [3, "Plugin directory structure" + "Directory structure mistakes"].

Current repo state: `/Users/jo3/src/fl03/myfi/.claude-plugin/plugin.json` declares no `agents`/`skills`/`commands` override, and the repo has `src/agents/` (advisor.md, auditor.md, quant.md, worker.md) and `src/skills/` (advise/, myfi/, plan/, trade/) instead of root-level `agents/`/`skills/`. **Confirmed: the `src/` prefix breaks auto-discovery today** -- default scan targets root `agents/`/`skills/`, so nothing under `src/` currently loads [3, "File locations reference"].

Two fixes, either legal: (a) move to plugin root `agents/`, `skills/` (docs recommend `skills/` layout for new plugins); or (b) keep `src/` and set in `plugin.json`: `"agents": ["./src/agents"]` (replaces default `agents/` scan -- safe, no root `agents/` exists) and `"skills": ["./src/skills"]` (ADDS to, does not replace, the default `skills/` scan) [3, "Path behavior rules"]. All custom paths must be relative, start with `./`, and cannot traverse outside the plugin root (`../` fails post-install since only the plugin dir is copied to cache) [3, "Path traversal limitations"].

### 2. Poetry-packaged CLI at `services/toolkit/`
Recommended layout: `services/toolkit/pyproject.toml` + `services/toolkit/myfi_toolkit/` package. Define `[tool.poetry.scripts] myfi-toolkit = "myfi_toolkit.cli:main"` [5] -- an installed console script, exposed identically whether installed via `poetry install`, `pipx install`, or `pip install` from a built wheel [5, "End-User Installation"], preferred over `python -m` for anything the plugin ships to consumers.

Agents invoke via a thin wrapper at plugin root `bin/myfi-toolkit` -- files under `bin/` are auto-added to the Bash tool's PATH while the plugin is enabled [3, "File locations reference"] -- that runs `cd "${CLAUDE_PLUGIN_ROOT}/services/toolkit" && poetry run myfi-toolkit "$@"`, falling back to `python -m myfi_toolkit.cli "$@"` if poetry is absent on the host.

Persistence: `${CLAUDE_PLUGIN_ROOT}` is ephemeral (old-version dir purged ~7 days after a plugin update -- do not install a venv there) [3, "${CLAUDE_PLUGIN_ROOT}"]. Install/refresh the venv or deps under `${CLAUDE_PLUGIN_DATA}` (survives updates, created on first reference) via a `SessionStart` hook that diffs the bundled `pyproject.toml`/lock against a copy stored in `${CLAUDE_PLUGIN_DATA}`, matching the documented `node_modules` pattern [3, "Persistent data directory"]. Consumer without poetry: `pipx install ./services/toolkit` or `pip install ./services/toolkit` -- poetry is a build-time tool only; the shipped artifact is a standard PEP 517 wheel [5].

### 3. stdio MCP server, same poetry project
Package: official `mcp` SDK (FastMCP bundled). `from mcp.server.fastmcp import FastMCP`; `mcp = FastMCP("myfi-toolkit")`; `@mcp.tool()` decorators; run with `mcp.run(transport="stdio")` [6]. Add a second entry point in the same `services/toolkit/pyproject.toml`: `myfi-mcp = "myfi_toolkit.mcp_server:main"`, where `main()` calls `mcp.run(transport="stdio")`.

Register in a root `.mcp.json` (sibling to `.claude-plugin/`, NOT nested under `services/toolkit/`):
```json
{"mcpServers": {"myfi-toolkit": {"command": "${CLAUDE_PLUGIN_ROOT}/bin/myfi-mcp"}}}
```
using the same poetry-run/fallback wrapper pattern as the CLI [plugin-dev:mcp-integration skill, "Method 1: Dedicated .mcp.json"]. Tools surface to agents as `mcp__plugin_myfi_myfi-toolkit__<tool>`; pre-allow specific tool names in agent/command frontmatter rather than wildcards [plugin-dev:mcp-integration, "Security Best Practices"]. Claude Code sets `CLAUDE_PROJECT_DIR` in the spawned stdio server's environment and answers MCP `roots/list` with the session's working directories, useful if the server needs to scope filesystem access [4, "Option 3: Add a local stdio server"].

## Open questions
- Whether `services/toolkit/` should manage its own `.venv` directly vs. relying solely on `${CLAUDE_PLUGIN_DATA}` for the persisted environment -- not addressed by any fetched source; needs an explicit engineering decision.
- Minimum Claude Code version required for `bin/` PATH auto-injection was not stated in the fetched reference; verify before relying on it in a hook or wrapper.

## Confidence
HIGH -- all three findings are grounded in current first-party docs (code.claude.com, python-poetry.org, official mcp python-sdk) plus direct repo inspection confirming the `src/` auto-discovery gap.

## Suggested follow-ups
- Engineering decision on `services/toolkit/` venv strategy (see Open questions).
- Verify `bin/` PATH-injection version gate via `claude --version` on target hosts before shipping the wrapper pattern.

new_findings: true
