"""Duplicate ticket creation in the same hour returns the original ticket."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from telecom_agent.core.enums import EscalationQueue, IssueCategory, Priority
from telecom_agent.store.repositories import TicketRepository
from telecom_agent.store.session import create_all, get_sessionmaker
from telecom_agent.tools.ticketing import TicketingTool


@pytest.fixture
def ticketing():
    tmp = Path(tempfile.mkdtemp(prefix="teleco_tkt_"))
    url = "sqlite:///" + str(tmp / "t.db").replace("\\", "/")
    create_all(url)
    return TicketingTool(TicketRepository(get_sessionmaker()))


def test_duplicate_create_returns_same_ticket(ticketing):
    kw = {
        "session_id": "sess_abc",
        "category": IssueCategory.DATA_SLOW,
        "priority": Priority.P2,
        "queue": EscalationQueue.NOC_L2,
        "summary": "slow data",
    }
    first = ticketing.create_ticket(**kw)
    second = ticketing.create_ticket(**kw)
    assert first.ticket_id == second.ticket_id
    assert first.idempotency_key == second.idempotency_key


def test_different_category_makes_new_ticket(ticketing):
    a = ticketing.create_ticket(
        session_id="sess_x",
        category=IssueCategory.DATA_SLOW,
        priority=Priority.P2,
        queue=EscalationQueue.NOC_L2,
        summary="s",
    )
    b = ticketing.create_ticket(
        session_id="sess_x",
        category=IssueCategory.BILLING_DISPUTE,
        priority=Priority.P3,
        queue=EscalationQueue.BILLING_OPS,
        summary="s",
    )
    assert a.ticket_id != b.ticket_id
