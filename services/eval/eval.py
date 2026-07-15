#!/usr/bin/env python3
"""services/eval/eval.py -- the myfi eval harness.

Scores a LATENT agent output (an advisor recommendation, a plan, a trade
thesis, a skill's own orientation, …) against a rubric, using the
local-Claude-Code judge in ``services/llm`` (see ``services/llm/llm.py``).
This is the behavioral eval half of CLAUDE.md's "tests + evals, same commit"
rule -- the plugin's latent instructions get a real judge, not just
gate-tested storage.

The latent/deterministic split this plugin teaches, applied to itself:

  LATENT (the model owns it):   the per-dimension 1..scale scores + rationale.
  DETERMINISTIC (code owns it): the rubric, the judge-prompt build, the
                                 weighted overall, the threshold verdict, the
                                 exit code. Same scores in => same verdict out.

Pure + stateless: reads a rubric + an input, returns a verdict. It does not
touch a DB -- that is myctx's job (Wave 3) via a caller that resolves subjects
and records verdicts. This stays a clean function so it is trivially testable
with a mocked judge (``MYFI_LLM_MOCK``).

Ported from shepherd's ``services/eval/eval.sh`` ("Python over bash" lesson,
discovery-harvest): the ``jq``-based JSON extraction/validation/weighting
becomes plain ``json`` + arithmetic, with no external dependency.

── Contract ──────────────────────────────────────────────────────────────────
  eval.py run --kind=K [--input-file=F | --input=TXT | -]  \\
              [--threshold=N] [--model=ALIAS] [--timeout=SEC] [--json|--md|--text]
      Score the input against rubrics/K.rubric.json. Default format: text.
      --json prints ONLY the machine verdict (the record-able artifact).
  eval.py rubrics            List available rubric kinds.
  eval.py show <kind>        Print a rubric.
  eval.py help

── Exit codes ──────────────────────────────────────────────────────────────
  0 pass · 1 fail (below threshold) · 2 usage · 4 judge / parse error

── Env ─────────────────────────────────────────────────────────────────────
  MYFI_EVAL_LLM    override path to the llm.py this shells to (default:
                   services/llm/llm.py next to this file's parent).
  MYFI_EVAL_LIVE   when "1", strips MYFI_LLM_MOCK / MYFI_LLM_MOCK_TEXT before
                   shelling to llm.py -- a stray mock from a parent shell must
                   not make the live judge lane a lie.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

PROG = "eval.py"

RUBRIC_DIR = Path(__file__).resolve().parent / "rubrics"
DEFAULT_LLM_PATH = Path(__file__).resolve().parent.parent / "llm" / "llm.py"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_JUDGE = 4


class UsageError(Exception):
    """A caller error: bad flags, missing rubric, missing input."""


class JudgeError(Exception):
    """The judge call failed, or its response could not be parsed/validated."""


def _die(message: str, code: int) -> int:
    print(f"{PROG}: {message}", file=sys.stderr)
    return code


# ── rubric access ──────────────────────────────────────────────────────────


def validate_rubric(rubric: dict, kind: str) -> None:
    """Validate rubric structure so a malformed rubric fails as a documented
    JudgeError (-> exit 4), not an uncaught KeyError/ZeroDivisionError escaping
    to a raw traceback (exit 1).

    Checks: "scale" is a positive number; "dimensions" is a non-empty list;
    every dimension is an object with a "key", a numeric "weight", and a
    "desc"; and the dimension weights do not sum to zero (which would make
    compute_verdict's overall a division by zero).
    """
    scale = rubric.get("scale")
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or scale <= 0:
        raise JudgeError(f"rubric '{kind}' has missing or invalid 'scale' (must be a positive number)")

    dims = rubric.get("dimensions")
    if not isinstance(dims, list) or not dims:
        raise JudgeError(f"rubric '{kind}' has no dimensions (missing or empty 'dimensions' list)")

    seen_keys: set[str] = set()
    for i, dim in enumerate(dims):
        label = f"dimension #{i}"
        if not isinstance(dim, dict):
            raise JudgeError(f"rubric '{kind}' {label} is not an object")
        if "key" not in dim or not isinstance(dim["key"], str) or not dim["key"]:
            raise JudgeError(f"rubric '{kind}' {label} is missing a non-empty 'key'")
        label = f"dimension '{dim['key']}'"
        if dim["key"] in seen_keys:
            raise JudgeError(f"rubric '{kind}' has duplicate dimension key '{dim['key']}'")
        seen_keys.add(dim["key"])
        if "weight" not in dim:
            raise JudgeError(f"rubric '{kind}' {label} is missing required 'weight'")
        weight = dim["weight"]
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise JudgeError(f"rubric '{kind}' {label} has a non-numeric 'weight'")
        if weight < 0:
            raise JudgeError(f"rubric '{kind}' {label} has a negative 'weight'")
        if "desc" not in dim or not isinstance(dim["desc"], str) or not dim["desc"]:
            raise JudgeError(f"rubric '{kind}' {label} is missing a non-empty 'desc'")

    total_weight = sum(dim["weight"] for dim in dims)
    if total_weight == 0:
        raise JudgeError(f"rubric '{kind}' dimension weights sum to 0 (need at least one weight > 0)")


def load_rubric(kind: str, rubric_dir: Path | None = None) -> dict:
    rubric_dir = rubric_dir or RUBRIC_DIR
    path = rubric_dir / f"{kind}.rubric.json"
    if not path.is_file():
        raise UsageError(f"no rubric for kind '{kind}' (try: {PROG} rubrics)")
    try:
        with open(path, encoding="utf-8") as fh:
            rubric = json.load(fh)
    except json.JSONDecodeError as exc:
        raise JudgeError(f"rubric '{kind}' is not valid JSON: {exc}") from exc
    validate_rubric(rubric, kind)
    return rubric


def list_rubrics(rubric_dir: Path | None = None) -> list[tuple[str, str]]:
    rubric_dir = rubric_dir or RUBRIC_DIR
    out: list[tuple[str, str]] = []
    for path in sorted(rubric_dir.glob("*.rubric.json")):
        kind = path.name[: -len(".rubric.json")]
        subject = ""
        try:
            with open(path, encoding="utf-8") as fh:
                subject = json.load(fh).get("subject", "")
        except (OSError, json.JSONDecodeError):
            pass
        out.append((kind, subject[:80]))
    return out


# ── judge-prompt build (deterministic -- reproducible from the rubric) ───────


def build_judge_prompt(rubric: dict, item: str) -> tuple[str, str]:
    scale = rubric["scale"]
    dims = rubric["dimensions"]
    subject = rubric.get("subject", "")
    guidance = rubric.get("guidance", "")
    keys = ", ".join(d["key"] for d in dims)
    dims_text = "\n".join(f"- {d['key']} (1..{scale}): {d['desc']}" for d in dims)

    system = (
        "You are a strict, calibrated evaluation judge for the myfi plugin. "
        f"Score the SUBJECT against each rubric dimension on an integer scale of "
        f"1..{scale} (1=poor, {scale}=excellent). Use the full range and default LOW "
        "when evidence is weak. Output ONLY a single JSON object and nothing else -- "
        'no prose, no markdown fences. Shape: {"scores":{<dimension>:<int>,...},'
        '"rationale":"<=160 chars"}. '
        f"Include exactly these dimension keys: {keys}."
    )
    prompt = (
        f"SUBJECT TYPE: {subject}\n\n"
        f"RUBRIC (score each dimension 1..{scale}):\n{dims_text}\n\n"
        f"GUIDANCE: {guidance}\n\n"
        f"=== ITEM TO EVALUATE (between the markers) ===\n<<<\n{item}\n>>>\n\n"
        "Return the JSON object now."
    )
    return system, prompt


# ── judge response parsing ──────────────────────────────────────────────────


def extract_json(raw: str) -> dict:
    """Extract a JSON object from a model response that may carry fences or prose.

    Tier 1: parse as-is. Tier 2: strip ``` fences. Tier 3: slice first { to last }.
    """
    candidates = [raw.strip()]
    fenced = raw.replace("```json", "").replace("```", "").strip()
    candidates.append(fenced)
    start, end = fenced.find("{"), fenced.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(fenced[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise JudgeError(f"judge did not return parseable JSON:\n{raw}")


def compute_verdict(
    rubric: dict,
    scores: dict,
    rationale: str = "",
    *,
    threshold: int | None,
    model: str,
    kind: str,
) -> dict:
    """The deterministic half: validate scores, compute the weighted overall.

    overall = round(100 * sum(score * weight) / (scale * sum(weight)))

    Rounding is round-half-up (``floor(x + 0.5)``), matching the ported bash
    harness's jq arithmetic exactly rather than Python's round-half-to-even.

    Validates rubric structure first (a caller that built ``rubric`` by hand
    rather than via ``load_rubric`` -- e.g. a test -- gets the same JudgeError
    on a malformed shape, never a raw KeyError/ZeroDivisionError).
    """
    validate_rubric(rubric, kind)
    scale = rubric["scale"]
    dims = rubric["dimensions"]
    if threshold is None:
        threshold = rubric.get("threshold", 60)

    missing = [d["key"] for d in dims if d["key"] not in scores]
    if missing:
        raise JudgeError(f"missing dimension score(s) in judge output: {', '.join(missing)}")

    nonnumeric = [
        d["key"]
        for d in dims
        if isinstance(scores[d["key"]], bool) or not isinstance(scores[d["key"]], (int, float))
    ]
    if nonnumeric:
        raise JudgeError(f"non-numeric dimension score(s): {', '.join(nonnumeric)}")

    out_of_range = [d["key"] for d in dims if not (1 <= scores[d["key"]] <= scale)]
    if out_of_range:
        raise JudgeError(f"dimension score out of range 1..{scale}: {', '.join(out_of_range)}")

    total_weight = sum(d["weight"] for d in dims)
    if total_weight == 0:  # pragma: no cover -- validate_rubric above already rejects this
        raise JudgeError(f"rubric '{kind}' dimension weights sum to 0 (need at least one weight > 0)")
    weighted_sum = sum(scores[d["key"]] * d["weight"] for d in dims)
    overall = math.floor(100 * weighted_sum / (scale * total_weight) + 0.5)

    return {
        "kind": kind,
        "model": model,
        "overall": overall,
        "threshold": threshold,
        "passed": overall >= threshold,
        "scale": scale,
        "scores": {d["key"]: scores[d["key"]] for d in dims},
        "rationale": rationale,
    }


# ── the judge call (the only model seam -- shells to services/llm/llm.py) ────


def run_judge(
    system: str,
    prompt: str,
    *,
    model: str | None = None,
    timeout: int | None = None,
    llm_path: Path | None = None,
    strip_mock: bool = False,
) -> str:
    llm_path = llm_path or DEFAULT_LLM_PATH
    cmd = [sys.executable, str(llm_path), "complete", f"--system={system}"]
    if model:
        cmd.append(f"--model={model}")
    if timeout:
        cmd.append(f"--timeout={timeout}")

    env = dict(os.environ)
    if strip_mock:
        env.pop("MYFI_LLM_MOCK", None)
        env.pop("MYFI_LLM_MOCK_TEXT", None)

    proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise JudgeError(f"judge call failed (llm.py exit {proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def evaluate(
    kind: str,
    item: str,
    *,
    threshold: int | None = None,
    model: str | None = None,
    timeout: int | None = None,
    rubric_dir: Path | None = None,
    llm_path: Path | None = None,
    live: bool = False,
) -> dict:
    """Score ``item`` against ``rubrics/<kind>.rubric.json``. Raises on error."""
    if not item or not item.strip():
        raise UsageError("nothing to evaluate (empty input)")

    rubric = load_rubric(kind, rubric_dir)
    system, prompt = build_judge_prompt(rubric, item)
    used_model = model or os.environ.get("MYFI_LLM_MODEL", "opus")

    resp = run_judge(system, prompt, model=model, timeout=timeout, llm_path=llm_path, strip_mock=live)
    parsed = extract_json(resp)
    scores = parsed.get("scores") or {}
    if not isinstance(scores, dict):
        raise JudgeError("judge output 'scores' is not an object")
    rationale = parsed.get("rationale", "")

    return compute_verdict(rubric, scores, rationale, threshold=threshold, model=used_model, kind=kind)


# ── CLI ──────────────────────────────────────────────────────────────────────


def _resolve_item(args: argparse.Namespace) -> str:
    if args.input_file:
        if not os.path.isfile(args.input_file):
            raise UsageError(f"--input-file not found: {args.input_file}")
        with open(args.input_file, encoding="utf-8") as fh:
            return fh.read()
    if args.input is not None:
        return args.input
    item = sys.stdin.read()
    if not item.strip():
        raise UsageError("nothing to evaluate (empty input)")
    return item


def _emit(result: dict, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(result))
        return
    verdict = "PASS" if result["passed"] else "FAIL"
    if fmt == "md":
        print(
            f"**EVAL `{result['kind']}`** -- score **{result['overall']}/100** "
            f"(threshold {result['threshold']}) -- {verdict} · model `{result['model']}`\n"
        )
        for key, value in result["scores"].items():
            print(f"- {key}: {value}/{result['scale']}")
        print(f"\n_{result['rationale']}_")
    else:
        print(
            f"EVAL {result['kind']} -- score={result['overall']}/100 "
            f"threshold={result['threshold']} {verdict}  model={result['model']}"
        )
        scored = "  ".join(f"{k}={v}/{result['scale']}" for k, v in result["scores"].items())
        print(f"  {scored}")
        print(f"  rationale: {result['rationale']}")


def cmd_run(args: argparse.Namespace) -> int:
    try:
        item = _resolve_item(args)
        result = evaluate(
            args.kind,
            item,
            threshold=args.threshold,
            model=args.model,
            timeout=args.timeout,
            live=(os.environ.get("MYFI_EVAL_LIVE") == "1"),
        )
    except UsageError as exc:
        return _die(str(exc), EXIT_USAGE)
    except JudgeError as exc:
        return _die(str(exc), EXIT_JUDGE)

    _emit(result, args.fmt)
    return EXIT_OK if result["passed"] else EXIT_FAIL


def cmd_rubrics(_args: argparse.Namespace) -> int:
    rubrics = list_rubrics()
    for kind, subject in rubrics:
        print(f"{kind:<14} {subject}")
    return EXIT_OK


def cmd_show(args: argparse.Namespace) -> int:
    if not args.kind:
        return _die("show needs a <kind>", EXIT_USAGE)
    try:
        rubric = load_rubric(args.kind)
    except UsageError as exc:
        return _die(str(exc), EXIT_USAGE)
    except JudgeError as exc:
        return _die(str(exc), EXIT_JUDGE)
    print(json.dumps(rubric, indent=2))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Rubric-driven quality eval of a latent agent output.",
        epilog="Exit: 0 pass · 1 fail (below threshold) · 2 usage · 4 judge/parse error",
    )
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="Score an input against a rubric.")
    p_run.add_argument("--kind", dest="kind", default=None)
    p_run.add_argument("--input-file", dest="input_file", default=None)
    p_run.add_argument("--input", dest="input", default=None)
    p_run.add_argument("--threshold", dest="threshold", type=int, default=None)
    p_run.add_argument("--model", dest="model", default=None)
    p_run.add_argument("--timeout", dest="timeout", type=int, default=None)
    fmt_group = p_run.add_mutually_exclusive_group()
    fmt_group.add_argument("--json", dest="fmt", action="store_const", const="json")
    fmt_group.add_argument("--md", dest="fmt", action="store_const", const="md")
    fmt_group.add_argument("--text", dest="fmt", action="store_const", const="text")
    p_run.set_defaults(fmt="text")
    p_run.add_argument("stdin_marker", nargs="?", default=None, help=argparse.SUPPRESS)

    sub.add_parser("rubrics", help="List available rubric kinds.")
    p_show = sub.add_parser("show", help="Print a rubric.")
    p_show.add_argument("kind", nargs="?", default=None)

    sub.add_parser("help", help="Show this help.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "help"):
        parser.print_help()
        return EXIT_OK
    if args.command == "run":
        if not args.kind:
            return _die("run needs --kind=<rubric>", EXIT_USAGE)
        return cmd_run(args)
    if args.command == "rubrics":
        return cmd_rubrics(args)
    if args.command == "show":
        return cmd_show(args)
    return _die(f"unknown subcommand: {args.command} (try: run | rubrics | show | help)", EXIT_USAGE)


if __name__ == "__main__":
    sys.exit(main())
