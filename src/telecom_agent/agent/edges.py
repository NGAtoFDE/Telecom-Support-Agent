"""Conditional-edge functions: pure ``state → next node name``.

They contain no side effects and no LLM calls — just the branching logic that reads the
gates the nodes populated. Thresholds arrive bound via ``functools.partial`` in graph.py,
so these stay easy to unit-test at and around each cut-off.
"""

from __future__ import annotations

from telecom_agent.agent.policies.thresholds import Thresholds
from telecom_agent.agent.state import TriageState
from telecom_agent.core.enums import Priority


def after_classify(state: TriageState, thresholds: Thresholds) -> str:
    # Both providers down → straight to escalate (rule-based classification already done).
    if state.get("error_code") == "ALL_PROVIDERS_DOWN":
        return "escalate"
    # P1 always goes to a human, regardless of confidence (human-review guarantee).
    if state.get("priority") == Priority.P1:
        return "escalate"
    if state.get("confidence", 1.0) < thresholds.clarify_confidence_floor:
        return "clarify"
    return "retrieve"


def after_retrieve(state: TriageState, thresholds: Thresholds) -> str:
    chunks = state.get("retrieved", [])
    max_score = max((c.score for c in chunks), default=0.0)
    if not chunks or max_score < thresholds.retrieval_score_floor:
        return "escalate"
    return "draft_answer"


def after_verify(state: TriageState, thresholds: Thresholds) -> str:
    grounded = state.get("groundedness", 0.0) >= thresholds.groundedness_floor
    if grounded:
        return "respond"
    if state.get("attempt", 0) < thresholds.max_verify_attempts:
        return "retrieve"
    return "escalate"
