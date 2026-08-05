# Responsible AI Controls

Each control has an implementation location in this codebase and a concrete piece of
evidence. This is the checklist from README §16, made specific to the code as built.

| Control | Implementation (file) | Evidence |
|---|---|---|
| Citations mandatory | `prompts/answer/v1.yaml` forbids uncited claims; `agent/nodes/verify.py` enforces groundedness; `agent/nodes/respond.py` narrows citations to those referenced | `evals/runners/run_groundedness.py` report |
| Answer-not-found behaviour | retrieval floor in `agent/edges.py::after_retrieve` + verify failure in `after_verify` → escalate | `evals/datasets/escalation.jsonl` results |
| No advice outside the KB | scope fence in `prompts/system/base.yaml`; off-scope → escalate | `evals/datasets/adversarial.jsonl` refusal rate |
| Human review for high-risk | `agent/policies/routing.py::route` sends every P1 → `NOC_L2` and every billing dispute → `BILLING_OPS`, regardless of confidence; `after_classify` checks P1 before confidence | `tests/unit/test_routing_policy.py` |
| Privacy | synthetic data only; `observability/logging.py::redact` strips phone/ICCID/email/Aadhaar; no PII in prompts or index | redaction unit test, repo secret scan (pre-commit) |
| Access control | `api/middleware/auth.py` (API-key), `api/middleware/rate_limit.py`, Key Vault secrets, no keys in images | `middleware/auth.py`, `infra/azure/containerapp.api.yaml` |
| Prompt-injection resistance | `llm/guards.py::scan_for_injection`; user text never interpolated into tool arguments — `tools/validators.py` coerces/cleans every tool arg | `validators.py` + adversarial suite |
| Provider transparency | `degraded` flag in the API `llm` block and a banner in the UI (`ui/components/degraded_banner.py`) | screenshot in the deck |
| Content safety | Azure AI Foundry content filtering on the primary path; `ContentFiltered` is not retried, it escalates (`llm/router.py`) | filter-block failure-mode test |
| Auditability | `agent/nodes/persist.py` writes every turn with prompt version, provider, sources, groundedness, tokens, cost (`store/models.py::TurnRow`) | `store/models.py` |

## Known asymmetry (state it plainly)

Azure content filtering applies on the Foundry path; the Groq (degraded) path relies on our
own prompt-level guards (`prompts/system/base.yaml` scope fence + `llm/guards.py` scanner).
Groq's Prompt Guard models are the documented v2 option for closing that gap.

## UI disclaimer

The console surfaces: *this is a support-assistance demo on synthetic data; it makes no
account-specific commitments and executes no billing actions.*
