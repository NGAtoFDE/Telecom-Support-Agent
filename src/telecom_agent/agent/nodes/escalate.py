"""escalate — the safe default. Selects the queue from the declarative routing table,
assembles a handover summary for the human agent, and creates the simulated ticket via
the ticketing tool (the "create_ticket" step of the graph, idempotent by key).

Reached from three places: P1 at classification, empty retrieval, and an exhausted verify
budget. Each sets ``error_code`` upstream so the handover records *why* it escalated.
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.policies.routing import route
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import IssueCategory, Priority, Resolution
from telecom_agent.observability import metrics
from telecom_agent.observability.logging import bind
from telecom_agent.tools.diagnostics import check_outage

_REASONS = {
    "P1_PRIORITY": "High-priority (P1) issue — routed to a human regardless of confidence.",
    "RETRIEVAL_EMPTY": "No approved source scored above the retrieval floor.",
    "GROUNDEDNESS_FAILED": "Answer could not be grounded within the retry budget.",
    "BUDGET_EXCEEDED": "Session token budget exhausted.",
    "ALL_PROVIDERS_DOWN": "Both LLM providers unavailable; classified by fallback rules.",
}


def escalate(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    category = state.get("category", IssueCategory.OTHER)
    priority = state.get("priority", Priority.P4)
    reason_code = state.get("error_code") or (
        "P1_PRIORITY" if priority == Priority.P1 else "GROUNDEDNESS_FAILED"
    )
    log = bind(__name__, trace_id=state.get("trace_id", ""), session_id=session_id, node="escalate")

    queue = route(category, priority)

    # Enrich P1 network cases with a simulated outage check for the NOC handover.
    diag = ""
    if priority == Priority.P1:
        outage = check_outage((state.get("entities") or {}).get("circle"))
        diag = f" Diagnostics: {outage['detail']}"

    summary = (
        f"[{priority.value}/{category.value}] {state.get('user_input', '')[:280]}\n"
        f"Reason for escalation: {_REASONS.get(reason_code, reason_code)}{diag}"
    )
    if state.get("draft"):
        summary += f"\nDraft attempt (for review): {state['draft'][:400]}"

    ticket = deps.ticketing.create_ticket(
        session_id=session_id,
        category=category,
        priority=priority,
        queue=queue,
        summary=summary,
        trace_id=state.get("trace_id", ""),
    )

    metrics.escalations_total.labels(queue=queue.value).inc()
    log.info(
        "escalated", extra={"queue": queue.value, "ticket": ticket.ticket_id, "reason": reason_code}
    )

    jira_ref = ""
    if "(Jira: " in ticket.summary:
        jira_key = ticket.summary.split("(Jira: ")[1].split(")")[0]
        jira_ref = f" (Jira: {jira_key})"

    customer_msg = (
        "I've raised this with our specialist team on your behalf. Your reference is "
        f"{ticket.ticket_id}{jira_ref} (queue: {queue.value}). A human agent will follow up."
    )
    return {
        "resolution": Resolution.ESCALATED,
        "queue": queue,
        "ticket": ticket,
        "answer": customer_msg,
    }
