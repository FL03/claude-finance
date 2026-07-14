#!/usr/bin/env bash
# myfi hook -- PreToolUse(Write|Edit) dedup gate
#
# Ported from shepherd's hooks/scripts/dedup_write_guard.sh
# (~/src/fl03/shepherd/hooks/scripts/dedup_write_guard.sh). Final-line defense
# against duplicate symbol creation: inspects pending Write/Edit content for
# new public-symbol declarations, and if the same identifier already exists
# elsewhere in the workspace, BLOCKS the write with a DEDUP-HIT message citing
# the existing location.
#
# Adaptation notes (myfi has no shepherd-style @coder-only role gate): the
# shepherd original polices only the `coder` role, resolved via a dispatch-tag
# file written by agent_invocation_tagger.sh. myfi's flock has no such
# per-role dispatch-tag mechanism in this unit's scope (W6-harness-hooks ships
# only dispatch_guard/dedup_write_guard/session_venv/adaptation_capture -- no
# tagger), and no shepherd-style "one role writes code, the rest review"
# split: `@worker`/`@designer` both hold Write+Edit, `@auditor`/`@trader` hold
# Write only, alongside the toolkit's own Python surface. So this port polices
# EVERY Write/Edit unconditionally rather than gating on an unavailable role
# signal -- the dedup contract (no duplicate public symbols) is a property of
# the codebase, not of who is editing it.
#
# Input  (stdin): PreToolUse JSON { tool_name, tool_input.{file_path, content|new_string}, session_id, ... }
# Output (stdout):
#   {"permissionDecision":"deny","message":"DEDUP-HIT: ..."}    -- when a hit
#   exit 0 silently otherwise.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_lib.sh"

input=$(cat)
is_myfi_project || exit 0

tool=$(json_field "$input" '.tool_name')
case "$tool" in Write|Edit) ;; *) exit 0 ;; esac

session=$(json_field "$input" '.session_id')

file_path=$(json_field "$input" '.tool_input.file_path')
[[ -z "$file_path" ]] && file_path=$(json_field "$input" '.tool_input.path')
[[ -z "$file_path" ]] && pass_silent "dedup_write_guard" "$tool" "$session"

# Extract pending content
if [[ "$tool" == "Write" ]]; then
  content=$(json_field "$input" '.tool_input.content')
else
  # Edit -- check the new_string for new symbol introductions
  content=$(json_field "$input" '.tool_input.new_string')
fi
[[ -z "$content" ]] && pass_silent "dedup_write_guard" "$tool" "$session"

# Determine language by extension
case "$file_path" in
  *.rs)              lang="rust"     ;;
  *.py)              lang="python"   ;;
  *.ts|*.tsx)        lang="typescript" ;;
  *.js|*.jsx|*.mjs)  lang="javascript" ;;
  *.go)              lang="go"       ;;
  *)                 pass_silent "dedup_write_guard" "$tool" "$session" ;;
esac

# Per-language regex for new PUBLIC symbol introductions
case "$lang" in
  rust)
    patterns='^[[:space:]]*pub(\([a-z_]+\))?[[:space:]]+(fn|struct|trait|enum|const|static|type|union)[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)'
    ;;
  python)
    # def / class / module-level uppercased name -- myfi_toolkit's own shape (stdlib-only CLI/myctx modules)
    patterns='^(def|class)[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)'
    ;;
  typescript|javascript)
    patterns='^export[[:space:]]+(async[[:space:]]+)?(function|class|interface|type|const|enum)[[:space:]]+([a-zA-Z_][a-zA-Z0-9_]*)'
    ;;
  go)
    patterns='^(func|type|var|const)[[:space:]]+([A-Z][a-zA-Z0-9_]*)'
    ;;
esac

# Extract candidate new symbols from content
new_symbols=$(printf '%s' "$content" | grep -oE "$patterns" 2>/dev/null | awk '{print $NF}' | sort -u || true)
[[ -z "$new_symbols" ]] && pass_silent "dedup_write_guard" "$tool" "$session"

# Resolve abs path so we can exclude the target file from the hit check
repo_root=$(myfi_repo_root)
abs_target=$(cd "$(dirname "$file_path")" 2>/dev/null && pwd)/$(basename "$file_path") || abs_target="$file_path"

# Directories excluded from the search -- myfi's own build/cache surface
# (poetry venv, per-project db namespace, python/ruff caches), not shepherd's
# rust `target`/`node_modules`/`.shepherd`/`.artifacts` set.
EXCLUDE_GLOBS=(--glob '!.venv' --glob '!.myfi' --glob '!.pytest_cache' --glob '!.ruff_cache' --glob '!node_modules' --glob '!__pycache__')
EXCLUDE_DIRS=(--exclude-dir='.venv' --exclude-dir='.myfi' --exclude-dir='.pytest_cache' --exclude-dir='.ruff_cache' --exclude-dir='node_modules' --exclude-dir='__pycache__')

hit_lines=""
hit_count=0
while IFS= read -r sym; do
  [[ -z "$sym" ]] && continue
  case "$lang" in
    rust)        search_pat="^[[:space:]]*pub(\([a-z_]+\))?[[:space:]]+(fn|struct|trait|enum|const|static|type|union)[[:space:]]+${sym}\b" ;;
    python)      search_pat="^(def|class)[[:space:]]+${sym}\b" ;;
    typescript|javascript) search_pat="^export[[:space:]]+(async[[:space:]]+)?(function|class|interface|type|const|enum)[[:space:]]+${sym}\b" ;;
    go)          search_pat="^(func|type|var|const)[[:space:]]+${sym}\b" ;;
  esac

  if command -v rg &>/dev/null; then
    hits=$(rg -n --no-heading -g "*.${file_path##*.}" "${EXCLUDE_GLOBS[@]}" "$search_pat" "$repo_root" 2>/dev/null | grep -v "^${abs_target}:" | head -3 || true)
  else
    hits=$(grep -rn -E "$search_pat" --include="*.${file_path##*.}" "${EXCLUDE_DIRS[@]}" "$repo_root" 2>/dev/null | grep -v "^${abs_target}:" | head -3 || true)
  fi

  if [[ -n "$hits" ]]; then
    hit_count=$((hit_count + 1))
    hit_lines+="  '$sym' already exists:"$'\n'
    while IFS= read -r line; do
      hit_lines+="    ${line}"$'\n'
    done <<<"$hits"
  fi
done <<<"$new_symbols"

# No hits -- pass
if [[ $hit_count -eq 0 ]]; then
  pass_silent "dedup_write_guard" "$tool" "$session"
fi

# At least one hit -- BLOCK
msg="[myfi] DEDUP-HIT BLOCKED -- Write/Edit would create duplicate(s) of existing symbol(s)."$'\n'
msg+="  Target file:  $file_path"$'\n'
msg+="  Language:     $lang"$'\n'
msg+=""$'\n'
msg+="$hit_lines"
msg+=""$'\n'
msg+="Per skills/improve/SKILL.md's bounded loop and CLAUDE.md's search-before-building rule:"$'\n'
msg+="  - REUSE the existing symbol (import + delegate)"$'\n'
msg+="  - EXTEND it (add method/variant; preserve callers)"$'\n'
msg+="  - or state explicitly why a new symbol is required"$'\n'
msg+=""$'\n'
msg+="Lazy duplication is more work, not less -- refuse it."

log_event "dedup_write_guard" "deny" "$tool" "$session" \
  "$(emit_json_obj symbols "$new_symbols" hit_count "$hit_count" file_path "$file_path")"
emit_json_obj permissionDecision "deny" message "$msg"
exit 0
