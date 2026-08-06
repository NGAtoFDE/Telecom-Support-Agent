"""BM25 keyword index — the half of retrieval that nails exact tokens: error codes,
plan names, APN strings, ICCIDs. Dense embeddings blur those; BM25 does not.

BM25 is rebuilt from ``chunks.jsonl`` at load time (cheap for a few hundred chunks), so
nothing extra needs to be serialised.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from telecom_agent.core.types import Chunk

_TOKEN = re.compile(r"[a-z0-9]+", re.I)

# Dropping function words stops BM25 from "matching" two texts that merely share "the" or
# "and"; without this, an off-topic query lands spurious hits on every document.
_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "my",
        "no",
        "not",
        "of",
        "on",
        "or",
        "so",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "this",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "will",
        "with",
        "you",
        "your",
        "me",
        "am",
        "pm",
    ]
)


def _tokenize(text: str) -> list[str]:
    return [
        t for t in (w.lower() for w in _TOKEN.findall(text)) if len(t) >= 2 and t not in _STOPWORDS
    ]


class KeywordIndex:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self._corpus = [_tokenize(f"{c.title} {c.text}") for c in chunks]
        self._bm25 = BM25Okapi(self._corpus) if self._corpus else None

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(i, float(s)) for i, s in ranked[:k] if s > 0]
