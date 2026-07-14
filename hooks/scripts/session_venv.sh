#!/usr/bin/env bash
# myfi hook -- SessionStart: persist the myfi_toolkit venv under ${CLAUDE_PLUGIN_DATA}
#
# Completes the seed §5 "${CLAUDE_PLUGIN_DATA} venv via SessionStart" decision:
# bin/myfi-venv-ensure (Wave 2) carries the actual idempotent poetry-install
# logic (diffs services/toolkit/pyproject.toml against a stamp file, no-ops
# when unchanged); this hook is just the SessionStart wire that calls it every
# session so the venv survives a plugin update (CLAUDE_PLUGIN_ROOT gets purged
# ~7 days after an update; CLAUDE_PLUGIN_DATA does not).
#
# bin/myfi-venv-ensure already prints its own "up to date" / "installing..."
# / "done" lines to stdout -- this hook relays that as a systemMessage (visible
# in the transcript per hook-development §Standard Output) rather than
# duplicating the logic here. Never blocks the session: myfi-venv-ensure exits
# 0 even when poetry is absent (bin/myfi-toolkit's PYTHONPATH fallback covers
# that case), so this hook only fails loudly on a genuinely broken plugin
# layout (missing bin/myfi-venv-ensure entirely).
#
# Input  (stdin): SessionStart JSON -- consumed, not otherwise used.
# Output (stdout): {"systemMessage":"..."} relaying myfi-venv-ensure's own
#   output, or exit 0 silently if it produced nothing worth surfacing.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_lib.sh"

cat >/dev/null  # consume the SessionStart payload; not otherwise needed

is_myfi_project || exit 0

# Resolve the plugin root the same way bin/myfi-toolkit does: prefer
# ${CLAUDE_PLUGIN_ROOT} (set when the plugin is installed), else derive it
# from this script's own location (hooks/scripts → repo root) so the hook
# also runs correctly from a bare repo clone / test sandbox.
if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
  root="$CLAUDE_PLUGIN_ROOT"
else
  root="$(cd "$HERE/../.." && pwd)"
fi

ensure_bin="$root/bin/myfi-venv-ensure"
if [[ ! -x "$ensure_bin" ]]; then
  # Not fatal -- a malformed layout shouldn't block session start, but it is
  # worth surfacing since the venv will silently stay stale otherwise.
  emit_message "[myfi] session_venv: $ensure_bin not found or not executable -- venv NOT ensured." "session_venv" "" ""
fi

output=""
if ! output="$("$ensure_bin" 2>&1)"; then
  emit_message "[myfi] session_venv: myfi-venv-ensure exited non-zero:"$'\n'"$output" "session_venv" "" ""
fi

[[ -z "$output" ]] && pass_silent "session_venv" "" ""

emit_message "[myfi] $output" "session_venv" "" ""
