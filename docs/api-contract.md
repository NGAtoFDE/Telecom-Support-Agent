# API Contract

Versioned under `/v1`. All `/v1/*` routes require header `X-API-Key: <API_KEY>`. Health and
metrics routes are public. The OpenAPI spec is served at `/openapi.json` and can be frozen
into `docs/openapi.json` via `scripts/export_openapi.py`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/chat` | Full triage turn → answer + citations + resolution |
| `POST` | `/v1/classify` | Classification only (evals, UI debug drawer) |
| `POST` | `/v1/tickets` | Simulated ticket creation (idempotent) |
| `GET` | `/v1/tickets/{ticket_id}` | Ticket status + audit fields |
| `GET` | `/v1/tickets` | Filter by `queue`, `priority`, `status`, `limit` |
| `POST` | `/v1/feedback` | Thumbs up/down + comment, keyed to `trace_id` |
| `GET` | `/healthz` | Liveness (no dependency checks) |
| `GET` | `/readyz` | Readiness: index loaded, DB writable, both providers probed |
| `GET` | `/metrics` | Prometheus exposition |

## `POST /v1/chat`

Request:

```json
{ "session_id": "sess_8f2a", "message": "no data since morning in Pune", "customer_ctx": null }
```

`session_id` is optional; a new one is minted if omitted. `customer_ctx` (optional) accepts
`{customer_id, circle, plan, device, account_type}`.

Response (README §7):

```json
{
  "trace_id": "01JBX...",
  "session_id": "sess_8f2a",
  "category": "DATA_SLOW",
  "priority": "P2",
  "resolution": "RESOLVED",
  "answer": "Three steps to restore data service ...",
  "citations": [
    { "doc_id": "KB-114", "title": "APN reset – Android", "section": "2.3", "score": 0.81 }
  ],
  "ticket": null,
  "llm": { "provider": "AZURE_FOUNDRY", "alias": "chat-main", "degraded": false },
  "usage": { "prompt_tokens": 2841, "completion_tokens": 402, "est_cost_usd": 0.0091 },
  "latency_ms": 4180
}
```

`resolution` is one of `RESOLVED | NEEDS_INFO | ESCALATED`. On escalation, `ticket` is a
brief `{ticket_id, queue, priority, status}` and `answer` is the customer-facing handover
message.

## `POST /v1/classify`

```json
// request
{ "message": "call drops every few minutes", "session_id": null }
// response
{ "category": "CALL_DROP", "priority": "P2", "confidence": 0.83, "entities": {} }
```

## `POST /v1/tickets`

```json
{ "session_id": "sess_8f2a", "category": "BILLING_DISPUTE", "priority": "P3",
  "queue": null, "summary": "double charge on recharge" }
```

If `queue` is omitted the routing table (`agent/policies/routing.py`) decides it. Creation
is idempotent on `sha256(session_id + category + hour_bucket)` — a retry in the same hour
returns the existing ticket.

## `POST /v1/feedback`

```json
{ "trace_id": "01JBX...", "session_id": "sess_8f2a", "thumbs": "down", "comment": "wrong steps" }
```

## Error envelope

Identical shape everywhere, so the UI has one error path:

```json
{ "error": { "code": "RETRIEVAL_EMPTY", "message": "...", "trace_id": "01JBX...", "retryable": false } }
```

### Error codes

Defined in `core/errors.py`:

| Code | HTTP | Retryable | Meaning |
|---|---|---|---|
| `VALIDATION_FAILED` | 422 | no | request failed schema validation |
| `UNAUTHORIZED` | 401 | no | missing/invalid `X-API-Key` |
| `RATE_LIMITED` | 429 | yes | per-key token bucket empty |
| `NOT_FOUND` | 404 | no | ticket id unknown |
| `RETRIEVAL_EMPTY` | 200* | no | no chunk above the retrieval floor → escalate |
| `GROUNDEDNESS_FAILED` | 200* | no | answer could not be grounded within retry budget |
| `SCHEMA_REPAIR_FAILED` | 200* | no | malformed LLM JSON survived one repair |
| `PROVIDER_ERROR` | 502 | yes | upstream provider error |
| `PROVIDER_TIMEOUT` | 502 | yes | provider timed out |
| `PROVIDER_QUOTA` | 429 | yes | provider 429 / quota |
| `CONTENT_FILTERED` | 200* | no | content filter blocked — escalate, do not retry |
| `ALL_PROVIDERS_DOWN` | 503 | yes | both providers unavailable → rule-based + escalate |
| `BUDGET_EXCEEDED` | 200* | no | session token budget exhausted |
| `BREAKER_OPEN` | 502 | yes | circuit breaker open for a provider |
| `INTERNAL_ERROR` | 500 | no | unhandled |

\* These are *graph* outcomes, not HTTP failures — the turn still returns 200 with an
escalation, because escalation is the designed safe default.
