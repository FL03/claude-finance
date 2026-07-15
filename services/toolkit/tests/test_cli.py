"""Gate tests for myfi_toolkit.cli -- deterministic, mock-free, <2s.

Exercises the argparse dispatcher directly against the two behaviors named in
the v0.0.0 plan's [ACCEPTANCE] predicate for W2-toolkit-scaffold: `version`
prints a semver and exits 0, and an unknown subcommand exits 2 (argparse's own
`parser.error()` path via `add_subparsers(required=True)`).
"""

from __future__ import annotations

import re

import pytest

from myfi_toolkit import __version__, cli

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def test_version_matches_package_version() -> None:
    assert _SEMVER.match(__version__), f"myfi_toolkit.__version__ is not a semver: {__version__!r}"


def test_version_prints_semver_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["version"])
    out = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert _SEMVER.match(out), f"expected a semver string on stdout, got {out!r}"


def test_unknown_subcommand_exits_two() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["frobnicate"])
    assert excinfo.value.code == 2


def test_no_subcommand_exits_two() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])
    assert excinfo.value.code == 2


def test_stats_subcommand_registered() -> None:
    # Confirms the `stats` subcommand parses without invoking its handler
    # (which lazy-imports numpy/pandas) -- parser construction alone must stay
    # on the fast, stdlib-only path.
    parser = cli.build_parser()
    args = parser.parse_args(["stats"])
    assert args.handler is cli._cmd_stats
