"""Helpers shared by nodes: building provider-agnostic message lists from the versioned
prompt registry, JSON extraction with one repair attempt, and context formatting.

Kept tiny and free of decision logic — the gates live in ``policies/`` and ``edges.py``.
"""

from __future__ import annotations

import json
import re

from telecom_agent.core.types import Chunk, Message, TokenUsage
from telecom_agent.llm.base import ChatResult
from telecom_agent.observability import metrics
from telecom_agent.prompts import registry


def track_usage(node: str, result: ChatResult) -> TokenUsage:
    """Record per-node token metrics and return this call's usage as a delta. Nodes add
    these deltas and return them under ``token_usage``; the state reducer sums them."""
    provider = result.provider.value if result.provider else "unknown"
    metrics.llm_tokens_total.labels(node=node, provider=provider).inc(result.usage.total)
    return result.usage


def system_message(version: str) -> Message:
    return Message(role="system", content=registry.render("system", version))


def node_messages(system_version: str, node_system: str, user_content: str) -> list[Message]:
    """A node's call = shared system framing + the node's own system instruction (which
    also tells the fake provider which node is calling) + the user/content payload."""
    return [
        Message(role="system", content=registry.render("system", system_version)),
        Message(role="system", content=node_system),
        Message(role="user", content=user_content),
    ]


def format_context(chunks: list[Chunk]) -> str:
    """Render retrieved chunks into a citable context block for answer/verify prompts."""
    blocks = []
    for c in chunks:
        blocks.append(f"[{c.doc_id} §{c.section}] {c.title}\n{c.text}")
    return "\n\n".join(blocks)


_JSON_OBJ = re.compile(r"\{.*\}", re.S)


def extract_json(text: str) -> dict:
    """Best-effort JSON object extraction. Raises ValueError if nothing parseable."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_OBJ.search(text)
    if m:
        return json.loads(m.group(0))
    raise ValueError("no JSON object found in model output")
