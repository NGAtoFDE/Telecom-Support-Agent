"""Azure Monitor / OpenTelemetry wiring.

``azure-monitor-opentelemetry`` gives traces, logs and metrics into Application Insights
from effectively one call, plus automatic FastAPI instrumentation. When no connection
string is configured (local dev), telemetry stays as stdout logs — the app runs identically
either way (README §15).
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def configure_azure_monitor(connection_string: str) -> bool:
    """Return True if Azure Monitor was configured, False if skipped (no connection string)."""
    if not connection_string:
        log.info("App Insights connection string empty; telemetry falls back to stdout.")
        return False
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor as _configure

        _configure(connection_string=connection_string)
        log.info("Azure Monitor configured.")
        return True
    except Exception as exc:  # noqa: BLE001 - telemetry must never crash the app
        log.warning("Azure Monitor setup failed, continuing without it: %s", exc)
        return False


def instrument_fastapi(app) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception as exc:  # noqa: BLE001
        log.warning("FastAPI OTel instrumentation skipped: %s", exc)
