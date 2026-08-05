# Setup Guide — Azure AI Foundry, Azure Cloud & External Services

This guide covers **every external setup** the Telecom Support Agent needs: local dev,
the two LLM providers (Azure AI Foundry primary, Groq backup), and the full Azure cloud
deployment (Container Apps, Key Vault, ACR, Azure Files, Application Insights).

> **This is a personal project.** It uses only your own personal accounts and generic
> placeholder names. It is **not** connected to, and must not use, any employer /
> organization subscription, tenant, resource, or data. All data in the app is synthetic.

Read the README for *what* the system is; this file is *how to stand it up*.

---

## 0. TL;DR — three ways to run

| Goal | Command | Credentials needed |
|---|---|---|
| Run fully offline (recommended first) | `LLM_PROVIDER=fake make dev` | **None** |
| Run with real models locally | fill `.env`, `make ingest`, `make dev` | Groq and/or Azure Foundry key |
| Run in the cloud | `bash infra/azure/provision.sh` → `make deploy` | Azure subscription |

The `fake` provider is deterministic and needs no network — do this first to confirm the
app works, *then* layer in real providers.

---

## 1. Prerequisites

Install these once. Versions are minimums.

| Tool | Why | Install |
|---|---|---|
| **Python 3.11+** | runtime | https://www.python.org/downloads/ |
| **uv** (optional, recommended) | fast, reproducible installs | `pip install uv` or https://docs.astral.sh/uv/ |
| **Git** | version control | https://git-scm.com/ |
| **Docker Desktop** | local stack + image builds | https://www.docker.com/products/docker-desktop/ |
| **Azure CLI** (`az`) 2.60+ | provisioning & deploy | https://learn.microsoft.com/cli/azure/install-azure-cli |
| **Azure account** | cloud hosting + Foundry | https://azure.microsoft.com/free/ (free tier is enough to start) |
| **Groq account** | backup LLM provider | https://console.groq.com/ |

Verify:

```bash
python --version        # 3.11+
az version              # 2.60+
docker --version
```

---

## 2. Clone & install

```bash
git clone <your-repo-url> telecom-support-agent
cd telecom-support-agent

# option A: uv (recommended)
uv sync

# option B: pip
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:        source .venv/bin/activate
pip install -e ".[dev,ui]"
```

Create your local env file (never commit it — it is git-ignored):

```bash
cp .env.example .env
```

---

## 3. Run offline first (no credentials)

This proves your install is good before any cloud setup. The index auto-builds from
`data/kb` on first start.

```bash
LLM_PROVIDER=fake make dev
# API  → http://localhost:8000  (docs at /docs)
# UI   → http://localhost:8501
```

Windows users: if `make dev` (which runs both) is awkward, run them in two terminals:

```powershell
$env:LLM_PROVIDER="fake"; uvicorn telecom_agent.api.main:app --reload --port 8000
# second terminal:
$env:API_BASE_URL="http://localhost:8000"; streamlit run ui/app.py
```

Smoke test:

```bash
curl -s http://localhost:8000/healthz
curl -s -X POST http://localhost:8000/v1/chat \
  -H "X-API-Key: dev-key-change-me" -H "Content-Type: application/json" \
  -d '{"message":"no internet in Pune since morning"}'
```

---

## 4. External setup — Groq (backup provider, chat only)

Groq is the failover provider. It is a **separate vendor from Azure**, which is exactly
why it is here: if your Azure subscription hits a quota wall, the demo still runs. Groq
has **no embeddings endpoint** — that is fine, embeddings only run at ingestion time on
the Azure path (README §4.3).

1. Sign up at **https://console.groq.com/**.
2. Create an API key: **API Keys → Create API Key**. Copy it (shown once).
3. Confirm the current production model ids — the catalogue changes:
   ```bash
   curl -s https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY" | python -m json.tool
   ```
4. Put the values in `.env`:
   ```bash
   GROQ_API_KEY=gsk_...
   GROQ_BASE_URL=https://api.groq.com/openai/v1
   GROQ_MODEL_CHAT_MAIN=openai/gpt-oss-120b     # verify against the list above
   GROQ_MODEL_CHAT_MINI=llama-3.1-8b-instant    # verify against the list above
   ```

Run against Groq directly:

```bash
LLM_PROVIDER=groq make dev
```

> If a model id 404s, `/readyz` fails **loudly at startup** (by design) rather than
> silently during the demo. Re-check the `/models` list and update `.env`.

---

## 5. External setup — Azure AI Foundry (primary provider)

Foundry gives the enterprise posture (Entra ID, content filtering, Azure Monitor, one
bill). You will create one Foundry resource and **three deployments** mapped to the code
aliases `chat-main`, `chat-mini`, `embed`.

