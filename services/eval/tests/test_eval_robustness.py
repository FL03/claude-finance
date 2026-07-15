"""services/eval/tests/test_eval_robustness.py -- malformed-rubric robustness gate.

A structurally-malformed rubric (a dimension missing "weight"/"key", an empty "dimensions"
list, or dimension weights that sum to 0) must fail the harness's documented way: a JudgeError
that `cmd_run` maps to exit 4. Before this test existed, `compute_verdict` (and, transitively,
`build_judge_prompt`) assumed a well-formed rubric shape and let a raw KeyError (missing "key"/
"weight") or ZeroDivisionError (dimensions summing to 0 weight, or an empty "dimensions" list)
escape `cmd_run`'s `except UsageError` / `except JudgeError` handlers as an uncaught traceback --
exit 1, indistinguishable from a hard crash, instead of the documented exit 4 judge/parse error.

Mirrors test_eval_math.py's / test_eval_rubrics.py's importlib-load pattern (no package install
needed) and calls `compute_verdict`/`load_rubric`/`cmd_run` directly -- no LLM subprocess, no
`MYFI_LLM_MOCK` seam needed since the failure is purely in rubric-shape validation, before any
judge call would happen. Deterministic, stdlib-only, <2s, no network.
"""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

EVAL_PY = Path(__file__).resolve().parent.parent / "eval.py"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location("myfi_eval_under_test_robustness", EVAL_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


myfi_eval = _load_eval_module()

VALID_DIM = {"key": "x", "weight": 1, "desc": "placeholder"}


def _base_rubric(**overrides) -> dict:
    """A minimal, structurally-valid rubric -- callers override one field at a
    time to produce exactly one malformation per test, isolating the cause."""
    rubric = {
        "kind": "malformed",
        "subject": "test rubric for robustness gate",
        "scale": 5,
        "threshold": 65,
        "dimensions": [dict(VALID_DIM)],
        "guidance": "test",
    }
    rubric.update(overrides)
    return rubric


class MalformedRubricLoadTests(unittest.TestCase):
    """load_rubric must reject a structurally-malformed rubric with JudgeError at load time,
    not let a KeyError/ZeroDivisionError surface later out of compute_verdict/build_judge_prompt."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rubric_dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _load(self, kind: str, rubric: dict):
        path = self.rubric_dir / f"{kind}.rubric.json"
        path.write_text(json.dumps(rubric), encoding="utf-8")
        return myfi_eval.load_rubric(kind, rubric_dir=self.rubric_dir)

    def test_dimension_missing_weight_raises_judge_error(self) -> None:
        rubric = _base_rubric(dimensions=[{"key": "x", "desc": "no weight here"}])
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("missing-weight", rubric)

    def test_dimension_missing_key_raises_judge_error(self) -> None:
        rubric = _base_rubric(dimensions=[{"weight": 1, "desc": "no key here"}])
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("missing-key", rubric)

    def test_empty_dimensions_list_raises_judge_error(self) -> None:
        rubric = _base_rubric(dimensions=[])
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("empty-dims", rubric)

    def test_missing_dimensions_field_raises_judge_error(self) -> None:
        rubric = _base_rubric()
        del rubric["dimensions"]
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("no-dims-field", rubric)

    def test_dimensions_not_a_list_raises_judge_error(self) -> None:
        rubric = _base_rubric(dimensions={"x": VALID_DIM})
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("dims-not-list", rubric)

    def test_zero_total_weight_raises_judge_error(self) -> None:
        rubric = _base_rubric(
            dimensions=[
                {"key": "a", "weight": 0, "desc": "zero"},
                {"key": "b", "weight": 0, "desc": "also zero"},
            ]
        )
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("zero-weight", rubric)

    def test_missing_scale_raises_judge_error(self) -> None:
        rubric = _base_rubric()
        del rubric["scale"]
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("no-scale", rubric)

    def test_non_numeric_weight_raises_judge_error(self) -> None:
        rubric = _base_rubric(dimensions=[{"key": "a", "weight": "high", "desc": "d"}])
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("string-weight", rubric)

    def test_dimension_missing_desc_raises_judge_error(self) -> None:
        rubric = _base_rubric(dimensions=[{"key": "a", "weight": 1}])
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("no-desc", rubric)

    def test_duplicate_dimension_keys_raise_judge_error(self) -> None:
        rubric = _base_rubric(
            dimensions=[
                {"key": "a", "weight": 1, "desc": "first"},
                {"key": "a", "weight": 1, "desc": "duplicate"},
            ]
        )
        with self.assertRaises(myfi_eval.JudgeError):
            self._load("dup-keys", rubric)

    def test_valid_rubric_still_loads_clean(self) -> None:
        # Control: a well-formed rubric must NOT raise -- proves the validator
        # rejects only what's actually malformed, not everything.
        rubric = self._load("valid", _base_rubric())
        self.assertEqual(rubric["kind"], "malformed")
        self.assertEqual(len(rubric["dimensions"]), 1)


class ComputeVerdictDirectMalformedTests(unittest.TestCase):
    """compute_verdict is also exercised directly (e.g. by test_eval_math.py, or any future
    caller that builds a rubric dict by hand) -- it must not raise a raw KeyError or
    ZeroDivisionError for a malformed rubric either, only JudgeError."""

    def test_missing_weight_raises_judge_error_not_keyerror(self) -> None:
        rubric = _base_rubric(dimensions=[{"key": "x", "desc": "no weight"}])
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(rubric, {"x": 3}, threshold=None, model="opus", kind="malformed")

    def test_missing_key_raises_judge_error_not_keyerror(self) -> None:
        rubric = _base_rubric(dimensions=[{"weight": 1, "desc": "no key"}])
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(rubric, {}, threshold=None, model="opus", kind="malformed")

    def test_empty_dimensions_raises_judge_error_not_zerodivision(self) -> None:
        rubric = _base_rubric(dimensions=[])
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(rubric, {}, threshold=None, model="opus", kind="malformed")

    def test_zero_total_weight_raises_judge_error_not_zerodivision(self) -> None:
        rubric = _base_rubric(
            dimensions=[
                {"key": "a", "weight": 0, "desc": "zero"},
                {"key": "b", "weight": 0, "desc": "also zero"},
            ]
        )
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.compute_verdict(
                rubric, {"a": 3, "b": 3}, threshold=None, model="opus", kind="malformed"
            )


class CmdRunExitCodeTests(unittest.TestCase):
    """End-to-end: `eval.py run --kind=<malformed>` (via cmd_run, the actual CLI handler) must
    exit EXIT_JUDGE (4) with a clean stderr message -- never let the malformed-rubric exception
    escape uncaught, which would print a Python traceback and exit 1 (indistinguishable from a
    genuine crash to any caller scripting against the documented exit codes)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.rubric_dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, kind: str, rubric: dict) -> None:
        (self.rubric_dir / f"{kind}.rubric.json").write_text(json.dumps(rubric), encoding="utf-8")

    class _Args:
        input_file = None
        threshold = None
        model = None
        timeout = None
        fmt = "text"

        def __init__(self, kind: str, text: str) -> None:
            self.kind = kind
            self.input = text

    def test_evaluate_raises_judge_error_for_malformed_rubric(self) -> None:
        # evaluate() is the function cmd_run's try/except JudgeError wraps.
        self._write("zero-weight", _base_rubric(dimensions=[{"key": "a", "weight": 0, "desc": "z"}]))
        with self.assertRaises(myfi_eval.JudgeError):
            myfi_eval.evaluate("zero-weight", "some item text", rubric_dir=self.rubric_dir)

    def test_cmd_run_exits_judge_not_a_traceback_for_empty_dimensions(self) -> None:
        self._write("empty-dims", _base_rubric(dimensions=[]))
        args = self._Args("empty-dims", "some item text")

        with mock.patch.object(myfi_eval, "RUBRIC_DIR", self.rubric_dir):
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = myfi_eval.cmd_run(args)

        self.assertEqual(code, myfi_eval.EXIT_JUDGE)
        self.assertIn("empty-dims", stderr.getvalue())

    def test_cmd_run_exits_judge_not_a_traceback_for_missing_weight(self) -> None:
        self._write("missing-weight", _base_rubric(dimensions=[{"key": "x", "desc": "no weight"}]))
        args = self._Args("missing-weight", "some item text")

        with mock.patch.object(myfi_eval, "RUBRIC_DIR", self.rubric_dir):
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = myfi_eval.cmd_run(args)

        self.assertEqual(code, myfi_eval.EXIT_JUDGE)
        self.assertIn("missing-weight", stderr.getvalue())

    def test_cmd_run_exits_judge_not_a_traceback_for_zero_total_weight(self) -> None:
        self._write(
            "zero-weight",
            _base_rubric(
                dimensions=[
                    {"key": "a", "weight": 0, "desc": "zero"},
                    {"key": "b", "weight": 0, "desc": "also zero"},
                ]
            ),
        )
        args = self._Args("zero-weight", "some item text")

        with mock.patch.object(myfi_eval, "RUBRIC_DIR", self.rubric_dir):
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = myfi_eval.cmd_run(args)

        self.assertEqual(code, myfi_eval.EXIT_JUDGE)
        self.assertIn("zero-weight", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
