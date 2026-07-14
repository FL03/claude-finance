#!/usr/bin/env bash
# myfi hook -- PreToolUse(Agent|Task) closed-flock dispatch guard
#
# Ported from shepherd's hooks/scripts/dispatch_guard.sh
# (~/src/fl03/shepherd/hooks/scripts/dispatch_guard.sh), adapted for myfi's
# flatter roster. shepherd's original guards a THREE-TIER topology
# (root → teammate-conductor "lane" → subagent "step"), because a shepherd
# sprint spans engineer/critic/conductor/coder/auditor/worker/discovery with
# Agent Teams in the mix. myfi has none of that: `@advisor` (agents/
# advisor.md) is the single dispatcher and every other flock member
# (`@quant`/`@auditor`/`@designer`/`@worker`/`@trader`) is dispatched as a
# plain Agent/Task subagent -- no teammate spawn, no team_name, no
# conductor/lane/step distinction to detect. So the shepherd original's
# checks 2/3/4/4b/4c/6 (all tier-detection, all keyed to team_name /
# teammate_mode) have no myfi analogue and are dropped rather than ported
# unused. What DOES port directly: checks 1 (missing/generic subagent_type)
# and 5 (closed-flock impersonation) -- myfi's flock is closed at six
# (advisor, quant, auditor, designer, worker, trader; skills/myfi/SKILL.md
# §The flock), no substitutes, same as shepherd's flock is closed at six.
#
# Decision table (first match wins):
#   1. subagent_type ∈ {∅, general-purpose, explore, chat} → DISPATCH-MISSING-SUBAGENT-TYPE (deny)
#   2. subagent_type ∉ the closed six                       → DISPATCH-OFF-FLOCK              (deny)
#
# Input  (stdin): PreToolUse JSON { tool_name, tool_input.subagent_type, session_id, ... }
# Output (stdout):
#   {"permissionDecision":"deny","message":"..."}   -- a forbidden dispatch (hard block)
#   exit 0 silently                                   -- a well-formed flock dispatch
#
# Doc: skills/myfi/SKILL.md §The flock.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_lib.sh"

input=$(cat)
is_myfi_project || exit 0

tool=$(json_field "$input" '.tool_name')
case "$tool" in Agent|Task) ;; *) exit 0 ;; esac

subagent_type=$(json_field "$input" '.tool_input.subagent_type')
session=$(json_field "$input" '.session_id')

st_lc=$(printf '%s' "$subagent_type" | tr '[:upper:]' '[:lower:]')
FLOCK_RE='^(advisor|quant|auditor|designer|worker|trader)$'
DOC='skills/myfi/SKILL.md §The flock'

# ---------------------------------------------------------------------------
# Check 1 -- missing / default subagent_type (DISPATCH-MISSING-SUBAGENT-TYPE)
# ---------------------------------------------------------------------------
case "$st_lc" in
  ""|general-purpose|explore|chat)
    msg="[myfi] DISPATCH-MISSING-SUBAGENT-TYPE -- refused."$'\n'
    msg+="  subagent_type: '${subagent_type:-<unset>}'"$'\n'
    msg+="Every flock dispatch MUST set subagent_type to one of the six flock roles"$'\n'
    msg+="(advisor/quant/auditor/designer/worker/trader). Omitting it, or using"$'\n'
    msg+="general-purpose/Explore/Chat, breaks the framework discipline (Hypothesis+"$'\n'
    msg+="Falsification+Confidence gating, dedup guard, REDO cap, harvest/store loop)."$'\n'
    msg+="See $DOC."
    emit_deny "$msg" "dispatch_guard" "$tool" "$session"
    ;;
esac

# ---------------------------------------------------------------------------
# Check 2 -- off-flock subagent_type (DISPATCH-OFF-FLOCK)
# myfi's flock is closed at six -- no substitutes, no ad hoc specialists.
# ---------------------------------------------------------------------------
if ! [[ "$st_lc" =~ $FLOCK_RE ]]; then
  msg="[myfi] DISPATCH-OFF-FLOCK -- refused."$'\n'
  msg+="  subagent_type: '$subagent_type' is not in the closed flock."$'\n'
  msg+="The flock is closed at six (advisor, quant, auditor, designer, worker, trader)."$'\n'
  msg+="Dispatch, modeling, compliance review, artifact finalization, routine execution,"$'\n'
  msg+="and the trade-cycle scaffold are never substitutable. See $DOC."
  emit_deny "$msg" "dispatch_guard" "$tool" "$session"
fi

pass_silent "dispatch_guard" "$tool" "$session"
