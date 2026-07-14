#!/usr/bin/env bash
# tests/integration/run.sh -- myfi's top-level integration suite.
#
# W7-integration-close [ACCEPTANCE]: `bash tests/integration/run.sh` exits 0
# with (1) plugin-load green (every component discovered, .mcp.json valid,
# no src/), (2) the /myfi:analyze mock-seam e2e green, (3) the toolkit
# db+quote smoke green, and (4) the close_report rubric's golden-margin
# wiring green (structural tripwire on the shipped close report). <2s
# aggregate via the mock seam (no live LLM call, no network) -- this suite is
# the fourth lane `bin/myfi-test` wires alongside toolkit pytest, services
# unittest, and hooks/tests/run.sh.
#
# Deterministic + mock-free beyond the analyze e2e's mocked LLM completion.
# bash-3.2-safe (macOS ships 3.2 as /bin/bash; no `${var,,}`, no associative
# arrays, no `mapfile`) -- mirrors hooks/tests/run.sh's own constraint.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

HERE="$(cd "$(dirname "$0")" && pwd)"

fail=0
total=0

run_suite() {
  local name="$1"
  shift
  total=$((total + 1))
  echo "== $name =="
  if "$@"; then
    echo "-- $name PASS --"
  else
    echo "-- $name FAIL --"
    fail=$((fail + 1))
  fi
  echo
}

run_suite "test_plugin_load (plugin-load: agents/skills/commands frontmatter + .mcp.json + no src/)" \
  python3 -m unittest tests.integration.test_plugin_load -v

run_suite "test_toolkit_smoke (toolkit db+quote smoke, end to end)" \
  bash "$HERE/test_toolkit_smoke.sh"

run_suite "test_analyze_e2e (/myfi:analyze mock-seam e2e)" \
  bash "$HERE/test_analyze_e2e.sh"

run_suite "test_close_report_eval (close_report rubric wiring + golden margin)" \
  python3 -m unittest tests.integration.test_close_report_eval -v

echo "== $((total - fail))/$total integration suites passed =="
if [ "$fail" = 0 ]; then
  echo "PASS tests/integration/run.sh"
else
  echo "FAIL tests/integration/run.sh"
fi
exit "$fail"
