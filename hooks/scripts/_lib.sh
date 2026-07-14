#!/usr/bin/env bash
# myfi hooks -- shared library
#
# Sourced by every hook script under hooks/scripts/. Adapted from shepherd's
# hooks/scripts/_lib.sh (~/src/fl03/shepherd/hooks/scripts/_lib.sh), trimmed to
# what myfi's flatter single-tier flock actually needs: myfi has no
# teammate/conductor/lane tiering and no per-role dispatch-tag file, so the
# shepherd original's current_role/current_sprint/in_subworktree machinery is
# dropped rather than ported unused.
#
# Exports:
#
#   is_myfi_project                  -- 0 if .claude/myfi.toml exists (this plugin's project marker)
#   myfi_repo_root                   -- echoes the git toplevel, else pwd
#   myfi_db_path [root]              -- echoes "<root>/.myfi/myfi.db" (mirrors
#                                       myfi_toolkit.myctx.db.resolve_db_path's per-project default)
#   cfg_get "<key>"                  -- echoes a top-level `key = value` from .claude/myfi.toml
#   json_field input '.path'         -- extract scalar from JSON stdin; jq-then-python3 fallback
#   json_response input              -- extract tool_response text (string/dict/list-of-blocks)
#   emit_json_obj key1 val1 ...      -- echo a single-line JSON object (jq-then-python3 fallback)
#   emit_deny "<msg>" [hook] [tool] [session]     -- {"permissionDecision":"deny","message":...}; exit 0
#   emit_context "<msg>" [hook] [tool] [session]  -- {"additionalContext":...}; exit 0
#   emit_message "<msg>" [hook] [tool] [session]  -- {"systemMessage":...}; exit 0 (Stop/SessionStart-safe)
#   pass_silent [hook] [tool] [session] [fields]  -- exit 0, optional log only
#   log_event hook decision tool session fields_json
#                                     -- append one JSONL entry to .myfi/logs/hooks/YYYY-MM-DD.jsonl
#
# All emit_* functions log_event before emitting JSON. Log failures are silent.
#
# This library does NOT set `set -euo pipefail` -- sourcing scripts decide.

# ---------------------------------------------------------------------------
# Predicates + paths
# ---------------------------------------------------------------------------

is_myfi_project() {
  [[ -f ".claude/myfi.toml" ]]
}

# The repo root (git toplevel), falling back to pwd for a non-git sandbox
# (hooks/tests/run.sh runs its own scratch dirs, some of which are plain
# tmpdirs with no .git -- see hooks/tests/run.sh).
myfi_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || pwd
}

# Per-project db path -- MUST mirror myfi_toolkit.myctx.db.resolve_db_path's
# default (PROJECT_DB_RELATIVE = ".myfi/myfi.db") or hooks and the toolkit
# read/write two different files (split-brain).
myfi_db_path() {
  local root="${1:-$(myfi_repo_root)}"
  printf '%s' "$root/.myfi/myfi.db"
}

# Echo the value of a top-level `key = value` from .claude/myfi.toml. Section-
# agnostic, last-match-wins; strips surrounding double-quotes and trailing
# " # inline comments". Echoes "" if unset; never returns non-zero (safe under
# `set -e`/pipefail). No TOML parser -- this project's config is small and flat.
cfg_get() {
  local key="$1" repo f v
  repo="$(myfi_repo_root)"
  f="$repo/.claude/myfi.toml"
  [[ -f "$f" ]] || { printf '%s' ""; return 0; }
  v="$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$f" 2>/dev/null | tail -1 \
        | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]+#.*$//; s/^"//; s/"$//' 2>/dev/null || true)"
  printf '%s' "$v"
  return 0
}

# ---------------------------------------------------------------------------
# JSON extraction (jq preferred, python3 fallback)
# ---------------------------------------------------------------------------

# Usage: json_field "$input_json" '.tool_input.command'
json_field() {
  local input="$1" path="$2"
  if command -v jq &>/dev/null; then
    printf '%s' "$input" | jq -r "$path // empty" 2>/dev/null || true
  else
    python3 -c '
import json, sys
data = json.load(sys.stdin)
path = sys.argv[1].lstrip(".").split(".")
for p in path:
    if isinstance(data, dict):
        data = data.get(p, "")
    else:
        data = ""
        break
print(data if isinstance(data, str) else (json.dumps(data) if data else ""))
' "$path" <<<"$input" 2>/dev/null || true
  fi
}

