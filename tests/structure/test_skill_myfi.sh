#!/usr/bin/env bash
# W2-myfi-skill structural gate -- the MYFI core scaffold orients a cold subagent.
# Wraps the unit [ACCEPTANCE] predicate: frontmatter name==myfi, references the
# toolkit CLI + services/llm law + all six flock agents + the MCP tool surface.
# Deterministic, python/rg only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

S=skills/myfi/SKILL.md
[ -f "$S" ] && ok "skills/myfi/SKILL.md present" || { bad "skills/myfi/SKILL.md missing"; echo FAIL; exit 1; }

python3 - "$S" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
fm = t.split('---')[1]
assert re.search(r'^name:\s*myfi\s*$', fm, re.M), "frontmatter name != myfi"
assert 'myfi-toolkit' in t, "does not reference the myfi-toolkit CLI"
assert 'services/llm' in t, "does not reference the services/llm LLM law"
agents = ('advisor', 'auditor', 'quant', 'designer', 'worker', 'trader')
n = sum(a in t for a in agents)
assert n == 6, f"names {n}/6 flock agents (need all: {agents})"
PY
[ $? -eq 0 ] && ok "frontmatter + toolkit + services/llm + all 6 agents referenced" \
              || bad "acceptance python check failed"

rg -n 'myfi-mcp|mcp__plugin_myfi' "$S" >/dev/null 2>&1 \
  && ok "references the MCP tool surface (myfi-mcp / mcp__plugin_myfi)" \
  || bad "no MCP tool-surface reference in SKILL.md"

if [ "$fail" = 0 ]; then echo "PASS test_skill_myfi"; else echo "FAIL test_skill_myfi"; fi
exit $fail
