"""verify — checks every claim in the draft maps to a retrieved chunk (groundedness).

Uses ``chat-mini`` (cheaper, and the verifier task is simpler than generation — README
§18 cost lever). Increments the retry counter so the edge function can bound the loop:
grounded → respond; not grounded and attempts left → retrieve again; budget exhausted →
escalate with the draft attached for a human.
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.nodes._shared import (
    extract_json,
    format_context,
    node_messages,
    track_usage,
)
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import Alias
from telecom_agent.core.types import TokenUsage, Verdict
from telecom_agent.observability import metrics
from telecom_agent.observability.logging import bind
from telecom_agent.prompts import registry


def verify(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    log = bind(__name__, trace_id=state.get("trace_id", ""), session_id=session_id, node="verify")
    context = format_context(state.get("retrieved", []))
    draft = state.get("draft", "")

    node_system = registry.render(
        "verifier", deps.settings.verifier_version, context=context, draft=draft
    )
    messages = node_messages(deps.settings.system_version, node_system, draft)

    groundedness = 0.0
    usage = TokenUsage()
    try:
        result = deps.router.chat(session_id, messages, alias=Alias.CHAT_MINI, json_mode=True)
        usage = track_usage("verify", result)
        verdict = Verdict.model_validate(extract_json(result.text))
        groundedness = verdict.groundedness
    except Exception as exc:  # noqa: BLE001 - a failed verifier is treated as not grounded
        log.warning("verifier failed (%s); treating as not grounded", exc)

    provider = state.get("provider")
    metrics.groundedness_score.labels(provider=provider.value if provider else "unknown").observe(
        groundedness
    )

    attempt = state.get("attempt", 0) + 1
    log.info("verified", extra={"groundedness": groundedness, "attempt": attempt})
    return {
        "groundedness": groundedness,
        "attempt": attempt,
        "error_code": "GROUNDEDNESS_FAILED",
        "token_usage": usage,
    }
