"""Fail-fast behaviour of the Temporal client while the server is unreachable."""

import pytest
from temporalio.client import Client

from orchestrator.services import temporal_client


@pytest.fixture(autouse=True)
def _reset_unreachable_state(monkeypatch):
    monkeypatch.setattr(temporal_client, "_unreachable_until", 0.0)
    monkeypatch.setattr(temporal_client, "_unreachable_message", None)


def _patch_connect(monkeypatch, outcomes):
    """Replace Client.connect with a stub that returns or raises the given outcomes in order."""
    calls = []

    async def fake_connect(cls, *args, **kwargs):
        calls.append((args, kwargs))
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(Client, "connect", classmethod(fake_connect))
    return calls


async def test_unreachable_server_fails_fast_within_retry_window(monkeypatch):
    calls = _patch_connect(monkeypatch, [ConnectionError("connection refused")])

    with pytest.raises(temporal_client.TemporalUnavailableError):
        await temporal_client._connect_client()
    with pytest.raises(temporal_client.TemporalUnavailableError) as second:
        await temporal_client._connect_client()

    # The second call is answered from the retry window without another connect attempt.
    assert len(calls) == 1
    assert "not reachable" in str(second.value)


async def test_connection_is_retried_after_window_and_success_clears_state(monkeypatch):
    connected = object()
    calls = _patch_connect(monkeypatch, [ConnectionError("connection refused"), connected])

    with pytest.raises(temporal_client.TemporalUnavailableError):
        await temporal_client._connect_client()

    # Simulate the retry window elapsing.
    monkeypatch.setattr(temporal_client, "_unreachable_until", 0.0)

    assert await temporal_client._connect_client() is connected
    assert len(calls) == 2
    assert temporal_client._unreachable_message is None
