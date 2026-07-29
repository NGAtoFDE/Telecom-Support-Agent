"""Builds and compiles the LangGraph.

Only this file wires edges — nodes live one-per-file so five people can add nodes without
colliding in ``graph.py`` (README §19 merge-conflict mitigation). Nodes are bound to the
shared :class:`AgentDeps` via ``partial`` so they stay ``(state) -> dict`` for LangGraph
while still receiving their collaborators.
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.edges import after_classify, after_retrieve, after_verify
from telecom_agent.agent.nodes.clarify import clarify
from telecom_agent.agent.nodes.classify import classify
from telecom_agent.agent.nodes.draft_answer import draft_answer
from telecom_agent.agent.nodes.escalate import escalate
from telecom_agent.agent.nodes.load_session import load_session
from telecom_agent.agent.nodes.persist import persist
from telecom_agent.agent.nodes.respond import respond
from telecom_agent.agent.nodes.retrieve import retrieve
from telecom_agent.agent.nodes.verify import verify
from telecom_agent.agent.state import TriageState


def build_graph(deps: AgentDeps):
    g = StateGraph(TriageState)

    # nodes (each bound to deps)
    g.add_node("load_session", partial(load_session, deps=deps))
    g.add_node("classify", partial(classify, deps=deps))
    g.add_node("clarify", partial(clarify, deps=deps))
    g.add_node("retrieve", partial(retrieve, deps=deps))
    g.add_node("draft_answer", partial(draft_answer, deps=deps))
    g.add_node("verify", partial(verify, deps=deps))
    g.add_node("respond", partial(respond, deps=deps))
    g.add_node("escalate", partial(escalate, deps=deps))
    g.add_node("persist", partial(persist, deps=deps))

    th = deps.thresholds

    g.set_entry_point("load_session")
    g.add_edge("load_session", "classify")
    g.add_conditional_edges(
        "classify",
        partial(after_classify, thresholds=th),
        {"clarify": "clarify", "escalate": "escalate", "retrieve": "retrieve"},
    )
    g.add_conditional_edges(
        "retrieve",
        partial(after_retrieve, thresholds=th),
        {"escalate": "escalate", "draft_answer": "draft_answer"},
    )
    g.add_edge("draft_answer", "verify")
    g.add_conditional_edges(
        "verify",
        partial(after_verify, thresholds=th),
        {"respond": "respond", "retrieve": "retrieve", "escalate": "escalate"},
    )
    # terminal paths — every path persists for auditability, then ends
    g.add_edge("respond", "persist")
    g.add_edge("escalate", "persist")
    g.add_edge("clarify", "persist")
    g.add_edge("persist", END)

    return g.compile()
