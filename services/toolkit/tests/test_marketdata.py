"""Gate tests for myfi_toolkit.marketdata — deterministic, offline, <2s.

Exercises the v0.0.0 plan's `W3-toolkit-marketdata` [ACCEPTANCE]: with NO
provider env set, the default source returns a typed `Quote` with
`source == "research"` and every field populated, no network call is ever
attempted on that path, and an unimplemented (deferred) provider raises
`NotImplementedError` rather than silently behaving like the default.

`test_eval_margin` is the self-contained mock-lane assertion for
`services/eval/rubrics/market_quote.rubric.json`, mirroring the pattern
`services/toolkit/tests/test_mcp_smoke.py` uses for `toolkit.rubric.json`:
it reproduces the eval harness's deterministic weighted-overall verdict math
against staged judge scores over the good/bad goldens in `tests/evals/`, kept
self-contained (no import of `services/eval/eval.py`) so this unit's gate
tests never couple to a same-wave/adjacent-wave sibling.
"""

from __future__ import annotations

import dataclasses
import json
import socket
from datetime import datetime
from pathlib import Path

import pytest

from myfi_toolkit.marketdata import Quote, default_source, quote
from myfi_toolkit.marketdata.registry import PROVIDER_ENV
from myfi_toolkit.marketdata.research import SOURCE_NAME

_TESTS_DIR = Path(__file__).resolve().parent
_RUBRIC_PATH = _TESTS_DIR.parent.parent / "eval" / "rubrics" / "market_quote.rubric.json"
_EVALS_DIR = _TESTS_DIR / "evals"

_GOOD_SCORES = {
    "quote-plausibility": 4,
    "source-honesty": 5,
    "field-completeness": 5,
}
_BAD_SCORES = {
    "quote-plausibility": 1,
    "source-honesty": 1,
    "field-completeness": 1,
}


@pytest.fixture(autouse=True)
def _no_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test in this module starts from "no provider env set" — the
    exact precondition the [ACCEPTANCE] predicate names.
    """
    monkeypatch.delenv(PROVIDER_ENV, raising=False)


def test_default_source_returns_typed_quote_with_all_fields_populated() -> None:
    result = default_source().quote("AAPL")

    assert isinstance(result, Quote)
    assert result.symbol == "AAPL"
    assert result.price is not None
    assert result.currency
    assert result.asof is not None
    assert result.source == SOURCE_NAME == "research"


def test_quote_is_the_declared_dataclass_shape() -> None:
    field_names = {f.name for f in dataclasses.fields(Quote)}
    assert field_names == {"symbol", "price", "currency", "asof", "source"}

    q = default_source().quote("MSFT")
    assert isinstance(q.asof, datetime)
    assert isinstance(q.price, float)
    assert isinstance(q.currency, str) and isinstance(q.source, str)

    # frozen — a Quote is immutable once returned.
    with pytest.raises(dataclasses.FrozenInstanceError):
        q.price = 1.0  # type: ignore[misc]


@pytest.mark.parametrize("provider", ["finnhub", "yfinance", "fred"])
def test_unimplemented_provider_raises_not_implemented(
    monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    monkeypatch.setenv(PROVIDER_ENV, provider)
    with pytest.raises(NotImplementedError):
        default_source().quote("AAPL")


def test_unknown_provider_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PROVIDER_ENV, "not-a-real-provider")
    with pytest.raises(ValueError):
        default_source()


def test_no_network_call_on_default_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked_connect(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("marketdata default path must not perform network I/O")

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    result = default_source().quote("AAPL")
    assert result.source == "research"


def test_quote_requires_a_non_empty_symbol() -> None:
    with pytest.raises(ValueError):
        default_source().quote("")


def test_cli_handler_prints_json_with_symbol_and_source(capsys: pytest.CaptureFixture[str]) -> None:
    # Exercises the same call myfi_toolkit.cli._cmd_quote makes
    # (`marketdata.quote(args.symbol)`) — the [ACCEPTANCE] predicate's
    # "emits JSON with symbol=='AAPL' and source=='research'" bar.
    exit_code = quote("AAPL")
    out = capsys.readouterr().out.strip()

    assert exit_code == 0
    payload = json.loads(out)
    assert payload["symbol"] == "AAPL"
    assert payload["source"] == "research"
    assert set(payload) == {"symbol", "price", "currency", "asof", "source"}


def _weighted_overall(rubric: dict, scores: dict[str, int]) -> int:
    """The eval harness's deterministic verdict math (`services/eval/eval.py`
    `compute_verdict`), reproduced here so this unit's mock-lane margin needs
    no sibling service at build time.
    """
    scale = rubric["scale"]
    dims = rubric["dimensions"]
    total_weight = sum(dim["weight"] for dim in dims)
    weighted_sum = sum(scores[dim["key"]] * dim["weight"] for dim in dims)
    return round(100 * weighted_sum / (scale * total_weight))


def test_eval_margin() -> None:
    rubric = json.loads(_RUBRIC_PATH.read_text())
    threshold = rubric["threshold"]
    dimension_keys = {dim["key"] for dim in rubric["dimensions"]}
    assert dimension_keys == set(_GOOD_SCORES) == set(_BAD_SCORES)

    good_text = (_EVALS_DIR / "marketdata_good.txt").read_text()
    bad_text = (_EVALS_DIR / "marketdata_bad.txt").read_text()
    assert good_text.strip() and bad_text.strip()

    good_overall = _weighted_overall(rubric, _GOOD_SCORES)
    bad_overall = _weighted_overall(rubric, _BAD_SCORES)

    assert good_overall >= threshold > bad_overall
