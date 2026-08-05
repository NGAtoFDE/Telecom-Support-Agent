#!/usr/bin/env bash
# Post one request to a running stack and assert HTTP 200.
# Respects API_BASE_URL and API_KEY; falls back to local defaults.
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-key-change-me}"

echo "smoke: ${API_BASE_URL}"

# 1) liveness
code=$(curl -sS -o /dev/null -w '%{http_code}' "${API_BASE_URL}/healthz")
echo "  GET  /healthz -> ${code}"
[ "${code}" = "200" ] || { echo "healthz failed"; exit 1; }

# 2) a real triage turn
body=$(cat <<'JSON'
{"message": "No internet on my phone since morning in Pune, prepaid."}
JSON
)

resp=$(curl -sS -w '\n%{http_code}' \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -X POST "${API_BASE_URL}/v1/chat" \
  -d "${body}")

http_code=$(echo "${resp}" | tail -n1)
payload=$(echo "${resp}" | sed '$d')

echo "  POST /v1/chat -> ${http_code}"
echo "${payload}" | sed 's/^/    /'

[ "${http_code}" = "200" ] || { echo "smoke test FAILED"; exit 1; }
echo "smoke test OK"
