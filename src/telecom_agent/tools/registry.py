"""One place to register tools: name → callable + JSON schema.

Adding a tool means adding one entry here, not editing a node. The JSON schema is what a
future function-calling model would receive; today the graph calls tools directly, but
the registry keeps the contract explicit and testable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolSpec:
    name: str
    fn: Callable[..., Any]
    schema: dict


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, name: str, fn: Callable[..., Any], schema: dict) -> None:
        self._tools[name] = ToolSpec(name=name, fn=fn, schema=schema)

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def call(self, name: str, **kwargs: Any) -> Any:
        return self._tools[name].fn(**kwargs)

    def schemas(self) -> list[dict]:
        return [t.schema for t in self._tools.values()]


def build_registry(ticketing, kb_search, diagnostics_fn) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        "create_ticket",
        ticketing.create_ticket,
        {
            "name": "create_ticket",
            "description": "Create a simulated support ticket routed to an escalation queue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "category": {"type": "string"},
                    "priority": {"type": "string"},
                    "queue": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["session_id", "category", "priority", "queue", "summary"],
            },
        },
    )
    reg.register(
        "kb_search",
        kb_search.search,
        {
            "name": "kb_search",
            "description": "Hybrid search over the approved knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
                "required": ["query"],
            },
        },
    )
    reg.register(
        "check_outage",
        diagnostics_fn,
        {
            "name": "check_outage",
            "description": "Simulated outage check for a telecom circle.",
            "parameters": {
                "type": "object",
                "properties": {"circle": {"type": "string"}},
                "required": ["circle"],
            },
        },
    )
    return reg