### 5.1 Check model & region availability FIRST

Model availability varies by region — decide this **before** anything else (it is the
top risk in README §19).

```bash
az login
az account set --subscription "<your-personal-subscription-id>"
# Browse the catalogue in the Azure AI Foundry portal: https://ai.azure.com
```

Pick a region that offers a GPT-5-class model, a GPT-5-mini-class model, and
`text-embedding-3-small` (e.g. `eastus`, `swedencentral`, `westus3` — confirm live).

### 5.2 Create the Foundry resource

Portal path (simplest): **https://ai.azure.com → Create a project** (this creates the
underlying Azure AI Foundry / Cognitive Services resource and a project).

Or CLI:

```bash
RG=rg-telecom-agent
LOC=eastus                     # a region with the models you need
FOUNDRY=telecom-foundry-$RANDOM

az group create -n "$RG" -l "$LOC"

# Azure AI Foundry resource (kind=AIServices exposes the models inference endpoint)
az cognitiveservices account create \
  -n "$FOUNDRY" -g "$RG" -l "$LOC" \
  --kind AIServices --sku S0 \
  --custom-domain "$FOUNDRY" --yes
```

### 5.3 Create the three deployments (alias = deployment name)

The code routes on the **deployment name** via the `model` parameter (README §4.2), so
name your deployments exactly `chat-main`, `chat-mini`, `embed`.

```bash
# chat-main — a GPT-5-class model
az cognitiveservices account deployment create \
  -n "$FOUNDRY" -g "$RG" \
  --deployment-name chat-main \
  --model-name gpt-5 --model-format OpenAI \
  --sku-name Standard --sku-capacity 20

# chat-mini — a smaller/cheaper model for classify/verify
az cognitiveservices account deployment create \
  -n "$FOUNDRY" -g "$RG" \
  --deployment-name chat-mini \
  --model-name gpt-5-mini --model-format OpenAI \
  --sku-name Standard --sku-capacity 20

# embed — used ONLY at ingestion time
az cognitiveservices account deployment create \
  -n "$FOUNDRY" -g "$RG" \
  --deployment-name embed \
  --model-name text-embedding-3-small --model-version "1" --model-format OpenAI \
  --sku-name Standard --sku-capacity 20
```

> Exact `--model-name` / `--model-version` strings change over time. If a create call
> errors on the version, list what's available:
> `az cognitiveservices account list-models -n "$FOUNDRY" -g "$RG" -o table`
> and substitute. **Record the real model behind each alias** in `docs/model-strategy.md`.

### 5.4 Get the endpoint & key

```bash
az cognitiveservices account show   -n "$FOUNDRY" -g "$RG" \
  --query "properties.endpoint" -o tsv
az cognitiveservices account keys list -n "$FOUNDRY" -g "$RG" \
  --query "key1" -o tsv
```

The models-inference endpoint the code expects looks like:
`https://<resource-name>.services.ai.azure.com/models`
(the `.../models` suffix is important). Put it in `.env`:

```bash
AZURE_AI_ENDPOINT=https://<resource-name>.services.ai.azure.com/models
AZURE_AI_API_KEY=<key1>
AZURE_AI_DEPLOYMENT_CHAT_MAIN=chat-main
AZURE_AI_DEPLOYMENT_CHAT_MINI=chat-mini
AZURE_AI_DEPLOYMENT_EMBED=embed
```

### 5.5 Build the index against Foundry, then run

Embeddings run **once** at ingestion and are baked into `data/index/`:

```bash
LLM_PROVIDER=azure_foundry make ingest    # calls the `embed` deployment
LLM_PROVIDER=azure_foundry make dev
```

---

## 6. Environment variable reference

Every variable the app reads lives in `.env.example`; the important ones:

| Variable | Meaning |
|---|---|
| `LLM_PROVIDER` | `fake` \| `groq` \| `azure_foundry` — the **primary** provider |
| `LLM_FAILOVER_ENABLED` | allow automatic switch to Groq when Foundry fails |
| `API_KEY` | inbound key clients must send as `X-API-Key` on `/v1/*` |
| `AZURE_AI_ENDPOINT` / `AZURE_AI_API_KEY` | Foundry models endpoint + key |
| `AZURE_AI_DEPLOYMENT_*` | deployment names for the three aliases |
| `GROQ_API_KEY` / `GROQ_MODEL_*` | Groq key + verified model ids |
| `INDEX_DIR` / `DATABASE_URL` | FAISS index dir + SQLite path |
| `SESSION_TOKEN_BUDGET` | hard per-conversation token cap |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | telemetry; empty = stdout only |

