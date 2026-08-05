"""Simulated ticketing tool: create / read / escalate, idempotent by construction.

Idempotency key is ``sha256(session_id + category + hour_bucket)`` (README §6): a retried
escalation in the same hour returns the existing ticket rather than creating a second.
"""

from __future__ import annotations

from telecom_agent.core.enums import EscalationQueue, IssueCategory, Priority, TicketStatus
from telecom_agent.core.types import Ticket
from telecom_agent.core.utils import idempotency_key, new_ticket_id, utcnow_iso
from telecom_agent.store.repositories import TicketRepository
from telecom_agent.tools.validators import (
    clean_text,
    coerce_category,
    coerce_priority,
    coerce_queue,
)


from telecom_agent.tools.jira_client import JiraClient

class TicketingTool:
    def __init__(self, repo: TicketRepository, jira_client: JiraClient | None = None) -> None:
        self._repo = repo
        self._jira_client = jira_client

    def create_ticket(
        self,
        *,
        session_id: str,
        category: str | IssueCategory,
        priority: str | Priority,
        queue: str | EscalationQueue,
        summary: str,
        trace_id: str = "",
    ) -> Ticket:
        category = coerce_category(category)
        priority = coerce_priority(priority)
        queue = coerce_queue(queue)
        key = idempotency_key(session_id, str(category))
        ticket = Ticket(
            ticket_id=new_ticket_id(),
            session_id=session_id,
            category=category,
            priority=priority,
            queue=queue,
            status=TicketStatus.OPEN,
            summary=clean_text(summary),
            idempotency_key=key,
            created_at=utcnow_iso(),
        )
        created = self._repo.create(ticket, trace_id=trace_id)

        # Create issue in Jira
        if self._jira_client:
            jira_desc = f"Session ID: {session_id}\nTrace ID: {trace_id}\nPriority: {priority.value}\nCategory: {category.value}\n\nSummary:\n{summary}"
            issue_key = self._jira_client.create_issue(
                summary=f"[{priority.value}] {category.value} Escalation",
                description=jira_desc
            )
            if issue_key:
                # Update the ticket summary locally with the Jira issue key
                created.summary = f"(Jira: {issue_key}) " + created.summary

        return created

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        return self._repo.get(ticket_id)

    def escalate_ticket(self, ticket_id: str, queue: str | EscalationQueue) -> Ticket | None:
        # In this simulation escalation is captured at creation via the routing table;
        # this hook exists for re-routing an existing ticket if a human overrides.
        return self._repo.get(ticket_id)
