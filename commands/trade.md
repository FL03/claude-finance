---
name: trade
description: "SCAFFOLD -- authorization-gate command for a trade-idea walkthrough. Documents the agentic trade cycle and halts at a permanently-closed authorization gate before any live action. Invokes no live-order path in this version: no order-placement, order-submission, or trade-execution tool is wired into this command's allowed-tools, anywhere below."
argument-hint: "<symbol-or-thesis> [--dry-run]"
allowed-tools: Read, Grep, Glob, Bash, Skill, Agent, Write, mcp__plugin_myfi_myfi-toolkit__quote
---

# /myfi:trade -- SCAFFOLD (authorization gate, no live execution)

> This is a SCAFFOLD command. It documents the shape of an agentic trade cycle and the
> authorization doctrine that would gate any future live step. It does not, and cannot, place an
> order, touch an exchange, or confirm a fill in v0.0.0 -- no live-order path is wired anywhere in
> this command, its `allowed-tools` list, or the `@trader` agent it dispatches. This is the
> command-tier twin of `agents/trader.md`'s no-exec boundary; both halt at the same gate.

## The cycle (documented, never executed)

1. **ASSESS** -- read the client's stated goal, risk tolerance, and any positions the client has
   reported directly (never fetched from a live exchange -- no such tool exists here).
2. **DISCOVER** -- pull real market data via `mcp__plugin_myfi_myfi-toolkit__quote`, or dispatch
   `@trader` (which loads the `finance` skill for modeling) for a research-grade pass. Never
   hallucinate a price or a level.
3. **RANK** -- rank candidate ideas by a stated edge (thesis strength, risk/reward, time horizon).
4. **GATE-CHECK** -- evaluate the top candidate against the documented gate contract below and log
   every result plainly, pass or fail.
5. **AUTHORIZATION GATE -- HALT** -- this command stops here, always. There is no "open" state in
   this version: no order/exchange tool is wired anywhere in this command's `allowed-tools` line
   above, so clearing steps 1-4 never produces an executed trade. The gate exists in this
   documented procedure, not as an exit path a run can take.
6. **REPORT** -- emit a trade thesis (idea, entry rationale, risk, invalidation condition, data
   citation) as the deliverable. A report, never a fill, is what this command produces.
7. **IDLE** -- nothing to resume; each invocation is a fresh scan holding no live position state.

## Authorization-gate doctrine

- **The gate is permanently closed in v0.0.0.** No live-order, exchange, or execution tool is
  wired into this command's `allowed-tools:` line (it names only read/research tools: `Read`,
  `Grep`, `Glob`, `Bash`, `Skill`, `Agent`, `Write`, and the toolkit's read-only `quote`) or into
  `@trader`'s tool list. There is nothing for the gate to open onto.
- **Opening it is a future, explicitly-approved patch decision -- never something this command can
  do on its own.** A later patch would need to add an explicit order/exchange tool, get direct
  operator sign-off on that scope change, and ship a 9-gate-style safety contract (balance, edge,
  source, sizing, correlation, drawdown, market-open, liquidity, sanity) as enforced code, not
  prose. None of that exists here.
- **Passing every gate-check is never authorization to execute.** Even a thesis that clears every
  documented check still stops at step 5; step 6's report is the terminal output.
- **A request for a trade to be PLACED is a misuse of this command.** The correct response states
  plainly that v0.0.0 has no execution surface -- it does not simulate one or narrate a fill.

## Step 0 -- Load skills

`skills/myfi/SKILL.md` first (toolkit surface + flock table), then `finance` for edge/risk math
(Kelly-style sizing language belongs in the documented thesis, never in an execution call).

## Step 1 -- Dispatch

Dispatch `@trader` (`agents/trader.md`) with the client's thesis or symbol to run the assess →
discover → rank → gate-check steps above and produce the `## TRADER REPORT (scaffold -- no live
action taken)` output its contract defines. Route the same output through `@auditor` for a
compliance pass (jurisdiction, disclosure, suitability) before it reaches the client.

## `--dry-run`

Skips the toolkit call and the `@trader`/`@auditor` dispatch, walking the same seven-step cycle
against placeholder data to verify the procedure shape without spending a real research pass or an
LLM call. Never used to imply a live action occurred.

## Output

The deliverable is always a report -- never an order confirmation, a fill, or a position update:

```
## TRADE REPORT (scaffold -- no live action taken)
- Idea / thesis: <one line>
- Data cited: <toolkit quote or research source>
- Risk / invalidation: <what breaks this thesis>
- Gate-check log: <pass/fail per documented gate, informational only>
- Authorization gate: HALTED -- no live-order tool wired in v0.0.0
```
