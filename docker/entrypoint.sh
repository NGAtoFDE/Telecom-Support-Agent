#!/usr/bin/env bash
# API container entrypoint: ensure the index exists and the DB is seeded, then exec the
# server command passed as CMD. Idempotent — safe to restart.
set -euo pipefail

INDEX_DIR="${INDEX_DIR:-./data/index}"

# 1) Build the index if it is not present. In fake mode this uses the offline
#    embedder; in azure_foundry mode it calls the Foundry `embed` deployment.
if [ ! -f "${INDEX_DIR}/dense.faiss" ]; then
  echo "entrypoint: no index at ${INDEX_DIR}; ingesting..."
  python scripts/ingest_kb.py || echo "entrypoint: ingest failed; API will auto-ingest on startup"
else
  echo "entrypoint: index present at ${INDEX_DIR}"
fi

# 2) Seed a few synthetic demo tickets if the DB looks empty (best-effort).
python scripts/seed_db.py || echo "entrypoint: seed skipped"

# 3) Hand off to CMD (uvicorn ...).
exec "$@"
