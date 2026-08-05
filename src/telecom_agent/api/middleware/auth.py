"""API-key verification for ``/v1/*``.

Public paths (health, metrics, docs) are exempt so probes and dashboards work without a
key. Everything under ``/v1`` requires a matching ``X-API-Key`` header. The error uses the
same envelope shape as the rest of the API.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_PUBLIC_PREFIXES = ("/healthz", "/readyz", "/metrics", "/docs", "/openapi.json", "/redoc", "/v1/discord")


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path == "/" or path.startswith(_PUBLIC_PREFIXES):
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)

        supplied = request.headers.get("x-api-key", "")
        if supplied != self._api_key:
            trace_id = getattr(request.state, "trace_id", "")
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "missing or invalid X-API-Key",
                        "trace_id": trace_id,
                        "retryable": False,
                    }
                },
            )
        return await call_next(request)
