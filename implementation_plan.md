# Step-by-Step Guide: Run Locally → Dockerize → Deploy to Azure (Portal UI)

Complete walkthrough using the **Azure Portal Web UI** — no CLI commands for Azure setup/deployment.

> [!IMPORTANT]
> This guide uses **GPT-5 series** models (GPT-5, GPT-5-mini). The older GPT-4.1 models are deprecated.

---

## Phase 1 — Prerequisites (Install Once)

| Tool | Why | Install Link |
|---|---|---|
| **Python 3.11+** | Runtime | https://www.python.org/downloads/ |
| **Git** | Version control | https://git-scm.com/ |
| **Docker Desktop** | Build & run containers | https://www.docker.com/products/docker-desktop/ |
| **Azure account** | Cloud hosting + Foundry | https://azure.microsoft.com/free/ |

**Verify** (PowerShell):

```powershell
python --version        # 3.11+
docker --version
git --version
```

---

## Phase 2 — Set Up Azure AI Foundry (Portal UI)

### Step 2.1 — Create a Resource Group

1. Go to **https://portal.azure.com**
2. Search for **"Resource groups"** in the top search bar
3. Click **"+ Create"**
4. Fill in:
   - **Subscription**: Your personal subscription
   - **Resource group**: `rg-telecom-agent`
   - **Region**: `East US` (or any region with GPT-5 availability)
5. Click **"Review + create"** → **"Create"**

---

### Step 2.2 — Create an Azure AI Foundry Resource

1. Go to **https://ai.azure.com**
2. Sign in with your Azure account
3. Click **"+ Create project"** (top-left or home page)
4. Fill in:
   - **Project name**: `telecom-agent-project`
   - **Hub**: Click **"Create new hub"**
     - **Hub name**: `telecom-foundry-hub`
     - **Subscription**: Your personal subscription
     - **Resource group**: `rg-telecom-agent` (the one you just created)
     - **Region**: `East US` (must match where GPT-5 models are available)
   - Leave other defaults
5. Click **"Next"** → **"Create"**
6. Wait for the project to be created (takes 1–2 minutes)

---

### Step 2.3 — Deploy the 3 Models

You need to deploy **3 models** with specific deployment names that the code expects.

#### Deploy `chat-main` (GPT-5)

1. In your project on **https://ai.azure.com**, click **"Model catalog"** in the left sidebar
2. Search for **"GPT-5"**
3. Click on **GPT-5** → Click **"Deploy"**
4. Choose **"Deploy with Azure AI Services"**
5. Configure:
   - **Deployment name**: `chat-main` ← **must be exactly this**
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 20K (adjust as needed)
6. Click **"Deploy"**

#### Deploy `chat-mini` (GPT-5 Mini)

1. Go back to **"Model catalog"**
2. Search for **"GPT-5 mini"**
3. Click on it → **"Deploy"**
4. Configure:
   - **Deployment name**: `chat-mini` ← **must be exactly this**
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 20K
5. Click **"Deploy"**

#### Deploy `embed` (text-embedding-3-small)

1. Go back to **"Model catalog"**
2. Search for **"text-embedding-3-small"**
3. Click on it → **"Deploy"**
4. Configure:
   - **Deployment name**: `embed` ← **must be exactly this**
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 20K
5. Click **"Deploy"**

> [!CAUTION]
> The deployment names **must** be exactly `chat-main`, `chat-mini`, and `embed`. The code routes requests based on these names.

---

### Step 2.4 — Get Your Endpoint & API Key

1. In your project on **https://ai.azure.com**, click **"Management center"** (gear icon) or go to **"Project settings"**
2. Look for **"Connected resources"** → click on your AI Services resource
3. You will see:
   - **Endpoint**: Something like `https://telecom-foundry-hub-xxxx.services.ai.azure.com`
   - **Keys**: Click **"Show keys"** → copy **Key 1**

