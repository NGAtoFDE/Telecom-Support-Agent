"""Dependency container handed to every node.

Nodes are pure-ish functions of ``(state, deps)``: all their collaborators (router,
retriever, ticketing, memory, thresholds, persistence) arrive through this object, so a
node is trivial to unit-test with fakes and never reaches for a global.
"""

from __future__ import annotations

from dataclasses import dataclass

from telecom_agent.agent.policies.thresholds import Thresholds
from telecom_agent.config.settings import Settings
from telecom_agent.llm.router import LLMRouter
from telecom_agent.memory.session_store import SessionStore
from telecom_agent.rag.retriever import HybridRetriever
from telecom_agent.store.repositories import TurnRepository
from telecom_agent.tools.ticketing import TicketingTool


@dataclass
class AgentDeps:
    settings: Settings
    router: LLMRouter
    retriever: HybridRetriever
    ticketing: TicketingTool
    session_store: SessionStore
    turn_repo: TurnRepository
    thresholds: Thresholds
