#!/usr/bin/env bash
# hooks/tests/run.sh -- gate tests for myfi's harness hooks.
#
# Ported in spirit from shepherd's hooks/tests/run.sh
# (~/src/fl03/shepherd/hooks/tests/run.sh: `set -eu -o pipefail` + a failing
# pipeline inside a command substitution can silently exit the whole script
# non-zero -- this file pins the same `run_case` contract shepherd's does).
# Scoped to exactly the four scripts this unit ships: dispatch_guard.sh,
# dedup_write_guard.sh, session_venv.sh, adaptation_capture.sh.
#
# Self-contained per this unit's [TESTS]/[EVALS]: no network, every external
# command that would otherwise be slow or non-deterministic is stubbed --
#   - bin/myfi-venv-ensure: a scratch STUB (never invokes real poetry).
#   - poetry itself: excluded from SAFE_PATH below, forcing bin/myfi-toolkit's
#     OWN already-designed PYTHONPATH fallback (services/toolkit's myctx.db
#     module is stdlib-only -- see myfi_toolkit/myctx/db.py's module docstring
#     -- so this fallback is not a test-only shortcut, it is bin/myfi-toolkit's
#     real poetry-less code path). This keeps the adaptation-roundtrip eval a
#     genuine round-trip against the REAL toolkit/schema (not a mock) while
#     staying <2s and network-free.
# bash-3.2-safe (macOS ships 3.2 as /bin/bash; no `${var,,}`, no associative
# arrays, no `mapfile`) and completes in well under 2s.

set -eu -o pipefail
cd "$(dirname "$0")"
HOOKS_DIR="$(cd .. && pwd)/scripts"
REPO_ROOT="$(cd ../.. && pwd)"

# A PATH with python3/jq/git/sqlite3 but WITHOUT poetry's directory -- forces
# bin/myfi-toolkit's stdlib PYTHONPATH fallback instead of the slow
# `poetry -C ... run` path. See header comment.
PY_DIR="$(dirname "$(command -v python3)")"
SAFE_PATH="/usr/bin:/bin:$PY_DIR"

fails=0
total=0

# Usage: run_case <name> <script> <payload-json> [expect-substring] [expect-empty|expect-nonempty]
run_case() {
  local name="$1" script="$2" payload="$3" expect="${4:-}" mode="${5:-}"
  total=$((total+1))
  local out rc
  set +e
  out=$(printf '%s' "$payload" | PATH="$SAFE_PATH" bash "$HOOKS_DIR/$script" 2>&1)
  rc=$?
  set -e
  if [[ "$rc" -ne 0 ]]; then
    printf '  FAIL  %-45s rc=%d out=%s\n' "$name" "$rc" "$out"
    fails=$((fails+1))
    return 0
  fi
  if [[ -n "$expect" ]] && [[ "$out" != *"$expect"* ]]; then
    printf '  FAIL  %-45s expected substring %q in: %s\n' "$name" "$expect" "$out"
    fails=$((fails+1))
    return 0
  fi
  if [[ "$mode" == "expect-empty" && -n "$out" ]]; then
    printf '  FAIL  %-45s expected empty stdout, got: %s\n' "$name" "$out"
    fails=$((fails+1))
    return 0
  fi
  if [[ "$mode" == "expect-nonempty" && -z "$out" ]]; then
    printf '  FAIL  %-45s expected non-empty stdout, got nothing\n' "$name"
    fails=$((fails+1))
    return 0
  fi
  printf '  PASS  %s\n' "$name"
}

# ---------------------------------------------------------------------------
# Scratch project -- every hook gates on .claude/myfi.toml (is_myfi_project).
# bin/ + services/ are symlinked to the REAL repo (read-only usage; this unit
# must not write there) so adaptation_capture.sh's roundtrip exercises the
# real myctx schema, not a synthetic stand-in.
# ---------------------------------------------------------------------------
tmp=$(mktemp -d -t myfi-hook-test.XXXXXX)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/.claude" "$tmp/bin"
printf '[toolkit]\ndb = ".myfi/myfi.db"\n' > "$tmp/.claude/myfi.toml"
ln -s "$REPO_ROOT/services" "$tmp/services"
cp "$REPO_ROOT/bin/myfi-toolkit" "$tmp/bin/myfi-toolkit"
chmod +x "$tmp/bin/myfi-toolkit"

