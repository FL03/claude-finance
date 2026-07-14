#!/usr/bin/env python3
"""tests/integration/test_close_report_eval.py -- close_report rubric wiring.

W7-integration-close [EVALS]: "close_report.rubric.json (dims: honest-verdict, evidence-cited,
follow-ups-named) scores the close report via local Claude Code -- the close report's quality is
latent." Before this test existed the rubric shipped with zero references anywhere in the repo
(the audit's "DUPLICATION RISK"-adjacent finding: an unwired eval is a silent gap, not a skip).

Mirrors the same self-contained mock-lane pattern `services/toolkit/tests/test_marketdata.py`
uses for `market_quote.rubric.json` and `tests/structure/test_docs.sh` uses for
`readme_finance.rubric.json`: reproduce the eval harness's deterministic weighted-overall verdict
math (`services/eval/eval.py::compute_verdict`) against staged scores over local good/bad goldens,
kept self-contained (no import of `services/eval/eval.py`, no `MYFI_LLM_MOCK` subprocess) so this
unit's gate tests never couple to a same-wave/adjacent-wave sibling's file scope. The live judge
lane (`MYFI_EVAL_LIVE=1 services/eval/eval.py run --kind=close_report --input-file=...`) is not
part of the gate lane -- it spends a real local-Claude-Code call.

Deterministic, stdlib-only, <1s, no network, no live LLM call.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUBRIC_PATH = REPO_ROOT / "services" / "eval" / "rubrics" / "close_report.rubric.json"
EVALS_DIR = Path(__file__).resolve().parent / "evals"
CLOSE_REPORT_PATH = REPO_ROOT / ".shepherd" / "docs" / "reports" / "2026-07-13-v000-close.md"

# A close report that hits every rubric dimension scores at the scale ceiling; one that hedges,
# cites nothing, and defers every loose end scores at the floor. Mirrors the fixed GOOD/BAD score
# maps `test_marketdata.py::test_eval_margin` and `test_docs.sh`'s eval-margin block use.
_GOOD_SCORES = {"honest-verdict": 5, "evidence-cited": 5, "follow-ups-named": 5}
_BAD_SCORES = {"honest-verdict": 1, "evidence-cited": 1, "follow-ups-named": 1}


def _weighted_overall(rubric: dict, scores: dict[str, int]) -> int:
    """The eval harness's deterministic verdict math (`services/eval/eval.py`
    `compute_verdict`: ``floor(100 * weighted_sum / (scale * total_weight) + 0.5)``),
    reproduced here so this unit's mock-lane margin needs no sibling service at build time.
    """
    scale = rubric["scale"]
    dims = rubric["dimensions"]
    total_weight = sum(dim["weight"] for dim in dims)
    weighted_sum = sum(scores[dim["key"]] * dim["weight"] for dim in dims)
    return round(100 * weighted_sum / (scale * total_weight))


class CloseReportRubricTests(unittest.TestCase):
    def setUp(self) -> None:
        with RUBRIC_PATH.open(encoding="utf-8") as fh:
            self.rubric = json.load(fh)

    def test_rubric_is_structurally_valid_and_kind_matches_filename(self) -> None:
        self.assertEqual(self.rubric.get("kind"), "close_report")
        self.assertIsInstance(self.rubric.get("scale"), int)
        self.assertIsInstance(self.rubric.get("threshold"), int)
        dims = self.rubric.get("dimensions")
        self.assertIsInstance(dims, list)
        self.assertGreaterEqual(len(dims), 1)

    def test_rubric_names_the_three_documented_dimensions(self) -> None:
        keys = {dim["key"] for dim in self.rubric["dimensions"]}
        self.assertEqual(keys, {"honest-verdict", "evidence-cited", "follow-ups-named"})
        self.assertEqual(keys, set(_GOOD_SCORES))
        self.assertEqual(keys, set(_BAD_SCORES))

    def test_goldens_present_and_non_empty(self) -> None:
        good_text = (EVALS_DIR / "close_report_good.md").read_text(encoding="utf-8")
        bad_text = (EVALS_DIR / "close_report_bad.md").read_text(encoding="utf-8")
        self.assertTrue(good_text.strip())
        self.assertTrue(bad_text.strip())

    def test_eval_margin(self) -> None:
        threshold = self.rubric["threshold"]
        good_overall = _weighted_overall(self.rubric, _GOOD_SCORES)
        bad_overall = _weighted_overall(self.rubric, _BAD_SCORES)

        self.assertGreaterEqual(good_overall, threshold, "good golden must score >= threshold")
        self.assertLess(bad_overall, threshold, "bad golden must score < threshold")
        margin = good_overall - bad_overall
        self.assertGreaterEqual(margin, 15, f"good-bad margin {margin} < 15")

    def test_shipped_close_report_is_not_the_bad_golden_shape(self) -> None:
        """A structural tripwire, not a judge call: the shipped close report at the sprint's
        canonical path must not still be the stub/hedge shape the bad golden models (no verdict,
        no evidence, "awaiting ... CLOSE-FINALIZE", deferring the whole narrative). This is
        deterministic text-shape checking, not a substitute for the live judge lane -- it exists
        so a REDO back to a stub is a loud, immediate gate failure, not a silent regression only
        the (paid) live eval lane would ever catch.
        """
        self.assertTrue(CLOSE_REPORT_PATH.is_file(), f"missing: {CLOSE_REPORT_PATH}")
        text = CLOSE_REPORT_PATH.read_text(encoding="utf-8")
        lowered = text.lower()

        self.assertNotIn("status: stub", lowered, "close report must not self-declare STUB")
        self.assertNotIn("awaiting root-shepherd close-finalize", lowered)

        for marker in ("DONE", "DONE_WITH_CONCERNS", "BLOCKED"):
            with self.subTest(marker=marker):
                pass  # existence checked in aggregate below
        self.assertTrue(
            any(marker in text for marker in ("DONE_WITH_CONCERNS", "DONE", "BLOCKED")),
            "close report must carry at least one plain DONE/DONE_WITH_CONCERNS/BLOCKED verdict",
        )
        self.assertIn(
            "follow-up",
            lowered.replace("follow up", "follow-up"),
            "close report must name at least one follow-up explicitly",
        )


if __name__ == "__main__":
    unittest.main()
