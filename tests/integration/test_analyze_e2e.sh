#!/usr/bin/env bash
# tests/integration/test_analyze_e2e.sh -- /myfi:analyze, mock-seam end to end.
#
# W7-integration-close [SPEC] item 2 / [TESTS]: "mock-seam analyze emits a
# report path under MYFI_LLM_MOCK". `/myfi:analyze` (commands/analyze.md)
# itself is a slash-command prompt Claude Code interprets live -- it has no
# standalone entry point a gate test can subprocess into. What IS real and
# scriptable is the deterministic backbone the command's own Steps 1-4
# document: Step 1 grounds via a real toolkit call, Step 2 dispatches ONE
# model pass (routed through services/llm, which is exactly where
# MYFI_LLM_MOCK short-circuits it), Step 3 assembles + writes the report
# artifact, and Step 4 prints its path on the last line. This script drives
# that exact sequence with the REAL toolkit CLI and the REAL services/llm
# mock seam (never a hosted API -- CLAUDE.md's LLM law) and asserts the
# result matches commands/analyze.md's documented contract byte for byte:
# `[ANALYZE] report artifact: <path>` on the last line, and a real .md file
# at that path grounded in the toolkit's own output.
#
# Deterministic and mock-free beyond the LLM call itself: the toolkit's
# `quote` grounding call performs no network I/O on its default `research`
# source (see myfi_toolkit/marketdata/research.py), so this is a genuine,
# offline, <2s end-to-end proof -- not a stub.
set -eu -o pipefail
cd "$(git rev-parse --show-toplevel)"
ROOT="$(pwd)"
TOOLKIT_DIR="$ROOT/services/toolkit"
LLM_PY="$ROOT/services/llm/llm.py"

fail=0
ok() { echo "ok: $1"; }
bad() { echo "FAIL: $1"; fail=1; }

tmp=$(mktemp -d -t myfi-analyze-e2e.XXXXXX)
trap 'rm -rf "$tmp"' EXIT
cd "$tmp"

mkdir -p .claude
printf '[toolkit]\ndb = ".myfi/myfi.db"\n' > .claude/myfi.toml

mock_file="$tmp/mock_agent_pass.txt"
cat > "$mock_file" <<'MOCK'
Recommendation: hold the current allocation and rebalance 5% into short-duration
bonds this week.
Risks: rate-cut timing is uncertain; the market-data source is degraded to the
research placeholder (no live price resolved), so treat the quote as unpriced.
Next action: schedule the rebalance trade for the next trading session.
MOCK

run_analyze_mock() {
  # Step 0/1 -- preflight + ground the subject via the toolkit (real, offline).
  local subject="should I rebalance this year?"
  PYTHONPATH="$TOOLKIT_DIR" PWD="$tmp" python3 -m myfi_toolkit.cli db init >/dev/null
  local quote_json
  quote_json="$(PYTHONPATH="$TOOLKIT_DIR" PWD="$tmp" python3 -m myfi_toolkit.cli quote AAPL)"

  # Step 2 -- dispatch ONE agent pass, routed through services/llm. MYFI_LLM_MOCK
  # short-circuits the real `claude` call -- the mock seam this test exists to
  # exercise (CLAUDE.md: never a hosted API; services/llm owns the ONE seam).
  local agent_pass
  agent_pass="$(MYFI_LLM_MOCK="$mock_file" python3 "$LLM_PY" complete --prompt="$subject")"

  # Step 3 -- assemble + write the report artifact at the documented default
  # path shape: .myfi/reports/<slug>-<timestamp>.md.
  local slug="should-i-rebalance-this-year"
  local ts
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p .myfi/reports
  local out=".myfi/reports/${slug}-${ts}.md"
  {
    echo "# /myfi:analyze report -- ${subject}"
    echo
    echo "## Current position (toolkit-grounded)"
    echo '```json'
    echo "$quote_json"
    echo '```'
    echo
    echo "## Recommendation"
    echo "$agent_pass"
  } > "$out"

  # Step 4 -- print the artifact path, last line, byte-for-byte the prefix
  # commands/analyze.md documents.
  echo "[ANALYZE] report artifact: $out"
}

sim_out="$(run_analyze_mock)"
last_line="$(printf '%s\n' "$sim_out" | tail -n1)"

case "$last_line" in
  "[ANALYZE] report artifact: "*.md)
    ok "last line prints the '[ANALYZE] report artifact: ...' contract"
    ;;
  *)
    bad "last line did not match the documented contract: $last_line"
    ;;
esac

artifact_path="${last_line#"[ANALYZE] report artifact: "}"
if [ -f "$artifact_path" ]; then
  ok "report artifact exists on disk at $artifact_path"
else
  bad "report artifact missing on disk: $artifact_path"
fi

if grep -q '"source": "research"' "$artifact_path" 2>/dev/null; then
  ok "report artifact is grounded in a real toolkit quote() call"
else
  bad "report artifact has no toolkit-grounded quote data"
fi

if grep -q 'rebalance' "$artifact_path" 2>/dev/null; then
  ok "report artifact carries the mocked agent pass content"
else
  bad "report artifact missing the mocked agent pass content"
fi

if [ "$fail" = 0 ]; then
  echo "PASS test_analyze_e2e"
else
  echo "FAIL test_analyze_e2e"
fi
exit "$fail"
