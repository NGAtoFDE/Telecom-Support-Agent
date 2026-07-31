"""Composition root + FastAPI dependency providers.

``build_container`` wires every collaborator once at startup and stashes it on
``app.state``; the ``get_*`` helpers pull pieces out for individual routes. This is the
only place object graphs are assembled, which keeps the routers thin and testable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Request

from telecom_agent.agent.deps import AgentDeps
from telecom_agent.agent.graph import build_graph
from telecom_agent.agent.policies.thresholds import Thresholds
from telecom_agent.config.settings import Settings, get_settings
from telecom_agent.llm.router import LLMRouter, set_failover_hook
from telecom_agent.observability import metrics
from telecom_agent.rag.embeddings import get_embedder
from telecom_agent.rag.ingest import ingest
from telecom_agent.rag.retriever import HybridRetriever
from telecom_agent.rag.vector_store import VectorStore
from telecom_agent.store.repositories import (
    FeedbackRepository,
    SessionRepository,
    TicketRepository,
    TurnRepository,
)
from telecom_agent.store.session import create_all, get_sessionmaker
from telecom_agent.tools.ticketing import TicketingTool

log = logging.getLogger(__name__)


@dataclass
class Container:
    settings: Settings
    router: LLMRouter
    retriever: HybridRetriever
    ticketing: TicketingTool
    ticket_repo: TicketRepository
    turn_repo: TurnRepository
    feedback_repo: FeedbackRepository
    session_repo: SessionRepository
    agent_deps: AgentDeps
    graph: Any  # compiled LangGraph (CompiledStateGraph); Any avoids a heavy import here


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()

    # -- persistence --
    create_all(settings.database_url)
    sm = get_sessionmaker()
    ticket_repo = TicketRepository(sm)
    turn_repo = TurnRepository(sm)
    feedback_repo = FeedbackRepository(sm)
    session_repo = SessionRepository(sm)

    # -- llm --
    router = LLMRouter(settings)
    set_failover_hook(metrics.record_failover)

    # -- retrieval (auto-ingest on first run so `make dev` needs zero setup in fake mode) --
    if not VectorStore.exists(settings.index_dir):
        if settings.auto_ingest:
            log.info("no index at %s; auto-ingesting from %s", settings.index_dir, settings.kb_dir)
            ingest(settings.kb_dir, settings.index_dir, settings)
        else:
            raise RuntimeError(
                f"no index at {settings.index_dir}; run `make ingest` or `make fetch-index`"
            )
    retriever = HybridRetriever.load(settings.index_dir, embed_fn=get_embedder(settings))

    ticketing = TicketingTool(ticket_repo)
    from telecom_agent.memory.session_store import SessionStore

    session_store = SessionStore()
    thresholds = Thresholds.from_settings(settings)
    agent_deps = AgentDeps(
        settings=settings,
        router=router,
        retriever=retriever,
        ticketing=ticketing,
        session_store=session_store,
        turn_repo=turn_repo,
        thresholds=thresholds,
    )
    graph = build_graph(agent_deps)

    return Container(
        settings=settings,
        router=router,
        retriever=retriever,
        ticketing=ticketing,
        ticket_repo=ticket_repo,
        turn_repo=turn_repo,
        feedback_repo=feedback_repo,
        session_repo=session_repo,
        agent_deps=agent_deps,
        graph=graph,
    )


# -- FastAPI dependency providers --------------------------------------------
def get_container(request: Request) -> Container:
    return request.app.state.container


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.container.settings