**Alternative way via Azure Portal:**
1. Go to **https://portal.azure.com**
2. Search for **"Cognitive Services"** or **"Azure AI Services"** in the search bar
3. Click on your resource (the one created by the Foundry hub)
4. In the left menu, click **"Keys and Endpoint"**
5. Copy:
   - **Key 1** → This is your `AZURE_AI_API_KEY`
   - **Endpoint** → Add `/models` at the end for `AZURE_AI_ENDPOINT`

> [!IMPORTANT]
> Your endpoint must end with `/models`. Example:
> ```
> https://telecom-foundry-hub-xxxx.services.ai.azure.com/models
> ```

**Write these down — you'll use them in Phase 3:**

| Value | Where to find | Example |
|---|---|---|
| `AZURE_AI_ENDPOINT` | Portal → Keys and Endpoint + `/models` | `https://xxx.services.ai.azure.com/models` |
| `AZURE_AI_API_KEY` | Portal → Keys and Endpoint → Key 1 | `abc123...` |

---

## Phase 3 — Run Locally (Without Docker)

### Step 3.1 — Install Dependencies

```powershell
cd C:\Users\abhis\OneDrive\Desktop\Telecom_Agent

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -e ".[dev,ui]"
```

### Step 3.2 — Create & Configure `.env`

```powershell
Copy-Item .env.example .env
```

Open `.env` in your editor and fill in these values:

```env
APP_ENV=local
API_KEY=dev-key-change-me
LLM_PROVIDER=azure_foundry

AZURE_AI_ENDPOINT=https://<your-resource>.services.ai.azure.com/models
AZURE_AI_API_KEY=<Key-1-from-portal>
AZURE_AI_DEPLOYMENT_CHAT_MAIN=chat-main
AZURE_AI_DEPLOYMENT_CHAT_MINI=chat-mini
AZURE_AI_DEPLOYMENT_EMBED=embed
```

> [!NOTE]
> The deployment names (`chat-main`, `chat-mini`, `embed`) are **aliases** — they map to GPT-5, GPT-5-mini, and text-embedding-3-small respectively via the Azure portal. The code never hardcodes model names.

### Step 3.3 — (Optional) Test Offline First

Run with the fake provider to verify the install works before using real keys:

```powershell
# Terminal 1 — API
$env:LLM_PROVIDER="fake"
uvicorn telecom_agent.api.main:app --reload --port 8000

# Terminal 2 — UI
$env:API_BASE_URL="http://localhost:8000"
streamlit run ui/app.py
```

- API → http://localhost:8000 (Swagger docs at http://localhost:8000/docs)
- UI → http://localhost:8501

### Step 3.4 — Build the Index with Foundry Embeddings

```powershell
$env:LLM_PROVIDER="azure_foundry"
python scripts/ingest_kb.py
```

### Step 3.5 — Run with Azure Foundry (GPT-5)

```powershell
# Terminal 1 — API
$env:LLM_PROVIDER="azure_foundry"
uvicorn telecom_agent.api.main:app --reload --port 8000

# Terminal 2 — UI
$env:API_BASE_URL="http://localhost:8000"
streamlit run ui/app.py
```

### Step 3.6 — Smoke Test

```powershell
# Health check
Invoke-RestMethod http://localhost:8000/healthz

# Readiness (confirms GPT-5 via Foundry is connected)
Invoke-RestMethod http://localhost:8000/readyz

# Test chat
$body = '{"message":"no internet in Pune since morning"}'
Invoke-RestMethod -Method POST http://localhost:8000/v1/chat `
  -Headers @{"X-API-Key"="dev-key-change-me"; "Content-Type"="application/json"} `
  -Body $body
```

✅ If `/readyz` shows `llm_azure_foundry=true`, your Foundry key is working with GPT-5!

---

## Phase 4 — Containerize with Docker

### Step 4.1 — Start Docker Desktop

Open **Docker Desktop** and wait until it shows "Running".

### Step 4.2 — Build & Run with Docker Compose

