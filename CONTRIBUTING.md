# Contributing

Short, enforced conventions so the board, the changelog and the review gate all work
without extra effort. (See README §10 for the full workflow.)

## Branches

Pattern: `<type>/<issue-number>-<slug>` — the issue number auto-links the branch to the
board item.

```
feat/42-classify-node
fix/57-citation-offset
docs/64-azure-diagram
```

`type` ∈ `feat` · `fix` · `docs` · `chore` · `test` · `refactor`.

## Commits — Conventional Commits, scoped to the component

```
feat(agent): add verifier node with claim-to-chunk mapping
feat(llm): add Groq adapter with session-pinned failover
fix(rag): preserve section heading when a chunk spans a page break
docs(adr): record embeddings-at-ingest-only decision
```

Scope ∈ `agent` · `llm` · `rag` · `api` · `ui` · `tools` · `store` · `infra` · `evals` · `docs`.

## Layering rule (blocking review comment if violated)

```
api → agent → { rag, tools, memory, prompts, llm } → store → config/core
```

Arrows point one way only. `ui/` must never `import telecom_agent...` — it is an HTTP
client of the API. `core/` and `config/` import nothing internal.

## Before you open a PR

- `make test` is green locally (ruff + mypy + pytest).
- If you touched `agent/`, `prompts/` or `rag/`, run `make eval` and paste the delta.
- If your change is LLM-facing, verify against **both** providers (or note why not).
- Update the relevant `docs/` section in the *same* PR.
- No secrets, no real data, no PII — in code, fixtures or screenshots.
- Add at least one eval case for any new capability.

## PR checklist

The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) encodes the checklist. Fill it in;
don't delete rows.

## Protected `main`

1 approving review from a Code Owner, required `ci` check (and `eval` when agent/prompt/rag
changed), conversation resolution, squash-merge only.
