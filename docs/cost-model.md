# Cost Model

Token maths per node for both providers. Prices are the per-million-token rates in
`observability/cost.py` (`_PRICES`); Groq figures are published rates (README §18), Foundry
figures are placeholders to replace with your deployment's actual pricing.

## Per-node token profile (typical resolved turn)

| Node | Alias | ~Input tokens | ~Output tokens |
|---|---|---|---|
| `classify` | chat-mini | 600 | 80 |
| `draft_answer` | chat-main | 3 000 (8 chunks) | 400 |
| `verify` | chat-mini | 1 500 | 120 |
| **Total** | | **~5 100** | **~600** |

An **escalated** turn skips `draft_answer` (and often `verify`), so it costs less — usually
just the classify call, plus retrieval which is free (local FAISS + BM25).

## Per-turn cost (USD)

Using `_PRICES` from `observability/cost.py`:

| Provider | chat-main (in/out per 1M) | chat-mini (in/out per 1M) | ~Resolved turn |
|---|---|---|---|
| Groq | 0.15 / 0.60 | 0.05 / 0.08 | ≈ $0.0009 (a tenth of a US cent) |
| Foundry (placeholder) | 2.50 / 10.00 | 0.15 / 0.60 | ≈ $0.0116 |

> Replace the Foundry row from the Azure pricing page for your chosen deployments on Day 1.
> A two-provider, per-node table is a stronger artefact than a single number.

## Embedding cost (one-off)

Embeddings run once at ingestion: ~40 docs → a few hundred chunks → a fraction of a cent,
paid once. This is the direct financial consequence of the ingest-only design (ADR-0004).

## Monthly projection (illustrative)

At 5 000 turns/month, 70% resolved / 30% escalated:

| Provider | Resolved (3 500) | Escalated (1 500) | Monthly |
|---|---|---|---|
| Groq | ~$3.15 | ~$0.30 | **~$3.45** |
| Foundry (placeholder) | ~$40.60 | ~$3.00 | **~$43.60** |

Infra (Container Apps scale-to-zero UI, Basic ACR, small Files share, App Insights) is the
larger line item at this volume; the LLM spend is dominated by fixed hosting.

## Cost levers (name these in the deck)

- Cache classification of repeated utterances.
- Drop retrieval `k` from 8 → 5 once precision allows.
- Verifier already on `chat-mini` (cheaper than `chat-main`).
- `SESSION_TOKEN_BUDGET=12000` hard cap (`llm/guards.py::TokenBudget`).
- Route deterministic categories to rules and skip the LLM entirely.
