"""Gate: the deterministic verdict — weighted overall, threshold pass/fail,
validation errors, and judge-response JSON extraction. The math is code, no
LLM: every case here calls ``compute_verdict``/``extract_json`` directly, no
subprocess, no mock seam needed. stdlib unittest, <2s.
"""

from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

EVAL_PY = Path(__file__).resolve().parent.parent / "eval.py"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test", EVAL_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()


def independent_overall(rubric: dict, scores: dict) -> int:
    """A second, independent implementation of the weighting formula, used to
    cross-check `compute_verdict` rather than hardcode magic numbers tied to
    one rubric's current shape."""
    scale = rubric["scale"]
    total_weight = sum(d["weight"] for d in rubric["dimensions"])
    weighted_sum = sum(scores[d["key"]] * d["weight"] for d in rubric["dimensions"])
    return math.floor(100 * weighted_sum / (scale * total_weight) + 0.5)


ADVISORY_RUBRIC = myfi_eval.load_rubric("advisory")


class ComputeVerdictTests(unittest.TestCase):
    def test_weighted_overall_matches_independent_formula(self) -> None:
        scores = {"actionable-recs": 4, "data-grounded": 4, "risk-disclosed": 3, "client-clarity": 3}
        result = myfi_eval.compute_verdict(
            ADVISORY_RUBRIC, scores, "ok", threshold=None, model="opus", kind="advisory"
        )
        self.assertEqual(result["overall"], independent_overall(ADVISORY_RUBRIC, scores))

    def test_all_max_scores_pass(self) -> None:
        scores = {d["key"]: ADVISORY_RUBRIC["scale"] for d in ADVISORY_RUBRIC["dimensions"]}
        result = myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=None, model="opus", kind="advisory")
        self.assertEqual(result["overall"], 100)
        self.assertTrue(result["passed"])

    def test_all_min_scores_fail(self) -> None:
        scores = {d["key"]: 1 for d in ADVISORY_RUBRIC["dimensions"]}
        result = myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=None, model="opus", kind="advisory")
        self.assertEqual(result["overall"], independent_overall(ADVISORY_RUBRIC, scores))
        self.assertFalse(result["passed"])

    def test_weighting_actually_matters(self) -> None:
        # Same unweighted mean (3.0), different distribution across weighted vs
        # unweighted dims -> different overall if (and only if) weights apply.
        high_on_heavy = {"actionable-recs": 5, "data-grounded": 5, "risk-disclosed": 1, "client-clarity": 1}
        high_on_light = {"actionable-recs": 1, "data-grounded": 1, "risk-disclosed": 1, "client-clarity": 9}
        # (the second is intentionally out of range to prove range validation fires)
        r1 = myfi_eval.compute_verdict(ADVISORY_RUBRIC, high_on_heavy, threshold=None, model="opus", kind="advisory")
        self.assertEqual(r1["overall"], independent_overall(ADVISORY_RUBRIC, high_on_heavy))
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(ADVISORY_RUBRIC, high_on_light, threshold=None, model="opus", kind="advisory")

    def test_threshold_override_flips_verdict(self) -> None:
        scores = {"actionable-recs": 4, "data-grounded": 4, "risk-disclosed": 4, "client-clarity": 4}
        low_bar = myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=10, model="opus", kind="advisory")
        high_bar = myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=99, model="opus", kind="advisory")
        self.assertTrue(low_bar["passed"])
        self.assertFalse(high_bar["passed"])
        self.assertEqual(low_bar["overall"], high_bar["overall"])  # same score, different bar

    def test_rubric_threshold_used_when_none_given(self) -> None:
        scores = {d["key"]: 3 for d in ADVISORY_RUBRIC["dimensions"]}
        result = myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=None, model="opus", kind="advisory")
        self.assertEqual(result["threshold"], ADVISORY_RUBRIC["threshold"])

    def test_missing_dimension_raises(self) -> None:
        scores = {"actionable-recs": 4, "data-grounded": 4, "risk-disclosed": 4}  # client-clarity missing
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=None, model="opus", kind="advisory")

    def test_non_numeric_score_raises(self) -> None:
        scores = {"actionable-recs": "high", "data-grounded": 4, "risk-disclosed": 4, "client-clarity": 4}
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=None, model="opus", kind="advisory")

    def test_bool_score_is_rejected_as_non_numeric(self) -> None:
        # bool is a subclass of int in Python — must NOT silently pass as a score.
        scores = {"actionable-recs": True, "data-grounded": 4, "risk-disclosed": 4, "client-clarity": 4}
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=None, model="opus", kind="advisory")

    def test_out_of_range_score_raises(self) -> None:
        scores = {"actionable-recs": 0, "data-grounded": 4, "risk-disclosed": 4, "client-clarity": 4}
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(ADVISORY_RUBRIC, scores, threshold=None, model="opus", kind="advisory")


class ExtractJsonTests(unittest.TestCase):
    def test_raw_json(self) -> None:
        self.assertEqual(myfi_eval.extract_json('{"scores":{"x":1}}'), {"scores": {"x": 1}})

    def test_fenced_json(self) -> None:
        raw = '```json\n{"scores":{"x":1}}\n```'
        self.assertEqual(myfi_eval.extract_json(raw), {"scores": {"x": 1}})

    def test_json_wrapped_in_prose(self) -> None:
        raw = 'Sure, here is the score:\n{"scores":{"x":1},"rationale":"ok"}\nHope that helps!'
        self.assertEqual(myfi_eval.extract_json(raw), {"scores": {"x": 1}, "rationale": "ok"})

    def test_unparseable_raises_judge_error(self) -> None:
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.extract_json("not json at all, no braces here")


if __name__ == "__main__":
    unittest.main()
