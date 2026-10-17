"""People, teams, projects, technologies, systems and tickets endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from ..graph import queries
from ..graph.client import GraphStore
from .deps import graph_store, require

router = APIRouter(prefix="/api", tags=["entities"])


@router.get("/people")
def list_people(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    """All employees with their team and knowledge tags."""

    teams = {t["id"]: t for t in store.list_nodes("Team")}
    output: list[dict[str, Any]] = []
    for person in store.list_nodes("Person"):
        props = person["props"]
        team = teams.get(props.get("team_id"))
        output.append(
            {
                "id": person["id"],
                "name": props.get("name", person["id"]),
                "role": props.get("role"),
                "team": queries.display_name(team) if team else None,
                "team_id": props.get("team_id"),
                "location": props.get("location"),
                "email": props.get("email"),
                "bio": props.get("bio"),
            }
        )
    output.sort(key=lambda item: item["name"] or "")
    return output


@router.get("/people/{person_id}")
def get_person(person_id: str, store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    """Full person profile assembled from graph relationships."""

    profile = queries.person_profile(store, person_id)
    return require(profile, "Person", person_id)


@router.get("/teams")
def list_teams(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    teams = queries.list_by_label(store, "Team")
    people = store.list_nodes("Person")
    for team in teams:
        members = [p for p in people if p["props"].get("team_id") == team["id"]]
        team["members"] = [
            {"id": m["id"], "name": queries.display_name(m), "role": m["props"].get("role")}
            for m in members
        ]
    return teams


@router.get("/teams/{team_id}")
def get_team(team_id: str, store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    team = store.get_node(team_id)
    if not team or team["label"] != "Team":
        from .deps import not_found

        raise not_found("Team", team_id)
    nodes, edges = store.expand(team_id, depth=1)
    index = {str(n["id"]): n for n in nodes}
    grouped = queries._edge_index(team_id, edges, index)  # noqa: SLF001 - internal reuse
    return {
        "id": team_id,
        "name": queries.display_name(team),
        "description": team["props"].get("description"),
        "members": [
            queries.summarise(n) for n in grouped.get("MEMBER_OF", []) if n["label"] == "Person"
        ],
        "projects": [
            queries.summarise(n) for n in grouped.get("OWNS", []) if n["label"] == "Project"
        ],
        "department": [
            queries.summarise(n) for n in grouped.get("REPORTS_IN", []) if n["label"] == "Department"
        ],
    }


@router.get("/projects")
def list_projects(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    projects = []
    people = {p["id"]: p for p in store.list_nodes("Person")}
    for project in store.list_nodes("Project"):
        props = project["props"]
        owner = people.get(props.get("owner_id"))
        projects.append(
            {
                "id": project["id"],
                "name": props.get("name", project["id"]),
                "key": props.get("key"),
                "status": props.get("status"),
                "health": props.get("health"),
                "description": props.get("description"),
                "owner": queries.display_name(owner) if owner else None,
                "owner_id": props.get("owner_id"),
                "target_date": props.get("target_date"),
            }
        )
    projects.sort(key=lambda item: item["name"] or "")
    return projects


@router.get("/projects/{project_id}")
def get_project(project_id: str, store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    """Full project profile: owner, team, members, stack, docs, tickets, decisions."""

    profile = queries.project_profile(store, project_id)
    return require(profile, "Project", project_id)


@router.get("/technologies")
def list_technologies(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    return queries.list_by_label(store, "Technology")


@router.get("/technologies/{technology_id}")
def get_technology(
    technology_id: str, store: GraphStore = Depends(graph_store)
) -> dict[str, Any]:
    profile = queries.technology_profile(store, technology_id)
    return require(profile, "Technology", technology_id)


@router.get("/systems")
def list_systems(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    people = {p["id"]: p for p in store.list_nodes("Person")}
    systems = []
    for system in store.list_nodes("System"):
        props = system["props"]
        owner = people.get(props.get("owner_id"))
        systems.append(
            {
                "id": system["id"],
                "name": props.get("name", system["id"]),
                "status": props.get("status"),
                "description": props.get("description"),
                "owner": queries.display_name(owner) if owner else None,
                "owner_id": props.get("owner_id"),
                "technology_id": props.get("technology_id"),
            }
        )
    systems.sort(key=lambda item: item["name"] or "")
    return systems


@router.get("/systems/{system_id}")
def get_system(system_id: str, store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    profile = queries.system_profile(store, system_id)
    return require(profile, "System", system_id)


@router.get("/tickets")
def list_tickets(
    store: GraphStore = Depends(graph_store),
    project_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Tickets, optionally filtered by project and status."""

    statuses = [status] if status else None
    if project_id:
        tickets = queries.tickets_for_project(store, project_id, statuses)
    else:
        tickets = [queries.summarise(n) for n in store.list_nodes("Ticket")]
    if status and not project_id:
        tickets = [t for t in tickets if str(t["props"].get("status", "")).lower() == status.lower()]
    tickets.sort(key=lambda item: str(item["props"].get("updated_at", "")), reverse=True)
    return tickets


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str, store: GraphStore = Depends(graph_store)) -> dict[str, Any]:
    profile = queries.ticket_profile(store, ticket_id)
    return require(profile, "Ticket", ticket_id)


@router.get("/meetings")
def list_meetings(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    meetings = queries.list_by_label(store, "Meeting")
    meetings.sort(key=lambda item: str(item["props"].get("date", "")), reverse=True)
    return meetings


@router.get("/skills")
def list_skills(store: GraphStore = Depends(graph_store)) -> list[dict[str, Any]]:
    return queries.list_by_label(store, "Skill")
