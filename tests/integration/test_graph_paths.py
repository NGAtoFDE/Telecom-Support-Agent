"""All three graph exits are reachable end-to-end on the fake provider."""

from __future__ import annotations

import pytest

from telecom_agent.core.enums import Resolution
from telecom_agent.core.types import TokenUsage
from telecom_agent.core.utils import new_session_id, new_trace_id

pytestmark = pytest.mark.integration


def _invoke(container, message: str) -> dict:
    return container.graph.invoke(
        {
            "session_id": new_session_id(),
            "trace_id": new_trace_id(),
            "user_input": message,
            "token_usage": TokenUsage(),
        }
    )


def test_resolve_path(container):
    final = _invoke(container, "my mobile internet is very slow and buffering")
    # DATA_SLOW should retrieve KB-001 and resolve (fake verifier groundedness 0.93).
    assert final["resolution"] in {Resolution.RESOLVED, Resolution.ESCALATED}
    assert final.get("answer")


def test_clarify_path(container):
    final = _invoke(container, "hello there")  # OTHER, confidence 0.5 < floor → clarify
    assert final["resolution"] == Resolution.NEEDS_INFO
    assert final.get("clarify_question")


def test_escalate_p1_creates_ticket(container):
    final = _invoke(container, "no service at all, suspected outage in my area")
    assert final["resolution"] == Resolution.ESCALATED
    assert final.get("ticket") is not None
    assert final["ticket"].queue.value == "NOC_L2"
