#!/usr/bin/env bash
# Provision the Azure footprint for the Telecom Support Agent (README §17).
#
# PERSONAL PROJECT — every value below is a placeholder. Edit the variables block, then:
#   az login
#   bash infra/azure/provision.sh
#
# Idempotent-ish: re-running skips resources that already exist where the CLI allows.
# Delete everything by deleting the resource group.
set -euo pipefail

# ---------------------------------------------------------------------------
# Variables — EDIT THESE. Do not commit real values.
# ---------------------------------------------------------------------------
SUFFIX="${SUFFIX:-$RANDOM}"                       # keeps globally-unique names unique
LOCATION="${LOCATION:-swedencentral}"             # pick a region with your model availability!
RG="${RG:-rg-telecom-agent}"
ACR="${ACR:-acrtelecom${SUFFIX}}"                 # 5-50 alphanumeric, globally unique
FOUNDRY="${FOUNDRY:-aif-telecom-${SUFFIX}}"       # Azure AI Foundry (AIServices) resource
KV="${KV:-kv-telecom-${SUFFIX}}"                  # 3-24 chars, globally unique
ACA_ENV="${ACA_ENV:-cae-telecom}"                 # Container Apps environment
LAW="${LAW:-law-telecom}"                         # Log Analytics workspace
APPINSIGHTS="${APPINSIGHTS:-appi-telecom}"
STORAGE="${STORAGE:-sttelecom${SUFFIX}}"          # 3-24 lowercase alphanumeric
SHARE="${SHARE:-agentdata}"                       # Azure Files share for index + sqlite

# Model deployments (aliases the code routes on — see README §4.2). Adjust model names to
# what is actually available in your region/subscription.
DEP_CHAT_MAIN="${DEP_CHAT_MAIN:-chat-main}"
DEP_CHAT_MINI="${DEP_CHAT_MINI:-chat-mini}"
DEP_EMBED="${DEP_EMBED:-embed}"
MODEL_CHAT_MAIN="${MODEL_CHAT_MAIN:-gpt-5}"
MODEL_CHAT_MINI="${MODEL_CHAT_MINI:-gpt-5-mini}"
MODEL_EMBED="${MODEL_EMBED:-text-embedding-3-small}"

echo "== Provisioning into RG=${RG} LOCATION=${LOCATION} =="

# ---------------------------------------------------------------------------
az extension add --name containerapp --upgrade -y >/dev/null 2>&1 || true
az provider register --namespace Microsoft.App >/dev/null 2>&1 || true
az provider register --namespace Microsoft.OperationalInsights >/dev/null 2>&1 || true

echo "-- resource group"
az group create --name "${RG}" --location "${LOCATION}" -o none

echo "-- container registry"
az acr create --resource-group "${RG}" --name "${ACR}" --sku Basic --admin-enabled true -o none

echo "-- azure ai foundry (AIServices) resource"
az cognitiveservices account create \
  --name "${FOUNDRY}" --resource-group "${RG}" --location "${LOCATION}" \
  --kind AIServices --sku S0 --yes -o none

FOUNDRY_ENDPOINT=$(az cognitiveservices account show -n "${FOUNDRY}" -g "${RG}" \
  --query "properties.endpoint" -o tsv)
FOUNDRY_KEY=$(az cognitiveservices account keys list -n "${FOUNDRY}" -g "${RG}" \
  --query "key1" -o tsv)

echo "-- model deployments (aliases: ${DEP_CHAT_MAIN}, ${DEP_CHAT_MINI}, ${DEP_EMBED})"
# NOTE: --model-version and --sku capacity vary by model/region. Check availability with:
#   az cognitiveservices account list-models -n "${FOUNDRY}" -g "${RG}" -o table
for pair in "${DEP_CHAT_MAIN}:${MODEL_CHAT_MAIN}" \
            "${DEP_CHAT_MINI}:${MODEL_CHAT_MINI}" \
            "${DEP_EMBED}:${MODEL_EMBED}"; do
  dep="${pair%%:*}"; model="${pair##*:}"
  echo "   deploying ${model} as '${dep}'"
  az cognitiveservices account deployment create \
    --name "${FOUNDRY}" --resource-group "${RG}" \
    --deployment-name "${dep}" \
    --model-name "${model}" --model-format OpenAI \
    --sku-capacity 10 --sku-name "Standard" -o none || \
    echo "   (deployment '${dep}' may already exist or need a different model-version)"