cd "$tmp"

echo "== dispatch_guard.sh -- closed-flock enforcement =="
for role in advisor quant auditor designer worker trader; do
  run_case "allows-$role" dispatch_guard.sh \
    "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"$role\"},\"session_id\":\"s1\"}" \
    "" expect-empty
done
run_case "denies-missing-subagent-type" dispatch_guard.sh \
  '{"tool_name":"Agent","tool_input":{},"session_id":"s1"}' \
  "DISPATCH-MISSING-SUBAGENT-TYPE"
run_case "denies-general-purpose" dispatch_guard.sh \
  '{"tool_name":"Task","tool_input":{"subagent_type":"general-purpose"},"session_id":"s1"}' \
  "DISPATCH-MISSING-SUBAGENT-TYPE"
run_case "denies-off-flock" dispatch_guard.sh \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"conductor"},"session_id":"s1"}' \
  "DISPATCH-OFF-FLOCK"
run_case "ignores-non-agent-tool" dispatch_guard.sh \
  '{"tool_name":"Read","tool_input":{"file_path":"a"},"session_id":"s1"}' \
  "" expect-empty

echo "== dedup_write_guard.sh -- DEDUP-HIT gate =="
mkdir -p "$tmp/src"
printf 'def already_here():\n    pass\n' > "$tmp/src/existing.py"
run_case "blocks-dup-symbol-write" dedup_write_guard.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"src/new.py","content":"def already_here():\n    pass\n"},"session_id":"s1"}' \
  "DEDUP-HIT"
run_case "blocks-dup-symbol-edit" dedup_write_guard.sh \
  '{"tool_name":"Edit","tool_input":{"file_path":"src/new.py","new_string":"def already_here():\n    pass\n"},"session_id":"s1"}' \
  "DEDUP-HIT"
run_case "allows-unique-symbol" dedup_write_guard.sh \
  '{"tool_name":"Write","tool_input":{"file_path":"src/new.py","content":"def brand_new_thing():\n    pass\n"},"session_id":"s1"}' \
  "" expect-empty
run_case "ignores-non-write-tool" dedup_write_guard.sh \
  '{"tool_name":"Bash","tool_input":{"command":"ls"},"session_id":"s1"}' \
  "" expect-empty
rm -rf "$tmp/src"

echo "== session_venv.sh -- SessionStart venv persistence, stubbed =="
# session_venv.sh resolves its plugin root from ${CLAUDE_PLUGIN_ROOT} first
# (falling back to its OWN script location otherwise) -- exactly like
# bin/myfi-toolkit does. Point it at the scratch dir so it finds OUR stub
# instead of the real repo's bin/myfi-venv-ensure.
export CLAUDE_PLUGIN_ROOT="$tmp"
mkdir -p "$tmp/bin"
cat > "$tmp/bin/myfi-venv-ensure" <<'STUB'
#!/usr/bin/env bash
# Test stub -- never touches real poetry/network (see run.sh header).
echo "myfi-venv-ensure: toolkit venv up to date (pyproject.toml unchanged)"
exit 0
STUB
chmod +x "$tmp/bin/myfi-venv-ensure"
run_case "noop-when-current" session_venv.sh '{"session_id":"s1"}' \
  "up to date" expect-nonempty

cat > "$tmp/bin/myfi-venv-ensure" <<'STUB'
#!/usr/bin/env bash
echo "myfi-venv-ensure: installing/refreshing myfi_toolkit venv via poetry..."
echo "myfi-venv-ensure: done"
exit 0
STUB
chmod +x "$tmp/bin/myfi-venv-ensure"
run_case "relays-install-message" session_venv.sh '{"session_id":"s1"}' \
  "done" expect-nonempty

