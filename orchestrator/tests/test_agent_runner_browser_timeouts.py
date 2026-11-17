"""A single browser action timeout is recoverable; only repeated timeouts end the agent session."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from orchestrator.utils.agent_runner import AgentRunner

TIMEOUT = "### Error\nTimeoutError: locator.click: Timeout 10000ms exceeded.\nCall log:\n  - waiting for getByRole('button', { name: 'Log in' })"


def _tool_use(tool_id, name):
    return SimpleNamespace(type="assistant", message=SimpleNamespace(content=[SimpleNamespace(type="tool_use", id=tool_id, name=name, input={})]))


def _tool_result(tool_id, text, is_error=False):
    return SimpleNamespace(
        type="user",
        message=SimpleNamespace(content=[SimpleNamespace(type="tool_result", tool_use_id=tool_id, content=text, is_error=is_error)]),
    )


def _runner(monkeypatch, tmp_path, stream):
    from orchestrator.utils import agent_runner as agent_runner_module

    async def fake_query(**_kwargs):
        for message in stream:
            yield message

    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"playwright-test": {"command": "true", "args": []}}}))
    monkeypatch.setattr(agent_runner_module, "query", fake_query)
    monkeypatch.setattr(agent_runner_module, "ClaudeAgentOptions", lambda **kwargs: kwargs)
    monkeypatch.setattr(agent_runner_module, "get_api_key_rotator", lambda: None)
    return AgentRunner(
        allowed_tools=["mcp__playwright-test__browser_click", "mcp__playwright-test__browser_snapshot"],
        tools=["mcp__playwright-test__browser_click", "mcp__playwright-test__browser_snapshot"],
        log_tools=False,
        session_dir=tmp_path,
        cwd=tmp_path,
        inject_memory=False,
        capture_memory=False,
        force_direct_execution=True,
    )


@pytest.mark.asyncio
async def test_agent_recovers_from_a_single_action_timeout(monkeypatch, tmp_path):
    runner = _runner(
        monkeypatch,
        tmp_path,
        [
            _tool_use("t1", "mcp__playwright-test__browser_click"),
            _tool_result("t1", TIMEOUT, is_error=True),
            _tool_use("t2", "mcp__playwright-test__browser_snapshot"),
            _tool_result("t2", "- button \"Login\" [ref=e12]"),
            SimpleNamespace(type="assistant", message=SimpleNamespace(content=[SimpleNamespace(type="text", text="explored")])),
        ],
    )

    result = await runner.run("explore the shop")

    assert result.success is True
    assert result.output == "explored"
    assert [call.success for call in result.tool_calls] == [False, True]


@pytest.mark.asyncio
async def test_repeated_action_timeouts_still_end_the_session(monkeypatch, tmp_path):
    stream = []
    for i in range(3):
        stream += [_tool_use(f"t{i}", "mcp__playwright-test__browser_click"), _tool_result(f"t{i}", TIMEOUT, is_error=True)]
    stream.append(SimpleNamespace(type="assistant", message=SimpleNamespace(content=[SimpleNamespace(type="text", text="gave up")])))
    runner = _runner(monkeypatch, tmp_path, stream)

    result = await runner.run("explore the shop")

    assert result.success is False
    assert result.error_type == "browser_tool_timeout"
