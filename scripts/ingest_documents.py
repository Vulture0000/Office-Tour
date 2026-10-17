"""Build the vector index used for graph-aware RAG.

Usage::

    python scripts/ingest_documents.py           # build + persist index
    python scripts/ingest_documents.py --force   # rebuild even if cached

The index is persisted to ``VECTOR_STORE_PATH`` (default ``backend/var/vector_store.json``).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def main() -> int:
    from app.config import get_settings
    from app.rag.loader import load_documents
    from app.rag.retriever import get_vector_store

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
    settings = get_settings()

    documents = load_documents()
    print(f"Loaded {len(documents)} documents from {settings.data_dir / 'documents'}")

    store = get_vector_store(settings, force=True)
    store.save(settings.resolved_vector_store_path())
    print(
        f"Built index with {len(store.chunks)} chunks using embedder '{store.embedder.name}'"
    )
    print(f"Persisted to {settings.resolved_vector_store_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
