"""``TriageState`` — the single shared contract every graph node reads and updates.

Frozen at end of Day 1. Nodes return a *partial* update of this object and never mutate
globals. Keys mirror README §3.2 exactly.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from telecom_agent.core.enums import (
    EscalationQueue,
    IssueCategory,
    Priority,
    Provider,
    Resolution,
)
from telecom_agent.core.types import (
    Chunk,
    Citation,
    CustomerCtx,
    Message,
    Ticket,
    TokenUsage,
)


def _accumulate_usage(existing: TokenUsage | None, update: TokenUsage | None) -> TokenUsage:
    """LangGraph reducer: token usage is *summed* across nodes within a turn rather than
    overwritten, so per-turn cost is the total of every LLM call the graph made."""
    if existing is None:
        return update or TokenUsage()
    if update is None:
        return existing
    return existing.add(update)


class TriageState(TypedDict, total=False):
    # --- identity & tracing ---
    session_id: str
    trace_id: str
    # --- provider pinning (see README §4) ---
    provider: Provider  # fixed for the whole session
    degraded: bool  # True when serving from the backup provider
    # --- conversation ---
    messages: list[Message]  # rolling window, trimmed by memory policy
    customer_ctx: CustomerCtx
    user_input: str  # the current turn's raw text
    # --- classification output ---
    category: IssueCategory
    priority: Priority
    confidence: float
    entities: dict
    # --- retrieval output ---
    retrieved: list[Chunk]
    citations: list[Citation]
    # --- generation & verification ---
    draft: str
    groundedness: float
    attempt: int
    # --- outcome ---
    resolution: Resolution
    answer: str
    ticket: Ticket | None
    queue: EscalationQueue | None
    clarify_question: str  # populated on the clarify branch
    error_code: str  # set when a failure short-circuits to escalate
    # --- budget ---
    # summed across nodes via the reducer; enforced against the session cap in the router
    token_usage: Annotated[TokenUsage, _accumulate_usage]
