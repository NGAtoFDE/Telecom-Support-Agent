"""Generates and propagates ``trace_id`` on every request.

The id is taken from an inbound ``X-Trace-Id`` header if present (so a UI-initiated id can
follow a request end to end) or minted here, then attached to ``request.state`` and echoed
on the response so logs, spans and DB rows all correlate.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from telecom_agent.core.utils import new_trace_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("x-trace-id") or new_trace_id()
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response
