"""Ticket endpoints: create (idempotent), read, list."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from telecom_agent.agent.policies.routing import route
from telecom_agent.api.deps import Container, get_container
from telecom_agent.api.schemas.ticket import TicketCreate, TicketOut
from telecom_agent.core.enums import EscalationQueue, Priority, TicketStatus

router = APIRouter(prefix="/v1/tickets", tags=["tickets"])


def _to_out(t) -> TicketOut:
    return TicketOut(
        ticket_id=t.ticket_id,
        session_id=t.session_id,
        category=t.category,
        priority=t.priority,
        queue=t.queue,
        status=t.status,
        summary=t.summary,
        created_at=t.created_at,
    )


@router.post("", response_model=TicketOut)
def create_ticket(
    req: TicketCreate, request: Request, container: Container = Depends(get_container)
) -> TicketOut:
    queue = req.queue or route(req.category, req.priority)
    ticket = container.ticketing.create_ticket(
        session_id=req.session_id,
        category=req.category,
        priority=req.priority,
        queue=queue,
        summary=req.summary,
        trace_id=getattr(request.state, "trace_id", ""),
    )
    return _to_out(ticket)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, container: Container = Depends(get_container)) -> TicketOut:
    ticket = container.ticket_repo.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    return _to_out(ticket)


@router.get("", response_model=list[TicketOut])
def list_tickets(
    container: Container = Depends(get_container),
    queue: EscalationQueue | None = Query(default=None),
    priority: Priority | None = Query(default=None),
    status: TicketStatus | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[TicketOut]:
    tickets = container.ticket_repo.list(queue=queue, priority=priority, status=status, limit=limit)
    return [_to_out(t) for t in tickets]
