"""Reset the demo to a pristine state.

Clears the graph, wipes the action history and rebuilds the vector index. Useful
before a live demo run.

Usage::

    python scripts/reset_demo.py
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
    from app.graph.client import get_store
    from app.graph.seed import print_statistics, seed_graph
    from app.rag.retriever import get_vector_store
    from app.services.action_store import get_action_store

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
    settings = get_settings()
    print(f"Resetting demo (backend='{settings.graph_backend}')…")

    store = get_store(settings, force=True)
    seed_graph(store, settings)
    print_statistics(store)

    # Clear any previously proposed/executed actions.
    actions_path = settings.resolved_actions_store_path()
    if actions_path.exists():
        actions_path.unlink()
    get_action_store(settings, force=True)
    print("Cleared action history.")

    vector_store = get_vector_store(settings, force=True)
    vector_store.save(settings.resolved_vector_store_path())
    print(f"Rebuilt vector index with {len(vector_store.chunks)} chunks.")

    print("Demo reset complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
