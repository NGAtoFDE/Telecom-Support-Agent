# Telecom Support Agent — one-word entrypoints.
# POSIX make. Windows users without `make` can run the underlying commands directly
# (see README §13); each recipe is a single, copy-pasteable command.

# Provider defaults to fake so every target works offline with zero credentials.
export LLM_PROVIDER ?= fake
API_HOST ?= 0.0.0.0
API_PORT ?= 8000
UI_PORT  ?= 8501
PY       ?= python

.DEFAULT_GOAL := help
.PHONY: help install dev api ui dev-all test lint type ingest fetch-index seed \
        eval smoke openapi deploy clean

help: ## List available targets
	@echo "Telecom Support Agent — make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Editable install with dev + ui extras
	pip install -e ".[dev,ui]"

api: ## Run the FastAPI service with hot reload (:8000)
	uvicorn telecom_agent.api.main:app --reload --host $(API_HOST) --port $(API_PORT)

ui: ## Run the Streamlit console (:8501)
	streamlit run ui/app.py --server.port $(UI_PORT)

# `make dev` runs the API in the foreground. Run `make ui` in a second terminal.
# `make dev-all` backgrounds the API and then launches the UI (POSIX shells only).
dev: api ## Run API (:8000). Run `make ui` in another terminal for the console.

dev-all: ## Run API in the background + UI in the foreground (POSIX shells)
	uvicorn telecom_agent.api.main:app --reload --host $(API_HOST) --port $(API_PORT) & \
	echo "API pid $$! on :$(API_PORT)"; \
	streamlit run ui/app.py --server.port $(UI_PORT)

lint: ## Ruff lint
	ruff check src tests ui evals scripts

type: ## mypy type-check
	mypy src

test: ## ruff + mypy + pytest (fake provider, no live LLM calls)
	ruff check src tests ui evals scripts
	mypy src
	LLM_PROVIDER=fake pytest -q

ingest: ## Rebuild FAISS + BM25 from data/kb (uses configured embed provider)
	$(PY) scripts/ingest_kb.py

fetch-index: ## Download the published index release artifact (INDEX_RELEASE_URL)
	$(PY) scripts/fetch_index.py

seed: ## Create the schema and load a few synthetic demo tickets
	$(PY) scripts/seed_db.py

eval: ## Run all eval runners against the configured provider
	$(PY) -m evals.runners.run_retrieval
	$(PY) -m evals.runners.run_classification
	$(PY) -m evals.runners.run_groundedness
	$(PY) -m evals.runners.run_e2e


smoke: ## POST one request to a running stack and assert 200
	bash scripts/smoke.sh

openapi: ## Regenerate docs/openapi.json from the live app
	$(PY) scripts/export_openapi.py

deploy: ## Build, push to ACR, update both container apps
	bash infra/azure/deploy.sh

clean: ## Remove the local index, db and caches
	rm -rf data/index data/app.db data/app.db-wal data/app.db-shm \
	       .pytest_cache .ruff_cache .mypy_cache evals/reports/*.md