rm -f "$tmp/bin/myfi-venv-ensure"
run_case "missing-ensure-binary-does-not-block" session_venv.sh '{"session_id":"s1"}' \
  "not found" expect-nonempty
unset CLAUDE_PLUGIN_ROOT

echo "== adaptation_capture.sh -- IMPROVE harvest sweep + roundtrip (EVAL) =="
# Isolated dir with .claude/myfi.toml but no bin/myfi-toolkit and no
# .myfi/myfi.db yet -- the "nothing to harvest from, schema unreachable"
# resilience path, decoupled from the round-trip scratch below.
tmp_nodb=$(mktemp -d -t myfi-hook-test-nodb.XXXXXX)
mkdir -p "$tmp_nodb/.claude"
printf '[toolkit]\ndb = ".myfi/myfi.db"\n' > "$tmp_nodb/.claude/myfi.toml"
# NOTE: run_case must run in THIS shell, not a `(...)` subshell -- a subshell
# would scope its `fails`/`total` increments away from the parent, silently
# losing a failure signal.
cd "$tmp_nodb"
run_case "noop-when-toolkit-absent" adaptation_capture.sh '{"session_id":"s1"}' "" expect-empty
cd "$tmp"
rm -rf "$tmp_nodb"

# test_bootstraps_schema_via_bin_myfi_toolkit: the FIRST adaptation_capture.sh
# call in this scratch dir (no .myfi/myfi.db yet) is what exercises the
# "bootstraps the schema via bin/myfi-toolkit" half of this unit's [EVALS] --
# zero audit_findings exist yet, so the harvest itself is a harmless no-op,
# but the db + schema now exist because the HOOK bootstrapped them (not a
# separate/redundant test-setup `db init` call, which would pay a second
# python3 cold-start for no additional coverage).
run_case "bootstraps-schema-via-bin-myfi-toolkit" adaptation_capture.sh \
  '{"session_id":"s1"}' "" expect-empty
total=$((total+1))
if [[ -f "$tmp/.myfi/myfi.db" ]]; then
  printf '  PASS  %s\n' "schema-bootstrapped-at-dot-myfi-myfi-db"
else
  printf '  FAIL  %s\n' "schema-bootstrapped-at-dot-myfi-myfi-db"
  fails=$((fails+1))
fi

# Seed a HIGH-severity audit_findings row directly (fast -- no python3
# cold-start; the schema already exists from the bootstrap call above),
# mirroring what a future @auditor write would leave behind.
PROJECT_ID="$tmp"
sqlite3 "$tmp/.myfi/myfi.db" <<SQL
INSERT INTO audit_findings (project_id, sprint_branch, concern, severity, hypothesis, finding, evidence_refs, created_at)
VALUES ('$PROJECT_ID', 'v0.0.0-dev.0', 'unvetted leverage claim', 'high',
        'the draft cites leverage with no margin-call scenario',
        'confirmed: no margin-call analysis present', NULL, strftime('%s','now'));
INSERT INTO audit_findings (project_id, sprint_branch, concern, severity, hypothesis, finding, evidence_refs, created_at)
VALUES ('$PROJECT_ID', 'v0.0.0-dev.0', 'trivial wording nit', 'low',
        'n/a', 'n/a', NULL, strftime('%s','now'));
SQL

