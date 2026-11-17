"""LLM-testing provider requests must not send sampling parameters to models that reject them."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from orchestrator.services.llm_provider import LlmProviderClient, ProviderConfig


def _client(model_id: str, calls: list[dict]) -> LlmProviderClient:
    async def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=2),
        )

    client = LlmProviderClient(ProviderConfig(base_url="https://llm.example.test/v1", api_key="test-key", model_id=model_id))
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return client


def test_temperature_is_left_out_for_models_that_reject_it():
    calls: list[dict] = []
    response = asyncio.run(_client("claude-haiku-5-5", calls).call([{"role": "user", "content": "hi"}], temperature=0.0))

    assert response.error is None
    assert response.output == "ok"
    assert "temperature" not in calls[0]
    assert calls[0]["max_tokens"] > 0


def test_temperature_is_sent_to_models_that_accept_it():
    calls: list[dict] = []
    asyncio.run(_client("gpt-4o-mini", calls).call([{"role": "user", "content": "hi"}], temperature=0.2))

    assert calls[0]["temperature"] == 0.2


def test_health_check_works_for_models_that_reject_temperature():
    calls: list[dict] = []
    result = asyncio.run(_client("claude-sonnet-5-5", calls).health_check())

    assert result["healthy"] is True
    assert "temperature" not in calls[0]
