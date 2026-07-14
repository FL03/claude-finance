"""Gate-lane half of the W6-harness-loops golden-margin eval (see the unit's [EVALS] in the
plan): with MYFI_LLM_MOCK staging plausible judge scores, the deterministic harness scores the
good loop-discipline golden above the loop_discipline rubric threshold and the bad one below,
separated by a clear margin.

The live lane runs the SAME goldens through a real local-Claude-Code judge:
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=loop_discipline \\
      --input-file=skills/myfi/references/evals/good.md
(and bad.md) -- excluded from the gate because it spends LLM calls. stdlib unittest, mock seam,
<2s. Mirrors services/eval/tests/test_skill_myfi_margin.py and
services/eval/tests/test_eval_rubrics.py::GoldenMarginTests.
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
GOLDEN_DIR = REPO_ROOT / "skills" / "myfi" / "references" / "evals"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test_harness_loops", EVAL_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()


class HarnessLoopsGoldenMarginTests(unittest.TestCase):
    MARGIN = 15

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / "good.md").read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / "bad.md").read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric("loop_discipline")
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]
        self.good_mock = json.dumps(
            {
                "scores": {k: self.rubric["scale"] for k in dim_keys},
                "rationale": "names REDO cap 3, a structured new_findings/PASS-REDO predicate, and the owning role",
            }
        )
        self.bad_mock = json.dumps(
            {
                "scores": {k: 1 for k in dim_keys},
                "rationale": "no numeric cap, no structured predicate, role-agnostic",
            }
        )

    def _score_with_mock(self, text: str, mock_payload: str) -> dict:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(mock_payload)
            mock_path = fh.name
        try:
            with mock.patch.dict(os.environ, {"MYFI_LLM_MOCK": mock_path}, clear=False):
                return myfi_eval.evaluate("loop_discipline", text)
        finally:
            os.unlink(mock_path)

    def test_goldens_and_rubric_present(self) -> None:
        self.assertTrue(self.golden_good.strip())
        self.assertTrue(self.golden_bad.strip())
        self.assertEqual(self.rubric["kind"], "loop_discipline")

    def test_golden_margin(self) -> None:
        good = self._score_with_mock(self.golden_good, self.good_mock)
        bad = self._score_with_mock(self.golden_bad, self.bad_mock)
        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad["overall"], threshold, "bad golden must score < threshold")
        margin = good["overall"] - bad["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")


if __name__ == "__main__":
    unittest.main()