# --- test_adaptation_roundtrip: the eval. Write via the hook (which writes
# through the bootstrapped myctx db, "via bin/myfi-toolkit" per this unit's
# [EVALS]), then a follow-up direct read confirms the mem_entries(kind='prior')
# row landed -- the generalization proof the memory wiring is live.
test_adaptation_roundtrip() {
  total=$((total+1))
  local out
  out=$(printf '{"session_id":"s1"}' | PATH="$SAFE_PATH" bash "$HOOKS_DIR/adaptation_capture.sh" 2>&1)
  if [[ "$out" != *"1 new prior"* ]]; then
    printf '  FAIL  %-45s harvest message missing/wrong: %s\n' "test_adaptation_roundtrip" "$out"
    fails=$((fails+1))
    return 0
  fi
  local row
  row=$(sqlite3 "$tmp/.myfi/myfi.db" \
    "SELECT title, source_path FROM mem_entries WHERE kind='prior' AND title='prior: unvetted leverage claim';")
  if [[ "$row" != "prior: unvetted leverage claim|audit_findings:1" ]]; then
    printf '  FAIL  %-45s follow-up read did not return the harvested row: %q\n' "test_adaptation_roundtrip" "$row"
    fails=$((fails+1))
    return 0
  fi
  # The LOW-severity row must NOT have been promoted (bounded, not a firehose).
  local low_count
  low_count=$(sqlite3 "$tmp/.myfi/myfi.db" \
    "SELECT count(*) FROM mem_entries WHERE title LIKE '%trivial wording nit%';")
  if [[ "$low_count" != "0" ]]; then
    printf '  FAIL  %-45s LOW-severity finding was harvested (must not be)\n' "test_adaptation_roundtrip"
    fails=$((fails+1))
    return 0
  fi
  printf '  PASS  %s\n' "test_adaptation_roundtrip"
}
test_adaptation_roundtrip

run_case "idempotent-second-run" adaptation_capture.sh '{"session_id":"s1"}' "" expect-empty

# A recurring concern (new audit_findings row, same concern text) refreshes
# the existing prior instead of growing a duplicate.
sqlite3 "$tmp/.myfi/myfi.db" <<SQL
INSERT INTO audit_findings (project_id, sprint_branch, concern, severity, hypothesis, finding, evidence_refs, created_at)
VALUES ('$PROJECT_ID', 'v0.0.0-dev.1', 'unvetted leverage claim', 'critical',
        'recurs again', 'still no margin-call analysis', NULL, strftime('%s','now'));
SQL
run_case "recurring-concern-refreshes" adaptation_capture.sh '{"session_id":"s1"}' \
  "recurring concern"

mem_count=$(sqlite3 "$tmp/.myfi/myfi.db" "SELECT count(*) FROM mem_entries WHERE kind='prior';")
total=$((total+1))
if [[ "$mem_count" == "1" ]]; then
  printf '  PASS  %s\n' "recurring-concern-stays-deduped-by-title"
else
  printf '  FAIL  %-45s expected 1 prior row, got %s\n' "recurring-concern-stays-deduped-by-title" "$mem_count"
  fails=$((fails+1))
fi

echo "== hooks.json wiring sanity =="
total=$((total+1))
if jq -e '.hooks.PreToolUse' "$REPO_ROOT/hooks/hooks.json" >/dev/null 2>&1 \
   && grep -q 'dispatch_guard' "$REPO_ROOT/hooks/hooks.json" \
   && grep -q 'dedup_write_guard' "$REPO_ROOT/hooks/hooks.json" \
   && grep -q 'session_venv' "$REPO_ROOT/hooks/hooks.json" \
   && grep -q 'adaptation_capture' "$REPO_ROOT/hooks/hooks.json"; then
  printf '  PASS  %s\n' "hooks-json-wires-all-four-scripts"
else
  printf '  FAIL  %s\n' "hooks-json-wires-all-four-scripts"
  fails=$((fails+1))
fi

echo "== exec bits =="
total=$((total+1))
missing=""
for f in dispatch_guard.sh dedup_write_guard.sh session_venv.sh adaptation_capture.sh _lib.sh; do
  [[ -x "$HOOKS_DIR/$f" ]] || missing="$missing $f"
done
if [[ -z "$missing" ]]; then
  printf '  PASS  %s\n' "all-hook-scripts-executable"
else
  printf '  FAIL  %-45s missing +x on:%s\n' "all-hook-scripts-executable" "$missing"
  fails=$((fails+1))
fi

echo "== $((total-fails))/$total passed =="
exit "$fails"
