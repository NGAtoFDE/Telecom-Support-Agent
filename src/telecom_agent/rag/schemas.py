"""Retrieval dataclasses. ``Chunk`` and ``Citation`` are the shared domain types from
``core``; ``RetrievalResult`` is retrieval-specific and lives here."""

from __future__ import annotations

from dataclasses import dataclass, field

from telecom_agent.core.types import Chunk, Citation

__all__ = ["Chunk", "Citation", "RetrievalResult"]


@dataclass
class RetrievalResult:
    query: str
    chunks: list[Chunk] = field(default_factory=list)

    @property
    def max_score(self) -> float:
        return max((c.score for c in self.chunks), default=0.0)

    def to_citations(self) -> list[Citation]:
        return [
            Citation(doc_id=c.doc_id, title=c.title, section=c.section, score=round(c.score, 3))
            for c in self.chunks
        ]
