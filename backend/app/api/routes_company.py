"""Company, health and world endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..config import get_settings
from ..graph import queries
from ..graph.client import GraphStore
from ..models.schemas import (
    CompanyOverview,
    DemoResetResponse,
    HealthResponse,
    WorldInteractiveObject,
    WorldResponse,
)
from ..workflows.company_brain import CompanyBrain
from .deps import brain, graph_store

router = APIRouter(prefix="/api", tags=["company"])

#: Root rooms the player can explore, with a stable id for the map.
ROOM_OBJECTS = [
    ("room_reception", "Reception", "NovaTech", "company", "View company overview"),
    ("room_library", "Knowledge Library", "Company Knowledge", "documents", "Search company knowledge"),
    ("room_decisions", "Decision Room", "Architecture Decisions", "decisions", "Explore company decisions"),
    ("room_meetings", "Meeting Room", "Meetings", "meetings", "Review company meetings"),
    ("room_support", "Support Room", "Tickets", "tickets", "Review tickets and issues"),
]


def _world_objects(store: GraphStore) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []

    for obj_id, name, subtitle, _kind, prompt in ROOM_OBJECTS:
        objects.append(
            {
                "id": obj_id,
                "label": "Room",
                "name": name,
                "subtitle": subtitle,
                "prompt": f"Press E — {prompt}",
                "room": obj_id,
                "root": True,
            }
        )

    for person in store.list_nodes("Person"):
        props = person["props"]
        first = str(props.get("name", "")).split()[0] or str(props.get("name", ""))
        objects.append(
            {
                "id": person["id"],
                "label": "Person",
                "name": props.get("name", person["id"]),
                "subtitle": props.get("role", ""),
                "prompt": f"Press E — Talk to {first}",
                "room": "employees",
            }
        )

    for project in store.list_nodes("Project"):
        props = project["props"]
        objects.append(
            {
                "id": project["id"],
                "label": "Project",
                "name": props.get("name", project["id"]),
                "subtitle": props.get("status", ""),
                "prompt": f"Press E — Explore {props.get('name', project['id'])}",
                "room": "project_room",
            }
        )

    for system in store.list_nodes("System"):
        props = system["props"]
        objects.append(
            {
                "id": system["id"],
                "label": "System",
                "name": props.get("name", system["id"]),
                "subtitle": props.get("status", ""),
                "prompt": f"Press E — Inspect {props.get('name', system['id'])}",
                "room": "server_room",
            }
        )

    return objects


@router.get("/health", response_model=HealthResponse)
def health(store: GraphStore = Depends(graph_store)) -> HealthResponse:
    """Liveness and dependency status for the backend."""

    settings = get_settings()
    from ..llm.provider import get_llm
    from ..rag.embeddings import get_embedder

    healthy = store.healthy()
    try:
        stats = store.stats().as_dict()
    except Exception:  # noqa: BLE001 - health must never raise
        stats = {}
    llm = get_llm(settings)
    return HealthResponse(
        status="ok" if healthy else "degraded",
        demo_mode=settings.demo_mode,
        graph_backend=store.backend,
        graph_healthy=healthy,
        llm_provider=llm.name,
        llm_available=getattr(llm, "available", False),
        embedding_provider=get_embedder(settings).name,
        stats=stats,
    )


@router.get("/company", response_model=CompanyOverview)
def company(store: GraphStore = Depends(graph_store)) -> CompanyOverview:
    """Company overview: org, projects, stack and graph statistics."""

    company_node = store.get_node("novatech")
    counts = {
        "people": len(store.list_nodes("Person")),
        "teams": len(store.list_nodes("Team")),
        "projects": len(store.list_nodes("Project")),
        "documents": len(store.list_nodes("Document")),
        "decisions": len(store.list_nodes("Decision")),
        "tickets": len(store.list_nodes("Ticket")),
        "meetings": len(store.list_nodes("Meeting")),
        "technologies": len(store.list_nodes("Technology")),
        "systems": len(store.list_nodes("System")),
        "skills": len(store.list_nodes("Skill")),
    }
    return CompanyOverview(
        company=company_node["props"] if company_node else {},
        stats=store.stats().as_dict(),
        teams=queries.list_by_label(store, "Team"),
        projects=queries.list_by_label(store, "Project"),
        technologies=queries.list_by_label(store, "Technology"),
        systems=queries.list_by_label(store, "System"),
        counts=counts,
    )


@router.get("/world", response_model=WorldResponse)
def world(store: GraphStore = Depends(graph_store)) -> WorldResponse:
    """Interactive objects for the 2D company world."""

    objects = [WorldInteractiveObject(**obj) for obj in _world_objects(store)]
    return WorldResponse(
        objects=objects,
        demo_questions=DEMO_QUESTIONS,
    )


@router.get("/demo/questions")
def demo_questions() -> dict[str, Any]:
    """Canonical demo questions for the guided tour."""

    return {"questions": DEMO_QUESTIONS, "scenario": DEMO_SCENARIO}


@router.post("/demo/reset", response_model=DemoResetResponse)
def demo_reset(store: GraphStore = Depends(graph_store)) -> DemoResetResponse:
    """Re-seed the demo graph from the dataset."""

    from ..graph.seed import seed_graph

    try:
        stats = seed_graph(store)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Could not reset the demo graph: {exc}") from exc
    return DemoResetResponse(
        status="ok",
        message="Demo graph re-seeded from the NovaTech dataset.",
        stats=stats,
    )


@router.get("/stats")
def stats(store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    """Raw graph statistics."""

    return store.stats().as_dict()


DEMO_QUESTIONS: list[str] = [
    "Who is Arun Kumar and what does he work on?",
    "What does Arun Kumar know?",
    "Who owns Project Atlas?",
    "What are the current issues with Project Atlas?",
    "Why did we choose PostgreSQL?",
    "Who should I talk to about the Atlas database migration?",
    "Who knows PostgreSQL?",
    "What decisions were made for Project Atlas?",
    "What documents support ADR-018?",
    "Which projects depend on PostgreSQL?",
    "Who made the PostgreSQL migration decision?",
    "What tickets are related to Project Atlas?",
    "Create a task for Arun Kumar to investigate the migration issue.",
]

DEMO_SCENARIO: list[dict[str, str]] = [
    {"step": "1", "action": "Enter the company at Reception."},
    {"step": "2", "action": "Walk to Arun Kumar's desk and press E."},
    {"step": "3", "action": "Ask: Who is Arun Kumar and what does he work on?"},
    {"step": "4", "action": "Walk to Project Atlas and press E."},
    {"step": "5", "action": "Ask: Who owns Project Atlas?"},
    {"step": "6", "action": "Enter the Decision Room and ask: Why did we choose PostgreSQL?"},
    {"step": "7", "action": "Ask: Who should I talk to about the Atlas database migration?"},
    {"step": "8", "action": "Ask: Create a task for Arun Kumar to investigate the migration issue."},
    {"step": "9", "action": "Confirm the action preview to create the ticket."},
]
