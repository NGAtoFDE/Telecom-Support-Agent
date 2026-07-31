"""Per-key token-bucket rate limiting to protect LLM spend.

In-process and best-effort — right-sized for a single-replica demo. The bucket is keyed by
API key (falling back to client host), refills at a steady rate, and rejects with a 429
using the standard error envelope when empty.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_LIMITED_PREFIX = "/v1"


@dataclass
class _Bucket:
    tokens: float
    last: float


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, rate_per_sec: float = 5.0, burst: int = 20) -> None:
        super().__init__(app)
        self._rate = rate_per_sec
        self._burst = burst
        self._buckets: dict[str, _Bucket] = {}

    def _key(self, request: Request) -> str:
        return request.headers.get("x-api-key") or (
            request.client.host if request.client else "anon"
        )

    def _allow(self, key: str) -> bool:
        now = time.monotonic()
        b = self._buckets.get(key)
        if b is None:
            self._buckets[key] = _Bucket(tokens=self._burst - 1, last=now)
            return True
        b.tokens = min(self._burst, b.tokens + (now - b.last) * self._rate)
        b.last = now
        if b.tokens < 1:
            return False
        b.tokens -= 1
        return True

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(_LIMITED_PREFIX) and not self._allow(self._key(request)):
            trace_id = getattr(request.state, "trace_id", "")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "too many requests",
                        "trace_id": trace_id,
                        "retryable": True,
                    }
                },
            )
        return await call_next(request)
