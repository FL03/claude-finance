# v0.0.0 close report (golden: good)

## Sprint verdict

DONE_WITH_CONCERNS. 15/16 units shipped and pass their own [ACCEPTANCE] predicate on re-run;
one unit (W7-integration-close) required a redo, documented below with the fix applied and
re-verified.

## Per-unit verdicts

| Unit | Verdict | Evidence |
| :--- | :--- | :--- |
| W1-relocate | DONE | commit `dd4409a`; `tests/integration/test_plugin_load.py::RelocationInvariantTests` passes (`src/` absent). |
| W2-toolkit-scaffold | DONE | commit `8a46385`; `poetry -C services/toolkit run pytest -q` reports 30 passed. |
| W3-toolkit-db | DONE | commit `5e99ef9`; `services/toolkit/tests/test_myctx.py` green, baseline checksum regression test added. |

## Follow-ups

- `.claude/shepherd.toml [gates].check` still wires only the toolkit pytest lane; `bin/myfi-test`
  aggregates four lanes. Filed as GH issue #<n> so the between-wave gate covers all four lanes,
  owner: root-shepherd, next action: extend `[gates].check` to call `bin/myfi-test`.
- The close_report rubric had zero test wiring before this redo; fixed by
  `tests/integration/test_close_report_eval.py`, re-run confirmed green.

No claim above is unbacked: every "passes" cites a command, a file, or a commit SHA a reader can
re-run.
