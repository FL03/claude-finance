#!/usr/bin/env bash
# W5-commands-analyze-plan structural gate -- /myfi:analyze (single-shot) + /myfi:plan
# (advisor-led pipeline). Wraps the unit [ACCEPTANCE]: both command files present with valid
# frontmatter, analyze names a report/artifact output, plan names the advisor pipeline. Also
# checks the rubric + golden files this unit ships per [FILES]. Deterministic, python3/rg only,
# <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

for f in commands/analyze.md commands/plan.md; do
  [ -f "$f" ] && ok "$f present" || { bad "$f missing"; echo FAIL; exit 1; }
done

python3 - <<'PY'
t = open("commands/analyze.md", encoding="utf-8").read()
assert t.startswith("---"), "commands/analyze.md does not start with frontmatter delimiter"
assert "description:" in t.split("---")[1], "commands/analyze.md frontmatter missing description:"
assert "report" in t.lower(), "commands/analyze.md never mentions 'report'"
PY
[ $? -eq 0 ] && ok "commands/analyze.md frontmatter + 'report' present" \
             || bad "commands/analyze.md acceptance python check failed"

rg -qni 'artifact|report.*path|\.md|\.html' commands/analyze.md \
  && ok "commands/analyze.md names a report/artifact output path" \
  || bad "commands/analyze.md never names a report/artifact output path"

rg -qni 'advisor' commands/plan.md \
  && ok "commands/plan.md references @advisor" \
  || bad "commands/plan.md never references @advisor"

python3 - <<'PY'
t = open("commands/plan.md", encoding="utf-8").read()
assert t.startswith("---"), "commands/plan.md does not start with frontmatter delimiter"
assert "description:" in t.split("---")[1], "commands/plan.md frontmatter missing description:"
assert "argument-hint:" in t.split("---")[1], "commands/plan.md frontmatter missing argument-hint:"
assert "allowed-tools:" in t.split("---")[1], "commands/plan.md frontmatter missing allowed-tools:"
t2 = open("commands/analyze.md", encoding="utf-8").read()
fm2 = t2.split("---")[1]
assert "argument-hint:" in fm2, "commands/analyze.md frontmatter missing argument-hint:"
assert "allowed-tools:" in fm2, "commands/analyze.md frontmatter missing allowed-tools:"
PY
[ $? -eq 0 ] && ok "both commands carry description/argument-hint/allowed-tools frontmatter" \
             || bad "frontmatter shape check failed"

for f in \
  services/eval/rubrics/analyze_report.rubric.json \
  services/eval/rubrics/plan_pipeline.rubric.json \
  commands/evals/analyze_good.md commands/evals/analyze_bad.md \
  commands/evals/plan_good.md commands/evals/plan_bad.md
do
  [ -f "$f" ] && ok "$f present" || bad "$f missing"
done

python3 -c "
import json
for k in ('analyze_report', 'plan_pipeline'):
    json.load(open(f'services/eval/rubrics/{k}.rubric.json', encoding='utf-8'))
" && ok "both new rubrics parse as valid JSON" || bad "a new rubric is not valid JSON"

if [ "$fail" = 0 ]; then echo "PASS test_commands_analyze_plan"; else echo "FAIL test_commands_analyze_plan"; fi
exit $fail
