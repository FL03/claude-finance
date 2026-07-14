"""Gate-lane half of the W5-commands-analyze-plan golden-margin eval (see the unit's [EVALS] in
the plan): with MYFI_LLM_MOCK staging plausible judge scores, the deterministic harness scores the
good /myfi:analyze report golden above the new `analyze_report` rubric threshold, and the good
/myfi:plan golden above the new `plan_pipeline` rubric threshold, each with its bad golden scoring
below threshold by a clear margin.

The live lane runs the SAME goldens through a real local-Claude-Code judge:
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=analyze_report --input-file=commands/evals/analyze_good.md
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=plan_pipeline --input-file=commands/evals/plan_good.md
(and the matching *_bad.md files) — excluded from the gate lane because it spends real LLM calls.
stdlib unittest, mock seam, <2s. Mirrors services/eval/tests/test_agents_actors_margin.py.
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
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test_commands_analyze_plan", EVAL_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()


class _GoldenMarginMixin:
    """Shared mock-scoring machinery; subclasses set kind/golden filenames.

    Deliberately NOT a ``unittest.TestCase`` subclass — unittest's loader collects every
    ``TestCase`` subclass in the module, and a bare mixin instantiated on its own has no
    ``kind``/``good_name``/``bad_name`` to read. Mixing this into a concrete ``TestCase``
    subclass (below) is what makes it collectible.
    """

    MARGIN = 15
    kind: str
    good_name: str
    bad_name: str
    good_rationale: str
    bad_rationale: str

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / self.good_name).read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / self.bad_name).read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric(self.kind)
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]
        self.good_mock = json.dumps(
            {"scores": {k: self.rubric["scale"] for k in dim_keys}, "rationale": self.good_rationale}
        )
        self.bad_mock = json.dumps({"scores": {k: 1 for k in dim_keys}, "rationale": self.bad_rationale})

    def _score_with_mock(self, text: str, mock_payload: str) -> dict:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(mock_payload)
            mock_path = fh.name
        try:
            with mock.patch.dict(os.environ, {"MYFI_LLM_MOCK": mock_path}, clear=False):
                return myfi_eval.evaluate(self.kind, text)
        finally:
            os.unlink(mock_path)

    def test_goldens_and_rubric_present(self) -> None:
        self.assertTrue(self.golden_good.strip())
        self.assertTrue(self.golden_bad.strip())
        self.assertEqual(self.rubric["kind"], self.kind)

    def test_golden_margin(self) -> None:
        good = self._score_with_mock(self.golden_good, self.good_mock)
        bad = self._score_with_mock(self.golden_bad, self.bad_mock)
        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad["overall"], threshold, "bad golden must score < threshold")
        margin = good["overall"] - bad["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")


class AnalyzeReportGoldenMarginTests(_GoldenMarginMixin, unittest.TestCase):
    """/myfi:analyze's report artifact, scored against the new `analyze_report` rubric."""

    kind = "analyze_report"
    good_name = "analyze_good.md"
    bad_name = "analyze_bad.md"
    good_rationale = "complete report shape, toolkit-cited figures, concrete actionable next step"
    bad_rationale = "hedged non-answer, no traceable figures, no concrete recommendation"


class PlanPipelineGoldenMarginTests(_GoldenMarginMixin, unittest.TestCase):
    """/myfi:plan's synthesized artifact, scored against the new `plan_pipeline` rubric."""

    kind = "plan_pipeline"
    good_name = "plan_good.md"
    bad_name = "plan_bad.md"
    good_rationale = "dispatch order visible end to end, synthesized into one coherent goal-aligned plan with risks disclosed"
    bad_rationale = "auditor stage skipped entirely, raw stitched specialist quotes with no synthesis"


if __name__ == "__main__":
    unittest.main()
