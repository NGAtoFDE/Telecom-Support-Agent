"""POST /v1/classify — classification only. Used by evals and the UI debug drawer.

Runs the classify node directly (no retrieval/answer), so it is cheap and side-effect free.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from telecom_agent.agent.nodes.classify import classify as classify_node
from telecom_agent.agent.state import TriageState
from telecom_agent.api.deps import Container, get_container
from telecom_agent.api.schemas.chat import ClassifyRequest, ClassifyResponse
from telecom_agent.core.types import TokenUsage
from telecom_agent.core.utils import new_session_id

router = APIRouter(prefix="/v1", tags=["classify"])


@router.post("/classify", response_model=ClassifyResponse)
def classify(
    req: ClassifyRequest, request: Request, container: Container = Depends(get_container)
) -> ClassifyResponse:
    session_id = req.session_id or new_session_id()
    state: TriageState = {
        "session_id": session_id,
        "trace_id": getattr(request.state, "trace_id", ""),
        "user_input": req.message,
        "token_usage": TokenUsage(),
    }
    out = classify_node(state, container.agent_deps)
    return ClassifyResponse(
        category=out["category"],
        priority=out["priority"],
        confidence=out["confidence"],
        entities=out.get("entities", {}),
    )
