"""Exposes hybrid retrieval as a callable tool, so the agent (or an eval) can search the
knowledge base through the same interface a tool call would use."""

from __future__ import annotations

from telecom_agent.rag.retriever import HybridRetriever
from telecom_agent.rag.schemas import RetrievalResult


class KbSearchTool:
    def __init__(self, retriever: HybridRetriever, top_k: int = 8) -> None:
        self._retriever = retriever
        self._top_k = top_k

    def search(self, query: str, k: int | None = None) -> RetrievalResult:
        return self._retriever.search(query, k=k or self._top_k)
