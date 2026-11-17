"""Per-event-loop Redis clients for queue singletons that are used from several event loops."""

from __future__ import annotations

import asyncio
import weakref
from typing import Any


class LoopLocalRedisMixin:
    """Give a class a ``_redis`` attribute that holds one client per running event loop.

    The API process uses the queue singletons from its main event loop and from worker
    threads that run their own loops (``asyncio.run``). A redis.asyncio client belongs to
    the loop that created it: sharing one across loops fails with "attached to a different
    loop" and lets two threads use the same connection at the same time.
    """

    @property
    def _redis(self) -> Any:
        clients = self.__dict__.get("_redis_clients_by_loop")
        if clients is None:
            return None
        try:
            return clients.get(asyncio.get_running_loop())
        except RuntimeError:  # no running event loop
            return None

    @_redis.setter
    def _redis(self, client: Any) -> None:
        clients = self.__dict__.setdefault("_redis_clients_by_loop", weakref.WeakKeyDictionary())
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            if client is None:
                return  # nothing to clear outside an event loop, e.g. in __init__
            raise
        if client is None:
            clients.pop(loop, None)
        else:
            clients[loop] = client
