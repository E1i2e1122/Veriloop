"""The AutoPilot runtime preflight folder must be absolute, because it is also the agent's working directory."""

from __future__ import annotations

from orchestrator.workflows.autopilot_pipeline import runtime_preflight_dir


def test_runtime_preflight_dir_is_absolute_under_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    preflight_dir = runtime_preflight_dir("autopilot_2026-11-17_18-04-58")

    assert preflight_dir.is_absolute()
    assert preflight_dir == tmp_path / "runs" / "autopilot_2026-11-17_18-04-58-runtime-preflight"
    # The MCP config the agent reads stays inside the folder when resolved from that folder.
    assert (preflight_dir / ".mcp.json").resolve() == tmp_path / "runs" / "autopilot_2026-11-17_18-04-58-runtime-preflight" / ".mcp.json"
