# Infrastructure

Scripted Azure deployment for the Telecom Support Agent. Reproducible with the `az` CLI —
no hand-clicking, no Terraform state to manage (README §12).

> This is a **personal project**. Every name below is a placeholder. Nothing here
> references any company subscription, tenant, region, or resource. Set your own values
> in the variables block at the top of each script before running.

## What is deployed this week (`azure/`)

| Script / file | Provisions |
|---|---|
| `azure/provision.sh` | Resource Group, ACR, Azure AI Foundry resource + `chat-main`/`chat-mini`/`embed` deployments, Key Vault, Container Apps environment + Log Analytics, Azure Files share, Application Insights |
| `azure/deploy.sh` | Builds + pushes both images to ACR and updates both Container Apps; wires Key Vault secrets |
| `azure/containerapp.api.yaml` | Declarative Container App spec for the API: env, secret refs, `/healthz` + `/readyz` probes, scale 1–3, Azure Files mount |

Deploy order:

```bash
# 1. one-time infrastructure (edit the variables block first)
bash infra/azure/provision.sh

# 2. build, push and roll out application revisions
bash infra/azure/deploy.sh          # or: make deploy
```

## What is design-only (`design/`)

`design/production-topology.md` documents the target-state architecture we deliberately
descoped for a 7-day build (README §12): Azure Database for PostgreSQL, Azure AI Search,
APIM, private endpoints + VNet, and managed identity to Foundry. Naming the cuts and
designing them is itself a deliverable.

## Security posture

**Implemented:** HTTPS only, secrets in Key Vault injected as Container App secrets (never
baked into images), API-key auth + per-key rate limiting on `/v1/*`, no PII in logs.

**Deferred (documented, not implemented):** managed identity instead of a Foundry key,
private endpoints + VNet, APIM for quotas/throttling, Entra ID sign-in with role-based
ticket visibility. See `design/production-topology.md`.
