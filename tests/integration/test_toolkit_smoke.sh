#!/usr/bin/env bash
# tests/integration/test_toolkit_smoke.sh -- toolkit CLI + DB smoke, end to end.
#
# W7-integration-close [SPEC] item 3 / [ACCEPTANCE]: "the toolkit CLI+MCP+DB
# smoke end-to-end" / "toolkit db+quote smoke green". Drives the REAL
# `myfi_toolkit.cli` dispatcher through a subprocess -- one layer up from
# `services/toolkit/tests/test_myctx.py` and `test_marketdata.py`, which call
# `myctx.dispatch(...)` / `marketdata.quote(...)` directly in-process. This
# script is what proves the actual command line a user or agent runs
# (`db init`, `quote <symbol>`) works end to end, not just the functions
# behind it.
#
# MCP smoke (`asyncio.run(mcp.list_tools())`) already lives in
# `services/toolkit/tests/test_mcp_smoke.py`, run by `bin/myfi-test`'s toolkit
# lane -- not duplicated here (the `mcp` SDK is only importable inside the
# poetry venv, and re-importing it here would risk this suite's <2s budget
# for no new coverage; see plan [NOTES] "DUPLICATION RISK").
#
# Uses the stdlib `PYTHONPATH` path (no poetry) -- `myfi_toolkit` is pure
# Python with no compiled extension, and neither `db` nor `quote` needs
# anything beyond the stdlib (sqlite3, dataclasses) -- so this stays fast and
# poetry-independent, exactly the fallback `bin/myfi-toolkit` itself uses when
# poetry is not on PATH.
set -eu -o pipefail
cd "$(git rev-parse --show-toplevel)"
ROOT="$(pwd)"
TOOLKIT_DIR="$ROOT/services/toolkit"

fail=0
ok() { echo "ok: $1"; }
bad() { echo "FAIL: $1"; fail=1; }

tmp=$(mktemp -d -t myfi-toolkit-smoke.XXXXXX)
trap 'rm -rf "$tmp"' EXIT
cd "$tmp"

run_cli() {
  PYTHONPATH="$TOOLKIT_DIR" PWD="$tmp" python3 -m myfi_toolkit.cli "$@"
}

if out=$(run_cli db init 2>&1) && [ -f .myfi/myfi.db ]; then
  ok "db init creates .myfi/myfi.db"
else
  bad "db init failed: $out"
fi

count1="$(sqlite3 .myfi/myfi.db 'select count(*) from schema_versions;' 2>/dev/null || echo ERR)"
if [ "$count1" != "ERR" ] && [ "$count1" -ge 1 ]; then
  ok "schema_versions has >= 1 row after db init ($count1)"
else
  bad "schema_versions unreadable or empty after db init: $count1"
fi

if run_cli db init >/dev/null 2>&1; then
  count2="$(sqlite3 .myfi/myfi.db 'select count(*) from schema_versions;' 2>/dev/null || echo ERR)"
  if [ "$count2" = "$count1" ]; then
    ok "db init is idempotent (schema_versions count unchanged: $count2)"
  else
    bad "db init re-run changed schema_versions count: $count1 -> $count2"
  fi
else
  bad "second db init call failed"
fi

if quote_out=$(run_cli quote AAPL 2>&1); then
  if printf '%s' "$quote_out" | python3 -c '
import json, sys
d = json.load(sys.stdin)
assert d["symbol"] == "AAPL", d
assert d["source"] == "research", d
assert set(d) == {"symbol", "price", "currency", "asof", "source"}, d
' 2>/dev/null; then
    ok "quote AAPL returns typed JSON (symbol=AAPL, source=research)"
  else
    bad "quote AAPL returned unexpected JSON shape: $quote_out"
  fi
else
  bad "quote AAPL failed: $quote_out"
fi

if [ "$fail" = 0 ]; then
  echo "PASS test_toolkit_smoke"
else
  echo "FAIL test_toolkit_smoke"
fi
exit "$fail"
