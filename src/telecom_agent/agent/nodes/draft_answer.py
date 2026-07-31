"""draft_answer — generates grounded troubleshooting steps that cite chunk ids only.

Uses ``chat-main`` and the citation-mandatory answer prompt. The retrieved context is the
only source the model is given; the system prompt forbids uncited claims. The citations
attached to state are narrowed in ``respond`` to just the docs actually referenced.
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.nodes._shared import format_context, node_messages, track_usage
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import Alias
from telecom_agent.core.errors import ProviderError
from telecom_agent.observability.logging import bind
from telecom_agent.prompts import registry


def draft_answer(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    log = bind(
        __name__, trace_id=state.get("trace_id", ""), session_id=session_id, node="draft_answer"
    )
    context = format_context(state.get("retrieved", []))

    node_system = registry.render(
        "answer",
        deps.settings.answer_version,
        user_input=state.get("user_input", ""),
        context=context,
    )
    messages = node_messages(deps.settings.system_version, node_system, state.get("user_input", ""))

    try:
        result = deps.router.chat(session_id, messages, alias=Alias.CHAT_MAIN, max_tokens=500)
    except ProviderError as exc:
        # Generation failed and cannot be retried into grounding — force escalation by
        # exhausting the verify budget so the next edge routes to a human.
        log.warning("draft generation failed (%s); forcing escalation", exc)
        return {
            "draft": "",
            "attempt": deps.thresholds.max_verify_attempts,
            "error_code": "GROUNDEDNESS_FAILED",
        }

    usage = track_usage("draft_answer", result)
    log.info("draft generated", extra={"attempt": state.get("attempt", 0)})
    return {"draft": result.text.strip(), "token_usage": usage}
