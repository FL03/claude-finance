#!/usr/bin/env bash
# tests/structure/run.sh -- myfi's structural gate: runs every tests/structure/
# test_*.sh and aggregates pass/fail.
#
# Each test_*.sh here is a standalone structural predicate (frontmatter shape,
# component layout, .mcp.json wiring, doc/skill/command invariants) -- git/jq/
# python3 only, deterministic, no network, no LLM call, <1s each. This runner
# adds no logic beyond discovering the scripts, running each, and aggregating,
# so it stays a thin dispatcher, not a place any test's behavior can drift.
#
# It is the fifth lane `bin/myfi-test` wires, alongside toolkit pytest, services
# unittest, hooks/tests/run.sh, and tests/integration/run.sh. Kept out of those
# four because a repo-layout assertion is neither a unit test of a package nor
# an end-to-end run -- it gates the SHAPE of the plugin (which agents/skills/
# commands exist, what their frontmatter must carry), the layer the other four
# lanes assume is already correct.
#
# bash-3.2-safe (macOS ships 3.2 as /bin/bash): no ${var,,}, no associative
# arrays, no mapfile -- mirrors tests/integration/run.sh's constraint.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

HERE="$(cd "$(dirname "$0")" && pwd)"

fail=0
total=0

run_suite() {
  local script="$1"
  local name
  name="$(basename "$script")"
  total=$((total + 1))
  echo "== $name =="
  if bash "$script"; then
    echo "-- $name PASS --"
  else
    echo "-- $name FAIL --"
    fail=$((fail + 1))
  fi
  echo
}

# Sorted glob so the run order is stable across machines. `test_*.sh` never
# matches this runner (run.sh), so the lane can't recurse into itself.
found=0
for script in "$HERE"/test_*.sh; do
  [ -f "$script" ] || continue
  found=$((found + 1))
  run_suite "$script"
done

if [ "$found" = 0 ]; then
  echo "FAIL tests/structure/run.sh -- no test_*.sh scripts found under $HERE"
  exit 1
fi

echo "== $((total - fail))/$total structure suites passed =="
if [ "$fail" = 0 ]; then
  echo "PASS tests/structure/run.sh"
else
  echo "FAIL tests/structure/run.sh"
fi
exit "$fail"
