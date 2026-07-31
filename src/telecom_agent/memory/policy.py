"""Window trimming: keep the conversation under a token ceiling so a long session cannot
blow the per-session budget on context alone."""

from __future__ import annotations

from telecom_agent.core.types import Message
from telecom_agent.core.utils import approx_tokens


def trim_window(
    messages: list[Message], max_tokens: int = 3000, keep_last: int = 8
) -> list[Message]:
    """Keep the most recent turns within ``max_tokens``; always retain any system message
    and at least ``keep_last`` recent messages."""
    if not messages:
        return []
    system = [m for m in messages if m.role == "system"]
    convo = [m for m in messages if m.role != "system"]

    kept: list[Message] = []
    budget = max_tokens - sum(approx_tokens(m.content) for m in system)
    for m in reversed(convo):
        cost = approx_tokens(m.content)
        if len(kept) >= keep_last and budget - cost < 0:
            break
        kept.append(m)
        budget -= cost
    kept.reverse()
    return system + kept
