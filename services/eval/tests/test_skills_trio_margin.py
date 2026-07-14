"""Gate-lane half of the W4-skills-trio golden-margin evals (see the unit's
[EVALS] in the plan): with MYFI_LLM_MOCK staging plausible judge scores, the
deterministic harness scores each skill's `good.md` golden above its rubric's
threshold and `bad.md` below, separated by a clear margin: one rubric/golden
pair each for IMPROVE (`improve_loop`), COMPLIANCE (`compliance_coverage`),
and TAXES (`taxes_knowledge`).

The live lane runs the SAME goldens through a real local-Claude-Code judge,
e.g.:
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=improve_loop \\
      --input-file=skills/improve/evals/good.md
(and bad.md, and the compliance/taxes pairs). Excluded from the gate because
it spends LLM calls. stdlib unittest, mock seam, <2s. Mirrors
services/eval/tests/test_skill_myfi_margin.py and
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

# One (rubric kind, golden dir) pair per W4-skills-trio skill.
CASES = (
    ("improve_loop", REPO_ROOT / "skills" / "improve" / "evals"),
    ("compliance_coverage", REPO_ROOT / "skills" / "compliance" / "evals"),
    ("taxes_knowledge", REPO_ROOT / "skills" / "taxes" / "evals"),
)


def _load_eval_module():
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test_skills_trio", EVAL_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()


class SkillsTrioGoldenMarginTests(unittest.TestCase):
    MARGIN = 15

    def _score_with_mock(self, kind: str, text: str, mock_payload: str) -> dict:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(mock_payload)
            mock_path = fh.name
        try:
            with mock.patch.dict(os.environ, {"MYFI_LLM_MOCK": mock_path}, clear=False):
                return myfi_eval.evaluate(kind, text)
        finally:
            os.unlink(mock_path)

    def test_goldens_and_rubrics_present(self) -> None:
        for kind, golden_dir in CASES:
            with self.subTest(kind=kind):
                rubric = myfi_eval.load_rubric(kind)
                self.assertEqual(rubric["kind"], kind)
                good = (golden_dir / "good.md").read_text(encoding="utf-8")
                bad = (golden_dir / "bad.md").read_text(encoding="utf-8")
                self.assertTrue(good.strip())
                self.assertTrue(bad.strip())

    def test_golden_margin(self) -> None:
        for kind, golden_dir in CASES:
            with self.subTest(kind=kind):
                rubric = myfi_eval.load_rubric(kind)
                dim_keys = [d["key"] for d in rubric["dimensions"]]
                good_mock = json.dumps(
                    {
                        "scores": {k: rubric["scale"] for k in dim_keys},
                        "rationale": "concrete, mechanism-grounded, actionable",
                    }
                )
                bad_mock = json.dumps(
                    {
                        "scores": {k: 1 for k in dim_keys},
                        "rationale": "vague, ungrounded, not actionable",
                    }
                )

                good_text = (golden_dir / "good.md").read_text(encoding="utf-8")
                bad_text = (golden_dir / "bad.md").read_text(encoding="utf-8")

                good_result = self._score_with_mock(kind, good_text, good_mock)
                bad_result = self._score_with_mock(kind, bad_text, bad_mock)

                threshold = rubric["threshold"]
                self.assertGreaterEqual(
                    good_result["overall"], threshold, f"{kind}: good golden must score >= threshold"
                )
                self.assertLess(bad_result["overall"], threshold, f"{kind}: bad golden must score < threshold")
                margin = good_result["overall"] - bad_result["overall"]
                self.assertGreaterEqual(margin, self.MARGIN, f"{kind}: good-bad margin {margin} < {self.MARGIN}")


if __name__ == "__main__":
    unittest.main()