---

## 7. Azure cloud deployment

Two container images (API + UI) run on **Azure Container Apps**, with secrets in **Key
Vault**, images in **Azure Container Registry**, the index + SQLite on an **Azure Files**
share, and telemetry in **Application Insights**. All of this is scripted.

### 7.1 One-command provisioning

```bash
az login
az account set --subscription "<your-personal-subscription-id>"
bash infra/azure/provision.sh          # edit the variables at the top first
```

`provision.sh` creates: resource group, ACR, the Foundry resource + 3 deployments, Key
Vault, Container Apps environment (+ Log Analytics), an Azure Files share, and
Application Insights. It is commented so you can run it section by section.

### 7.2 Store secrets in Key Vault

```bash
KV=<your-keyvault-name>
az keyvault secret set --vault-name "$KV" --name azure-ai-api-key --value "<foundry-key>"
az keyvault secret set --vault-name "$KV" --name groq-api-key     --value "<groq-key>"
az keyvault secret set --vault-name "$KV" --name inbound-api-key  --value "<a-strong-random-key>"
```

These are injected as Container App secrets by `deploy.sh` — keys are **never** baked into
images (README §16).

### 7.3 Build, push, deploy

```bash
make deploy        # === bash infra/azure/deploy.sh
# builds docker/Dockerfile.api + Dockerfile.ui, pushes to ACR,
# runs `az containerapp update` for both apps with Key Vault secret refs.
```

`infra/azure/containerapp.api.yaml` holds the API app spec: env vars, secret refs,
`/healthz` liveness + `/readyz` readiness probes, scale rules, and the Azure Files mount.

### 7.4 Publish the index as a release artifact (recommended)

So containers never re-embed (README §4.3):

```bash
make ingest                                  # build data/index locally with Foundry embeddings
# zip and attach data/index/ to a GitHub Release, then set INDEX_RELEASE_URL so
# `make fetch-index` / the container entrypoint can download it.
```

---

## 8. Verify the deployment

```bash
APP_URL=$(az containerapp show -n <api-app> -g "$RG" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

curl -s "https://$APP_URL/readyz" | python -m json.tool
# expect: index loaded=true, db=true, and BOTH providers probed
```

Run the failover drill (README §11, Day 4 — worth a rubric point):

```bash
make drill        # === bash scripts/failover_drill.sh
# breaks the Foundry key, confirms Groq serves with llm.degraded=true within ~20s, restores
```

---

## 9. Cost & quota notes

- **Request Foundry quota on day one, not deploy day.** Personal/free subscriptions have
  low default TPM; raise it via **Azure AI Foundry → Quotas**/support if needed.
- Foundry model prices: read them off the Azure pricing page for the exact deployments you
  chose and fill both columns in `docs/cost-model.md`. Placeholder prices are seeded in
  `src/telecom_agent/observability/cost.py` — replace them.
- Groq prices are cheap (backup path ≈ a tenth of a US cent per resolved turn).
- Container Apps **scale-to-zero** on the UI keeps the overnight bill near nothing.
- Embedding cost is one-off (~a fraction of a cent for the whole KB).

---

## 10. Teardown (avoid surprise charges)

Everything lives in one resource group — delete it to remove all of it:

```bash
az group delete -n "$RG" --yes --no-wait
```

Also delete the Groq API key from the Groq console if you no longer need it.

---

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/readyz` 503, `llm_azure_foundry=false` | wrong endpoint/key or deployment name | endpoint must end in `/models`; deployment names must be `chat-main`/`chat-mini`/`embed` |
| `/readyz` 503, `llm_groq=false` | Groq model id deprecated | re-check `GET /openai/v1/models`, update `.env` |
| `no index at ./data/index` | index not built | `make ingest`, or keep `AUTO_INGEST=true` (default) |
| `401 UNAUTHORIZED` on `/v1/*` | missing header | send `X-API-Key: <API_KEY>` |
| `database is locked` | concurrent writers | SQLite is single-writer; WAL is on; keep one API replica writing, or move to Postgres |
| deployment create fails on model version | version string moved | `az cognitiveservices account list-models ... -o table` and substitute |
| everything works but answers are generic | running the `fake` provider | set `LLM_PROVIDER` to a real provider and `make ingest` |

---

## 12. Security reminders (personal project)

- Never commit `.env`, keys, or the index. `.gitignore` already excludes them.
- Rotate any key that touches a terminal you shared.
- Use a **personal** Azure subscription and Groq account only — do not point this at any
  employer tenant, subscription, or data.
- The app logs are PII-redacted, but keep using **synthetic data only**.
