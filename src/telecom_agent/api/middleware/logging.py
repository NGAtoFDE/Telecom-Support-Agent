"""Structured access log: one JSON line per request with method, path, status, latency
and trace_id. Uses a monotonic clock so latency is unaffected by wall-clock changes."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from telecom_agent.observability.logging import bind


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        latency_ms = int((time.monotonic() - start) * 1000)
        bind(
            "telecom_agent.access",
            trace_id=getattr(request.state, "trace_id", ""),
        ).info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": latency_ms,
            },
        )
        response.headers["X-Response-Time-ms"] = str(latency_ms)
        return response
