"""Offline ingestion pipeline: load → chunk → embed → index.

Run once (``make ingest`` / ``scripts/ingest_kb.py``). Writes ``data/index/`` which is
then published as a GitHub Release artifact so no teammate and no container ever needs to
re-embed (README §4.3). Embeddings are only ever called here.
"""

from __future__ import annotations

import logging
from pathlib import Path

from telecom_agent.config.settings import Settings, get_settings
from telecom_agent.rag.chunking import chunk_docs
from telecom_agent.rag.embeddings import get_embedder
from telecom_agent.rag.loaders import load_kb
from telecom_agent.rag.vector_store import VectorStore

log = logging.getLogger(__name__)


def ingest(kb_dir: str | Path, index_dir: str | Path, settings: Settings | None = None) -> int:
    """Build FAISS + chunk store from ``kb_dir`` into ``index_dir``. Returns chunk count."""
    settings = settings or get_settings()
    docs = load_kb(kb_dir)
    if not docs:
        raise RuntimeError(f"no documents found under {kb_dir}")
    chunks = chunk_docs(docs)
    log.info("ingest: %d docs -> %d chunks", len(docs), len(chunks))

    embedder = get_embedder(settings)
    vectors = embedder([c.text for c in chunks])

    store = VectorStore.build(chunks, vectors)
    store.save(index_dir)
    log.info("ingest: wrote index to %s (dim=%d)", index_dir, store.dim)
    return len(chunks)
