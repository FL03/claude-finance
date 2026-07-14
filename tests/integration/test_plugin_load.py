#!/usr/bin/env python3
"""tests/integration/test_plugin_load.py -- plugin-load structural gate.

W7-integration-close [SPEC] item 1: every agent/skill/command the plugin ships
must auto-discover. Confirms every `agents/*.md`, `skills/*/SKILL.md`, and
`commands/*.md` file carries a well-formed `---`-delimited frontmatter block
with a non-empty `name:` and `description:`, `.mcp.json` parses as JSON and
registers the `myfi-toolkit` server at the locked command path, and the
Wave-1 relocation invariant holds (`src/` stays gone).

Stdlib-only -- no PyYAML. This repo carries no YAML dependency anywhere (see
`rg -n 'import yaml'`, zero hits), and every frontmatter block this plugin
ships is a flat `key: value` list, simple enough for a hand-rolled regex
check rather than pulling in a parser for it. No mock seam needed -- nothing
in this module calls an LLM. <1s, no network.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
_NAME_RE = re.compile(r"^name:\s*(\S.*)$", re.MULTILINE)
_DESCRIPTION_RE = re.compile(r"^description:\s*(\S.*)$", re.MULTILINE)


def _frontmatter(path: Path) -> str:
    """Return the raw text between the opening/closing `---` delimiters.

    Raises ``AssertionError`` naming the offending path -- not a bare regex
    failure -- so a broken component is legible straight from the test output.
    """
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    assert match, f"{path}: does not open with a well-formed '---'-delimited frontmatter block"
    return match.group(1)


def _assert_valid_frontmatter(path: Path) -> None:
    fm = _frontmatter(path)
    name_match = _NAME_RE.search(fm)
    assert name_match and name_match.group(1).strip(), f"{path}: frontmatter missing a non-empty 'name:'"
    desc_match = _DESCRIPTION_RE.search(fm)
    assert desc_match and desc_match.group(1).strip(), (
        f"{path}: frontmatter missing a non-empty 'description:'"
    )


class AgentsLoadTests(unittest.TestCase):
    def test_every_agent_has_valid_frontmatter(self) -> None:
        agent_files = sorted((REPO_ROOT / "agents").glob("*.md"))
        self.assertGreaterEqual(
            len(agent_files), 6, "expected the full six-agent flock under agents/*.md"
        )
        for path in agent_files:
            with self.subTest(agent=path.name):
                _assert_valid_frontmatter(path)


class SkillsLoadTests(unittest.TestCase):
    def test_every_skill_has_valid_frontmatter(self) -> None:
        skill_files = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
        self.assertGreaterEqual(
            len(skill_files), 4, "expected myfi + improve + compliance + taxes under skills/*/SKILL.md"
        )
        for path in skill_files:
            with self.subTest(skill=path.parent.name):
                _assert_valid_frontmatter(path)


class CommandsLoadTests(unittest.TestCase):
    def test_every_command_has_valid_frontmatter(self) -> None:
        command_files = sorted((REPO_ROOT / "commands").glob("*.md"))
        self.assertGreaterEqual(
            len(command_files), 4, "expected analyze/plan/taxes/trade under commands/*.md"
        )
        for path in command_files:
            with self.subTest(command=path.name):
                _assert_valid_frontmatter(path)


class McpManifestTests(unittest.TestCase):
    def test_mcp_json_parses_and_registers_the_toolkit_server(self) -> None:
        mcp_path = REPO_ROOT / ".mcp.json"
        with mcp_path.open(encoding="utf-8") as fh:
            manifest = json.load(fh)
        command = manifest.get("mcpServers", {}).get("myfi-toolkit", {}).get("command")
        self.assertEqual(
            command,
            "${CLAUDE_PLUGIN_ROOT}/bin/myfi-mcp",
            ".mcp.json must register myfi-toolkit -> ${CLAUDE_PLUGIN_ROOT}/bin/myfi-mcp",
        )


class RelocationInvariantTests(unittest.TestCase):
    def test_no_src_directory(self) -> None:
        self.assertFalse(
            (REPO_ROOT / "src").is_dir(), "src/ must stay gone (Wave 1 relocation invariant)"
        )


if __name__ == "__main__":
    unittest.main()
