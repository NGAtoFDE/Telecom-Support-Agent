# ADR 0004 — Embeddings at ingest time only

- **Status:** Accepted
- **Date:** 2026-07
- **Deciders:** M2 (RAG), M5 (LLMOps)

## Context

Groq — our failover provider — has **no embeddings endpoint**; its production catalogue is
chat plus audio. If the query path depended on a live embedding call, a Foundry outage
would break retrieval even though chat had successfully failed over to Groq. That would
defeat the whole point of having a backup.

## Decision

Compute embeddings **only at ingestion time**, never on the query path.

- `make ingest` calls the Foundry `embed` deployment once, over the ~40-doc KB, and writes
  `data/index/` (FAISS vectors + the chunk store).
- The built index is published as a **GitHub Release artifact**, so no teammate and no
  container ever re-embeds. `make fetch-index` downloads it.
- Query-time retrieval is **FAISS + BM25**, both local, both offline. The query embedding
  for the dense side is produced by an injected embedder; in the offline/demo (`fake`)
  configuration this is a deterministic local embedder, so the demo cannot be broken by an
  embedding outage.

## Consequences

- **Positive:** the single biggest reliability win in a 7-day build — the query path has
  no hard cloud dependency; the failover is genuinely usable because chat fails over and
  retrieval keeps working. Embedding cost is a one-off fraction of a cent.
- **Negative:** rebuilding the index requires Foundry embed access (or the local
  fallback); a KB change means a re-ingest and a new release artifact. Acceptable: the KB
  is static within a release cycle.

## Alternatives considered

- **Local sentence-transformer (`bge-small-en-v1.5`)** removes the Azure dependency for
  embeddings entirely but adds ~120 MB to the image and a second embedding quality to
  evaluate. Revisit if we want to drop the Azure embed dependency in v2.
- **Azure AI Search (managed vector index):** overkill for ~40 docs and adds a
  provisioning dependency to the critical path.
