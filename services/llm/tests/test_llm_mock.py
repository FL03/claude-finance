"""Gate: the mock seam returns the staged payload verbatim, and NEVER touches
the claude binary -- proved by pointing MYFI_LLM_BIN at a script that fails
loudly if it is ever invoked. stdlib unittest, <2s, no network, no real LLM.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LLM_PY = Path(__file__).resolve().parent.parent / "llm.py"


def run_llm(args: list[str], env: dict[str, str], stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LLM_PY), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


class LlmMockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_path = Path(self.tmp.name)

        # A binary that, if ever called, makes the test fail unmistakably.
        self.sentinel_bin = tmp_path / "should-never-run"
        self.sentinel_bin.write_text("#!/bin/sh\necho REAL_CLAUDE_WAS_CALLED >&2\nexit 99\n")
        self.sentinel_bin.chmod(self.sentinel_bin.stat().st_mode | stat.S_IEXEC)

        self.base_env = dict(os.environ)
        self.base_env["MYFI_LLM_BIN"] = str(self.sentinel_bin)
        self.base_env.pop("MYFI_LLM_MOCK", None)
        self.base_env.pop("MYFI_LLM_MOCK_TEXT", None)

        self.mock_file = tmp_path / "mock.json"
        self.mock_file.write_text('{"scores":{"x":4}}\n')

    def test_mock_from_file(self) -> None:
        env = dict(self.base_env)
        env["MYFI_LLM_MOCK"] = str(self.mock_file)
        proc = run_llm(["complete", "--prompt=ignored"], env)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, '{"scores":{"x":4}}\n')

    def test_mock_from_inline_text(self) -> None:
        env = dict(self.base_env)
        env["MYFI_LLM_MOCK_TEXT"] = "HELLO_MOCK"
        proc = run_llm(["complete"], env, stdin="")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "HELLO_MOCK\n")

    def test_mock_short_circuits_without_a_prompt(self) -> None:
        env = dict(self.base_env)
        env["MYFI_LLM_MOCK"] = str(self.mock_file)
        proc = run_llm(["complete"], env, stdin="")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, '{"scores":{"x":4}}\n')

    def test_ping_reports_mock_mode(self) -> None:
        env = dict(self.base_env)
        env["MYFI_LLM_MOCK"] = str(self.mock_file)
        proc = run_llm(["ping"], env)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("MOCK mode active", proc.stdout)

    def test_missing_mock_file_is_a_hard_error(self) -> None:
        env = dict(self.base_env)
        env["MYFI_LLM_MOCK"] = str(Path(self.tmp.name) / "absent.json")
        proc = run_llm(["complete", "--prompt=x"], env)
        self.assertEqual(proc.returncode, 4)
        self.assertIn("MYFI_LLM_MOCK file not found", proc.stderr)


if __name__ == "__main__":
    unittest.main()
