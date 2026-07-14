"""Gate: every shipped rubric is structurally valid, and the golden-margin
proof — with MYFI_LLM_MOCK staged scores, the deterministic harness correctly
discriminates a good advisory from a bad one by a clear margin. A malformed
rubric would make `eval run` produce garbage scores silently, so the
structural checks fail loudly instead. stdlib unittest, mock seam, <2s.
"""

from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest import mock

EVAL_DIR = Path(__file__).resolve().parent.parent
EVAL_PY = EVAL_DIR / "eval.py"
RUBRIC_DIR = EVAL_DIR / "rubrics"
GOLDEN_DIR = EVAL_DIR / "evals"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test_rubrics", EVAL_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()

RUBRIC_FILES = sorted(RUBRIC_DIR.glob("*.rubric.json"))


class RubricShapeTests(unittest.TestCase):
    def test_at_least_one_rubric_shipped(self) -> None:
        self.assertGreaterEqual(len(RUBRIC_FILES), 1)

    def test_every_rubric_is_structurally_valid(self) -> None:
        for path in RUBRIC_FILES:
            with self.subTest(rubric=path.name):
                with open(path, encoding="utf-8") as fh:
                    rubric = json.load(fh)  # raises loudly if not valid JSON

                expected_kind = path.name[: -len(".rubric.json")]
                self.assertEqual(rubric.get("kind"), expected_kind, f"{path.name}: kind mismatch")

                scale = rubric.get("scale")
                self.assertIsInstance(scale, int, f"{path.name}: scale must be an integer")
                self.assertGreaterEqual(scale, 2, f"{path.name}: scale must be >= 2")

                threshold = rubric.get("threshold")
                self.assertIsInstance(threshold, int, f"{path.name}: threshold must be an integer")
                self.assertTrue(0 <= threshold <= 100, f"{path.name}: threshold must be 0..100")

                dims = rubric.get("dimensions")
                self.assertIsInstance(dims, list, f"{path.name}: dimensions must be a list")
                self.assertGreaterEqual(len(dims), 1, f"{path.name}: needs at least one dimension")

                keys = []
                for dim in dims:
                    self.assertIn("key", dim, f"{path.name}: dimension missing key")
                    self.assertIsInstance(dim["key"], str) and self.assertTrue(dim["key"])
                    weight = dim.get("weight")
                    self.assertIsInstance(weight, int, f"{path.name}: weight must be an integer")
                    self.assertGreater(weight, 0, f"{path.name}: weight must be > 0")
                    desc = dim.get("desc")
                    self.assertIsInstance(desc, str)
                    self.assertTrue(desc, f"{path.name}: dimension needs a non-empty desc")
                    keys.append(dim["key"])
                self.assertEqual(len(keys), len(set(keys)), f"{path.name}: duplicate dimension keys")

                total_weight = sum(d["weight"] for d in dims)
                self.assertGreater(total_weight, 0, f"{path.name}: weights must sum > 0")

    def test_advisory_plan_trade_baseline_rubrics_shipped(self) -> None:
        shipped = {path.name[: -len(".rubric.json")] for path in RUBRIC_FILES}
        for kind in ("advisory", "plan", "trade"):
            self.assertIn(kind, shipped)


class GoldenMarginTests(unittest.TestCase):
    """The gate-lane half of the golden-margin eval (see [EVALS] in the plan):
    with MYFI_LLM_MOCK staging plausible judge scores, `evaluate()` must score
    the good advisory golden above threshold and the bad one below, separated
    by a clear margin. The live lane runs the SAME golden files through a real
    local-Claude-Code judge: `MYFI_EVAL_LIVE=1 bin/myfi-eval run --kind=advisory
    --input-file=evals/golden_good.txt` (and golden_bad.txt) — not part of the
    gate lane because it spends real LLM calls.
    """

    MARGIN = 15

    def setUp(self) -> None:
        self.golden_good = (GOLDEN_DIR / "golden_good.txt").read_text(encoding="utf-8")
        self.golden_bad = (GOLDEN_DIR / "golden_bad.txt").read_text(encoding="utf-8")
        self.rubric = myfi_eval.load_rubric("advisory")
        dim_keys = [d["key"] for d in self.rubric["dimensions"]]

        self.good_mock = json.dumps(
            {"scores": {k: self.rubric["scale"] for k in dim_keys}, "rationale": "grounded, actionable, risk stated"}
        )
        self.bad_mock = json.dumps(
            {"scores": {k: 1 for k in dim_keys}, "rationale": "vague, ungrounded, no risk disclosure"}
        )

    def _score_with_mock(self, text: str, mock_payload: str) -> dict:
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(mock_payload)
            mock_path = fh.name
        try:
            with mock.patch.dict(os.environ, {"MYFI_LLM_MOCK": mock_path}, clear=False):
                return myfi_eval.evaluate("advisory", text)
        finally:
            os.unlink(mock_path)

    def test_golden_margin(self) -> None:
        good_result = self._score_with_mock(self.golden_good, self.good_mock)
        bad_result = self._score_with_mock(self.golden_bad, self.bad_mock)

        threshold = self.rubric["threshold"]
        self.assertGreaterEqual(good_result["overall"], threshold, "good golden must score >= threshold")
        self.assertLess(bad_result["overall"], threshold, "bad golden must score < threshold")
        margin = good_result["overall"] - bad_result["overall"]
        self.assertGreaterEqual(margin, self.MARGIN, f"good-bad margin {margin} < {self.MARGIN}")

    def test_live_lane_strips_a_stray_mock(self) -> None:
        # MYFI_EVAL_LIVE=1 must not let an inherited mock silently fake the
        # "live" lane — run_judge should ignore MYFI_LLM_MOCK when live=True.
        # We prove this deterministically: pointing MYFI_LLM_BIN at a fake
        # non-mock claude that echoes a fixed JSON response confirms the
        # mock env var was actually stripped before the llm.py subprocess ran
        # (a real claude call would otherwise be attempted and fail fast
        # since the sentinel binary is not `claude`).
        import stat
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fake_claude = Path(tmp) / "fake-claude"
            fake_claude.write_text(
                "#!/bin/sh\ncat <<'EOF'\n"
                '{"scores":{"actionable-recs":5,"data-grounded":5,"risk-disclosed":5,"client-clarity":5}}\n'
                "EOF\n"
            )
            fake_claude.chmod(fake_claude.stat().st_mode | stat.S_IEXEC)

            stray_mock = Path(tmp) / "stray_mock.json"
            stray_mock.write_text('{"scores":{"actionable-recs":1,"data-grounded":1,"risk-disclosed":1,"client-clarity":1}}')

            env_overrides = {
                "MYFI_LLM_MOCK": str(stray_mock),
                "MYFI_LLM_BIN": str(fake_claude),
                "MYFI_EVAL_LIVE": "1",
            }
            with mock.patch.dict(os.environ, env_overrides, clear=False):
                result = myfi_eval.evaluate("advisory", "some client text", live=True)
            # If the stray mock had leaked through, overall would be the
            # low (1,1,1,1) score. Because live=True strips it, the fake
            # claude binary is invoked instead and returns the high score.
            self.assertEqual(result["overall"], 100)


if __name__ == "__main__":
    unittest.main()
