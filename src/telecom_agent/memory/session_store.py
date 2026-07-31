"""In-process session memory with TTL expiry.

Holds the rolling message window, the synthetic customer context and the pinned provider
for each session. Deliberately in-memory: the demo runs a single API replica, and durable
turn history already lives in SQLite via the turn repository. Swapping this for Redis is a
one-file change behind the same interface.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from telecom_agent.core.enums import Provider
from telecom_agent.core.types import CustomerCtx, Message
from telecom_agent.memory.policy import trim_window


@dataclass
class SessionMemory:
    messages: list[Message] = field(default_factory=list)
    customer_ctx: CustomerCtx = field(default_factory=CustomerCtx)
    provider: Provider | None = None
    last_seen: float = 0.0


class SessionStore:
    def __init__(self, ttl_seconds: int = 3600, clock=time.monotonic) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._data: dict[str, SessionMemory] = {}
        self._lock = threading.Lock()

    def _expire(self) -> None:
        now = self._clock()
        stale = [k for k, v in self._data.items() if now - v.last_seen > self._ttl]
        for k in stale:
            self._data.pop(k, None)

    def load(self, session_id: str) -> SessionMemory:
        with self._lock:
            self._expire()
            mem = self._data.get(session_id)
            if mem is None:
                mem = SessionMemory(last_seen=self._clock())
                self._data[session_id] = mem
            mem.last_seen = self._clock()
            return mem

    def append(self, session_id: str, message: Message, *, max_tokens: int = 3000) -> None:
        with self._lock:
            mem = self._data.setdefault(session_id, SessionMemory())
            mem.messages.append(message)
            mem.messages = trim_window(mem.messages, max_tokens=max_tokens)
            mem.last_seen = self._clock()

    def set_provider(self, session_id: str, provider: Provider) -> None:
        with self._lock:
            mem = self._data.setdefault(session_id, SessionMemory())
            mem.provider = provider
            mem.last_seen = self._clock()

    def set_customer_ctx(self, session_id: str, ctx: CustomerCtx) -> None:
        with self._lock:
            mem = self._data.setdefault(session_id, SessionMemory())
            mem.customer_ctx = ctx
            mem.last_seen = self._clock()
