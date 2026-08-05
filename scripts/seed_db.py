#!/usr/bin/env python
"""Create the schema and load a handful of synthetic demo tickets.

Runs `create_all` then inserts a few tickets through the repository/tool layer so the UI
ticket panel is not empty on first launch. Everything here is synthetic.
"""

from __future__ import annotations

import sys

from telecom_agent.agent.policies.routing import route
from telecom_agent.config.settings import get_settings
from telecom_agent.core.enums import IssueCategory, Priority
from telecom_agent.store.repositories import TicketRepository
from telecom_agent.store.session import create_all, get_sessionmaker
from telecom_agent.tools.ticketing import TicketingTool

# (session_id, category, priority, summary) — synthetic only.
_DEMO = [
    (
        "sess_demo01",
        IssueCategory.NETWORK_COVERAGE,
        Priority.P1,
        "No service since morning across Maharashtra circle; suspected outage.",
    ),
    (
        "sess_demo02",
        IssueCategory.BILLING_DISPUTE,
        Priority.P3,
        "Customer charged twice for the same recharge of Rs 299.",
    ),
    (
        "sess_demo03",
        IssueCategory.SIM_ACTIVATION,
        Priority.P3,
        "New prepaid SIM not activated 48h after KYC.",
    ),
    (
        "sess_demo04",
        IssueCategory.ROAMING,
        Priority.P3,
        "International roaming pack not working in Singapore.",
    ),
    (
        "sess_demo05",
        IssueCategory.DATA_SLOW,
        Priority.P2,
        "Data speeds throttled below 512kbps after FUP dispute.",
    ),
]


def main() -> int:
    settings = get_settings()
    create_all(settings.database_url)
    tool = TicketingTool(TicketRepository(get_sessionmaker()))

    created = 0
    for session_id, category, priority, summary in _DEMO:
        ticket = tool.create_ticket(
            session_id=session_id,
            category=category,
            priority=priority,
            queue=route(category, priority),
            summary=summary,
            trace_id="seed",
        )
        created += 1
        print(f"  {ticket.ticket_id}  {ticket.queue}  {ticket.priority}  {ticket.category}")
    print(f"seeded {created} synthetic demo tickets into {settings.database_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
