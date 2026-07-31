"""POST /v1/feedback — thumbs up/down + free text, keyed to trace_id (README §14)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from telecom_agent.api.deps import Container, get_container
from telecom_agent.api.schemas.common import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/v1", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(
    req: FeedbackRequest, container: Container = Depends(get_container)
) -> FeedbackResponse:
    # provider is looked up from the session's current pin for later slice-by-provider analysis
    provider = ""
    try:
        provider = container.router.provider_for(req.session_id).value if req.session_id else ""
    except Exception:  # noqa: BLE001
        provider = ""
    fid = container.feedback_repo.add(
        trace_id=req.trace_id,
        session_id=req.session_id,
        thumbs=req.thumbs,
        comment=req.comment,
        provider=provider,
    )
    return FeedbackResponse(id=fid, accepted=True)
