"""Gate-lane half of the W4-agents-actors golden-margin eval (see the unit's [EVALS] in the
plan): with MYFI_LLM_MOCK staging plausible judge scores, the deterministic harness scores the
good @advisor golden above the `advisory` rubric threshold (the W2 baseline rubric, reused per
[FILES]) and the good @quant golden above the new `quant_analysis` rubric threshold, each with
its bad golden scoring below threshold by a clear margin.

The live lane runs the SAME goldens through a real local-Claude-Code judge:
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=advisory --input-file=agents/evals/advisor_good.md
  MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=quant_analysis --input-file=agents/evals/quant_good.md
(and the matching *_bad.md files) — excluded from the gate lane because it spends real LLM calls.
stdlib unittest, mock seam, <2s. Mirrors services/eval/tests/test_skill_myfi_margin.py.
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
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test_agents_actors", EVAL_PY)
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


class AdvisorGoldenMarginTests(_GoldenMarginMixin, unittest.TestCase):
    """@advisor is scored against the `advisory` rubric (W2 baseline, reused per [FILES])."""

    kind = "advisory"
    good_name = "advisor_good.md"
    bad_name = "advisor_bad.md"
    good_rationale = "concrete numbered steps, toolkit-grounded figures, risk stated plainly, client-actionable"
    bad_rationale = "vague upside-only platitudes, no real figures, no risk disclosed, generic hype"


class QuantGoldenMarginTests(_GoldenMarginMixin, unittest.TestCase):
    """@quant is scored against the new `quant_analysis` rubric."""

    kind = "quant_analysis"
    good_name = "quant_good.md"
    bad_name = "quant_bad.md"
    good_rationale = "explicit assumptions/methodology, model fits the question, toolkit-cited data, decisive read"
    bad_rationale = "no stated methodology, no data citations, non-committal hedge-everything non-answer"


if __name__ == "__main__":
    unittest.main()
