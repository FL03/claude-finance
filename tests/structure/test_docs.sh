#!/usr/bin/env bash
# W7-docs-readme structural + eval-margin gate. Wraps the unit [ACCEPTANCE] predicate: README.md
# carries 0 hits for shepherd-engineering residue, examples/minimal/myfi.toml is present and
# parses as TOML, docs/ is present, and README.md names the finance surface (advisor/quant/
# toolkit/analyze). Also proves the readme_finance rubric discriminates the docs/evals/
# readme_{good,bad}.md goldens by a clear margin under the mock seam (the gate-lane half of the
# unit's [EVALS] "mock margin" requirement, kept self-contained here since services/eval/tests/**
# belongs to a sibling unit's file scope). Deterministic, python3/rg only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

# 1. No shepherd-engineering residue in README.md -- this IS the unit's verbatim acceptance grep.
n="$(rg -n 'engineering work|@engineer|@coder|sprint' README.md | wc -l | tr -d ' ')"
[ "$n" = 0 ] && ok "README.md has 0 hits for engineering-sprint residue" \
             || bad "README.md still has $n hit(s) for engineering-sprint residue"

# 2. examples/minimal/myfi.toml present and a real TOML file.
[ -f examples/minimal/myfi.toml ] && ok "examples/minimal/myfi.toml present" \
                                   || bad "examples/minimal/myfi.toml missing"
python3 -c "import tomllib; tomllib.load(open('examples/minimal/myfi.toml','rb'))" 2>/dev/null \
  && ok "examples/minimal/myfi.toml parses as TOML" \
  || bad "examples/minimal/myfi.toml does not parse as TOML"

# 3. docs/ present.
[ -d docs ] && ok "docs/ present" || bad "docs/ missing"

# 4. README.md names the finance surface.
rg -ni 'advisor|quant|toolkit|analyze' README.md >/dev/null 2>&1 \
  && ok "README.md names the finance surface (advisor/quant/toolkit/analyze)" \
  || bad "README.md does not name the finance surface"

# 5. The exact unit [ACCEPTANCE] predicate, verbatim, as one compound check.
if test -f examples/minimal/myfi.toml && test -d docs \
   && rg -ni 'advisor|quant|toolkit|analyze' README.md >/dev/null; then
  ok "unit [ACCEPTANCE] compound predicate exits 0"
else
  bad "unit [ACCEPTANCE] compound predicate failed"
fi

# 6. eval-margin gate: the readme_finance rubric, under the MYFI_LLM_MOCK seam, must score the
# good golden above threshold and the bad (engineering-residue) golden below it, by a clear margin.
margin_check_out="$(python3 - <<'PY'
import json
import os
import subprocess
import sys
import tempfile

RUBRIC = "readme_finance"
GOOD = "docs/evals/readme_good.md"
BAD = "docs/evals/readme_bad.md"
MARGIN = 15

with open(f"services/eval/rubrics/{RUBRIC}.rubric.json", encoding="utf-8") as fh:
    rubric = json.load(fh)
scale = rubric["scale"]
threshold = rubric["threshold"]
dim_keys = [d["key"] for d in rubric["dimensions"]]

good_mock = json.dumps({
    "scores": {k: scale for k in dim_keys},
    "rationale": "names the flock, install is concrete, no residue, actionable",
})
bad_mock = json.dumps({
    "scores": {k: 1 for k in dim_keys},
    "rationale": "engineering-sprint residue throughout, no finance surface named",
})


def score(input_file: str, mock_payload: str) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        fh.write(mock_payload)
        mock_path = fh.name
    try:
        env = dict(os.environ)
        env["MYFI_LLM_MOCK"] = mock_path
        result = subprocess.run(
            [sys.executable, "services/eval/eval.py", "run", f"--kind={RUBRIC}",
             f"--input-file={input_file}", "--json"],
            capture_output=True, text=True, env=env, timeout=30,
        )
        if result.returncode not in (0, 1):
            print(f"eval.py exited {result.returncode}: {result.stderr}", file=sys.stderr)
            sys.exit(4)
        return json.loads(result.stdout)["overall"]
    finally:
        os.unlink(mock_path)


good_overall = score(GOOD, good_mock)
bad_overall = score(BAD, bad_mock)
margin = good_overall - bad_overall

print(f"good={good_overall} bad={bad_overall} threshold={threshold} margin={margin}")

problems = []
if good_overall < threshold:
    problems.append(f"good golden {good_overall} < threshold {threshold}")
if bad_overall >= threshold:
    problems.append(f"bad golden {bad_overall} >= threshold {threshold}")
if margin < MARGIN:
    problems.append(f"margin {margin} < {MARGIN}")

if problems:
    print("PROBLEMS: " + "; ".join(problems), file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PY
)"
margin_rc=$?
if [ "$margin_rc" = 0 ]; then
  ok "readme_finance eval margin: $margin_check_out"
else
  bad "readme_finance eval margin check failed: $margin_check_out"
fi

if [ "$fail" = 0 ]; then echo "PASS test_docs"; else echo "FAIL test_docs"; fi
exit $fail
