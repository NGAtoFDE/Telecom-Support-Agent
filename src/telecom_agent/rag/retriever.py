"""Hybrid retrieval: dense (FAISS cosine) fused with sparse (BM25), deduped by
(doc_id, section), score-normalised, top-k.

Why hybrid (ADR-0002): dense catches paraphrase ("no internet" ≈ "data not working"),
BM25 catches exact tokens (error codes, plan names, APN strings). Either alone misses a
class of telecom queries.

The dense side needs a query embedding. Per README §4.3 the *production* query path is
designed to lean on BM25 + a local FAISS lookup; here the query embedder is injected so
the whole thing runs offline with the fake embedder, and dense degrades gracefully to
BM25-only if embedding fails.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from telecom_agent.core.types import Chunk
from telecom_agent.rag.keyword_index import KeywordIndex
from telecom_agent.rag.schemas import RetrievalResult
from telecom_agent.rag.vector_store import VectorStore

log = logging.getLogger(__name__)

Embedder = Callable[[list[str]], list[list[float]]]

_DENSE_WEIGHT = 0.6
_SPARSE_WEIGHT = 0.4
# BM25 raw scores are unbounded; a saturating transform maps them to (0,1) while keeping
# *absolute* strength — a weak single-term match stays small instead of being normalised
# up to 1.0. This is what makes the retrieval score floor meaningful.
_BM25_SATURATION = 3.0


class HybridRetriever:
    def __init__(
        self,
        store: VectorStore,
        keyword: KeywordIndex,
        embed_fn: Embedder | None = None,
    ) -> None:
        self._store = store
        self._keyword = keyword
        self._embed_fn = embed_fn

    @classmethod
    def load(cls, index_dir: str | Path, embed_fn: Embedder | None = None) -> HybridRetriever:
        store = VectorStore.load(index_dir)
        keyword = KeywordIndex(store.chunks)
        return cls(store, keyword, embed_fn)

    def search(self, query: str, k: int = 8) -> RetrievalResult:
        chunks = self._store.chunks
        pool = max(k * 3, k)

        dense: dict[int, float] = {}
        if self._embed_fn is not None:
            try:
                qvec = self._embed_fn([query])[0]
                dense = {i: max(0.0, s) for i, s in self._store.search(qvec, pool)}
            except Exception as exc:  # noqa: BLE001 - dense is best-effort
                log.warning("dense retrieval unavailable, falling back to BM25 only: %s", exc)

        sparse_raw = dict(self._keyword.search(query, pool))
        sparse = {i: s / (s + _BM25_SATURATION) for i, s in sparse_raw.items()}

        # fuse
        fused: dict[int, tuple[float, str]] = {}
        for i in set(dense) | set(sparse):
            d, s = dense.get(i, 0.0), sparse.get(i, 0.0)
            score = _DENSE_WEIGHT * d + _SPARSE_WEIGHT * s
            src = "hybrid" if (i in dense and i in sparse) else ("dense" if i in dense else "bm25")
            fused[i] = (score, src)

        # dedup by (doc_id, section), keep the best-scoring chunk per section
        best: dict[tuple[str, str], Chunk] = {}
        for i, (score, src) in fused.items():
            c = chunks[i]
            key = (c.doc_id, c.section)
            cand = c.model_copy(update={"score": round(score, 4), "source": src})
            if key not in best or cand.score > best[key].score:
                best[key] = cand

        ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)[:k]
        return RetrievalResult(query=query, chunks=ranked)
