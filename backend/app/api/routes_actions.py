"""Action proposal, confirmation and history endpoints.

Implements the *confirm-before-execute* workflow: the reasoning agent only ever
proposes actions; a human confirms them, and only then are they executed against
the graph.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..agents import action_agent
from ..graph.client import GraphStore
from ..models.schemas import ActionConfirmRequest, ActionConfirmResponse
from ..services.action_store import ActionStore
from ..services.action_store import get_action_store
from .deps import graph_store

router = APIRouter(prefix="/api/actions", tags=["actions"])


def action_store_dep() -> ActionStore:
    return get_action_store()


@router.get("")
def list_actions(store: ActionStore = Depends(action_store_dep)) -> list[dict[str, Any]]:
    """Executed/cancelled action history, newest first."""

    return store.history()


@router.get("/{action_id}")
def get_action(
    action_id: str, store: ActionStore = Depends(action_store_dep)
) -> dict[str, Any]:
    """The pending preview for an action id."""

    action = store.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' is not pending.")
    return action


@router.post("/confirm", response_model=ActionConfirmResponse)
def confirm_action(
    request: ActionConfirmRequest,
    store: ActionStore = Depends(action_store_dep),
    graph: GraphStore = Depends(graph_store),
) -> ActionConfirmResponse:
    """Confirm and execute a previously proposed action."""

    action = store.get(request.action_id)
    if not action:
        raise HTTPException(
            status_code=404,
            detail=f"Action '{request.action_id}' is not pending or has already been handled.",
        )
    result = action_agent.execute(graph, action)
    confirmed = store.confirm(request.action_id)
    return ActionConfirmResponse(status="executed", action=confirmed, result=result)


@router.post("/cancel", response_model=ActionConfirmResponse)
def cancel_action(
    request: ActionConfirmRequest,
    store: ActionStore = Depends(action_store_dep),
) -> ActionConfirmResponse:
    """Cancel a pending action without executing it."""

    action = store.cancel(request.action_id)
    if not action:
        raise HTTPException(
            status_code=404,
            detail=f"Action '{request.action_id}' is not pending or has already been handled.",
        )
    return ActionConfirmResponse(status="cancelled", action=action)
