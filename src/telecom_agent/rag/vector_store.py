"""FAISS save/load behind one small interface.

On-disk layout under ``index_dir``:
    dense.faiss    – FAISS IndexFlatIP over L2-normalised vectors (inner product = cosine)
    chunks.jsonl   – one chunk per line; row i aligns with FAISS row i
    meta.json      – {dim, count, embed_model}

Keeping chunks next to the vectors means the retriever loads text and metadata without a
second datastore, and BM25 can be rebuilt from the same file.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from telecom_agent.core.types import Chunk

_DENSE = "dense.faiss"
_CHUNKS = "chunks.jsonl"
_META = "meta.json"


def _normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


class VectorStore:
    def __init__(self, chunks: list[Chunk], index=None, dim: int = 0) -> None:
        self.chunks = chunks
        self._index = index
        self.dim = dim

    # -- build / persist ----------------------------------------------------
    @classmethod
    def build(cls, chunks: list[Chunk], vectors: list[list[float]]) -> VectorStore:
        import faiss

        mat = _normalize(np.asarray(vectors, dtype="float32"))
        dim = mat.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(mat)
        return cls(chunks=chunks, index=index, dim=dim)

    def save(self, index_dir: str | Path) -> None:
        import faiss

        d = Path(index_dir)
        d.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(d / _DENSE))
        with (d / _CHUNKS).open("w", encoding="utf-8") as fh:
            for c in self.chunks:
                fh.write(json.dumps(c.model_dump(), ensure_ascii=False) + "\n")
        (d / _META).write_text(
            json.dumps({"dim": self.dim, "count": len(self.chunks)}), encoding="utf-8"
        )

    @classmethod
    def load(cls, index_dir: str | Path) -> VectorStore:
        import faiss

        d = Path(index_dir)
        index = faiss.read_index(str(d / _DENSE))
        chunks = [
            Chunk(**json.loads(line))
            for line in (d / _CHUNKS).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        meta = json.loads((d / _META).read_text(encoding="utf-8"))
        return cls(chunks=chunks, index=index, dim=meta.get("dim", 0))

    # -- query --------------------------------------------------------------
    def search(self, query_vec: list[float], k: int) -> list[tuple[int, float]]:
        q = _normalize(np.asarray([query_vec], dtype="float32"))
        scores, idx = self._index.search(q, min(k, len(self.chunks)))
        return [(int(i), float(s)) for i, s in zip(idx[0], scores[0], strict=False) if i >= 0]

    @staticmethod
    def exists(index_dir: str | Path) -> bool:
        d = Path(index_dir)
        return (d / _DENSE).exists() and (d / _CHUNKS).exists()
