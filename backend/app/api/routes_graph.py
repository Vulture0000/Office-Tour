"""Graph visualisation and search endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from ..graph import queries
from ..graph.client import GraphStore
from ..models.schemas import GraphModel, SearchResponse
from .deps import graph_store, not_found

router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/graph/entity/{entity_id}", response_model=GraphModel)
def entity_graph(
    entity_id: str,
    store: GraphStore = Depends(graph_store),
    depth: int = Query(default=2, ge=1, le=3),
) -> GraphModel:
    """Neighbourhood graph around a single entity for the 2D overlay."""

    if not store.get_node(entity_id):
        raise not_found("Entity", entity_id)
    graph = queries.subgraph(store, [entity_id], depth=depth)
    return GraphModel(**graph)


@router.get("/graph/subgraph", response_model=GraphModel)
def multi_subgraph(
    store: GraphStore = Depends(graph_store),
    ids: str = Query(..., description="Comma separated node ids"),
    depth: int = Query(default=1, ge=1, le=3),
) -> GraphModel:
    """Merged neighbourhood for several focus entities."""

    node_ids = [part.strip() for part in ids.split(",") if part.strip()]
    if not node_ids:
        raise not_found("Entity", ids)
    graph = queries.subgraph(store, node_ids, depth=depth)
    return GraphModel(**graph)


@router.get("/graph/explain")
def explain(
    store: GraphStore = Depends(graph_store),
    ids: str = Query(..., description="Comma separated node ids"),
    depth: int = Query(default=2, ge=1, le=3),
) -> list[dict[str, Any]]:
    """Readable, ordered explanation of the graph around some entities."""

    node_ids = [part.strip() for part in ids.split(",") if part.strip()]
    return queries.explain_path(store, node_ids, depth=depth)


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, max_length=120),
    store: GraphStore = Depends(graph_store),
    labels: str | None = Query(default=None, description="Comma separated labels"),
) -> SearchResponse:
    """Search the graph for entities and documents."""

    label_filter = [part.strip() for part in labels.split(",")] if labels else None
    nodes = store.search_nodes(q, label_filter)
    results = []
    for node in nodes:
        summary = queries.summarise(node)
        results.append(
            {
                "id": summary["id"],
                "label": summary["label"],
                "name": summary["name"],
                "subtitle": summary.get("subtitle", ""),
                "score": None,
                "snippet": str(node["props"].get("description") or node["props"].get("summary") or "")[
                    :160
                ],
            }
        )
    return SearchResponse(query=q, count=len(results), results=results)
