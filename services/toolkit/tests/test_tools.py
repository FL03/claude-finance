"""Gate tests for myfi_toolkit.tools — deterministic, mock-free, <2s.

`tools.py` is the declared single source of truth for the toolkit's capability
surface (`CAPABILITIES`, `describe_toolkit()`), shared by the CLI's implicit
self-description and the MCP `describe_toolkit` tool. It had no direct payload
test before this file — the MCP smoke test only checked tool registration, not
the content of the payload itself.
"""

from __future__ import annotations

from myfi_toolkit import __version__, tools


def test_describe_toolkit_returns_documented_keys() -> None:
    payload = tools.describe_toolkit()
    assert set(payload) == {"name", "version", "capabilities"}
    assert payload["name"] == "myfi-toolkit"
    assert payload["version"] == __version__
    assert isinstance(payload["capabilities"], list)
    assert payload["capabilities"], "capabilities list must not be empty"
    assert all(isinstance(item, str) and item for item in payload["capabilities"])


def test_describe_toolkit_capabilities_have_no_delivery_wave_labels() -> None:
    """Shipped verbs (db, quote) must not be tagged with an internal delivery-wave
    label like "Wave 3" in the agent-facing payload -- that misdescribes a live,
    shipped feature as deferred to a caller with no visibility into the roadmap.
    """
    payload = tools.describe_toolkit()
    for capability in payload["capabilities"]:
        assert "Wave" not in capability, f"capability string leaks a delivery-wave label: {capability!r}"


def test_describe_stats_returns_non_empty_string() -> None:
    summary = tools.describe_stats()
    assert isinstance(summary, str)
    assert summary.strip()
    for expected in ("numpy", "pandas", "scipy"):
        assert expected in summary
