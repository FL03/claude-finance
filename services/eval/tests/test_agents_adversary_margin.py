"""Gate-lane half of the W4-agents-adversary-editor golden-margin evals (see
the unit's [EVALS] in the plan): with MYFI_LLM_MOCK staging plausible judge
scores, the deterministic harness scores the good @auditor finding / good
@designer artifact goldens above their rubric thresholds and the bad ones
below, separated by a clear margin.

The live lane runs the SAME goldens through a real local-Claude-Code judge:
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=audit_finding \\
      --input-file=agents/evals/auditor_good.md
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=designer_artifact \\
      --input-file=agents/evals/designer_good.md
(and the corresponding *_bad.md goldens) -- excluded from the gate because it
spends LLM calls. stdlib unittest, mock seam, <2s. Mirrors
services/eval/tests/test_skill_myfi_margin.py.
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
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test_agents_adversary", EVAL_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()


class _GoldenMarginMixin:
    """Shared mock-margin proof, parameterized by rubric kind + golden basename."""

    MARGIN = 15
    KIND: str
    GOOD_RATIONALE: str
    BAD_RATIONALE: str

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / f"{self.KIND_BASENAME}_good.md").read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / f"{self.KIND_BASENAME}_bad.md").read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric(self.KIND)
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]
        self.good_mock = json.dumps(
            {"scores": {k: self.rubric["scale"] for k in dim_keys}, "rationale": self.GOOD_RATIONALE}
        )
        self.bad_mock = json.dumps({"scores": {k: 1 for k in dim_keys}, "rationale": self.BAD_RATIONALE})

    def _score_with_mock(self, text: str, mock_payload: str) -> dict:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(mock_payload)
            mock_path = fh.name
        try:
            with mock.patch.dict(os.environ, {"MYFI_LLM_MOCK": mock_path}, clear=False):
                return myfi_eval.evaluate(self.KIND, text)
        finally:
            os.unlink(mock_path)

    def test_goldens_and_rubric_present(self) -> None:
        self.assertTrue(self.golden_good.strip())
        self.assertTrue(self.golden_bad.strip())
        self.assertEqual(self.rubric["kind"], self.KIND)

    def test_golden_margin(self) -> None:
        good = self._score_with_mock(self.golden_good, self.good_mock)
        bad = self._score_with_mock(self.golden_bad, self.bad_mock)
        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad["overall"], threshold, "bad golden must score < threshold")
        margin = good["overall"] - bad["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")


class AuditFindingGoldenMarginTests(_GoldenMarginMixin, unittest.TestCase):
    KIND = "audit_finding"
    KIND_BASENAME = "auditor"
    GOOD_RATIONALE = "clear hypothesis, concrete falsification with a literal result, calibrated confidence"
    BAD_RATIONALE = "vague hypothesis, no concrete check, overconfident label, unsourced legal claims"


class DesignerArtifactGoldenMarginTests(_GoldenMarginMixin, unittest.TestCase):
    KIND = "designer_artifact"
    KIND_BASENAME = "designer"
    GOOD_RATIONALE = "valid markup, captioned traceable chart, readable, no reopened finding"
    BAD_RATIONALE = "placeholder text, broken markup, unsourced/altered figures, mismatched content"


if __name__ == "__main__":
    unittest.main()
