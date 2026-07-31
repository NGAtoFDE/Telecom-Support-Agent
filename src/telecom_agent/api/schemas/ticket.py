"""Ticket request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from telecom_agent.core.enums import EscalationQueue, IssueCategory, Priority, TicketStatus


class TicketCreate(BaseModel):
    session_id: str
    category: IssueCategory
    priority: Priority
    queue: EscalationQueue | None = None  # if omitted, routing table decides
    summary: str = Field(default="", max_length=2000)


class TicketOut(BaseModel):
    ticket_id: str
    session_id: str
    category: IssueCategory
    priority: Priority
    queue: EscalationQueue
    status: TicketStatus
    summary: str
    created_at: str = ""


class EscalationInfo(BaseModel):
    queue: EscalationQueue
    reason: str = ""