```powershell
cd C:\Users\abhis\OneDrive\Desktop\Telecom_Agent\docker

# ---- Option A: Run with fake provider (no credentials) ----
docker compose up --build

# ---- Option B: Run with Azure Foundry (GPT-5) ----
$env:LLM_PROVIDER="azure_foundry"
$env:AZURE_AI_ENDPOINT="https://<your-resource>.services.ai.azure.com/models"
$env:AZURE_AI_API_KEY="<your-key>"
docker compose up --build
```

- **API** → http://localhost:8000
- **UI** → http://localhost:8501

### Step 4.3 — Verify

```powershell
Invoke-RestMethod http://localhost:8000/healthz
```

### Step 4.4 — Stop

```powershell
cd C:\Users\abhis\OneDrive\Desktop\Telecom_Agent\docker
docker compose down
```

---

## Phase 5 — Deploy to Azure (Portal UI)

### Step 5.1 — Create Azure Container Registry (ACR)

1. Go to **https://portal.azure.com**
2. Search for **"Container registries"**
3. Click **"+ Create"**
4. Fill in:
   - **Subscription**: Your personal subscription
   - **Resource group**: `rg-telecom-agent`
   - **Registry name**: `acrtelecomagent` (must be globally unique, lowercase alphanumeric)
   - **Location**: `East US`
   - **SKU**: `Basic`
5. Click **"Review + create"** → **"Create"**
6. After creation, go to the resource → **"Settings"** → **"Access keys"**
7. **Enable** "Admin user"
8. Copy the **Login server**, **Username**, and **Password**

---

### Step 5.2 — Push Docker Images to ACR

```powershell
cd C:\Users\abhis\OneDrive\Desktop\Telecom_Agent

# Login to your ACR
docker login <your-acr-name>.azurecr.io -u <username> -p <password>

# Build the images
docker build -t <your-acr-name>.azurecr.io/telecom-api:latest -f docker/Dockerfile.api .
docker build -t <your-acr-name>.azurecr.io/telecom-ui:latest -f docker/Dockerfile.ui .

# Push to ACR
docker push <your-acr-name>.azurecr.io/telecom-api:latest
docker push <your-acr-name>.azurecr.io/telecom-ui:latest
```

---

### Step 5.3 — Create a Key Vault for Secrets

1. Go to **https://portal.azure.com**
2. Search for **"Key vaults"**
3. Click **"+ Create"**
4. Fill in:
   - **Resource group**: `rg-telecom-agent`
   - **Key vault name**: `kv-telecom-agent` (must be globally unique)
   - **Region**: `East US`
   - **Pricing tier**: Standard
5. Click **"Review + create"** → **"Create"**
6. Go to the Key Vault → **"Secrets"** → **"+ Generate/Import"**
7. Add these 3 secrets one by one:

| Name | Value |
|---|---|
| `azure-ai-api-key` | Your Foundry Key 1 from Phase 2 |
| `groq-api-key` | Your Groq API key (if you have one, or any placeholder) |
| `inbound-api-key` | A strong random API key for your app (e.g., `telecom-prod-key-2026`) |

---

### Step 5.4 — Create the API Container App

1. Go to **https://portal.azure.com**
2. Search for **"Container Apps"**
3. Click **"+ Create"** → **"Container App"**
4. **Basics tab:**
   - **Subscription**: Your personal subscription
   - **Resource group**: `rg-telecom-agent`
   - **Container app name**: `telecom-api`
   - **Region**: `East US`
   - **Container Apps Environment**: Click **"Create new"**
     - **Name**: `cae-telecom`
     - Click **"Create"**
