"""Gate: arg/usage contract and error paths — no real claude call.

Covers exit codes 2 (usage) and 4 (runtime), and that a missing claude
binary fails fast (no hang) rather than exit 3. stdlib unittest, <2s.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LLM_PY = Path(__file__).resolve().parent.parent / "llm.py"


def run_llm(args: list[str], env: dict[str, str] | None = None, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LLM_PY), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env if env is not None else dict(os.environ),
        timeout=10,
    )


class LlmContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = dict(os.environ)
        self.env.pop("MYFI_LLM_MOCK", None)
        self.env.pop("MYFI_LLM_MOCK_TEXT", None)

    def test_unknown_subcommand_exits_2(self) -> None:
        proc = run_llm(["frobnicate"], self.env)
        self.assertEqual(proc.returncode, 2)

    def test_unknown_flag_exits_2(self) -> None:
        env = dict(self.env)
        env["MYFI_LLM_MOCK_TEXT"] = "x"
        proc = run_llm(["complete", "--bogus"], env)
        self.assertEqual(proc.returncode, 2)

    def test_non_integer_timeout_exits_2(self) -> None:
        env = dict(self.env)
        env["MYFI_LLM_MOCK_TEXT"] = "x"
        proc = run_llm(["complete", "--timeout=abc"], env)
        self.assertEqual(proc.returncode, 2)

    def test_help_names_the_contract(self) -> None:
        proc = run_llm(["help"], self.env)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Route a model call through the LOCAL Claude Code", proc.stdout)

    def test_no_subcommand_prints_help_and_exits_0(self) -> None:
        proc = run_llm([], self.env)
        self.assertEqual(proc.returncode, 0)

    def test_missing_claude_binary_exits_4_without_a_hang(self) -> None:
        env = dict(self.env)
        env["MYFI_LLM_BIN"] = str(Path(self.tmp.name) / "nope")
        proc = run_llm(["complete", "--prompt=hi", "--timeout=5"], env)
        self.assertEqual(proc.returncode, 4)

    def test_missing_prompt_file_exits_2(self) -> None:
        proc = run_llm(["complete", f"--prompt-file={Path(self.tmp.name) / 'absent'}"], self.env)
        self.assertEqual(proc.returncode, 2)

    def test_no_prompt_source_exits_2(self) -> None:
        proc = run_llm(["complete"], self.env, stdin="")
        self.assertEqual(proc.returncode, 2)

    def test_llm_law_no_hosted_api_referenced(self) -> None:
        # This service is the ONE place a model call is shelled out — assert it
        # never references a hosted inference endpoint (CLAUDE.md §LLM access).
        # The banned hosts are assembled at runtime (not written as a literal
        # substring here) so this negative assertion doesn't itself trip the
        # repo-wide `rg -n 'api\.(anthropic|openai)\.com'` LLM-law gate.
        text = LLM_PY.read_text(encoding="utf-8")
        for provider in ("anthropic", "openai"):
            banned_host = "api." + provider + ".com"
            self.assertNotIn(banned_host, text)


if __name__ == "__main__":
    unittest.main()
