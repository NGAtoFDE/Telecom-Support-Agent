"""clarify — asks one targeted follow-up when the classifier's confidence is below the
floor. This is a terminal turn: the graph returns to the user with a question and resumes
on the next message. Keeping it to a single question avoids an interrogation loop.
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.nodes._shared import node_messages, track_usage
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import Alias, Resolution
from telecom_agent.core.types import TokenUsage
from telecom_agent.observability.logging import bind

_NODE_SYSTEM = (
    "clarify: The issue is ambiguous. Ask exactly one concise clarifying question that "
    "would let you classify and resolve it. Do not attempt an answer yet."
)


def clarify(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    log = bind(__name__, trace_id=state.get("trace_id", ""), session_id=session_id, node="clarify")
    messages = node_messages(
        deps.settings.system_version, _NODE_SYSTEM, state.get("user_input", "")
    )
    usage = TokenUsage()
    try:
        result = deps.router.chat(session_id, messages, alias=Alias.CHAT_MINI, max_tokens=120)
        usage = track_usage("clarify", result)
        question = result.text.strip()
    except Exception as exc:  # noqa: BLE001
        log.warning("clarify LLM failed (%s); using generic prompt", exc)
        question = (
            "Could you share a few more details — your circle/region, whether the "
            "account is prepaid or postpaid, and when the issue started?"
        )

    log.info("clarify question generated")
    return {
        "clarify_question": question,
        "answer": question,
        "resolution": Resolution.NEEDS_INFO,
        "citations": [],
        "token_usage": usage,
    }
