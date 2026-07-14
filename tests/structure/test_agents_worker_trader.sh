#!/usr/bin/env bash
# W4-agents-worker-trader structural gate — @worker (bounded catch-all) +
# @trader (scaffold-only, no live exec). This IS the unit's [ACCEPTANCE]
# predicate plus the "no executable surface" regression test (seed §11's
# trader-boundary open question, sharpened to a `tools:`-line banned-
# substring assertion). Deterministic, python/rg only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

W=agents/worker.md
T=agents/trader.md

[ -f "$W" ] && ok "agents/worker.md present" || { bad "agents/worker.md missing"; echo FAIL; exit 1; }
[ -f "$T" ] && ok "agents/trader.md present" || { bad "agents/trader.md missing"; echo FAIL; exit 1; }

# Frontmatter shape: name, description, when-to-use, tools: — both agents.
python3 - "$W" "$T" <<'PY'
import re, sys
for path in sys.argv[1:]:
    t = open(path, encoding="utf-8").read()
    assert t.startswith("---"), f"{path}: does not start with frontmatter delimiter"
    fm = t.split("---")[1]
    assert re.search(r"^name:\s*\S+", fm, re.M), f"{path}: missing name"
    assert "description:" in fm, f"{path}: missing description"
    assert "when-to-use:" in fm, f"{path}: missing when-to-use"
    assert re.search(r"^tools:", fm, re.M), f"{path}: missing tools:"
    body = t.split("---", 2)[2]
    nonblank = [l for l in body.splitlines() if l.strip()]
    assert len(nonblank) > 30, f"{path}: body has only {len(nonblank)} non-blank lines (need >30)"
PY
[ $? -eq 0 ] && ok "both agents carry name/description/when-to-use/tools + body >30 lines" \
             || bad "frontmatter/body shape check failed"

# The unit's runnable [ACCEPTANCE]: trader.md documents the cycle + the
# authorization gate, and its tools: line wires NO live-order/exchange tool.
python3 - <<'PY'
t = open('agents/trader.md', encoding="utf-8").read()
fm = t.split('---')[1].lower()
assert 'tools:' in fm
tools = fm.split('tools:')[1].split('\n')[0]
banned = ('order', 'exchange', 'execute', 'place_trade', 'submit')
hit = [b for b in banned if b in tools]
assert not hit, f"live-exec tool wired: {hit} in {tools!r}"
assert any(k in t.lower() for k in ('scaffold', 'no live', 'authorization')), \
    "trader.md names none of scaffold/no live/authorization"
assert 'cycle' in t.lower() or 'loop' in t.lower(), "trader.md does not describe a cycle/loop"
PY
[ $? -eq 0 ] && ok "trader.md tools: line wires no live-order tool + names scaffold/no-live/authorization + cycle" \
             || bad "trader.md acceptance predicate failed"

rg -ni 'authorization' "$T" >/dev/null 2>&1 \
  && ok "agents/trader.md names 'authorization'" \
  || bad "agents/trader.md does not name 'authorization'"

# Regression: no banned live-exec substring anywhere on trader.md's tools: line,
# re-asserted directly via rg so a future edit that reintroduces one fails loudly
# even without running the python block above.
tools_line="$(grep -i '^tools:' "$T" | head -1)"
if echo "$tools_line" | rg -qi 'order|exchange|execute|place_trade|submit'; then
  bad "agents/trader.md tools: line contains a banned live-exec substring: $tools_line"
else
  ok "agents/trader.md tools: line ($tools_line) is exec-clean"
fi

# LLM law: no hosted-API reference anywhere in either agent file.
if rg -n 'api\.(anthropic|openai)\.com' "$W" "$T" >/dev/null 2>&1; then
  bad "hosted LLM API referenced in worker.md/trader.md (LLM law violation)"
else
  ok "no hosted LLM API reference in worker.md/trader.md"
fi

if [ "$fail" = 0 ]; then echo "PASS test_agents_worker_trader"; else echo "FAIL test_agents_worker_trader"; fi
exit $fail
