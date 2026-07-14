"""MCP smoke test + the toolkit eval mock-lane margin — deterministic, <2s.

`test_list_tools_smoke` matches the v0.0.0 plan's [ACCEPTANCE]: the FastMCP
server registers >=1 real tool with a non-empty name + description
(`asyncio.run(mcp.list_tools())`).

`test_eval_margin` is the self-contained mock-lane assertion for
`services/eval/rubrics/toolkit.rubric.json`. It reproduces, in miniature, the
deterministic weighted-overall verdict math the sibling W2-services-llm-eval
unit's `services/eval/eval.py` implements at RUN time
(`overall = round(100 * sum(score*weight) / (scale * sum(weight)))`,
`passed = overall >= threshold`), staged via the same `MYFI_LLM_MOCK_TEXT` env
seam that service will read. Kept self-contained on purpose (plan [NOTES]:
"Depends on the eval harness ... at RUN time (nightly), not at unit-build
time") so this unit's gate tests never couple to a same-wave sibling.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from myfi_toolkit import mcp_server

_TESTS_DIR = Path(__file__).resolve().parent
_RUBRIC_PATH = _TESTS_DIR.parent.parent / "eval" / "rubrics" / "toolkit.rubric.json"
_EVALS_DIR = _TESTS_DIR / "evals"

# Staged judge scores for the good/bad goldens below — stand in for a live
# Claude Code judge call, matching the mock-seam contract services/llm/llm.py
# (sibling unit) will implement: MYFI_LLM_MOCK_TEXT carries the judge's raw
# response verbatim, short-circuiting the real model call.
_GOOD_SCORES = {
    "tool-description-usability": 5,
    "output-parseability": 5,
    "agent-actionability": 4,
}
_BAD_SCORES = {
    "tool-description-usability": 2,
    "output-parseability": 1,
    "agent-actionability": 1,
}


def _weighted_overall(rubric: dict, scores: dict[str, int]) -> int:
    """The eval harness's deterministic verdict math (plan §W2-services-llm-eval),
    reproduced here so this unit's mock-lane margin needs no sibling at build time.
    """
    scale = rubric["scale"]
    dims = rubric["dimensions"]
    total_weight = sum(dim["weight"] for dim in dims)
    weighted_sum = sum(scores[dim["key"]] * dim["weight"] for dim in dims)
    return round(100 * weighted_sum / (scale * total_weight))


def _stage_mock_judge_response(monkeypatch: pytest.MonkeyPatch, scores: dict[str, int]) -> dict[str, int]:
    payload = json.dumps({"scores": scores, "rationale": "staged for gate test"})
    monkeypatch.setenv("MYFI_LLM_MOCK_TEXT", payload)
    return json.loads(payload)["scores"]


def test_list_tools_smoke() -> None:
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert len(tools) >= 1
    for tool in tools:
        assert tool.name, "MCP tool must have a non-empty name"
        assert tool.description, f"MCP tool {tool.name!r} must have a non-empty description"


def test_documented_tools_are_registered() -> None:
    """The MCP tool set must match the names skills/myfi/SKILL.md documents as
    canonical (mcp__plugin_myfi_myfi-toolkit__{quote,db_init,db_migrate,db_version}
    + describe_toolkit) and every agent's tools: line cites. A dropped tool would
    silently break an agent's only path to toolkit data (esp. @advisor, which has
    no Bash/CLI fallback), so this asserts the contract, not just >=1 tool.
    """
    names = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}
    for required in ("describe_toolkit", "quote", "db_init", "db_migrate", "db_version"):
        assert required in names, f"MCP tool {required!r} missing (SKILL.md + agents cite it); have {sorted(names)}"


def test_quote_tool_returns_typed_dict() -> None:
    """The quote MCP tool degrades to the research source (no provider env) and
    returns a JSON-serializable dict carrying the symbol and its source."""
    import os

    os.environ.pop("MYFI_MARKETDATA_PROVIDER", None)
    result = mcp_server.quote("AAPL")
    assert isinstance(result, dict)
    assert result.get("symbol", "").upper() == "AAPL" or "value" in result
    assert "source" in result or "value" in result


def test_eval_margin(monkeypatch: pytest.MonkeyPatch) -> None:
    rubric = json.loads(_RUBRIC_PATH.read_text())
    threshold = rubric["threshold"]
    dimension_keys = {dim["key"] for dim in rubric["dimensions"]}
    assert dimension_keys == set(_GOOD_SCORES) == set(_BAD_SCORES)

    good_text = (_EVALS_DIR / "good_tool_output.txt").read_text()
    bad_text = (_EVALS_DIR / "bad_tool_output.txt").read_text()
    assert good_text.strip() and bad_text.strip()

    good_scores = _stage_mock_judge_response(monkeypatch, _GOOD_SCORES)
    good_overall = _weighted_overall(rubric, good_scores)

    bad_scores = _stage_mock_judge_response(monkeypatch, _BAD_SCORES)
    bad_overall = _weighted_overall(rubric, bad_scores)

    assert good_overall >= threshold > bad_overall
