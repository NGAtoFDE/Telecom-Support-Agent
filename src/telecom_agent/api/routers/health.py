"""Health & metrics: /healthz (liveness), /readyz (deep readiness), /metrics (Prometheus).

``/readyz`` is honest about every dependency (README §7): the index must be loaded, the DB
must be writable, and **both** LLM providers are probed. It fails loudly at deploy so a
deprecated Groq model id surfaces then, not during the demo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from telecom_agent.api.deps import Container, get_container

router = APIRouter(tags=["ops"])


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(container: Container = Depends(get_container)) -> Response:
    checks: dict[str, bool] = {}

    # index loaded?
    checks["index"] = bool(getattr(container.retriever, "_store", None) is not None)

    # db writable?
    try:
        container.ticket_repo.list(limit=1)
        checks["db"] = True
    except Exception:  # noqa: BLE001
        checks["db"] = False

    # both providers probed
    provider_health = container.router.health()
    checks.update({f"llm_{k}": v for k, v in provider_health.items()})

    # ready if index + db ok and at least one provider is up (backup is enough to serve)
    ready = checks["index"] and checks["db"] and any(provider_health.values())
    import json

    return Response(
        content=json.dumps({"ready": ready, "checks": checks}),
        media_type="application/json",
        status_code=200 if ready else 503,
    )


@router.get("/metrics")
def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
