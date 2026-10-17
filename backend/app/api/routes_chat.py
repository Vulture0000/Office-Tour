"""Chat / natural-language query endpoints backed by the Company Brain."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models.schemas import ChatRequest, ChatResponse, QueryRequest
from ..workflows.company_brain import CompanyBrain
from .deps import brain, graph_error

router = APIRouter(prefix="/api", tags=["chat"])


def _context(request: ChatRequest | QueryRequest) -> dict[str, str | None]:
    if isinstance(request, ChatRequest):
        ctx = request.context
        if ctx is None:
            return {}
        return {
            "entity_id": ctx.entity_id,
            "entity_type": ctx.entity_type,
            "room": ctx.room,
            "room_id": ctx.room_id,
        }
    return {
        "entity_id": request.entity_id,
        "entity_type": request.entity_type,
        "room": request.room,
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, company_brain: CompanyBrain = Depends(brain)) -> ChatResponse:
    """Ask the Company Brain a question with optional world context."""

    try:
        result = company_brain.run(request.message, _context(request))
    except Exception as exc:  # noqa: BLE001
        raise graph_error(exc) from exc
    return ChatResponse(**result)


@router.post("/query", response_model=ChatResponse)
def query(request: QueryRequest, company_brain: CompanyBrain = Depends(brain)) -> ChatResponse:
    """Simplified query endpoint without chat context."""

    try:
        result = company_brain.run(request.question, _context(request))
    except Exception as exc:  # noqa: BLE001
        raise graph_error(exc) from exc
    return ChatResponse(**result)
