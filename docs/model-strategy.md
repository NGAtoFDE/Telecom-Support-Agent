# Model Strategy

Foundry primary, `fake` for offline. Implemented in `llm/`.

## Aliases, not model names

Code refers to stable aliases (`core/enums.py::Alias`); the mapping to concrete model
ids / deployment names lives in one place, `llm/aliases.py`, driven by settings. A model
upgrade is a portal/config change, never a code change.

| Alias | Foundry (deployment name) | Used by |
|---|---|---|
| `chat-main` | a GPT-5-class deployment | `draft_answer` |
| `chat-mini` | a GPT-5-mini-class deployment | `classify`, `clarify`, `verify` |
| `embed` | `text-embedding-3-small` | ingestion only |

The Foundry models-inference endpoint (`https://<resource>.services.ai.azure.com/models`)
routes on the `model` parameter matched against the deployment name — that is what makes an
alias a portal action.

### Model behind each alias (fill in on deploy day)

| Alias | Provider | Exact model / deployment | Set on (date) | Notes |
|---|---|---|---|---|
| `chat-main` | Foundry | _e.g. gpt-5_ | | |
| `chat-mini` | Foundry | _e.g. gpt-5-mini_ | | |
| `embed` | Foundry | text-embedding-3-small | | |

## Failover semantics

Implemented in `llm/router.py`:

1. Provider is **pinned per session** in `load_session`, not per call.
2. On a chat call, the pinned provider is tried first with up to 2 retries on *retryable*
   errors (timeouts, 5xx, 429). `ContentFiltered` is never retried.
3. Repeated failure trips a `CircuitBreaker` (`llm/guards.py`) — 2 consecutive failures →
   open for `LLM_BREAKER_COOLDOWN_SECONDS` (default 60), then half-open probe.
4. If the provider fails, `BreakerOpen` or `ProviderError` is raised; `classify` catches it, falls back
   to a deterministic keyword classifier, and the graph escalates to `GENERAL_L1`.

Every `ChatResult` carries `provider` and `model`; these are stamped on logs and the API
`llm` block so "why was this answer bad?" is answerable after the fact.

## Both baselines

`evals/baselines/` holds `foundry.json`.
