"""Edge/gate behaviour at and around each cut-off."""

from __future__ import annotations

from telecom_agent.agent.edges import after_classify, after_retrieve, after_verify
from telecom_agent.agent.policies.thresholds import Thresholds
from telecom_agent.core.enums import Priority
from telecom_agent.core.types import Chunk

TH = Thresholds()  # defaults: clarify 0.60, retrieval 0.35, groundedness 0.75, max_attempts 2


def _chunk(score: float) -> Chunk:
    return Chunk(doc_id="KB-1", title="t", section="1", text="x", score=score)


# ---- after_classify ----
def test_p1_always_escalates_even_high_confidence():
    state = {"priority": Priority.P1, "confidence": 0.99}
    assert after_classify(state, TH) == "escalate"


def test_low_confidence_clarifies():
    state = {"priority": Priority.P2, "confidence": 0.59}
    assert after_classify(state, TH) == "clarify"


def test_confidence_at_floor_retrieves():
    state = {"priority": Priority.P2, "confidence": 0.60}
    assert after_classify(state, TH) == "retrieve"


def test_all_providers_down_escalates():
    state = {"priority": Priority.P2, "confidence": 0.99, "error_code": "ALL_PROVIDERS_DOWN"}
    assert after_classify(state, TH) == "escalate"


# ---- after_retrieve ----
def test_retrieval_below_floor_escalates():
    assert after_retrieve({"retrieved": [_chunk(0.34)]}, TH) == "escalate"


def test_retrieval_empty_escalates():
    assert after_retrieve({"retrieved": []}, TH) == "escalate"


def test_retrieval_at_floor_drafts():
    assert after_retrieve({"retrieved": [_chunk(0.35)]}, TH) == "draft_answer"


# ---- after_verify ----
def test_grounded_responds():
    assert after_verify({"groundedness": 0.75, "attempt": 1}, TH) == "respond"


def test_not_grounded_with_budget_retries():
    assert after_verify({"groundedness": 0.5, "attempt": 1}, TH) == "retrieve"


def test_not_grounded_budget_exhausted_escalates():
    assert after_verify({"groundedness": 0.5, "attempt": 2}, TH) == "escalate"
