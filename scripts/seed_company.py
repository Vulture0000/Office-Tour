"""Seed the company knowledge graph from ``data/``.

Usage::

    python scripts/seed_company.py            # seed using configured backend
    GRAPH_BACKEND=memory python scripts/seed_company.py

The script clears the target graph first so it is safe to re-run.
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
    from app.graph.seed import run

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s — %(message)s")
    settings = get_settings()
    print(f"Seeding graph using backend='{settings.graph_backend}'…")
    run(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
