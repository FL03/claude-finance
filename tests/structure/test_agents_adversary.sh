#!/usr/bin/env bash
# W4-agents-adversary-editor structural gate — @auditor (compliance adversary) +
# @designer (final artifact editor). Wraps the unit [ACCEPTANCE] predicate:
# auditor carries the Hypothesis+Falsification+Confidence triple + REDO
# verdicts; designer names its artifact/live-HTML duties; both have valid
# frontmatter (name/description/tools) and a system-prompt body >30 lines.
# Deterministic, python3/rg only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

A=agents/auditor.md
D=agents/designer.md

[ -f "$A" ] && ok "agents/auditor.md present" || { bad "agents/auditor.md missing"; echo FAIL; exit 1; }
[ -f "$D" ] && ok "agents/designer.md present" || { bad "agents/designer.md missing"; echo FAIL; exit 1; }

rg -n 'Hypothesis' "$A" >/dev/null 2>&1 && ok "auditor names Hypothesis"    || bad "auditor missing Hypothesis"
rg -n 'Falsification' "$A" >/dev/null 2>&1 && ok "auditor names Falsification" || bad "auditor missing Falsification"
rg -n 'Confidence' "$A" >/dev/null 2>&1 && ok "auditor names Confidence"   || bad "auditor missing Confidence"
rg -n 'REDO' "$A" >/dev/null 2>&1 && ok "auditor names REDO verdicts"      || bad "auditor missing REDO"
rg -n '\b3\b' "$A" >/dev/null 2>&1 && ok "auditor states a numeric REDO cap" || bad "auditor missing numeric REDO cap"

rg -ni 'artifact' "$D" >/dev/null 2>&1 && ok "designer names artifact duties" || bad "designer missing artifact reference"
rg -ni 'live.?html' "$D" >/dev/null 2>&1 && ok "designer names live-HTML duties" || bad "designer missing live-HTML reference"

python3 - "$A" "$D" <<'PY'
import re, sys
for path in sys.argv[1:]:
    t = open(path, encoding="utf-8").read()
    parts = t.split('---')
    assert len(parts) >= 3, f"{path}: missing frontmatter fences"
    fm, body = parts[1], parts[2]
    assert re.search(r'^name:\s*\S+', fm, re.M), f"{path}: frontmatter missing name:"
    assert 'description:' in fm, f"{path}: frontmatter missing description:"
    assert 'tools:' in fm, f"{path}: frontmatter missing tools:"
    lines = [ln for ln in body.strip().splitlines() if ln.strip()]
    assert len(lines) > 30, f"{path}: body has {len(lines)} non-blank lines, need >30"
print("OK: frontmatter (name/description/tools) + body >30 lines for both files")
PY
[ $? -eq 0 ] && ok "frontmatter + body-length checks" || bad "frontmatter/body-length python check failed"

for f in agents/evals/auditor_good.md agents/evals/auditor_bad.md \
         agents/evals/designer_good.md agents/evals/designer_bad.md; do
  [ -s "$f" ] && ok "$f present + non-empty" || bad "$f missing or empty"
done

for r in services/eval/rubrics/audit_finding.rubric.json services/eval/rubrics/designer_artifact.rubric.json; do
  [ -f "$r" ] && python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$r" >/dev/null 2>&1 \
    && ok "$r present + valid json" || bad "$r missing or invalid json"
done

if [ "$fail" = 0 ]; then echo "PASS test_agents_adversary"; else echo "FAIL test_agents_adversary"; fi
exit $fail
