"""Chat & classify request/response models. Mirrors README §7 response shape exactly."""

from __future__ import annotations

from pydantic import BaseModel, Field

from telecom_agent.api.schemas.common import UsageOut
from telecom_agent.core.enums import IssueCategory, Priority, Provider, Resolution


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)
    customer_ctx: dict | None = None


class CitationOut(BaseModel):
    doc_id: str
    title: str
    section: str
    score: float = 0.0


class LlmInfoOut(BaseModel):
    provider: Provider
    alias: str = "chat-main"
    degraded: bool = False


class TicketBrief(BaseModel):
    ticket_id: str
    queue: str
    priority: str
    status: str


class ChatResponse(BaseModel):
    trace_id: str
    session_id: str
    category: IssueCategory | None = None
    priority: Priority | None = None
    resolution: Resolution
    answer: str
    citations: list[CitationOut] = []
    ticket: TicketBrief | None = None
    llm: LlmInfoOut
    usage: UsageOut
    latency_ms: int = 0


class ClassifyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class ClassifyResponse(BaseModel):
    category: IssueCategory
    priority: Priority
    confidence: float
    entities: dict = {}
