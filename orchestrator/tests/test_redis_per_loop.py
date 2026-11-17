"""Queue singletons must keep a separate Redis client for each event loop that uses them."""

from __future__ import annotations

import asyncio

from orchestrator.services import agent_queue
from orchestrator.services.redis_per_loop import LoopLocalRedisMixin


class _Holder(LoopLocalRedisMixin):
    def __init__(self):
        self._redis = None  # allowed outside an event loop, like the queues' __init__


def test_each_event_loop_sees_only_its_own_client():
    holder = _Holder()
    loop_a, loop_b = asyncio.new_event_loop(), asyncio.new_event_loop()

    async def set_client(name):
        holder._redis = name
        return holder._redis

    async def read_client():
        return holder._redis

    try:
        assert loop_a.run_until_complete(set_client("client-a")) == "client-a"
        assert loop_b.run_until_complete(read_client()) is None
        assert loop_b.run_until_complete(set_client("client-b")) == "client-b"
        assert loop_a.run_until_complete(read_client()) == "client-a"
    finally:
        loop_a.close()
        loop_b.close()

    assert holder._redis is None  # outside any event loop


def test_agent_queue_connects_once_per_event_loop(monkeypatch):
    created = []

    class FakeRedis:
        async def ping(self):
            return True

        async def close(self):
            return None

    def fake_from_url(*args, **kwargs):
        client = FakeRedis()
        created.append(client)
        return client

    monkeypatch.setattr(agent_queue.aioredis, "from_url", fake_from_url)
    queue = agent_queue.AgentQueue("redis://example.test:6379/0")

    async def connect_twice():
        await queue.connect()
        first = queue._redis
        await queue.connect()
        return first, queue._redis

    first, second = asyncio.run(connect_twice())
    assert first is second  # one client per loop
    other, _ = asyncio.run(connect_twice())
    assert other is not first  # a new loop gets its own client
    assert len(created) == 2
