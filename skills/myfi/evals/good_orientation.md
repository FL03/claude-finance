# Orientation -- good

After reading `skills/myfi/SKILL.md`, here is what I know before doing anything else:

**Toolkit.** The toolkit lives at `services/toolkit/` (package `myfi_toolkit`) and is reachable two
ways: the CLI `bin/myfi-toolkit <verb>` (`--version`, `quote <symbol> [--json]`, `db init`, `db
migrate`, `db version`), and the MCP server `bin/myfi-mcp`, registered in `.mcp.json` under the key
`myfi-toolkit`, whose tools surface to me as `mcp__plugin_myfi_myfi-toolkit__<tool>` (e.g.
`mcp__plugin_myfi_myfi-toolkit__quote`). Inside an agent turn I prefer the MCP tool over shelling
out to the CLI. Data persists in a per-project `.myfi/myfi.db` (git-ignored SQLite, WAL,
`foreign_keys=ON`), plus an optional global `~/.myfi/global.db`.

**The flock.** Six agents. `@advisor` (opus) decomposes the client's goal, dispatches the rest of
the flock, and assembles the final report -- I reach for it when I need a plan, not a single
analysis. `@quant` builds research-grade models (numpy/pandas/scipy) and cites its data -- I reach
for it for the actual number-crunching. `@auditor` is the compliance/local-law adversary that
reviews actor output with a Hypothesis+Falsification+Confidence triple and issues PASS/REDO
(cap 3) -- every actor output should pass through it before it ships. `@designer` does the final
artifact pass -- matplotlib (Agg backend) charts, live HTML, data exports. `@worker` is the bounded
catch-all for routine tasks like form-fill or aggregation that don't need a specialist. `@trader`
is scaffold-only in this version: it documents the agentic cycle and the authorization gate, but
its `tools:` list wires no order/exchange tool and it never executes live.

**Commands.** `/myfi:analyze` is a single-shot report. `/myfi:plan` is the `@advisor`-led pipeline
that dispatches the flock. `/myfi:taxes` runs the tax workflow. `/myfi:trade` is the
authorization-gated scaffold that halts before any live action.

**LLM law.** Every model call in this plugin -- mine included -- routes through `services/llm`,
which shells out to local Claude Code. I will never call a hosted inference API (Anthropic's,
OpenAI's, or anyone else's) directly, and neither should any tool I dispatch.

I can now dispatch the right agent, call the right CLI/MCP verb, and invoke the right command
without reading anything else first.
