"""persist — writes the turn, token usage, citations, provider and outcome to the store.

The terminal node on every path. Auditability (README §16) depends on this row existing
for every turn, carrying prompt version, provider and sources so any answer can be
explained after the fact.
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import Alias, Resolution
from telecom_agent.core.types import TokenUsage
from telecom_agent.observability import metrics
from telecom_agent.observability.cost import estimate_cost
from telecom_agent.observability.logging import bind


def persist(state: TriageState, deps: AgentDeps) -> dict:
    session_id = state["session_id"]
    provider = state.get("provider")
    usage: TokenUsage = state.get("token_usage") or TokenUsage()
    resolution = state.get("resolution", Resolution.ESCALATED)
    log = bind(__name__, trace_id=state.get("trace_id", ""), session_id=session_id, node="persist")

    # Cost is charged at the answer-tier price as a reasonable per-turn approximation.
    est_cost = estimate_cost(provider, Alias.CHAT_MAIN, usage) if provider else 0.0
    category = state.get("category")
    priority = state.get("priority")

    try:
        deps.turn_repo.add(
            trace_id=state.get("trace_id", ""),
            session_id=session_id,
            user_input=state.get("user_input", ""),
            category=category.value if category else "",
            priority=priority.value if priority else "",
            resolution=str(resolution),
            answer=state.get("answer", ""),
            citations=[c.model_dump() for c in state.get("citations", [])],
            provider=provider.value if provider else "",
            degraded=bool(state.get("degraded", False)),
            prompt_version=deps.settings.classifier_version,
            groundedness=float(state.get("groundedness", 0.0)),
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            est_cost_usd=est_cost,
        )
    except Exception as exc:  # noqa: BLE001 - persistence must not sink a served answer
        log.error("failed to persist turn: %s", exc)

    metrics.resolution_total.labels(outcome=str(resolution)).inc()
    log.info(
        "persisted turn",
        extra={"resolution": str(resolution), "tokens": usage.total, "est_cost_usd": est_cost},
    )
    return {}
