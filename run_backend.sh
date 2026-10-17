#!/usr/bin/env bash
cd "$(dirname "$0")"
export GRAPH_BACKEND=memory
export DEMO_MODE=true
export LLM_PROVIDER=demo
export EMBEDDING_PROVIDER=hashing
./.venv/bin/python scripts/seed_company.py >/dev/null 2>&1 || true
./.venv/bin/python scripts/ingest_documents.py >/dev/null 2>&1 || true
exec ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload
