"""Gate-lane half of the W4-agents-worker-trader golden-margin eval (see the
unit's [EVALS] in the plan): with MYFI_LLM_MOCK staging plausible judge
scores, the deterministic harness scores the good `@worker` task output above
the worker_task rubric threshold and the bad one below, and separately scores
the good `@trader` scaffold report above the trader_scaffold threshold and the
bad one (a trader that attempts a live order) below it -- each pair separated
by a clear margin.

The live lane runs the SAME goldens through a real local-Claude-Code judge:
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=worker_task \\
      --input-file=agents/evals/worker_good.md
  (and worker_bad.md, trader_good.md, trader_bad.md against trader_scaffold)
-- excluded from the gate because it spends LLM calls. stdlib unittest, mock
seam, <2s. Mirrors services/eval/tests/test_skill_myfi_margin.py.
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
GOLDEN_DIR = REPO_ROOT / "agents" / "evals"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location(
        "myfi_eval_under_test_agents_worker_trader", EVAL_PY
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


class WorkerTaskGoldenMarginTests(unittest.TestCase):
    MARGIN = 15

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / "worker_good.md").read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / "worker_bad.md").read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric("worker_task")
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]
        self.good_mock = json.dumps(
            {"scores": {k: self.rubric["scale"] for k in dim_keys},
             "rationale": "bounded to the deliverable, toolkit-grounded, no scope-creep"}
        )
        self.bad_mock = json.dumps(
            {"scores": {k: 1 for k in dim_keys},
             "rationale": "scope-creeps into advisory judgment, hallucinated totals"}
        )

    def test_goldens_and_rubric_present(self) -> None:
        self.assertTrue(self.golden_good.strip())
        self.assertTrue(self.golden_bad.strip())
        self.assertEqual(self.rubric["kind"], "worker_task")

    def test_golden_margin(self) -> None:
        good = _score_with_mock("worker_task", self.golden_good, self.good_mock)
        bad = _score_with_mock("worker_task", self.golden_bad, self.bad_mock)
        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad["overall"], threshold, "bad golden must score < threshold")
        margin = good["overall"] - bad["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")


class TraderScaffoldGoldenMarginTests(unittest.TestCase):
    MARGIN = 15

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / "trader_good.md").read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / "trader_bad.md").read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric("trader_scaffold")
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]
        self.good_mock = json.dumps(
            {"scores": {k: self.rubric["scale"] for k in dim_keys},
             "rationale": "halts at the authorization gate, no live-exec attempted, cycle documented"}
        )
        self.bad_mock = json.dumps(
            {"scores": {k: 1 for k in dim_keys},
             "rationale": "narrates a filled live order, no gate discipline"}
        )

    def test_goldens_and_rubric_present(self) -> None:
        self.assertTrue(self.golden_good.strip())
        self.assertTrue(self.golden_bad.strip())
        self.assertEqual(self.rubric["kind"], "trader_scaffold")

    def test_golden_margin(self) -> None:
        good = _score_with_mock("trader_scaffold", self.golden_good, self.good_mock)
        bad = _score_with_mock("trader_scaffold", self.golden_bad, self.bad_mock)
        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad["overall"], threshold, "bad golden must score < threshold")
        margin = good["overall"] - bad["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")


if __name__ == "__main__":
    unittest.main()
