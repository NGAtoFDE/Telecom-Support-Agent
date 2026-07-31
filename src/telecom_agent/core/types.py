"""Shared domain primitives used across layers.

These are deliberately plain Pydantic models / dataclasses with no behaviour and no
imports from higher layers. They are the vocabulary the whole app speaks.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from telecom_agent.core.enums import (
    EscalationQueue,
    IssueCategory,
    Priority,
    Provider,
    Resolution,
    TicketStatus,
)

Role = Literal["system", "user", "assistant"]


class Message(BaseModel):
    role: Role
    content: str


class CustomerCtx(BaseModel):
    """Synthetic customer context. Never contains real PII."""

    customer_id: str = "anon"
    circle: str | None = None  # telecom "circle" ~ region, e.g. "Maharashtra"
    plan: str | None = None
    device: str | None = None
    account_type: Literal["prepaid", "postpaid"] | None = None


class Chunk(BaseModel):
    """A retrieved piece of an approved KB document, citable by (doc_id, section)."""

    doc_id: str
    title: str
    section: str
    text: str
    score: float = 0.0
    source: Literal["dense", "bm25", "hybrid"] = "hybrid"


class Citation(BaseModel):
    doc_id: str
    title: str
    section: str
    score: float = 0.0


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
        )


class LlmInfo(BaseModel):
    provider: Provider
    alias: str
    model: str = ""
    degraded: bool = False


class Ticket(BaseModel):
    ticket_id: str
    session_id: str
    category: IssueCategory
    priority: Priority
    queue: EscalationQueue
    status: TicketStatus = TicketStatus.OPEN
    summary: str = ""
    idempotency_key: str = ""
    created_at: str = ""


class Classification(BaseModel):
    """Strict-JSON contract the classifier LLM must satisfy (validated with Pydantic)."""

    category: IssueCategory
    priority: Priority
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict = Field(default_factory=dict)


class Verdict(BaseModel):
    """Groundedness verifier output."""

    groundedness: float = Field(ge=0.0, le=1.0)
    supported: bool
    unsupported_claims: list[str] = Field(default_factory=list)


class TurnOutcome(BaseModel):
    """Flattened outcome, convenient for persistence and API serialisation."""

    resolution: Resolution
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)
    ticket: Ticket | None = None
