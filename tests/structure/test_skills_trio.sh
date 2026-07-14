#!/usr/bin/env bash
# W4-skills-trio structural gate: IMPROVE + COMPLIANCE + TAXES skills.
# Wraps the unit [ACCEPTANCE]: frontmatter name==dir for all three, each body
# non-trivial (>200 chars after the frontmatter), and IMPROVE names all four
# loop verbs (harvest/store/inject/cite). Deterministic, python3 only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

for s in improve compliance taxes; do
  p="skills/${s}/SKILL.md"
  if [ -f "$p" ]; then
    ok "$p present"
  else
    bad "$p missing"
    continue
  fi

  python3 - "$s" "$p" <<'PY'
import re, sys
skill, path = sys.argv[1], sys.argv[2]
t = open(path, encoding="utf-8").read()
parts = t.split('---', 2)
assert len(parts) >= 3, f"{path}: not valid frontmatter-delimited markdown"
fm = t.split('---')[1]
assert re.search(rf'^name:\s*{skill}\s*$', fm, re.M), f"{path}: frontmatter name != {skill}"
body = parts[2].strip()
assert len(body) > 200, f"{path}: body too thin ({len(body)} chars, need >200)"
PY
  if [ $? -eq 0 ]; then
    ok "$p frontmatter name==${s} + non-trivial body"
  else
    bad "$p acceptance python check failed"
  fi
done

I=skills/improve/SKILL.md
if [ -f "$I" ]; then
  python3 - "$I" <<'PY'
import sys
t = open(sys.argv[1], encoding="utf-8").read().lower()
missing = [v for v in ("harvest", "store", "inject", "cite") if v not in t]
assert not missing, f"missing loop verb(s): {missing}"
PY
  if [ $? -eq 0 ]; then
    ok "IMPROVE names all four loop verbs (harvest/store/inject/cite)"
  else
    bad "IMPROVE missing one or more loop verbs"
  fi
fi

for f in \
  services/eval/rubrics/improve_loop.rubric.json \
  services/eval/rubrics/compliance_coverage.rubric.json \
  services/eval/rubrics/taxes_knowledge.rubric.json \
  skills/improve/evals/good.md skills/improve/evals/bad.md \
  skills/compliance/evals/good.md skills/compliance/evals/bad.md \
  skills/taxes/evals/good.md skills/taxes/evals/bad.md
do
  [ -f "$f" ] && ok "$f present" || bad "$f missing"
done

python3 -c "
import json
for k in ('improve_loop', 'compliance_coverage', 'taxes_knowledge'):
    json.load(open(f'services/eval/rubrics/{k}.rubric.json', encoding='utf-8'))
" && ok "all three new rubrics parse as valid JSON" || bad "a new rubric is not valid JSON"

if [ "$fail" = 0 ]; then echo "PASS test_skills_trio"; else echo "FAIL test_skills_trio"; fi
exit $fail