# Extract the tool_response text (string, dict.content/.text, or list-of-blocks).
# Usage: json_response "$input_json"
json_response() {
  local input="$1"
  if command -v jq &>/dev/null; then
    printf '%s' "$input" | jq -r '
      (.tool_response.content? // .tool_response.text? // .tool_response // empty)
      | if type == "array" then map(.text? // .) | join("\n") else . end' 2>/dev/null || true
  else
    python3 -c '
import json, sys
d = json.load(sys.stdin)
r = d.get("tool_response", "")
if isinstance(r, dict):
    r = r.get("content") or r.get("text") or ""
if isinstance(r, list):
    r = "\n".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in r)
print(r)
' 2>/dev/null <<<"$input" || true
  fi
}

# ---------------------------------------------------------------------------
# JSON emission
# ---------------------------------------------------------------------------

# Usage: emit_json_obj key1 val1 key2 val2 ...
emit_json_obj() {
  if command -v jq &>/dev/null; then
    local args=() i=0
    while [[ $# -gt 0 ]]; do
      args+=(--arg "k$i" "$1")
      args+=(--arg "v$i" "$2")
      i=$((i+1))
      shift 2
    done
    local jq_filter=""
    for ((j=0; j<i; j++)); do
      [[ -n "$jq_filter" ]] && jq_filter+=" + "
      jq_filter+="{ (\$k$j): \$v$j }"
    done
    jq -nc "${args[@]}" "$jq_filter"
  else
    python3 -c '
import json, sys
args = sys.argv[1:]
obj = {args[i]: args[i+1] for i in range(0, len(args), 2)}
print(json.dumps(obj))
' "$@"
  fi
}

# Emit a permissionDecision:deny and exit 0. Usage: emit_deny "<msg>" [hook] [tool] [session]
emit_deny() {
  local msg="$1" hook="${2:-}" tool="${3:-}" session="${4:-}"
  [[ -n "$hook" ]] && log_event "$hook" "deny" "$tool" "$session" "$(emit_json_obj reason "$msg")"
  emit_json_obj permissionDecision "deny" message "$msg"
  exit 0
}

# Emit an additionalContext note and exit 0 (PreToolUse/SessionStart-shaped).
# Usage: emit_context "<msg>" [hook] [tool] [session]
emit_context() {
  local msg="$1" hook="${2:-}" tool="${3:-}" session="${4:-}"
  [[ -n "$hook" ]] && log_event "$hook" "warn" "$tool" "$session" "$(emit_json_obj reason "$msg")"
  emit_json_obj additionalContext "$msg"
  exit 0
}

# Emit a systemMessage and exit 0 -- the one output field documented as safe
# across every hook type (Stop included), so the harvest sweep in
# adaptation_capture.sh uses this rather than additionalContext (PreToolUse/
# SessionStart-specific). Usage: emit_message "<msg>" [hook] [tool] [session]
emit_message() {
  local msg="$1" hook="${2:-}" tool="${3:-}" session="${4:-}"
  [[ -n "$hook" ]] && log_event "$hook" "info" "$tool" "$session" "$(emit_json_obj reason "$msg")"
  emit_json_obj systemMessage "$msg"
  exit 0
}

# Emit nothing, just exit 0 with optional log. Usage: pass_silent [hook] [tool] [session] [fields_json]
pass_silent() {
  local hook="${1:-}" tool="${2:-}" session="${3:-}" fields="${4:-}"
  [[ -z "$fields" ]] && fields='{}'
  [[ -n "$hook" ]] && log_event "$hook" "pass" "$tool" "$session" "$fields"
  exit 0
}

# ---------------------------------------------------------------------------
# Event log
# ---------------------------------------------------------------------------

# Append one JSONL entry to <repo_root>/.myfi/logs/hooks/YYYY-MM-DD.jsonl.
# Errors are silent; log failures must not break hooks.
log_event() {
  local hook="$1" decision="$2" tool="$3" session="$4" fields_json="$5"
  local root log_dir log_file ts
  # bash's `${var:-{}}` default-value syntax mis-parses a literal `{}`
  # default (the FIRST unescaped `}` closes the expansion early, leaking a
  # stray `}` onto the command line) -- confirmed empirically, not a shepherd
  # carry-over bug. Default explicitly instead of via `:-`.
  [[ -z "$fields_json" ]] && fields_json='{}'
  root=$(myfi_repo_root) || return 0
  log_dir="$root/.myfi/logs/hooks"
  mkdir -p "$log_dir" 2>/dev/null || return 0
  log_file="$log_dir/$(date -u +%Y-%m-%d).jsonl"
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ 2>/dev/null) || ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  if command -v jq &>/dev/null; then
    jq -cn \
      --arg ts "$ts" --arg hook "$hook" --arg decision "$decision" \
      --arg tool "$tool" --arg session "$session" \
      --argjson fields "$fields_json" \
      '{ts:$ts, hook:$hook, decision:$decision, tool:$tool, session_id:$session, fields:$fields}' \
      >> "$log_file" 2>/dev/null || true
  else
    python3 -c '
import json, sys
print(json.dumps({
    "ts":         sys.argv[1],
    "hook":       sys.argv[2],
    "decision":   sys.argv[3],
    "tool":       sys.argv[4],
    "session_id": sys.argv[5],
    "fields":     json.loads(sys.argv[6] or "{}"),
}))
' "$ts" "$hook" "$decision" "$tool" "$session" "$fields_json" \
      >> "$log_file" 2>/dev/null || true
  fi
  return 0
}
