# High Level Design

Expanded companion to README §2. This document describes the architecture as actually
implemented in `src/telecom_agent/`.

## 1. Layering

The dependency rule is enforced in review and mirrored by the package layout:

```
api  →  agent  →  { rag, tools, memory, prompts, llm }  →  store  →  config/core
```

Arrows point one way. `core/` and `config/` import nothing internal and may be imported by
anything. `ui/` sits outside the package and speaks HTTP only.

| Layer | Package | Responsibility |
|---|---|---|
| HTTP boundary | `api/` | validation, auth, rate-limit, tracing, serialisation |
| Orchestration | `agent/` | LangGraph, nodes, routing policy, thresholds, budget |
| Model access | `llm/` | provider adapters, router, failover, breaker, guards |
| Retrieval | `rag/` | ingest, chunk, embed (ingest-only), FAISS + BM25 hybrid |
| Side effects | `tools/` | ticketing, kb_search, diagnostics, arg validators |
| Continuity | `memory/` | session window trimming, pinned provider, TTL |
| Persistence | `store/` | SQLAlchemy models, WAL engine, repositories |
| Observability | `observability/` | JSON logs + redaction, metrics, cost, OTel |
| Primitives | `core/`, `config/` | enums, types, errors, utils, settings |

## 2. Runtime composition

`api/deps.py::build_container` is the single composition root. At startup it:

1. `create_all()` on the configured `DATABASE_URL` (SQLite WAL).
2. Constructs the `LLMRouter` and wires the failover hook to `metrics.record_failover`.
3. Auto-ingests `data/kb → data/index` if no index is present (dev convenience; disable
   with `AUTO_INGEST=false`).
4. Loads the `HybridRetriever` with a query embedder from `rag.embeddings.get_embedder`.
5. Builds `AgentDeps` and compiles the graph via `agent.graph.build_graph`.

The container is stashed on `app.state` and pulled into routes with FastAPI `Depends`.

## 3. Non-functional targets

See README §2.4. The measurement hooks that back each target:

| Attribute | Target | Where measured |
|---|---|---|
| Latency p95 resolve | < 6 s Foundry / < 4 s Groq | `turn_latency_seconds{provider}` histogram |
| Latency p95 escalate | < 9 s | same histogram, escalate path |
| Retrieval recall@5 | ≥ 0.85 | `evals/runners/run_retrieval.py` |
| Classification accuracy | ≥ 0.90 cat / ≥ 0.85 pri | `evals/runners/run_classification.py` |
| Groundedness | ≥ 0.90 answered turns cited | `verify` node + `run_groundedness.py` |
| Escalation recall P1 | 1.00 | `evals/datasets/escalation.jsonl` |
| Cost | ≤ 12 000 tokens/session | `TokenBudget` in `llm/guards.py` |
| Failover time | < 20 s | `scripts/failover_drill.sh` |

## 4. Key design decisions

Recorded as ADRs in `docs/adr/`:

- **0001** LangGraph over plain chains — cycles (verify→retrieve retry) and conditional
  exits (clarify / escalate) are native to a state machine.
- **0002** Hybrid retrieval — dense for paraphrase, BM25 for error codes / plan names.
- **0003** Groq as failover — a second vendor boundary independent of the Azure tenant.
- **0004** Embeddings at ingest only — Groq has no embeddings endpoint; the query path is
  designed so a build-time artifact (FAISS + chunk store) carries retrieval.

## 5. Failure posture

Every row of README §6 maps to code: retries + breaker in `llm/router.py`, rule-based
classifier fallback in `agent/nodes/classify.py`, retrieval floor + verify budget in
`agent/edges.py`, idempotent tickets in `tools/ticketing.py`, injection scan in
`llm/guards.py`. Escalation is the safe default: anything that cannot be grounded becomes a
ticket for a human.
