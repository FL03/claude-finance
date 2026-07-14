#!/usr/bin/env bash
# W1-relocate structural gate — root-level component layout + .mcp.json + no src/.
# Deterministic, jq/git only, <1s. This IS the unit's acceptance predicate.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

[ -d agents ]            && ok "agents/ exists"                  || bad "agents/ missing"
[ -f agents/advisor.md ] && ok "agents/advisor.md relocated"    || bad "agents/advisor.md missing"
[ -d skills/myfi ]      && ok "skills/myfi/ exists"             || bad "skills/myfi/ missing"
[ -d commands ]         && ok "commands/ exists"                || bad "commands/ missing"
[ -d bin ]              && ok "bin/ exists"                     || bad "bin/ missing"
[ ! -d src ]            && ok "src/ removed"                    || bad "src/ still present"
[ ! -d src/skills/plan ] && ok "src/skills/plan removed"        || bad "src/skills/plan still present"
jq empty .mcp.json 2>/dev/null && ok ".mcp.json valid json"     || bad ".mcp.json invalid json"

# ${CLAUDE_PLUGIN_ROOT} must stay a literal token — single-quote the expected value.
cmd="$(jq -r '.mcpServers["myfi-toolkit"].command' .mcp.json 2>/dev/null)"
[ "$cmd" = '${CLAUDE_PLUGIN_ROOT}/bin/myfi-mcp' ] \
  && ok ".mcp.json registers myfi-toolkit -> bin/myfi-mcp" \
  || bad ".mcp.json myfi-toolkit command wrong: '$cmd'"

[ -f .claude/myfi.toml ] && ok ".claude/myfi.toml present"      || bad ".claude/myfi.toml missing"

n="$(git ls-files src/ | wc -l | tr -d ' ')"
[ "$n" = 0 ] && ok "no tracked files under src/"                || bad "$n tracked file(s) still under src/"

# plugin.json must not carry any src/-prefixed component path (root dirs auto-discover).
grep -q '"src/' .claude-plugin/plugin.json 2>/dev/null \
  && bad "plugin.json carries a src/-prefixed path" \
  || ok "plugin.json has no src/-prefixed component path"

if [ "$fail" = 0 ]; then echo "PASS test_layout"; else echo "FAIL test_layout"; fi
exit $fail
