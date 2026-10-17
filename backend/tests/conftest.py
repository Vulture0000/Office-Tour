"""Shared pytest fixtures.

The tests exercise the whole stack against the in-process graph backend so they
run without FalkorDB, network access or API keys. Environment variables are set
before importing the app so settings and singletons pick up the test config.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

_TMP = Path(tempfile.mkdtemp(prefix="company-brain-tests-"))
os.environ.setdefault("GRAPH_BACKEND", "memory")
os.environ.setdefault("LLM_PROVIDER", "demo")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("EMBEDDING_PROVIDER", "hashing")
os.environ["ACTIONS_STORE_PATH"] = str(_TMP / "actions.json")
os.environ["VECTOR_STORE_PATH"] = str(_TMP / "vector_store.json")


@pytest.fixture(scope="session")
def client():
    """A TestClient with a seeded in-memory graph, running the full app."""

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def store(client):
    """The seeded graph store backing the test client."""

    from app.graph.client import get_store

    return get_store()


@pytest.fixture(scope="session")
def brain(client):
    """The Company Brain singleton used by the API."""

    from app.workflows.company_brain import get_brain

    return get_brain()
