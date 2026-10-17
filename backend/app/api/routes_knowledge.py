"""Knowledge documents and decision (ADR) endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from ..graph import queries
from ..graph.client import GraphStore
from .deps import graph_store, require

router = APIRouter(prefix="/api", tags=["knowledge"])


@router.get("/documents")
def list_documents(
    store: GraphStore = Depends(graph_store),
    q: str | None = Query(default=None, max_length=200),
    doc_type: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """All knowledge documents, with optional text/type/project filters."""

    documents = queries.documents_index(store)
    if doc_type:
        documents = [d for d in documents if str(d["type"]).lower() == doc_type.lower()]
    if project_id:
        documents = [d for d in documents if d["project_id"] == project_id]
    if q:
        needle = q.lower()
        documents = [
            d
            for d in documents
            if needle in str(d["title"]).lower() or needle in str(d["excerpt"]).lower()
        ]
    return documents


@router.get("/documents/{document_id}")
def get_document(document_id: str, store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    """A document with its graph links (author, project, decisions, tech)."""

    profile = queries.document_profile(store, document_id)
    return require(profile, "Document", document_id)


@router.get("/decisions")
def list_decisions(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    decisions = queries.list_by_label(store, "Decision")
    decisions.sort(key=lambda item: str(item["props"].get("date", "")), reverse=True)
    return decisions


@router.get("/decisions/{decision_id}")
def get_decision(decision_id: str, store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    """Full decision trace: rationale, makers, supporting docs, related tech."""

    profile = queries.decision_profile(store, decision_id)
    return require(profile, "Decision", decision_id)
