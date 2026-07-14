#!/usr/bin/env bash
# W5-commands-taxes-trade structural gate — /myfi:taxes (tax-workflow pipeline) +
# /myfi:trade (authorization-gate scaffold). Wraps the unit [ACCEPTANCE]: trade.md
# halts-gate grep + no-live-order assertion, taxes.md valid frontmatter, plus the
# regression test for the trade non-goal (seed §11's "no executable surface" rule
# re-asserted at the command tier, mirroring test_agents_worker_trader.sh).
# Deterministic, python3/rg only, <1s.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
ok(){ echo "ok: $1"; }
bad(){ echo "FAIL: $1"; fail=1; }

TAXES=commands/taxes.md
TRADE=commands/trade.md

[ -f "$TAXES" ] && ok "commands/taxes.md present" || { bad "commands/taxes.md missing"; echo FAIL; exit 1; }
[ -f "$TRADE" ] && ok "commands/trade.md present" || { bad "commands/trade.md missing"; echo FAIL; exit 1; }

# Frontmatter shape: description + argument-hint + allowed-tools on both commands.
python3 - "$TAXES" "$TRADE" <<'PY'
import sys
for path in sys.argv[1:]:
    t = open(path, encoding="utf-8").read()
    assert t.startswith("---"), f"{path}: does not start with frontmatter delimiter"
    fm = t.split("---")[1]
    assert "description:" in fm, f"{path}: missing description"
    assert "argument-hint:" in fm, f"{path}: missing argument-hint"
    assert "allowed-tools:" in fm, f"{path}: missing allowed-tools"
    body = t.split("---", 2)[2]
    nonblank = [l for l in body.splitlines() if l.strip()]
    assert len(nonblank) > 15, f"{path}: body has only {len(nonblank)} non-blank lines (need >15)"
PY
[ $? -eq 0 ] && ok "both commands carry description/argument-hint/allowed-tools + non-trivial body" \
             || bad "frontmatter/body shape check failed"

# The unit's runnable [ACCEPTANCE], re-run verbatim.
rg -ni 'scaffold|no live|authorization' "$TRADE" >/dev/null 2>&1 \
  && ok "trade.md names scaffold/no-live/authorization" \
  || bad "trade.md names none of scaffold/no-live/authorization"

python3 -c "
t=open('$TRADE').read().lower()
banned=('place_order','submit_order','execute_trade','live order')
assert not any(b in t for b in banned) or 'no live' in t
assert 'authorization' in t
" && ok "trade.md clears the no-live-order acceptance predicate" \
   || bad "trade.md fails the no-live-order acceptance predicate"

test -f "$TAXES" && python3 -c "assert 'description:' in open('$TAXES').read().split('---')[1]" \
  && ok "taxes.md has a description: frontmatter key" \
  || bad "taxes.md missing description: in frontmatter"

# Regression: no banned live-exec substring anywhere in trade.md's allowed-tools:
# line, re-asserted directly via rg (independent of the python parse above) so a
# future edit that reintroduces one fails loudly.
tools_line="$(grep -i '^allowed-tools:' "$TRADE" | head -1)"
if echo "$tools_line" | rg -qi 'order|exchange|execute'; then
  bad "commands/trade.md allowed-tools: line contains a banned live-exec substring: $tools_line"
else
  ok "commands/trade.md allowed-tools: line ($tools_line) is exec-clean"
fi

# LLM law: no hosted-API reference in either command.
if rg -n 'api\.(anthropic|openai)\.com' "$TAXES" "$TRADE" >/dev/null 2>&1; then
  bad "hosted LLM API referenced in taxes.md/trade.md (LLM law violation)"
else
  ok "no hosted LLM API reference in taxes.md/trade.md"
fi

# taxes.md wires the TAXES skill + @auditor gate per [SPEC].
rg -ni 'skills/taxes|TAXES' "$TAXES" >/dev/null 2>&1 \
  && ok "taxes.md loads the TAXES skill" \
  || bad "taxes.md does not reference skills/taxes"
rg -ni '@auditor' "$TAXES" >/dev/null 2>&1 \
  && ok "taxes.md dispatches @auditor" \
  || bad "taxes.md does not dispatch @auditor"

# Sibling rubrics + goldens present and the rubrics parse as valid JSON.
for f in \
  services/eval/rubrics/trade_gate.rubric.json \
  services/eval/rubrics/taxes_workflow.rubric.json \
  commands/evals/trade_good.md commands/evals/trade_bad.md \
  commands/evals/taxes_good.md commands/evals/taxes_bad.md
do
  [ -f "$f" ] && ok "$f present" || bad "$f missing"
done

python3 -c "
import json
for k in ('trade_gate', 'taxes_workflow'):
    r = json.load(open(f'services/eval/rubrics/{k}.rubric.json', encoding='utf-8'))
    assert r['kind'] == k
" && ok "both new rubrics parse as valid JSON with matching kind" \
   || bad "a new rubric is not valid JSON or has a kind mismatch"

if [ "$fail" = 0 ]; then echo "PASS test_commands_taxes_trade"; else echo "FAIL test_commands_taxes_trade"; fi
exit $fail
