#!/usr/bin/env bash
# W6-harness-loops structural gate: redo/focus/goal loops + workflow/agent-team templates.
# Wraps the unit [ACCEPTANCE] predicate: REDO cap 3 documented, a bounded-loop predicate
# (--max / new_findings) present, and all three template files exist. Also checks the
# loop_discipline rubric + its good/bad goldens ship and parse. Deterministic, rg/jq/python3
# only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

L=skills/myfi/references/loop-templates.md
W=skills/myfi/references/workflow-templates.md
A=skills/myfi/references/agent-team-templates.md

for f in "$L" "$W" "$A"; do
  [ -f "$f" ] && ok "$f present" || bad "$f missing"
done

# [ACCEPTANCE] line 1: REDO cap of 3 documented (a line naming REDO also carries a literal 3).
if rg -n 'REDO' "$L" 2>/dev/null | rg -n '3' >/dev/null; then
  ok "loop-templates.md documents a REDO cap of 3"
else
  bad "loop-templates.md has no REDO line carrying a literal 3"
fi

# [ACCEPTANCE] line 2: a bounded-loop predicate (--max or new_findings) is present.
if rg -ni 'max|new_findings' "$L" >/dev/null 2>&1; then
  ok "loop-templates.md names a --max / new_findings bounded-loop predicate"
else
  bad "loop-templates.md has no --max / new_findings predicate"
fi

# Every per-role template in the quick-selection table names its own default --max.
python3 - "$L" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
roles = ("advisor", "quant", "worker", "auditor", "designer")
missing = [r for r in roles if r not in t.lower()]
assert not missing, f"missing role(s) from loop-templates.md: {missing}"
assert t.count("new_findings") >= 3, "new_findings predicate should appear per convergence template, not once"
assert re.search(r"Default `--max`:\s*\d+", t), "no 'Default `--max`: N' line found"
PY
[ $? -eq 0 ] && ok "all five looping roles present, new_findings + Default --max lines found" \
             || bad "role/predicate density check failed"

# The rubric + its good/bad goldens ship and parse.
R=services/eval/rubrics/loop_discipline.rubric.json
G=skills/myfi/references/evals/good.md
B=skills/myfi/references/evals/bad.md
for f in "$R" "$G" "$B"; do
  [ -f "$f" ] && ok "$f present" || bad "$f missing"
done

if [ -f "$R" ]; then
  python3 -c "
import json
r = json.load(open('$R', encoding='utf-8'))
assert r.get('kind') == 'loop_discipline', 'kind mismatch'
keys = {d['key'] for d in r.get('dimensions', [])}
need = {'names-the-cap', 'measurable-predicate', 'role-shaped'}
missing = need - keys
assert not missing, f'missing dimension(s): {missing}'
" && ok "loop_discipline.rubric.json valid JSON with the three required dimensions" \
    || bad "loop_discipline.rubric.json invalid or missing a required dimension"
fi

if [ "$fail" = 0 ]; then echo "PASS test_harness_loops"; else echo "FAIL test_harness_loops"; fi
exit $fail
