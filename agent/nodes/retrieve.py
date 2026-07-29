"""retrieve — hybrid search over the approved KB, then apply the score floor.

If the best chunk scores below ``retrieval_score_floor`` the turn cannot be grounded, so
the edge function sends it straight to escalate (answer-not-found). This node just gathers
evidence and records the retrieval-score metric; the gate decision lives in ``edges.py``.
"""

from __future__ import annotations

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.state import TriageState
from telecom_agent.observability import metrics
from telecom_agent.observability.logging import bind


def retrieve(state: TriageState, deps: AgentDeps) -> dict:
    query = state.get("user_input", "")
    log = bind(
        __name__,
        trace_id=state.get("trace_id", ""),
        session_id=state.get("session_id", ""),
        node="retrieve",
    )

    result = deps.retriever.search(query, k=deps.settings.retrieval_top_k)
    metrics.retrieval_score.observe(result.max_score)
    log.info(
        "retrieved chunks",
        extra={"n": len(result.chunks), "max_score": round(result.max_score, 3)},
    )
    below_floor = result.max_score < deps.settings.retrieval_score_floor
    return {
        "retrieved": result.chunks,
        "citations": result.to_citations(),
        "error_code": "RETRIEVAL_EMPTY" if below_floor else "",
    }
