"""Gate: the [llm].model key in .claude/myfi.toml reaches the actual `claude`
invocation through myfi_toolkit.config -- and MYFI_LLM_MODEL still wins over
it, per the documented precedence (explicit arg > env > myfi.toml > default).

No real claude call: MYFI_LLM_BIN points at a recording stub that echoes its
own argv and exits 0, so `cmd_complete`'s constructed command line (including
the `--model` value) is directly observable in stdout without a mock (the
mock seam short-circuits before `--model` is ever built, so it can't be used
to observe this). stdlib unittest, <2s, no network, no real LLM, never
touches the repo's own .claude/myfi.toml or .myfi/ (every test runs in its
own tmp dir with cwd/PWD pointed at it).
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
TOOLKIT_CONFIG = (
    Path(__file__).resolve().parent.parent.parent / "toolkit" / "myfi_toolkit" / "config.py"
)


def run_llm(
    args: list[str],
    env: dict[str, str],
    cwd: Path,
    stdin: str | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LLM_PY), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd),
        timeout=10,
    )


def _write_toml(root: Path, content: str) -> None:
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "myfi.toml").write_text(content)


def _make_recording_claude(tmp_path: Path) -> Path:
    """A fake `claude` binary that prints its own argv (space-joined) to
    stdout and exits 0 -- never a real completion, but the resolved --model
    value is directly visible in the output `cmd_complete` writes verbatim.
    """
    stub = tmp_path / "fake-claude"
    stub.write_text('#!/bin/sh\necho "ARGV:$@"\nexit 0\n')
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return stub


class LlmConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = Path(self.tmp.name)
        self.fake_claude = _make_recording_claude(self.tmp_path)

        self.env = dict(os.environ)
        self.env["PWD"] = str(self.tmp_path)
        self.env["MYFI_LLM_BIN"] = str(self.fake_claude)
        self.env.pop("MYFI_LLM_MOCK", None)
        self.env.pop("MYFI_LLM_MOCK_TEXT", None)
        self.env.pop("MYFI_LLM_MODEL", None)

    def test_toolkit_config_module_exists_and_is_importable_standalone(self) -> None:
        # Sanity: the sibling config module this service optionally imports
        # actually exists at the path _default_model() computes relative to
        # __file__ -- guards against the two services drifting apart on
        # directory layout (services/llm and services/toolkit as siblings).
        self.assertTrue(TOOLKIT_CONFIG.is_file())

    def test_model_resolves_from_toml_when_env_unset(self) -> None:
        _write_toml(self.tmp_path, "[llm]\nmodel = 'claude-toml-model'\n")

        proc = run_llm(["complete", "--prompt=hi"], self.env, cwd=self.tmp_path)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("--model", proc.stdout)
        self.assertIn("claude-toml-model", proc.stdout)

    def test_env_wins_over_toml_model(self) -> None:
        _write_toml(self.tmp_path, "[llm]\nmodel = 'claude-toml-model'\n")
        env = dict(self.env)
        env["MYFI_LLM_MODEL"] = "claude-env-model"

        proc = run_llm(["complete", "--prompt=hi"], env, cwd=self.tmp_path)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("claude-env-model", proc.stdout)
        self.assertNotIn("claude-toml-model", proc.stdout)

    def test_missing_toml_falls_back_to_hardcoded_default_model(self) -> None:
        # No .claude/myfi.toml anywhere under self.tmp_path.
        proc = run_llm(["complete", "--prompt=hi"], self.env, cwd=self.tmp_path)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("--model opus", proc.stdout)

    def test_malformed_toml_falls_back_to_default_model_without_crashing(self) -> None:
        _write_toml(self.tmp_path, "= invalid =\n")

        proc = run_llm(["complete", "--prompt=hi"], self.env, cwd=self.tmp_path)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("--model opus", proc.stdout)

    def test_ping_reports_the_toml_resolved_model(self) -> None:
        _write_toml(self.tmp_path, "[llm]\nmodel = 'claude-toml-model'\n")

        proc = run_llm(["ping"], self.env, cwd=self.tmp_path)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("default model=claude-toml-model", proc.stdout)

    def test_falls_back_to_default_when_no_sibling_toolkit_checkout(self) -> None:
        # The standalone-resilience property the module docstring promises:
        # exercise _default_model()'s `except -> DEFAULT_MODEL` branch by running
        # a COPY of llm.py from a dir with NO sibling services/toolkit, so the
        # best-effort `from myfi_toolkit import config` import genuinely fails.
        # A [llm].model toml is present but must be IGNORED, since the import
        # that would read it can't resolve without the sibling package.
        import shutil

        lone_dir = self.tmp_path / "lone"
        lone_dir.mkdir()
        lone_llm = lone_dir / "llm.py"
        shutil.copyfile(LLM_PY, lone_llm)
        _write_toml(lone_dir, "[llm]\nmodel = 'claude-should-be-ignored'\n")

        env = dict(self.env)
        env["PWD"] = str(lone_dir)
        env.pop("PYTHONPATH", None)  # myfi_toolkit must only be reachable via the (absent) sibling

        proc = subprocess.run(
            [sys.executable, str(lone_llm), "complete", "--prompt=hi"],
            input=None,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(lone_dir),
            timeout=10,
        )

        self.assertEqual(proc.returncode, 0)
        self.assertIn("--model opus", proc.stdout)
        self.assertNotIn("claude-should-be-ignored", proc.stdout)

    def test_local_claude_code_routing_is_unchanged(self) -> None:
        # Regression guard for the LLM law (CLAUDE.md / skills/myfi/SKILL.md):
        # wiring config into the model default must not change *how* the
        # local claude binary is invoked -- still `-p --output-format text
        # --model <alias>`, nothing that looks like a hosted API call.
        _write_toml(self.tmp_path, "[llm]\nmodel = 'claude-toml-model'\n")

        proc = run_llm(["complete", "--prompt=hi"], self.env, cwd=self.tmp_path)

        self.assertEqual(proc.returncode, 0)
        self.assertIn("-p --output-format text --model claude-toml-model", proc.stdout)
        for provider in ("anthropic", "openai"):
            self.assertNotIn("api." + provider + ".com", proc.stdout)


if __name__ == "__main__":
    unittest.main()
