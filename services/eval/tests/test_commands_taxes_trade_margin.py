"""Gate-lane half of the W5-commands-taxes-trade golden-margin eval (see the
unit's [EVALS] in the plan): with MYFI_LLM_MOCK staging plausible judge
scores, the deterministic harness scores the good `/myfi:taxes` pipeline
output above the taxes_workflow rubric threshold and the bad one (a
single-step, ungrounded, gate-skipping answer) below it, and separately
scores the good `/myfi:trade` halt report above the trade_gate rubric
threshold and the bad one (a report that narrates a filled live order) below
it — each pair separated by a clear margin.

The live lane runs the SAME goldens through a real local-Claude-Code judge:
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=taxes_workflow \\
      --input-file=commands/evals/taxes_good.md
  (and taxes_bad.md, trade_good.md, trade_bad.md against trade_gate)
— excluded from the gate because it spends LLM calls. stdlib unittest, mock
seam, <2s. Mirrors services/eval/tests/test_agents_worker_trader_margin.py.
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

EVAL_DIR = Path(__file__).resolve().parent.parent
EVAL_PY = EVAL_DIR / "eval.py"
REPO_ROOT = EVAL_DIR.parent.parent
GOLDEN_DIR = REPO_ROOT / "commands" / "evals"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location(
        "myfi_eval_under_test_commands_taxes_trade", EVAL_PY
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()


def _score_with_mock(kind: str, text: str, mock_payload: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        fh.write(mock_payload)
        mock_path = fh.name
    try:
        with mock.patch.dict(os.environ, {"MYFI_LLM_MOCK": mock_path}, clear=False):
            return myfi_eval.evaluate(kind, text)
    finally:
        os.unlink(mock_path)


class TaxesWorkflowGoldenMarginTests(unittest.TestCase):
    MARGIN = 15

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / "taxes_good.md").read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / "taxes_bad.md").read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric("taxes_workflow")
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]
        self.good_mock = json.dumps(
            {"scores": {k: self.rubric["scale"] for k in dim_keys},
             "rationale": "full pipeline walked, forms cited, gate visibly cleared"}
        )
        self.bad_mock = json.dumps(
            {"scores": {k: 1 for k in dim_keys},
             "rationale": "single vague step, no forms, no trace of a compliance pass"}
        )

    def test_goldens_and_rubric_present(self) -> None:
        self.assertTrue(self.golden_good.strip())
        self.assertTrue(self.golden_bad.strip())
        self.assertEqual(self.rubric["kind"], "taxes_workflow")

    def test_golden_margin(self) -> None:
        good = _score_with_mock("taxes_workflow", self.golden_good, self.good_mock)
        bad = _score_with_mock("taxes_workflow", self.golden_bad, self.bad_mock)
        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad["overall"], threshold, "bad golden must score < threshold")
        margin = good["overall"] - bad["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")


class TradeGateGoldenMarginTests(unittest.TestCase):
    MARGIN = 15

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / "trade_good.md").read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / "trade_bad.md").read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric("trade_gate")
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]
        self.good_mock = json.dumps(
            {"scores": {k: self.rubric["scale"] for k in dim_keys},
             "rationale": "halts at the authorization gate, no live-exec attempted, gate explained"}
        )
        self.bad_mock = json.dumps(
            {"scores": {k: 1 for k in dim_keys},
             "rationale": "narrates a filled live order, no gate discipline, treats the gate as a rubber stamp"}
        )

    def test_goldens_and_rubric_present(self) -> None:
        self.assertTrue(self.golden_good.strip())
        self.assertTrue(self.golden_bad.strip())
        self.assertEqual(self.rubric["kind"], "trade_gate")

    def test_golden_margin(self) -> None:
        good = _score_with_mock("trade_gate", self.golden_good, self.good_mock)
        bad = _score_with_mock("trade_gate", self.golden_bad, self.bad_mock)
        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad["overall"], threshold, "bad golden must score < threshold")
        margin = good["overall"] - bad["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")


if __name__ == "__main__":
    unittest.main()