done

echo "-- key vault"
az keyvault create --name "${KV}" --resource-group "${RG}" --location "${LOCATION}" -o none
az keyvault secret set --vault-name "${KV}" --name "azure-ai-api-key" --value "${FOUNDRY_KEY}" -o none
az keyvault secret set --vault-name "${KV}" --name "azure-ai-endpoint" --value "${FOUNDRY_ENDPOINT}models" -o none
# Set your inbound API key manually (kept out of scripts on purpose):
echo "   >> set inbound API key secret:"
echo "      az keyvault secret set --vault-name ${KV} --name inbound-api-key --value <YOUR_API_KEY>"
echo "   >> set Jira secrets:"
echo "      az keyvault secret set --vault-name ${KV} --name jira-api-token --value <YOUR_JIRA_TOKEN>"
echo "   >> set Discord secrets:"
echo "      az keyvault secret set --vault-name ${KV} --name discord-bot-token --value <YOUR_DISCORD_TOKEN>"

echo "-- log analytics + application insights"
az monitor log-analytics workspace create --resource-group "${RG}" \
  --workspace-name "${LAW}" -o none
LAW_ID=$(az monitor log-analytics workspace show -g "${RG}" --workspace-name "${LAW}" \
  --query customerId -o tsv)
LAW_KEY=$(az monitor log-analytics workspace get-shared-keys -g "${RG}" --workspace-name "${LAW}" \
  --query primarySharedKey -o tsv)
az monitor app-insights component create --app "${APPINSIGHTS}" --location "${LOCATION}" \
  --resource-group "${RG}" --workspace "${LAW}" -o none || true
APPI_CONN=$(az monitor app-insights component show --app "${APPINSIGHTS}" -g "${RG}" \
  --query connectionString -o tsv || echo "")

echo "-- storage account + files share (FAISS index + SQLite)"
az storage account create --name "${STORAGE}" --resource-group "${RG}" \
  --location "${LOCATION}" --sku Standard_LRS -o none
STORAGE_KEY=$(az storage account keys list -g "${RG}" -n "${STORAGE}" --query "[0].value" -o tsv)
az storage share create --name "${SHARE}" --account-name "${STORAGE}" \
  --account-key "${STORAGE_KEY}" -o none

echo "-- container apps environment"
az containerapp env create --name "${ACA_ENV}" --resource-group "${RG}" \
  --location "${LOCATION}" \
  --logs-workspace-id "${LAW_ID}" --logs-workspace-key "${LAW_KEY}" -o none

echo "-- mounting the files share into the environment"
az containerapp env storage set --name "${ACA_ENV}" --resource-group "${RG}" \
  --storage-name "${SHARE}" \
  --azure-file-account-name "${STORAGE}" \
  --azure-file-account-key "${STORAGE_KEY}" \
  --azure-file-share-name "${SHARE}" \
  --access-mode ReadWrite -o none

cat <<EOF

== Provisioning complete ==
  Resource group : ${RG}
  ACR            : ${ACR}.azurecr.io
  Foundry endpt  : ${FOUNDRY_ENDPOINT}models
  Key Vault      : ${KV}
  ACA env        : ${ACA_ENV}
  App Insights   : ${APPINSIGHTS}
  Files share    : ${SHARE} on ${STORAGE}

Next:
  1. Set the inbound-api-key, jira-api-token, and discord-bot-token secrets in Key Vault (see above).
  2. Verify model deployments:  az cognitiveservices account deployment list -n ${FOUNDRY} -g ${RG} -o table
  3. Deploy the apps:           RG=${RG} ACR=${ACR} ACA_ENV=${ACA_ENV} bash infra/azure/deploy.sh
EOF
