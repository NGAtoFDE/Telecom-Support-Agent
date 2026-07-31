"""load_session — hydrates conversation memory AND pins the LLM provider for the session.

Provider pinning here (not per call) is README §4.4 rule 1: every downstream node in this
session reasons with the same model, so the verifier does not reject the classifier's work
just because a mid-graph failover swapped the model underneath it.
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.state import TriageState
from telecom_agent.core.types import Message
from telecom_agent.observability.logging import bind


def load_session(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    user_input = state.get("user_input", "")

    provider = deps.router.ensure_session(session_id)
    degraded = deps.router.is_degraded(session_id)

    mem = deps.session_store.load(session_id)
    if user_input:
        deps.session_store.append(session_id, Message(role="user", content=user_input))

    deps.session_store.set_provider(session_id, provider)

    log = bind(
        __name__, trace_id=state.get("trace_id", ""), session_id=session_id, provider=provider.value
    )
    log.info("session loaded; provider pinned", extra={"node": "load_session"})

    return {
        "provider": provider,
        "degraded": degraded,
        "messages": list(mem.messages),
        "customer_ctx": mem.customer_ctx,
        "attempt": 0,
    }
