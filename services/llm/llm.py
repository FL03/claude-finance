#!/usr/bin/env python3
"""services/llm/llm.py -- the myfi LLM service.

A self-contained service that routes every model call through the LOCAL Claude
Code in headless print mode (``claude -p``). Per CLAUDE.md: the software we
build never calls a hosted inference API -- it shells out to the local Claude
Code. Every other service (services/eval, agents, commands, hooks) calls THIS
contract, never ``claude`` directly, so there is exactly one place that owns
the model invocation, the timeout, the model default, and the mock seam.

Standalone by design (services-first / parallel-safe): stdlib only, reads only
its own env vars plus one optional best-effort layer -- the [llm].model key in
.claude/myfi.toml, read through myfi_toolkit.config when that sibling package
happens to be importable (see _default_model() below). That lookup is soft:
if myfi_toolkit can't be imported (a bare `python3 services/llm/llm.py` with
no sibling checkout, a stripped-down deployment, anything at all), this
degrades straight back to the env-var-or-hardcoded-default behavior this
service has always had -- so a second session can still work anywhere else in
the repo without colliding here, and this service never hard-depends on
another service's package. Timeout still comes from a flag/env only, never
myfi.toml -- there is no [llm].timeout key.

Ported from shepherd's ``services/llm/llm.sh`` ("Python over bash" lesson,
discovery-harvest): Python's own ``subprocess.run(..., timeout=...)`` replaces
bash's hand-rolled watchdog (macOS ships no ``timeout`` binary) with a single
keyword argument, and is exact where the bash version was an approximation.

── Contract ──────────────────────────────────────────────────────────────────
  llm.py complete [--prompt-file=F | --prompt=TXT | -]  \\
                   [--system-file=F | --system=TXT]      \\
                   [--model=ALIAS] [--timeout=SEC]
      Prompt source precedence: --prompt-file > --prompt > stdin.
      Prints the model's raw text response to stdout. Nothing else on stdout.
  llm.py ping            Verify the claude binary is reachable (no completion).
  llm.py help

── Env ─────────────────────────────────────────────────────────────────────
  MYFI_LLM_BIN        claude binary (default: claude)
  MYFI_LLM_MODEL      default model alias, wins over .claude/myfi.toml's
                       [llm].model (default: opus -- best by default, per
                       CLAUDE.md; never silently downgrade for cost). See
                       _default_model() -- the myfi.toml lookup is best-effort.
  MYFI_LLM_TIMEOUT    default timeout seconds (default: 120)
  MYFI_LLM_MOCK       path to a file whose contents `complete` returns
                       verbatim, short-circuiting the claude call. The seam
                       that makes downstream gate tests deterministic + free.
  MYFI_LLM_MOCK_TEXT  inline mock string (used when MYFI_LLM_MOCK is unset)

── Exit codes ──────────────────────────────────────────────────────────────
  0 ok · 2 usage · 3 timeout · 4 runtime error
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

DEFAULT_MODEL = "opus"
DEFAULT_TIMEOUT = 120

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_TIMEOUT = 3
EXIT_RUNTIME = 4

PROG = "llm.py"


def _die(message: str, code: int = EXIT_RUNTIME) -> int:
    print(f"{PROG}: {message}", file=sys.stderr)
    return code


def _default_model() -> str:
    """Resolve the default model: MYFI_LLM_MODEL env > [llm].model in
    .claude/myfi.toml (via myfi_toolkit.config, best-effort) > DEFAULT_MODEL.

    The env check happens first and short-circuits before any import is
    attempted -- when MYFI_LLM_MODEL is set, that's authoritative and this
    never touches myfi_toolkit at all. Otherwise it appends the sibling
    services/toolkit directory to sys.path and imports myfi_toolkit.config;
    if that import (or the lookup itself) fails for any reason -- no sibling
    checkout, no tomllib, anything -- this silently falls back to
    DEFAULT_MODEL, exactly this service's original behavior. The
    local-Claude-Code routing in cmd_complete() is unaffected either way.
    """
    env_value = os.environ.get("MYFI_LLM_MODEL")
    if env_value:
        return env_value
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        toolkit_src = os.path.normpath(os.path.join(here, "..", "toolkit"))
        if toolkit_src not in sys.path:
            sys.path.append(toolkit_src)
        from myfi_toolkit import config as _myfi_config

        return _myfi_config.llm_model()
    except Exception:
        return DEFAULT_MODEL


def _resolve_mock() -> str | None:
    """Return the mock payload if a mock is configured, else None.

    Mirrors the bash service's ``_emit_mock_if_set``: file wins over inline
    text; a configured-but-missing mock file is a hard error (exit 4), not a
    silent fall-through to a real call.
    """
    mock_file = os.environ.get("MYFI_LLM_MOCK")
    if mock_file:
        if not os.path.isfile(mock_file):
            raise FileNotFoundError(mock_file)
        with open(mock_file, encoding="utf-8") as fh:
            return fh.read()
    mock_text = os.environ.get("MYFI_LLM_MOCK_TEXT")
    if mock_text:
        return mock_text + "\n"
    return None


def cmd_complete(args: argparse.Namespace) -> int:
    # Mock short-circuits before resolving the prompt source at all -- gate
    # tests don't need a prompt to assert the harness around the call.
    try:
        mock = _resolve_mock()
    except FileNotFoundError as exc:
        return _die(f"MYFI_LLM_MOCK file not found: {exc}", EXIT_RUNTIME)
    if mock is not None:
        sys.stdout.write(mock)
        return EXIT_OK

    # Resolve the prompt: --prompt-file > --prompt > stdin.
    if args.prompt_file:
        if not os.path.isfile(args.prompt_file):
            return _die(f"--prompt-file not found: {args.prompt_file}", EXIT_USAGE)
        with open(args.prompt_file, encoding="utf-8") as fh:
            prompt_text = fh.read()
    elif args.prompt is not None:
        prompt_text = args.prompt
    else:
        prompt_text = sys.stdin.read()
        if not prompt_text.strip():
            return _die(
                "no prompt: pass --prompt-file, --prompt, or pipe via stdin",
                EXIT_USAGE,
            )

    # Resolve the (optional) system prompt: --system-file > --system.
    system_text: str | None = None
    if args.system_file:
        if not os.path.isfile(args.system_file):
            return _die(f"--system-file not found: {args.system_file}", EXIT_USAGE)
        with open(args.system_file, encoding="utf-8") as fh:
            system_text = fh.read()
    elif args.system is not None:
        system_text = args.system

    binary = os.environ.get("MYFI_LLM_BIN", "claude")
    cmd = [binary, "-p", "--output-format", "text", "--model", args.model]
    if system_text:
        cmd += ["--append-system-prompt", system_text]

    try:
        proc = subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    except FileNotFoundError:
        return _die(f"claude binary not found: {binary} (set MYFI_LLM_BIN)", EXIT_RUNTIME)
    except subprocess.TimeoutExpired:
        return _die(f"completion timed out after {args.timeout}s", EXIT_TIMEOUT)

    if proc.returncode != 0:
        for line in proc.stderr.splitlines():
            print(f"  claude: {line}", file=sys.stderr)
        return _die(f"claude exited {proc.returncode}", EXIT_RUNTIME)

    sys.stdout.write(proc.stdout)
    return EXIT_OK


def cmd_ping(_args: argparse.Namespace) -> int:
    if os.environ.get("MYFI_LLM_MOCK") or os.environ.get("MYFI_LLM_MOCK_TEXT"):
        print(f"{PROG}: MOCK mode active (no claude call)")
        return EXIT_OK
    binary = os.environ.get("MYFI_LLM_BIN", "claude")
    if shutil.which(binary) is None:
        return _die(f"claude binary not found: {binary}", EXIT_RUNTIME)
    version = "?"
    try:
        probe = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        version = probe.stdout.strip() or version
    except (OSError, subprocess.TimeoutExpired):
        pass
    model = _default_model()
    print(f"{PROG}: claude reachable -- {version}; default model={model}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Route a model call through the LOCAL Claude Code.",
        epilog=(
            "Env: MYFI_LLM_BIN (default claude) · MYFI_LLM_MODEL (default opus, or "
            "[llm].model in .claude/myfi.toml) · MYFI_LLM_TIMEOUT (default 120s)\n"
            "     MYFI_LLM_MOCK=<file> / MYFI_LLM_MOCK_TEXT=<str> -- return verbatim, "
            "short-circuiting the claude call.\n"
            "Exit: 0 ok · 2 usage · 3 timeout · 4 llm/runtime error"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_complete = sub.add_parser("complete", help="Complete a prompt via the local Claude Code.")
    p_complete.add_argument("--prompt-file", dest="prompt_file", default=None)
    p_complete.add_argument("--prompt", dest="prompt", default=None)
    p_complete.add_argument("--system-file", dest="system_file", default=None)
    p_complete.add_argument("--system", dest="system", default=None)
    p_complete.add_argument("--model", dest="model", default=_default_model())
    p_complete.add_argument(
        "--timeout",
        dest="timeout",
        type=int,
        default=int(os.environ.get("MYFI_LLM_TIMEOUT", DEFAULT_TIMEOUT)),
    )
    # A bare '-' explicitly marks stdin -- identical to the default fallback,
    # accepted for parity with the ported bash contract.
    p_complete.add_argument("stdin_marker", nargs="?", default=None, help=argparse.SUPPRESS)

    sub.add_parser("ping", help="Verify the claude binary is reachable (no completion).")
    sub.add_parser("help", help="Show this help.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "help"):
        parser.print_help()
        return EXIT_OK
    if args.command == "complete":
        return cmd_complete(args)
    if args.command == "ping":
        return cmd_ping(args)
    return _die(f"unknown subcommand: {args.command} (try: complete | ping | help)", EXIT_USAGE)


if __name__ == "__main__":
    sys.exit(main())
