# services/llm -- the myfi LLM service

One job: route a model call through the **local Claude Code** in headless print
mode (`claude -p`). Per `CLAUDE.md`: the software we build never calls a
hosted inference API -- it shells out to the local Claude Code. Every other
service (`services/eval`, agents, commands, hooks) calls this contract;
nothing else invokes `claude` directly.

Stdlib-only (no `poetry` env required) -- runs with any Python 3 on `PATH`.

## Contract

```bash
python3 services/llm/llm.py complete [--prompt-file=F | --prompt=TXT | -] \
                                      [--system-file=F | --system=TXT]     \
                                      [--model=ALIAS] [--timeout=SEC]
```

- Prompt source precedence: `--prompt-file` > `--prompt` > stdin.
- Writes **only** the model's text response to stdout. Diagnostics go to stderr.
- `llm.py ping` verifies the binary is reachable without spending a completion.

Exit codes: `0` ok · `2` usage · `3` timeout · `4` llm/runtime error.

The root wrapper `bin/myfi-llm` is a thin `exec python3 .../llm.py "$@"`.

## Why a service and not a one-liner

A single owner for the model call means a single place for the things that
are easy to get wrong eight different ways: the timeout (this service uses
Python's own `subprocess.run(..., timeout=...)` -- no hand-rolled watchdog
process needed, unlike the bash original this was ported from, since macOS
ships no `timeout` binary but Python's stdlib always has one), the default
model (`opus` -- best by default, never a silent downgrade for cost), and the
**mock seam**.

## The mock seam

```bash
MYFI_LLM_MOCK=<file>       # complete returns the file contents verbatim
MYFI_LLM_MOCK_TEXT=<str>   # … or this inline string
```

Either short-circuits the claude call entirely, before the prompt is even
resolved. This is what lets downstream gate tests (`services/eval`) assert the
harness around the model -- prompt-building, score math, threshold verdict --
deterministically, for free, in under two seconds. The latent part (the
model's judgement) is mocked; everything deterministic is tested for real.

## Config

This service reads only its own env (`MYFI_LLM_BIN`, `MYFI_LLM_MODEL`,
`MYFI_LLM_TIMEOUT`, the two mock vars). It does not read `.claude/myfi.toml` --
callers resolve config (which model, etc.) and pass it via flags, keeping the
service standalone and parallel-session-safe.

## Tests

```bash
python3 -m unittest discover -s services/llm/tests -v   # gate lane -- mock-only, no real claude call
```
