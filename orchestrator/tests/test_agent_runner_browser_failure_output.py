"""A finished agent that describes a browser timeout in its summary must not be treated as a dead browser."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from orchestrator.utils.agent_runner import AgentRunner

HEALER_SUMMARY = (
    "strategy: hardened the startup-dialog dismissal in place. While debugging, the browser hit "
    "'Timeout 30000ms exceeded' on the first click because the welcome dialog was still open, so the "
    "test now dismisses it first. The test body and all assertions are unchanged."
)


def _patch_queue(monkeypatch, telemetry):
    from orchestrator.api import settings as settings_api
    from orchestrator.utils import agent_runner as agent_runner_module

    class FakeQueue:
        async def connect(self):
            return None

        async def get_metrics(self):
            return {"workers_alive": 1, "queue_length": 0, "running": 0}

        async def enqueue_task(self, **_kwargs):
            return "agent-task-1"

        async def wait_for_result(self, *_args, **_kwargs):
            return HEALER_SUMMARY

        async def get_task(self, task_id):
            return SimpleNamespace(telemetry=telemetry)

    monkeypatch.setattr(
        settings_api,
        "runtime_env_vars",
        lambda: {"VERILOOP_LLM_PROVIDER": "anthropic", "VERILOOP_LLM_AUTH_MODE": "api_key", "VERILOOP_LLM_API_KEY": "test-key"},
    )
    monkeypatch.setattr(agent_runner_module, "get_agent_queue", lambda: FakeQueue())


@pytest.mark.asyncio
async def test_finished_agent_summary_mentioning_a_browser_timeout_succeeds(monkeypatch):
    _patch_queue(monkeypatch, {"stop_reason": "end_turn"})

    result = await AgentRunner(allowed_tools=[], model_tier="tool_deep")._run_via_queue("heal the test", timeout=5)

    assert result.success is True
    assert result.timed_out is False
    assert result.output == HEALER_SUMMARY


@pytest.mark.asyncio
async def test_output_of_an_unfinished_session_is_still_checked_for_browser_failures(monkeypatch):
    _patch_queue(monkeypatch, {})

    result = await AgentRunner(allowed_tools=[], model_tier="tool_deep")._run_via_queue("heal the test", timeout=5)

    assert result.success is False
    assert result.error_type == "browser_tool_timeout"


@pytest.mark.asyncio
async def test_explicit_browser_error_still_fails_a_finished_session(monkeypatch):
    _patch_queue(monkeypatch, {"stop_reason": "end_turn", "last_browser_error": "Target page, context or browser has been closed"})

    result = await AgentRunner(allowed_tools=[], model_tier="tool_deep")._run_via_queue("heal the test", timeout=5)

    assert result.success is False
    assert result.error_type == "browser_session_closed"