5. **Container tab:**
   - Uncheck **"Use quickstart image"**
   - **Image source**: Azure Container Registry
   - **Registry**: `<your-acr-name>.azurecr.io`
   - **Image**: `telecom-api`
   - **Image tag**: `latest`
   - **CPU and Memory**: 1 vCPU, 2 Gi memory
   - **Environment variables** — add each one:

   | Name | Source | Value |
   |---|---|---|
   | `APP_ENV` | Manual | `prod` |
   | `LLM_PROVIDER` | Manual | `azure_foundry` |
   | `LLM_FAILOVER_ENABLED` | Manual | `true` |
   | `AZURE_AI_ENDPOINT` | Manual | `https://<your-resource>.services.ai.azure.com/models` |
   | `AZURE_AI_API_KEY` | Manual | `<your-foundry-key>` |
   | `API_KEY` | Manual | `<your-inbound-api-key>` |
   | `INDEX_DIR` | Manual | `./data/index` |
   | `DATABASE_URL` | Manual | `sqlite:///./data/app.db` |

6. **Ingress tab:**
   - **Ingress**: ✅ Enabled
   - **Ingress traffic**: Accepting traffic from anywhere
   - **Ingress type**: HTTP
   - **Target port**: `8000`
7. Click **"Review + create"** → **"Create"**
8. Wait for deployment to complete (2–5 minutes)
9. Go to the resource → copy the **Application URL**

---

### Step 5.5 — Create the UI Container App

1. Go to **"Container Apps"** → **"+ Create"** → **"Container App"**
2. **Basics tab:**
   - **Resource group**: `rg-telecom-agent`
   - **Container app name**: `telecom-ui`
   - **Region**: `East US`
   - **Container Apps Environment**: Select **`cae-telecom`** (already created)
3. **Container tab:**
   - Uncheck **"Use quickstart image"**
   - **Image source**: Azure Container Registry
   - **Registry**: `<your-acr-name>.azurecr.io`
   - **Image**: `telecom-ui`
   - **Image tag**: `latest`
   - **CPU and Memory**: 0.5 vCPU, 1 Gi memory
   - **Environment variables**:

   | Name | Source | Value |
   |---|---|---|
   | `API_BASE_URL` | Manual | `https://telecom-api.xxx.azurecontainerapps.io` ← API URL from Step 5.4 |
   | `API_KEY` | Manual | `<your-inbound-api-key>` (same as the API app's `API_KEY`) |

4. **Ingress tab:**
   - **Ingress**: ✅ Enabled
   - **Ingress traffic**: Accepting traffic from anywhere
   - **Target port**: `8501`
5. Click **"Review + create"** → **"Create"**

---

### Step 5.6 — Verify the Deployment

1. Go to **Container Apps** → **`telecom-api`** → copy the **Application URL**
2. Open in browser: `https://<api-url>/healthz` → should return `{"status":"ok"}`
3. Open: `https://<api-url>/readyz` → should show GPT-5 via Foundry as healthy
4. Go to **Container Apps** → **`telecom-ui`** → copy the **Application URL**
5. Open the UI URL in your browser → **Your Telecom Agent is live!** 🎉

---

## Phase 6 — Teardown (Avoid Surprise Charges)

1. Go to **https://portal.azure.com**
2. Search for **"Resource groups"**
3. Click on **`rg-telecom-agent`**
4. Click **"Delete resource group"**
5. Type the resource group name to confirm → Click **"Delete"**

---

## Models Summary

| Deployment Name | Model | Purpose |
|---|---|---|
| `chat-main` | **GPT-5** | Main reasoning — `draft_answer`, `verify` |
| `chat-mini` | **GPT-5 Mini** | Lighter tasks — `classify`, `clarify` |
| `embed` | **text-embedding-3-small** | One-time ingestion only |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/readyz` shows `llm_azure_foundry=false` | Endpoint must end in `/models`; verify deployment names are `chat-main`, `chat-mini`, `embed` |
| Model not found in catalog | GPT-5 may not be available in your region — try `eastus` or `swedencentral` |
| Container App stuck in "Provisioning" | Check **"Log stream"** for errors |
| `no index at ./data/index` | The entrypoint auto-ingests; check container logs |
| Docker push fails with "unauthorized" | Re-run `docker login`; ensure ACR admin user is enabled |
| UI shows "Connection refused" | `API_BASE_URL` must point to the API's Application URL with `https://` |
