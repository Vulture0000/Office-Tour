"""Shared FastAPI dependencies and error helpers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from ..graph import queries
from ..graph.client import GraphStore, GraphUnavailable, get_store
from ..workflows.company_brain import CompanyBrain, get_brain


def graph_store() -> GraphStore:
    """FastAPI dependency returning the graph store."""

    return get_store()


def brain() -> CompanyBrain:
    """FastAPI dependency returning the Company Brain."""

    return get_brain()


def not_found(kind: str, entity_id: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail=f"{kind} '{entity_id}' was not found in the company graph.",
    )


def require(profile: dict[str, Any] | None, kind: str, entity_id: str) -> dict[str, Any]:
    if not profile:
        raise not_found(kind, entity_id)
    return profile


def graph_error(exc: Exception) -> HTTPException:
    if isinstance(exc, GraphUnavailable):
        return HTTPException(
            status_code=503,
            detail="The company graph is currently unavailable. Please retry shortly.",
        )
    return HTTPException(status_code=500, detail="Unexpected server error.")


__all__ = [
    "graph_store",
    "brain",
    "not_found",
    "require",
    "graph_error",
    "queries",
]
