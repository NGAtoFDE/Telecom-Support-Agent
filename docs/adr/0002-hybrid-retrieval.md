# ADR 0002 — Hybrid retrieval (BM25 + dense)

Status: Accepted

## Context

Telecom queries mix natural-language paraphrase ("no internet since morning") with exact
tokens that must match precisely: APN names, error codes (`ERR-RCH-402`), plan names, USSD
strings, ICCIDs. Dense embeddings blur exact tokens; BM25 nails them but misses paraphrase.
Either retriever alone systematically misses a class of queries.

## Decision

Fuse both. `rag/vector_store.py` holds a FAISS `IndexFlatIP` over L2-normalised vectors
(cosine); `rag/keyword_index.py` builds a BM25 index over the same chunks (rebuilt at load,
cheap for a few hundred chunks). `rag/retriever.py::HybridRetriever` normalises each side,
fuses with weights (0.6 dense / 0.4 sparse), dedups by `(doc_id, section)`, and returns
top-k. The dense query embedder is injected so the whole thing runs offline in `fake` mode
and degrades gracefully to BM25-only if embedding fails.

## Consequences

- Exact-token queries and paraphrase queries both retrieve well.
- The retrieval score is meaningful enough to gate the answer-not-found floor (0.35).
- No managed vector service to provision — removes a critical-path dependency.
- Fusion weights are a small tuning surface; recorded here so a change is deliberate.

## Alternatives considered

- **Dense-only (FAISS)** — rejected: misses error codes / plan names.
- **BM25-only** — rejected: misses paraphrase, and dense is nearly free to add.
- **Managed Azure AI Search** — deferred (README §12): 40 docs do not need it, and it adds a
  provisioning dependency to Day 1.
- **Cross-encoder reranker** — deferred: adds latency and a tuning loop; revisit if
  precision@3 becomes the bottleneck.
