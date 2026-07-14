# Loop discipline: good

Excerpt from an `@advisor` dispatch log after a client engagement:

"`@quant`'s pricing model came back with an unsourced volatility input, so `@auditor` returned
`REDO` on the Hypothesis+Falsification+Confidence pass (finding: HIGH, the 22% implied vol figure
traced to no toolkit call). That is REDO attempt 1 of the flock's REDO cap 3 (AUDITOR-GATE-REDO,
`skills/myfi/references/loop-templates.md`). I re-dispatched `@quant` with the finding attached
rather than patching the number myself. `@quant` re-pulled the option chain via
`mcp__plugin_myfi_myfi-toolkit__quote`, cited the real implied vol, and `@auditor` re-ran the same
triple against the revised draft. Verdict: PASS, `new_findings: false`, zero CRITICAL/HIGH findings
outstanding. Had this gone to a third REDO with the finding still open, I would have escalated to
myself rather than dispatching `@quant` a fourth time; that ceiling is hard, not a suggestion. The
draft now moves to `@designer` for the final-edit checklist (DESIGNER-CHECKLIST-CONVERGE, default
`--max` 3), which halts `DESIGNER-PRE-GATE` on anything without a recorded PASS."

This is the shape every loop in `skills/myfi/references/loop-templates.md` takes: a numeric cap
declared before the loop starts (REDO cap 3, or a template's own default `--max`), a structured
`new_findings: true|false` or `PASS|REDO` signal on every tick, and an explicit role binding
(here, `@quant` as the iterator and `@auditor`'s verdict as the gate) rather than a generic "keep
trying until it's good" description that could apply to any agent in the flock.
