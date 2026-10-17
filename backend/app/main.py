"""FastAPI application entry point for the Company Brain backend.

Run locally with::

    uvicorn app.main:app --reload --port 8000

The app is resilient by design: it works with no LLM key (deterministic,
graph-grounded answers) and falls back to an in-process graph store when
FalkorDB is unreachable, so the demo always responds.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    routes_actions,
    routes_chat,
    routes_company,
    routes_entities,
    routes_graph,
    routes_knowledge,
    routes_office,
)
from .config import get_settings
from .graph.client import GraphUnavailable, get_store
from .rag.retriever import get_vector_store

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm dependencies and, in demo mode, seed an empty graph."""

    _configure_logging()
    settings = get_settings()
    logger.info(
        "Starting Company Brain (backend=%s, llm=%s, embeddings=%s, demo_mode=%s)",
        settings.graph_backend,
        settings.llm_provider,
        settings.embedding_provider,
        settings.demo_mode,
    )

    store = get_store(settings)
    try:
        store.ensure_schema()
        stats = store.stats()
        if settings.demo_mode and stats.nodes == 0:
            from .graph.seed import seed_graph

            logger.info("Graph is empty; seeding the NovaTech demo dataset…")
            seed_graph(store, settings)
    except GraphUnavailable as exc:
        logger.warning("Graph unavailable at startup: %s", exc)

    try:
        get_vector_store(settings)
    except Exception as exc:  # noqa: BLE001 - retrieval is best effort
        logger.warning("Vector store unavailable at startup: %s", exc)

    yield
    logger.info("Company Brain shutting down.")


app = FastAPI(
    title="Company Brain API",
    version="1.0.0",
    description=(
        "A graph-backed company knowledge brain powered by FalkorDB, LangGraph "
        "agents and graph-aware RAG. Answers are grounded in the company graph "
        "with cited sources, graph paths and a confirm-before-execute action flow."
    ),
    lifespan=lifespan,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_company.router)
app.include_router(routes_entities.router)
app.include_router(routes_knowledge.router)
app.include_router(routes_graph.router)
app.include_router(routes_chat.router)
app.include_router(routes_actions.router)
app.include_router(routes_office.router)


@app.exception_handler(GraphUnavailable)
async def _graph_unavailable_handler(request: Request, exc: GraphUnavailable) -> JSONResponse:
    logger.warning("Graph unavailable handling %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "The company graph is currently unavailable. Please retry shortly."
        },
    )


@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request.", "errors": exc.errors()},
    )


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    """Service banner."""

    return {
        "name": "Company Brain API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> JSONResponse:
    return JSONResponse(status_code=204, content=None)


# Optionally serve a built frontend (frontend/dist) as static files.
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.exists():  # pragma: no cover - only in deployed/demo environments
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
