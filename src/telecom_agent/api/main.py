"""FastAPI app factory: lifespan (build container, configure logging + telemetry),
middleware stack, router registration and a single error-envelope exception handler.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from telecom_agent.api.deps import build_container
from telecom_agent.api.middleware.auth import ApiKeyMiddleware
from telecom_agent.api.middleware.logging import AccessLogMiddleware
from telecom_agent.api.middleware.rate_limit import RateLimitMiddleware
from telecom_agent.api.middleware.request_id import RequestIdMiddleware
from telecom_agent.api.routers import chat, classify, discord, feedback, health, tickets
from telecom_agent.config.settings import get_settings
from telecom_agent.core.errors import AppError
from telecom_agent.observability.logging import configure_logging
from telecom_agent.observability.telemetry import configure_azure_monitor, instrument_fastapi


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, json_logs=settings.app_env != "local")
    configure_azure_monitor(settings.applicationinsights_connection_string)
    app.state.container = build_container(settings)
    yield
    # nothing to tear down: SQLite + in-process stores close with the process


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Telecom Support Agent",
        version="0.1.0",
        description="Network issue triage & escalation (Azure AI Foundry primary, Groq failover).",
        lifespan=lifespan,
    )

    # middleware runs bottom-to-top on the request path; register outermost last.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(ApiKeyMiddleware, api_key=settings.api_key)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    instrument_fastapi(app)

    for r in (chat.router, classify.router, discord.router, tickets.router, feedback.router, health.router):
        app.include_router(r)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):  # noqa: ANN001
        trace_id = getattr(request.state, "trace_id", "")
        return JSONResponse(
            status_code=exc.http_status if exc.http_status >= 400 else 500,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "trace_id": trace_id,
                    "retryable": exc.retryable,
                }
            },
        )

    @app.get("/")
    def root() -> dict:
        return {"service": "telecom-support-agent", "docs": "/docs", "health": "/healthz"}

    return app


app = create_app()
