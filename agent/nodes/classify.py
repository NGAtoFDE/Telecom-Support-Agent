"""classify — turns the customer utterance into (category, priority, confidence, entities).

Robustness ladder (README §6):
1. LLM call on ``chat-mini`` asking for strict JSON.
2. Malformed JSON → one repair prompt.
3. Still malformed, or all providers down → deterministic rule-based keyword classifier,
   which guarantees the graph always produces *something* and never crashes a turn.

Also runs the injection scanner; a hit is logged and the text is still classified (the
scope fence and tool-arg validators are what actually contain injection).
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.nodes._shared import extract_json, node_messages, track_usage
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import Alias, IssueCategory, Priority
from telecom_agent.core.errors import AllProvidersDown
from telecom_agent.core.types import Classification, TokenUsage
from telecom_agent.llm.guards import scan_for_injection
from telecom_agent.llm.providers.fake import _classify as _keyword_classify  # reuse rules
from telecom_agent.observability import metrics
from telecom_agent.observability.logging import bind
from telecom_agent.prompts import registry


def _rule_based(user_input: str) -> Classification:
    cat, pri, conf = _keyword_classify(user_input)
    return Classification(category=cat, priority=pri, confidence=min(conf, 0.6), entities={})


def classify(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    user_input = state.get("user_input", "")
    log = bind(__name__, trace_id=state.get("trace_id", ""), session_id=session_id, node="classify")

    injection_hits = scan_for_injection(user_input)
    if injection_hits:
        log.warning("prompt-injection patterns detected", extra={"hits": injection_hits})

    node_system = registry.render(
        "classifier",
        deps.settings.classifier_version,
        categories=", ".join(c.value for c in IssueCategory),
        priorities=", ".join(p.value for p in Priority),
        user_input=user_input,
    )
    messages = node_messages(deps.settings.system_version, node_system, user_input)

    classification: Classification | None = None
    providers_down = False
    usage = TokenUsage()
    try:
        result = deps.router.chat(session_id, messages, alias=Alias.CHAT_MINI, json_mode=True)
        usage = usage.add(track_usage("classify", result))
        try:
            classification = Classification.model_validate(extract_json(result.text))
        except Exception:  # noqa: BLE001 - one repair attempt
            from telecom_agent.core.types import Message

            repair = messages + [
                Message(
                    role="user",
                    content="Your previous reply was not valid JSON. "
                    "Reply with ONLY the JSON object described.",
                )
            ]
            result2 = deps.router.chat(session_id, repair, alias=Alias.CHAT_MINI, json_mode=True)
            usage = usage.add(track_usage("classify", result2))
            classification = Classification.model_validate(extract_json(result2.text))
    except AllProvidersDown:
        log.error("all providers down; using rule-based classifier")
        classification = _rule_based(user_input)
        providers_down = True
    except Exception as exc:  # noqa: BLE001
        log.warning("classification failed (%s); using rule-based fallback", exc)
        prov = state.get("provider")
        metrics.llm_errors_total.labels(
            provider=prov.value if prov else "unknown",
            kind="schema",
        ).inc()
        classification = _rule_based(user_input)

    metrics.turns_total.labels(
        category=classification.category.value, priority=classification.priority.value
    ).inc()
    log.info(
        "classified",
        extra={
            "category": classification.category.value,
            "priority": classification.priority.value,
            "confidence": classification.confidence,
        },
    )
    return {
        "category": classification.category,
        "priority": classification.priority,
        "confidence": classification.confidence,
        "entities": classification.entities,
        "error_code": "ALL_PROVIDERS_DOWN" if providers_down else "",
        "token_usage": usage,
    }
