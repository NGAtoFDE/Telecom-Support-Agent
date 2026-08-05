#!/usr/bin/env bash
# Build + push both images to ACR and roll out both Container Apps (README §17).
# Pulls secrets from Key Vault and wires them as Container App secrets.
#
#   RG=rg-telecom-agent ACR=acrtelecom123 ACA_ENV=cae-telecom bash infra/azure/deploy.sh
set -euo pipefail

# ---- variables (must match provision.sh) ----
RG="${RG:-rg-telecom-agent}"
ACR="${ACR:?set ACR to your registry name, e.g. acrtelecom123}"
ACA_ENV="${ACA_ENV:-cae-telecom}"
KV="${KV:-}"                                  # optional: pull secrets from this vault
SHARE="${SHARE:-agentdata}"
TAG="${TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo latest)}"

API_APP="${API_APP:-telecom-api}"
UI_APP="${UI_APP:-telecom-ui}"
REGISTRY="${ACR}.azurecr.io"

echo "== Building images (tag=${TAG}) via ACR build =="
az acr build --registry "${ACR}" --image "telecom-api:${TAG}" \
  --file docker/Dockerfile.api .
az acr build --registry "${ACR}" --image "telecom-ui:${TAG}" \
  --file docker/Dockerfile.ui .

ACR_USER=$(az acr credential show -n "${ACR}" --query username -o tsv)
ACR_PASS=$(az acr credential show -n "${ACR}" --query "passwords[0].value" -o tsv)

# ---- resolve secrets from Key Vault (fall back to env) ----
kv_get() { [ -n "${KV}" ] && az keyvault secret show --vault-name "${KV}" --name "$1" --query value -o tsv 2>/dev/null || true; }
AZURE_AI_ENDPOINT="${AZURE_AI_ENDPOINT:-$(kv_get azure-ai-endpoint)}"
AZURE_AI_API_KEY="${AZURE_AI_API_KEY:-$(kv_get azure-ai-api-key)}"
INBOUND_API_KEY="${INBOUND_API_KEY:-$(kv_get inbound-api-key)}"
JIRA_API_TOKEN="${JIRA_API_TOKEN:-$(kv_get jira-api-token)}"
DISCORD_BOT_TOKEN="${DISCORD_BOT_TOKEN:-$(kv_get discord-bot-token)}"
APPI_CONN="${APPLICATIONINSIGHTS_CONNECTION_STRING:-}"

echo "== Deploy API container app =="
if az containerapp show -n "${API_APP}" -g "${RG}" >/dev/null 2>&1; then
  az containerapp update -n "${API_APP}" -g "${RG}" \
    --image "${REGISTRY}/telecom-api:${TAG}" -o none
else
  az containerapp create -n "${API_APP}" -g "${RG}" --environment "${ACA_ENV}" \
    --image "${REGISTRY}/telecom-api:${TAG}" \
    --registry-server "${REGISTRY}" --registry-username "${ACR_USER}" --registry-password "${ACR_PASS}" \
    --target-port 8000 --ingress external \
    --min-replicas 1 --max-replicas 3 \
    --secrets azure-ai-api-key="${AZURE_AI_API_KEY}" \
              inbound-api-key="${INBOUND_API_KEY}" appi-conn="${APPI_CONN}" \
              jira-api-token="${JIRA_API_TOKEN}" discord-bot-token="${DISCORD_BOT_TOKEN}" \
    --env-vars APP_ENV=prod LLM_PROVIDER=azure_foundry LLM_FAILOVER_ENABLED=false \
              AZURE_AI_ENDPOINT="${AZURE_AI_ENDPOINT}" \
              AZURE_AI_API_KEY=secretref:azure-ai-api-key \
              API_KEY=secretref:inbound-api-key \
              JIRA_API_TOKEN=secretref:jira-api-token \
              DISCORD_BOT_TOKEN=secretref:discord-bot-token \
              APPLICATIONINSIGHTS_CONNECTION_STRING=secretref:appi-conn \
              INDEX_DIR=/data/index DATABASE_URL=sqlite:////data/app.db \
    -o none
  # Mount the Azure Files share for index + sqlite persistence.
  echo "   (attach the '${SHARE}' volume via 'az containerapp update --yaml infra/azure/containerapp.api.yaml')"
fi

API_FQDN=$(az containerapp show -n "${API_APP}" -g "${RG}" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo "== Deploy UI container app =="
if az containerapp show -n "${UI_APP}" -g "${RG}" >/dev/null 2>&1; then
  az containerapp update -n "${UI_APP}" -g "${RG}" \
    --image "${REGISTRY}/telecom-ui:${TAG}" \
    --set-env-vars API_BASE_URL="https://${API_FQDN}" -o none
else
  az containerapp create -n "${UI_APP}" -g "${RG}" --environment "${ACA_ENV}" \
    --image "${REGISTRY}/telecom-ui:${TAG}" \
    --registry-server "${REGISTRY}" --registry-username "${ACR_USER}" --registry-password "${ACR_PASS}" \
    --target-port 8501 --ingress external \
    --min-replicas 0 --max-replicas 2 \
    --secrets inbound-api-key="${INBOUND_API_KEY}" \
    --env-vars API_BASE_URL="https://${API_FQDN}" API_KEY=secretref:inbound-api-key \
    -o none
fi

UI_FQDN=$(az containerapp show -n "${UI_APP}" -g "${RG}" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

cat <<EOF

== Deployed ==
  API : https://${API_FQDN}   (health: https://${API_FQDN}/healthz)
  UI  : https://${UI_FQDN}

Smoke test:
  API_BASE_URL=https://${API_FQDN} API_KEY=<your-key> bash scripts/smoke.sh
EOF
