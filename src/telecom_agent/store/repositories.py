"""Query methods — the only place raw ORM queries are allowed.

Repositories take a ``sessionmaker`` and open a short-lived unit of work per method, so
callers never hold a Session across an LLM call (that is how SQLite locks pile up).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from telecom_agent.core.enums import EscalationQueue, Priority, TicketStatus
from telecom_agent.core.types import Ticket
from telecom_agent.store.models import FeedbackRow, SessionRow, TicketRow, TurnRow


class TicketRepository:
    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def get_by_idempotency(self, key: str) -> Ticket | None:
        with self._sm() as s:
            row = s.scalar(select(TicketRow).where(TicketRow.idempotency_key == key))
            return _to_ticket(row) if row else None

    def create(self, ticket: Ticket, trace_id: str = "") -> Ticket:
        """Idempotent create: if the key already exists, return the existing ticket."""
        existing = self.get_by_idempotency(ticket.idempotency_key)
        if existing:
            return existing
        with self._sm() as s:
            row = TicketRow(
                ticket_id=ticket.ticket_id,
                session_id=ticket.session_id,
                trace_id=trace_id,
                category=str(ticket.category),
                priority=str(ticket.priority),
                queue=str(ticket.queue),
                status=str(ticket.status),
                summary=ticket.summary,
                idempotency_key=ticket.idempotency_key,
            )
            s.add(row)
            s.commit()
            s.refresh(row)
            return _to_ticket(row)

    def get(self, ticket_id: str) -> Ticket | None:
        with self._sm() as s:
            row = s.get(TicketRow, ticket_id)
            return _to_ticket(row) if row else None

    def list(
        self,
        *,
        queue: EscalationQueue | None = None,
        priority: Priority | None = None,
        status: TicketStatus | None = None,
        limit: int = 100,
    ) -> list[Ticket]:
        with self._sm() as s:
            stmt = select(TicketRow).order_by(TicketRow.created_at.desc())
            if queue:
                stmt = stmt.where(TicketRow.queue == str(queue))
            if priority:
                stmt = stmt.where(TicketRow.priority == str(priority))
            if status:
                stmt = stmt.where(TicketRow.status == str(status))
            rows = s.scalars(stmt.limit(limit)).all()
            return [_to_ticket(r) for r in rows]


class TurnRepository:
    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def add(self, **fields: object) -> int:
        with self._sm() as s:
            row = TurnRow(**fields)
            s.add(row)
            s.commit()
            s.refresh(row)
            return row.id

    def list_for_session(self, session_id: str) -> list[TurnRow]:
        with self._sm() as s:
            return list(
                s.scalars(
                    select(TurnRow)
                    .where(TurnRow.session_id == session_id)
                    .order_by(TurnRow.created_at)
                ).all()
            )


class SessionRepository:
    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def upsert(self, session_id: str, provider: str = "", customer_ctx: dict | None = None) -> None:
        with self._sm() as s:
            row = s.get(SessionRow, session_id)
            if row is None:
                row = SessionRow(session_id=session_id)
                s.add(row)
            if provider:
                row.provider = provider
            if customer_ctx is not None:
                row.customer_ctx = customer_ctx
            s.commit()

    def get(self, session_id: str) -> SessionRow | None:
        with self._sm() as s:
            return s.get(SessionRow, session_id)


class FeedbackRepository:
    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def add(
        self, *, trace_id: str, session_id: str, thumbs: str, comment: str, provider: str
    ) -> int:
        with self._sm() as s:
            row = FeedbackRow(
                trace_id=trace_id,
                session_id=session_id,
                thumbs=thumbs,
                comment=comment,
                provider=provider,
            )
            s.add(row)
            s.commit()
            s.refresh(row)
            return row.id


def _to_ticket(row: TicketRow) -> Ticket:
    return Ticket(
        ticket_id=row.ticket_id,
        session_id=row.session_id,
        category=row.category,
        priority=row.priority,
        queue=row.queue,
        status=row.status,
        summary=row.summary,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )
