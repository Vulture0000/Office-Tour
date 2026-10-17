"""Domain level graph operations.

The low level :class:`~app.graph.client.GraphStore` exposes primitive
operations (create node, expand neighbours, search). This module composes them
into the questions the product actually asks: who owns a project, which people
know a technology, why a decision was made, and so on.

Everything returned here is plain JSON-serialisable data so it can flow straight
through FastAPI and into the frontend.
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterable

from . import schema
from .client import GraphStore

Node = dict[str, Any]
Edge = dict[str, str]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def display_name(node: Node) -> str:
    """Return the human readable name of a node."""

    props = node.get("props", {})
    prop = schema.NAME_PROPERTY.get(node.get("label", ""), "name")
    return str(props.get(prop) or props.get("name") or props.get("id") or "Unknown")


def summarise(node: Node) -> dict[str, Any]:
    """A compact projection of a node for lists and graph panels."""

    props = node.get("props", {})
    return {
        "id": node.get("id"),
        "label": node.get("label"),
        "name": display_name(node),
        "subtitle": props.get("role")
        or props.get("type")
        or props.get("status")
        or props.get("description")
        or "",
        "props": props,
    }


def _edge_index(node_id: str, edges: list[Edge], nodes: dict[str, Node]) -> dict[str, list[Node]]:
    """Group the neighbours of ``node_id`` by relationship type."""

    grouped: dict[str, list[Node]] = {}
    for edge in edges:
        if edge["source"] == node_id:
            other = nodes.get(edge["target"])
        elif edge["target"] == node_id:
            other = nodes.get(edge["source"])
        else:
            continue
        if not other:
            continue
        grouped.setdefault(edge["rel"], []).append(other)
    return grouped


def _dedupe(nodes: Iterable[Node]) -> list[Node]:
    seen: dict[str, Node] = {}
    for node in nodes:
        seen.setdefault(str(node.get("id")), node)
    return list(seen.values())


def _by_label(grouped: dict[str, list[Node]], *rels: str) -> list[Node]:
    collected: list[Node] = []
    for rel in rels:
        collected.extend(grouped.get(rel, []))
    return _dedupe(collected)


def _neighbourhood(store: GraphStore, node_id: str, depth: int = 1):
    nodes, edges = store.expand(node_id, depth=depth)
    index = {str(n["id"]): n for n in nodes}
    return index, edges, _edge_index(node_id, edges, index)


def _primary_team(props: dict[str, Any], teams: list[Node]) -> Node:
    """Pick the team a person primarily belongs to."""

    primary_id = props.get("team_id")
    if primary_id:
        for team in teams:
            if team["id"] == primary_id:
                return team
    return teams[0]


# ---------------------------------------------------------------------------
# listings
# ---------------------------------------------------------------------------
def list_by_label(store: GraphStore, label: str) -> list[dict[str, Any]]:
    return [summarise(n) for n in sorted(store.list_nodes(label), key=display_name)]


def list_people(store: GraphStore) -> list[dict[str, Any]]:
    return list_by_label(store, "Person")


def documents_index(store: GraphStore) -> list[dict[str, Any]]:
    """Documents with author/project denormalised for the library UI."""

    docs = store.list_nodes("Document")
    people = {p["id"]: summarise(p) for p in store.list_nodes("Person")}
    projects = {p["id"]: summarise(p) for p in store.list_nodes("Project")}
    out: list[dict[str, Any]] = []
    for doc in sorted(docs, key=display_name):
        props = doc["props"]
        out.append(
            {
                "id": doc["id"],
                "title": props.get("title", doc["id"]),
                "type": props.get("type", "Document"),
                "author": people.get(props.get("author_id"), {}).get("name"),
                "author_id": props.get("author_id"),
                "project_id": props.get("project_id"),
                "project": projects.get(props.get("project_id"), {}).get("name"),
                "created_at": props.get("created_at"),
                "updated_at": props.get("updated_at"),
                "excerpt": (props.get("content") or "")[:240],
                "source_path": props.get("source_path"),
            }
        )
    return out


# ---------------------------------------------------------------------------
# profiles
# ---------------------------------------------------------------------------
def person_profile(store: GraphStore, person_id: str) -> dict[str, Any] | None:
    person = store.get_node(person_id)
    if not person or person["label"] != "Person":
        return None
    index, edges, grouped = _neighbourhood(store, person_id, depth=1)
    props = person["props"]

    teams = _by_label(grouped, "MEMBER_OF")
    owned = _by_label(grouped, "OWNS")
    works_on = _by_label(grouped, "WORKS_ON")
    technologies = _by_label(grouped, "KNOWS", "EXPERT_IN")
    skills = _by_label(grouped, "HAS_SKILL")
    authored = _by_label(grouped, "AUTHORED")
    meetings = _by_label(grouped, "PARTICIPATED_IN")
    decisions = [n for n in meetings if n["label"] == "Decision"]
    meetings = [n for n in meetings if n["label"] == "Meeting"]
    tickets = [n for n in _by_label(grouped, "ASSIGNED_TO") if n["label"] == "Ticket"]

    projects = _dedupe(works_on + owned)
    collaborators: list[Node] = []
    for project in projects:
        member_nodes, member_edges = store.expand(str(project["id"]), ["WORKS_ON"], 1)
        member_index = {str(n["id"]): n for n in member_nodes}
        collaborators.extend(
            _edge_index(str(project["id"]), member_edges, member_index).get("WORKS_ON", [])
        )
    collaborators = [
        n for n in _dedupe(collaborators) if n["id"] != person_id and n["label"] == "Person"
    ]

    return {
        "id": person_id,
        "name": display_name(person),
        "label": "Person",
        "role": props.get("role"),
        "email": props.get("email"),
        "location": props.get("location"),
        "bio": props.get("bio"),
        "team": summarise(_primary_team(props, teams)) if teams else None,
        "teams": [summarise(n) for n in teams],
        "projects_owned": [summarise(n) for n in _dedupe(owned) if n["label"] == "Project"],
        "projects": [summarise(n) for n in projects],
        "technologies": [summarise(n) for n in technologies],
        "skills": [summarise(n) for n in skills],
        "documents": [summarise(n) for n in authored],
        "decisions": [summarise(n) for n in decisions],
        "meetings": [summarise(n) for n in meetings],
        "tickets": [summarise(n) for n in tickets],
        "collaborators": [summarise(n) for n in collaborators],
        "props": props,
    }


def project_profile(store: GraphStore, project_id: str) -> dict[str, Any] | None:
    project = store.get_node(project_id)
    if not project or project["label"] != "Project":
        return None
    index, edges, grouped = _neighbourhood(store, project_id, depth=1)
    props = project["props"]

    people = {p["id"]: p for p in store.list_nodes("Person")}
    owner = people.get(props.get("owner_id"))
    lead = people.get(props.get("lead_id"))

    documents = [n for n in _by_label(grouped, "HAS_DOCUMENT") if n["label"] == "Document"]
    tickets = [n for n in _by_label(grouped, "HAS_TICKET") if n["label"] == "Ticket"]
    decisions = _by_label(grouped, "HAS_DECISION")
    meetings = [n for n in _by_label(grouped, "DISCUSSED_IN") if n["label"] == "Meeting"]
    technologies = _by_label(grouped, "USES")
    works_on = [n for n in _by_label(grouped, "WORKS_ON") if n["label"] == "Person"]

    if not documents:
        documents = [
            n for n in _by_label(grouped, "REFERENCES") if n["label"] == "Document"
        ]
    if not meetings:
        for decision in decisions:
            meeting_nodes, meeting_edges = store.expand(str(decision["id"]), ["DISCUSSED_IN"], 1)
            meeting_index = {str(n["id"]): n for n in meeting_nodes}
            meetings.extend(
                _edge_index(str(decision["id"]), meeting_edges, meeting_index).get(
                    "DISCUSSED_IN", []
                )
            )

    open_statuses = {"To Do", "In Progress", "In Review", "Blocked"}
    open_tickets = [
        t for t in tickets if str(t["props"].get("status", "")) in open_statuses
    ]

    owning_team = store.get_node(str(props["team_id"])) if props.get("team_id") else None

    return {
        "id": project_id,
        "name": display_name(project),
        "label": "Project",
        "key": props.get("key"),
        "description": props.get("description"),
        "status": props.get("status"),
        "health": props.get("health"),
        "start_date": props.get("start_date"),
        "target_date": props.get("target_date"),
        "owner": summarise(owner) if owner else None,
        "lead": summarise(lead) if lead else None,
        "team": summarise(owning_team) if owning_team else None,
        "members": [summarise(n) for n in works_on],
        "technologies": [summarise(n) for n in technologies],
        "documents": [summarise(n) for n in documents],
        "tickets": [summarise(n) for n in tickets],
        "open_tickets": [summarise(n) for n in open_tickets],
        "decisions": [summarise(n) for n in decisions],
        "meetings": [summarise(n) for n in _dedupe(meetings)],
        "props": props,
    }


def document_profile(store: GraphStore, document_id: str) -> dict[str, Any] | None:
    doc = store.get_node(document_id)
    if not doc or doc["label"] != "Document":
        return None
    index, edges, grouped = _neighbourhood(store, document_id, depth=1)
    props = doc["props"]
    people = {p["id"]: p for p in store.list_nodes("Person")}
    projects = {p["id"]: p for p in store.list_nodes("Project")}
    author = people.get(props.get("author_id"))
    return {
        "id": document_id,
        "name": display_name(doc),
        "label": "Document",
        "title": props.get("title"),
        "type": props.get("type"),
        "author": summarise(author) if author else None,
        "created_at": props.get("created_at"),
        "updated_at": props.get("updated_at"),
        "project": summarise(projects[props["project_id"]])
        if props.get("project_id") in projects
        else None,
        "content": props.get("content"),
        "source_path": props.get("source_path"),
        "references": [summarise(n) for n in _dedupe(_by_label(grouped, "REFERENCES"))],
        "related_decisions": [
            summarise(n) for n in _by_label(grouped, "SUPPORTED_BY") if n["label"] == "Decision"
        ],
        "props": props,
    }


def decision_profile(store: GraphStore, decision_id: str) -> dict[str, Any] | None:
    decision = store.get_node(decision_id)
    if not decision or decision["label"] != "Decision":
        return None
    index, edges, grouped = _neighbourhood(store, decision_id, depth=1)
    props = decision["props"]

    projects = {p["id"]: p for p in store.list_nodes("Project")}
    docs = {d["id"]: d for d in store.list_nodes("Document")}
    meetings = {m["id"]: m for m in store.list_nodes("Meeting")}
    people = {p["id"]: p for p in store.list_nodes("Person")}

    makers = [n for n in _by_label(grouped, "MADE_BY") if n["label"] == "Person"]
    if not makers:
        makers = [people[i] for i in props.get("maker_ids", []) if i in people]

    supporting = [n for n in _by_label(grouped, "SUPPORTED_BY") if n["label"] == "Document"]
    if not supporting:
        supporting = [docs[i] for i in props.get("supporting_document_ids", []) if i in docs]

    about = [n for n in _by_label(grouped, "ABOUT") if n["label"] == "Project"]

    discussed_in = [n for n in _by_label(grouped, "DISCUSSED_IN") if n["label"] == "Meeting"]
    meeting = meetings.get(props.get("meeting_id"))
    if not discussed_in and meeting:
        discussed_in = [meeting]

    project = projects.get(props.get("project_id"))

    path = [
        {"label": "Decision", "id": decision_id, "name": display_name(decision)},
    ]
    if project:
        path.append({"label": "Project", "id": project["id"], "name": display_name(project)})
    for doc in supporting[:3]:
        path.append({"label": "Document", "id": doc["id"], "name": display_name(doc)})
    for maker in makers[:3]:
        path.append({"label": "Person", "id": maker["id"], "name": display_name(maker)})
    if discussed_in:
        path.append(
            {
                "label": "Meeting",
                "id": discussed_in[0]["id"],
                "name": display_name(discussed_in[0]),
            }
        )

    return {
        "id": decision_id,
        "name": display_name(decision),
        "label": "Decision",
        "title": props.get("title"),
        "status": props.get("status"),
        "date": props.get("date"),
        "summary": props.get("summary"),
        "reason": props.get("reason"),
        "alternatives": _load_json(props.get("alternatives_json"), []),
        "confidence": props.get("confidence"),
        "project": summarise(project) if project else None,
        "makers": [summarise(n) for n in makers],
        "supporting_documents": [summarise(n) for n in supporting],
        "meetings": [summarise(n) for n in discussed_in],
        "path": path,
        "props": props,
    }


def technology_profile(store: GraphStore, technology_id: str) -> dict[str, Any] | None:
    tech = store.get_node(technology_id)
    if not tech or tech["label"] != "Technology":
        return None
    index, edges, grouped = _neighbourhood(store, technology_id, depth=1)
    props = tech["props"]
    systems = [n for n in _by_label(grouped, "PART_OF") if n["label"] == "System"]
    # Technology -PART_OF-> System, so also check the reverse direction.
    if not systems:
        systems = [
            n
            for n in _dedupe(
                [store.get_node(sid) for sid in props.get("system_ids", [])]
            )
            if n
        ]
    experts = [n for n in _by_label(grouped, "KNOWS", "EXPERT_IN") if n["label"] == "Person"]
    projects = [n for n in _by_label(grouped, "USES") if n["label"] == "Project"]
    return {
        "id": technology_id,
        "name": display_name(tech),
        "label": "Technology",
        "category": props.get("category"),
        "description": props.get("description"),
        "systems": [summarise(n) for n in systems],
        "experts": [summarise(n) for n in experts],
        "projects": [summarise(n) for n in projects],
        "props": props,
    }


def system_profile(store: GraphStore, system_id: str) -> dict[str, Any] | None:
    system = store.get_node(system_id)
    if not system or system["label"] != "System":
        return None
    index, edges, grouped = _neighbourhood(store, system_id, depth=1)
    props = system["props"]
    people = {p["id"]: p for p in store.list_nodes("Person")}
    techs = {t["id"]: t for t in store.list_nodes("Technology")}
    owner = people.get(props.get("owner_id"))
    technology = techs.get(props.get("technology_id"))
    dependents: list[Node] = [
        n for n in _by_label(grouped, "RELATED_TO", "USES") if n["label"] == "Project"
    ]
    if technology and not dependents:
        tech_nodes, tech_edges = store.expand(str(technology["id"]), ["USES"], 1)
        tech_index = {str(n["id"]): n for n in tech_nodes}
        dependents = [
            n
            for n in _edge_index(str(technology["id"]), tech_edges, tech_index).get("USES", [])
            if n["label"] == "Project"
        ]
    decisions = [n for n in _by_label(grouped, "HAS_DECISION") if n["label"] == "Decision"]
    incidents = [n for n in _by_label(grouped, "RELATED_TO") if n["label"] == "Document"]
    return {
        "id": system_id,
        "name": display_name(system),
        "label": "System",
        "description": props.get("description"),
        "status": props.get("status"),
        "owner": summarise(owner) if owner else None,
        "technology": summarise(technology) if technology else None,
        "projects": [summarise(n) for n in dependents],
        "documents": [summarise(n) for n in incidents],
        "decisions": [summarise(n) for n in decisions],
        "props": props,
    }


def ticket_profile(store: GraphStore, ticket_id: str) -> dict[str, Any] | None:
    ticket = store.get_node(ticket_id)
    if not ticket or ticket["label"] != "Ticket":
        return None
    index, edges, grouped = _neighbourhood(store, ticket_id, depth=1)
    props = ticket["props"]
    return {
        "id": ticket_id,
        "name": display_name(ticket),
        "label": "Ticket",
        "status": props.get("status"),
        "priority": props.get("priority"),
        "description": props.get("description"),
        "assignee_id": props.get("assignee_id"),
        "reporter_id": props.get("reporter_id"),
        "comments": _load_json(props.get("comments_json"), []),
        "project": summarise(grouped.get("RELATED_TO", [None])[0])
        if grouped.get("RELATED_TO")
        else None,
        "props": props,
    }


def _load_json(value: Any, default: Any) -> Any:
    if not value:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


# ---------------------------------------------------------------------------
# relationship questions
# ---------------------------------------------------------------------------
def _technology_by_name(store: GraphStore, term: str) -> Node | None:
    term_lower = term.strip().lower()
    for tech in store.list_nodes("Technology"):
        if tech["id"] == term_lower or display_name(tech).lower() == term_lower:
            return tech
    for tech in store.list_nodes("Technology"):
        if term_lower and term_lower in display_name(tech).lower():
            return tech
    return None


def people_who_know(store: GraphStore, technology: str) -> list[dict[str, Any]]:
    tech = _technology_by_name(store, technology)
    if not tech:
        return []
    nodes, edges = store.expand(str(tech["id"]), ["KNOWS", "EXPERT_IN"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(str(tech["id"]), edges, index)
    people = [n for n in _by_label(grouped, "KNOWS", "EXPERT_IN") if n["label"] == "Person"]
    out: list[dict[str, Any]] = []
    for person in sorted(people, key=display_name):
        profile = person_profile(store, str(person["id"]))
        out.append(
            {
                "person": summarise(person),
                "expertise": [t["name"] for t in profile["technologies"]] if profile else [],
                "projects": [p["name"] for p in profile["projects"]] if profile else [],
                "documents": [d["name"] for d in profile["documents"]] if profile else [],
                "decisions": [d["name"] for d in profile["decisions"]] if profile else [],
                "reason": f"{display_name(person)} is connected to {display_name(tech)} "
                "through the KNOWS relationship in the company graph.",
            }
        )
    return out


def project_members(store: GraphStore, project_id: str) -> list[dict[str, Any]]:
    project = store.get_node(project_id)
    if not project or project["label"] != "Project":
        return []
    nodes, edges = store.expand(project_id, ["WORKS_ON", "OWNS"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(project_id, edges, index)
    people = [n for n in _by_label(grouped, "WORKS_ON") if n["label"] == "Person"]
    owner = store.get_node(str(project["props"].get("owner_id"))) if project["props"].get("owner_id") else None
    if owner:
        people = _dedupe([owner] + people)
    return [summarise(n) for n in people]


def decisions_for_project(store: GraphStore, project_id: str) -> list[dict[str, Any]]:
    nodes, edges = store.expand(project_id, ["HAS_DECISION", "ABOUT"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(project_id, edges, index)
    decisions = [n for n in _by_label(grouped, "HAS_DECISION", "ABOUT") if n["label"] == "Decision"]
    return [summarise(n) for n in sorted(_dedupe(decisions), key=display_name)]


def decisions_about_technology(store: GraphStore, technology: str) -> list[dict[str, Any]]:
    """Decisions that are traceable to a technology via its projects.

    Decisions whose own text mentions the technology rank first; if none
    mention it, every decision of the projects that use the technology is
    returned as context.
    """

    tech = _technology_by_name(store, technology)
    if not tech:
        return []
    tech_name = display_name(tech).lower()
    nodes, edges = store.expand(str(tech["id"]), ["USES"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(str(tech["id"]), edges, index)
    projects = [n for n in _by_label(grouped, "USES") if n["label"] == "Project"]
    out: list[dict[str, Any]] = []
    for project in projects:
        out.extend(decisions_for_project(store, str(project["id"])))

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for decision in out:
        if decision["id"] in seen:
            continue
        seen.add(decision["id"])
        unique.append(decision)

    def mentions(decision: dict[str, Any]) -> bool:
        props = decision.get("props", {})
        text = " ".join(
            str(props.get(field) or "")
            for field in ("title", "summary", "reason", "description")
        ).lower()
        return tech_name in text

    mentioning = sorted(
        [d for d in unique if mentions(d)],
        key=lambda d: (
            tech_name not in str(d.get("props", {}).get("title", "")).lower(),
            str(d.get("props", {}).get("date", "")),
        ),
    )
    return mentioning or unique


def tickets_for_project(
    store: GraphStore, project_id: str, statuses: Iterable[str] | None = None
) -> list[dict[str, Any]]:
    nodes, edges = store.expand(project_id, ["HAS_TICKET", "RELATED_TO"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(project_id, edges, index)
    tickets = [n for n in _by_label(grouped, "HAS_TICKET", "RELATED_TO") if n["label"] == "Ticket"]
    if statuses:
        allowed = {s.lower() for s in statuses}
        tickets = [
            t for t in tickets if str(t["props"].get("status", "")).lower() in allowed
        ]
    return [
        summarise(n)
        for n in sorted(_dedupe(tickets), key=lambda n: str(n["props"].get("priority", "")))
    ]


def documents_for_project(store: GraphStore, project_id: str) -> list[dict[str, Any]]:
    nodes, edges = store.expand(project_id, ["HAS_DOCUMENT"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(project_id, edges, index)
    documents = [n for n in _by_label(grouped, "HAS_DOCUMENT") if n["label"] == "Document"]
    return [summarise(n) for n in sorted(_dedupe(documents), key=display_name)]


def documents_for_decision(store: GraphStore, decision_id: str) -> list[dict[str, Any]]:
    profile = decision_profile(store, decision_id)
    return profile["supporting_documents"] if profile else []


def technology_projects(store: GraphStore, technology: str) -> list[dict[str, Any]]:
    tech = _technology_by_name(store, technology)
    if not tech:
        return []
    nodes, edges = store.expand(str(tech["id"]), ["USES"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(str(tech["id"]), edges, index)
    return [summarise(n) for n in _by_label(grouped, "USES") if n["label"] == "Project"]


def documents_for_technology(store: GraphStore, technology: str) -> list[dict[str, Any]]:
    """Documents that reference a technology anywhere in the graph."""

    tech = _technology_by_name(store, technology)
    if not tech:
        return []
    nodes, edges = store.expand(str(tech["id"]), ["REFERENCES"], 1)
    index = {str(n["id"]): n for n in nodes}
    grouped = _edge_index(str(tech["id"]), edges, index)
    documents = [n for n in _by_label(grouped, "REFERENCES") if n["label"] == "Document"]
    return [summarise(n) for n in sorted(_dedupe(documents), key=display_name)]


# ---------------------------------------------------------------------------
# expertise ranking
# ---------------------------------------------------------------------------
def expertise_rank(
    store: GraphStore, terms: Iterable[str], project_id: str | None = None
) -> list[dict[str, Any]]:
    """Rank people by how strongly the graph connects them to ``terms``.

    Scoring is deliberately transparent: each contributing edge type adds a
    fixed weight and is recorded as a human readable reason.
    """

    terms_lower = [t.strip().lower() for t in terms if t and t.strip()]
    if not terms_lower:
        return []

    projects = {p["id"]: p for p in store.list_nodes("Project")}

    results: list[dict[str, Any]] = []
    for person in store.list_nodes("Person"):
        profile = person_profile(store, str(person["id"]))
        if not profile:
            continue
        score = 0.0
        reasons: list[str] = []

        tech_matches = [
            t for t in profile["technologies"] if _matches(t["name"], terms_lower)
        ]
        if tech_matches:
            score += 3.0 * len(tech_matches)
            reasons.append(
                "Knows " + ", ".join(sorted(t["name"] for t in tech_matches))
            )

        skill_matches = [s for s in profile["skills"] if _matches(s["name"], terms_lower)]
        if skill_matches:
            score += 2.0 * len(skill_matches)
            reasons.append("Skilled in " + ", ".join(sorted(s["name"] for s in skill_matches)))

        project_matches = [p for p in profile["projects"] if _matches(p["name"], terms_lower)]
        if project_matches:
            score += 3.0 * len(project_matches)
            reasons.append("Works on " + ", ".join(sorted(p["name"] for p in project_matches)))

        doc_matches = [d for d in profile["documents"] if _matches(d["name"], terms_lower)]
        if doc_matches:
            score += 2.0 * len(doc_matches)
            reasons.append("Authored " + ", ".join(sorted(d["name"] for d in doc_matches)))

        decision_matches = [d for d in profile["decisions"] if _matches(d["name"], terms_lower)]
        if decision_matches:
            score += 2.5 * len(decision_matches)
            reasons.append("Involved in " + ", ".join(sorted(d["name"] for d in decision_matches)))

        if project_id and any(
            str(p["id"]) == project_id for p in profile["projects"]
        ):
            project_name = display_name(projects[project_id]) if project_id in projects else project_id
            score += 4.0
            reasons.append(f"Works on {project_name}")

        if score <= 0:
            continue
        results.append(
            {
                "person": summarise(person),
                "score": round(score, 2),
                "reasons": reasons,
                "expertise": [t["name"] for t in profile["technologies"]],
                "projects": [p["name"] for p in profile["projects"]],
                "documents": [d["name"] for d in profile["documents"]],
                "decisions": [d["name"] for d in profile["decisions"]],
                "role": profile.get("role"),
                "team": profile["team"]["name"] if profile.get("team") else None,
            }
        )
    results.sort(key=lambda item: (-item["score"], item["person"]["name"]))
    return results


def _matches(value: str, terms: list[str]) -> bool:
    value_lower = value.lower()
    return any(term in value_lower or value_lower in term for term in terms)


# ---------------------------------------------------------------------------
# entity resolution and subgraphs
# ---------------------------------------------------------------------------
def resolve_entity(
    store: GraphStore, text: str, labels: Iterable[str] | None = None
) -> Node | None:
    """Resolve free text to a graph node.

    Preference order: exact id, exact display name, then a scored containment
    match that rewards prefix and word-boundary hits over arbitrary substrings
    (so "postgres" resolves to the PostgreSQL technology, not to a ticket title
    that happens to mention it).
    """

    needle = (text or "").strip().lower()
    if not needle:
        return None
    label_filter = {schema.validate_label(l) for l in (labels or [])} or None
    candidates: list[Node] = []
    for label in sorted(label_filter or schema.LABELS):
        candidates.extend(store.list_nodes(label))

    for node in candidates:
        if str(node["id"]).lower() == needle:
            return node
    for node in candidates:
        if display_name(node).lower() == needle:
            return node

    # Nodes whose label is a strong hub get a small boost on ties.
    label_priority = {
        "Person": 0,
        "Project": 1,
        "Technology": 2,
        "Team": 3,
        "Decision": 4,
        "Document": 5,
        "Meeting": 6,
        "Ticket": 7,
        "System": 8,
        "Skill": 9,
        "Department": 10,
    }

    def score(node: Node) -> tuple[int, int, int]:
        name = display_name(node).lower()
        if name.startswith(needle):
            base = 4
        elif re.search(rf"\b{re.escape(needle)}", name):
            base = 3
        elif needle in name:
            base = 2
        elif name in needle:
            base = 1
        else:
            base = 0
        return (base, -len(name), label_priority.get(node["label"], 50))

    scored = [(score(node), node) for node in candidates]
    best_score, best_node = max(scored, key=lambda item: item[0])
    if best_score[0] > 0:
        return best_node
    found = store.search_nodes(needle, labels=label_filter)
    return found[0] if found else None


def subgraph(
    store: GraphStore, node_ids: Iterable[str], depth: int = 1
) -> dict[str, Any]:
    """Merge the neighbourhoods of several nodes into one visualisation graph."""

    nodes: dict[str, Node] = {}
    edges: dict[tuple[str, str, str], Edge] = {}
    for node_id in node_ids:
        if not node_id:
            continue
        local_nodes, local_edges = store.expand(str(node_id), depth=depth)
        for node in local_nodes:
            nodes.setdefault(str(node["id"]), node)
        for edge in local_edges:
            edges.setdefault((edge["source"], edge["rel"], edge["target"]), edge)

    payload_nodes = [summarise(n) for n in nodes.values()]
    payload_edges = [
        {"id": f"{s}->{r}->{t}", "source": s, "target": t, "rel": r}
        for (s, r, t) in edges
        if s in nodes and t in nodes
    ]
    return {"nodes": payload_nodes, "edges": payload_edges}


def explain_path(store: GraphStore, node_ids: Iterable[str], depth: int = 2) -> list[dict[str, Any]]:
    """A readable, ordered explanation of the graph around some entities."""

    ids = [i for i in node_ids if i]
    graph = subgraph(store, ids, depth=depth)
    focus = {str(i) for i in ids}
    steps: list[dict[str, Any]] = []
    for node in graph["nodes"]:
        nid = str(node["id"])
        relations = [
            f"{e['rel'].replace('_', ' ').title()} → "
            f"{next((n['name'] for n in graph['nodes'] if str(n['id']) == e['target']), e['target'])}"
            if e["source"] == nid
            else f"{e['rel'].replace('_', ' ').title()} ← "
            f"{next((n['name'] for n in graph['nodes'] if str(n['id']) == e['source']), e['source'])}"
            for e in graph["edges"]
            if e["source"] == nid or e["target"] == nid
        ]
        steps.append(
            {
                "id": nid,
                "label": node["label"],
                "name": node["name"],
                "focus": nid in focus,
                "relations": relations[:6],
            }
        )
    steps.sort(key=lambda item: (not item["focus"], item["label"], item["name"]))
    return steps


def graph_stats(store: GraphStore) -> dict[str, Any]:
    return store.stats().as_dict()
