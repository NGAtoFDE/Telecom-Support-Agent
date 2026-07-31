"""Shared response models: the single error envelope, token usage, pagination, feedback."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    trace_id: str = ""
    retryable: bool = False


class ErrorEnvelope(BaseModel):
    """Identical everywhere, so the UI has exactly one error code path."""

    error: ErrorBody


class UsageOut(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    est_cost_usd: float = 0.0


class Pagination(BaseModel):
    limit: int = 100
    count: int = 0


class FeedbackRequest(BaseModel):
    trace_id: str
    session_id: str = ""
    thumbs: str = Field(pattern="^(up|down)$")
    comment: str = ""


class FeedbackResponse(BaseModel):
    id: int
    accepted: bool = True
