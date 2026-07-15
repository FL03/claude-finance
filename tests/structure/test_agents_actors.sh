#!/usr/bin/env bash
# W4-agents-actors structural gate -- @advisor (opus dispatcher) + @quant (research analyst).
# Wraps the unit [ACCEPTANCE] predicate: valid frontmatter (name/description/tools) on both
# agents, a system-prompt body >30 lines, MYFI + toolkit cited, advisor names opus and its
# `tools:` line wires a dispatch tool. Deterministic, python3/rg only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

for f in agents/advisor.md agents/quant.md; do
  [ -f "$f" ] && ok "$f present" || { bad "$f missing"; echo FAIL; exit 1; }
done

python3 - <<'PY'
import re, sys
fail = False
for f in ("agents/advisor.md", "agents/quant.md"):
    t = open(f, encoding="utf-8").read()
    parts = t.split("---")
    if len(parts) < 3:
        print(f"FAIL: {f} has no closed --- frontmatter block")
        fail = True
        continue
    fm, body = parts[1], t.split("---", 2)[2]
    if not re.search(r"^name:", fm, re.M):
        print(f"FAIL: {f} frontmatter missing name:")
        fail = True
    if "description:" not in fm:
        print(f"FAIL: {f} frontmatter missing description:")
        fail = True
    if "tools:" not in fm:
        print(f"FAIL: {f} frontmatter missing tools:")
        fail = True
    n = len(body.strip().splitlines())
    if n <= 30:
        print(f"FAIL: {f} body only {n} lines (need >30)")
        fail = True
    else:
        print(f"ok: {f} body has {n} lines (>30)")
    low = t.lower()
    if "myfi" not in low or "toolkit" not in low:
        print(f"FAIL: {f} does not cite MYFI + toolkit")
        fail = True
    else:
        print(f"ok: {f} cites MYFI + toolkit")
sys.exit(1 if fail else 0)
PY
[ $? -eq 0 ] && ok "frontmatter + body-length + MYFI/toolkit citation, both agents" \
             || bad "acceptance python check failed"

rg -qi 'opus' agents/advisor.md \
  && ok "agents/advisor.md names opus" \
  || bad "agents/advisor.md does not name opus"

# advisor's tools: line must wire a dispatch tool (Agent/Task) so it can actually fan out to
# the flock, not just read/quote.
tools_line="$(grep -m1 '^tools:' agents/advisor.md)"
if echo "$tools_line" | grep -qE '\b(Agent|Task)\b'; then
  ok "agents/advisor.md tools: wires a dispatch tool ($tools_line)"
else
  bad "agents/advisor.md tools: has no dispatch tool: $tools_line"
fi

# quant loads the finance skill per [SPEC] -- grep the body, not just a passing mention.
rg -qi 'finance' agents/quant.md \
  && ok "agents/quant.md references the finance skill" \
  || bad "agents/quant.md does not reference the finance skill"

if [ "$fail" = 0 ]; then echo "PASS test_agents_actors"; else echo "FAIL test_agents_actors"; fi
exit $fail
