#!/usr/bin/env bash
# Plugin-packaging structural gate: proves claude-finance is a `myfi` plugin whose OWN embedded
# catalog can never collide with the dedicated `fl03` catalog hosted at FL03/claude.
#
# The bug this locks out: `.claude-plugin/marketplace.json` shipped its catalog under the name
# `fl03` -- the SAME name as the dedicated FL03/claude catalog that lists every fl03 plugin. Claude
# Code registers only one marketplace per name, so `/plugin marketplace add FL03/claude-finance`
# (the old README instruction) silently REPLACED the real catalog, dropping its other plugins
# (shepherd) and leaving `myfi@fl03` resolving from the wrong place -- "unable to access the
# plugin." This gate fails if the embedded catalog ever reclaims the `fl03` name, or if any doc
# reships the collision-era pairing (`add FL03/claude-finance` next to `install myfi@fl03`).
#
# Deterministic, jq/rg/python3 only, no network, no LLM call, <1s. bash-3.2-safe.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

PJ=".claude-plugin/plugin.json"
MP=".claude-plugin/marketplace.json"
DEDICATED_NAME="fl03"   # the dedicated FL03/claude catalog's name; this repo's catalog must differ

# 1. plugin.json is present, valid, and identifies the plugin as `myfi`.
jq empty "$PJ" 2>/dev/null && ok "$PJ is valid json" || bad "$PJ missing or invalid json"
pn="$(jq -r '.name // empty' "$PJ" 2>/dev/null)"
[ "$pn" = "myfi" ] && ok "plugin.json name == myfi" || bad "plugin.json name is '$pn', expected myfi"

# 2. If this repo ships its own catalog, its name MUST differ from the dedicated fl03 catalog.
if [ -f "$MP" ]; then
  jq empty "$MP" 2>/dev/null && ok "$MP is valid json" || bad "$MP invalid json"
  mn="$(jq -r '.name // empty' "$MP" 2>/dev/null)"
  if [ "$mn" = "$DEDICATED_NAME" ]; then
    bad "embedded catalog name '$mn' collides with the dedicated FL03/claude catalog (same name replaces it)"
  else
    ok "embedded catalog name '$mn' does not collide with the dedicated '$DEDICATED_NAME' catalog"
  fi
  jq -e '.plugins[]? | select(.name == "myfi")' "$MP" >/dev/null 2>&1 \
    && ok "embedded catalog lists the myfi plugin" \
    || bad "embedded catalog does not list a plugin named myfi"
else
  ok "no embedded marketplace.json (pure plugin) -- no collision possible"
fi

# 3. No doc ships the collision-era instruction: `add FL03/claude-finance` next to `myfi@fl03`.
pair_out="$(python3 - <<'PY'
import glob, re
add_re = re.compile(r'marketplace add FL03/claude-finance\b')
inst_re = re.compile(r'install myfi@fl03\b')
count = 0
for f in ["README.md"] + glob.glob("docs/**/*.md", recursive=True):
    try:
        lines = open(f, encoding="utf-8").read().splitlines()
    except OSError:
        continue
    for i, ln in enumerate(lines):
        if add_re.search(ln) and inst_re.search("\n".join(lines[i:i + 4])):
            print(f"{f}:{i + 1}: collision-era pairing (add FL03/claude-finance + install myfi@fl03)")
            count += 1
print(f"COUNT={count}")
PY
)"
if echo "$pair_out" | grep -q '^COUNT=0$'; then
  ok "no doc pairs 'add FL03/claude-finance' with 'install myfi@fl03'"
else
  echo "$pair_out" | grep -v '^COUNT='
  bad "a doc still ships the collision-era install pairing"
fi

# 4. README documents the recommended dedicated-catalog path.
rg -qF '/plugin marketplace add FL03/claude' README.md \
  && rg -qF '/plugin install myfi@fl03' README.md \
  && ok "README documents the dedicated-catalog install (add FL03/claude + install myfi@fl03)" \
  || bad "README missing the dedicated-catalog install commands"

# 5. Any standalone-path doc pairs `add FL03/claude-finance` with the matching `myfi@claude-finance`.
if rg -qF '/plugin marketplace add FL03/claude-finance' docs/install.md 2>/dev/null; then
  rg -qF '/plugin install myfi@claude-finance' docs/install.md \
    && ok "standalone path pairs add FL03/claude-finance with install myfi@claude-finance" \
    || bad "standalone add FL03/claude-finance present but matching install myfi@claude-finance missing"
else
  ok "no standalone add-this-repo instruction to reconcile"
fi

if [ "$fail" = 0 ]; then echo "PASS test_plugin_packaging"; else echo "FAIL test_plugin_packaging"; fi
exit $fail
