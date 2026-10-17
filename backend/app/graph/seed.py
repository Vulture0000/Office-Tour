"""Seed the NovaTech company knowledge graph.

Usage::

    python -m app.graph.seed          # from the backend directory
    python scripts/seed_company.py    # from the repository root

The script clears the target graph, creates every node and relationship from
``data/`` and prints statistics. It is idempotent: running it twice produces the
same graph.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..config import Settings, get_settings
from ..rag.loader import load_documents
from .client import GraphStore, get_store

logger = logging.getLogger(__name__)

#: Incident and runbook documents that describe a specific system.
DOCUMENT_SYSTEM_LINKS: dict[str, list[str]] = {
    "doc_incident_inc_042": ["sys_cloud_infra"],
    "doc_incident_inc_047": ["sys_ai_services"],
    "doc_platform_runbook": ["sys_cloud_infra", "sys_primary_db", "sys_cache"],
}


def _read_json(settings: Settings, *parts: str) -> Any:
    path = settings.data_dir.joinpath(*parts)
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def seed_graph(store: GraphStore, settings: Settings | None = None) -> dict[str, Any]:
    """Clear and rebuild the company graph. Returns graph statistics."""

    settings = settings or get_settings()
    store.clear()
    store.ensure_schema()

    company = _read_json(settings, "company.json")
    people = _read_json(settings, "people", "people.json")
    projects = _read_json(settings, "projects", "projects.json")
    tickets = _read_json(settings, "tickets", "tickets.json")
    meetings = _read_json(settings, "meetings", "meetings.json")
    decisions = _read_json(settings, "decisions", "decisions.json")
    documents = load_documents(settings.data_dir / "documents")

    # -- nodes -----------------------------------------------------------
    store.create_node("Company", company["company"])

    for department in company["departments"]:
        store.create_node("Department", department)
    for team in company["teams"]:
        store.create_node("Team", team)
    for technology in company["technologies"]:
        store.create_node("Technology", technology)
    for system in company["systems"]:
        store.create_node("System", system)
    for skill in company["skills"]:
        store.create_node("Skill", skill)

    for person in people:
        store.create_node("Person", person)
    for project in projects:
        store.create_node("Project", project)
    for document in documents:
        store.create_node("Document", document.as_node_props())
    for ticket in tickets:
        props = dict(ticket)
        props["comments_json"] = _dump(props.pop("comments", []))
        store.create_node("Ticket", props)
    for meeting in meetings:
        store.create_node("Meeting", meeting)
    for decision in decisions:
        props = dict(decision)
        props["alternatives_json"] = _dump(props.pop("alternatives", []))
        store.create_node("Decision", props)

    # -- relationships ---------------------------------------------------
    # Org structure
    for team in company["teams"]:
        store.create_edge(team["id"], team["department_id"], "REPORTS_IN")
    store.create_edge(company["company"]["id"], "dept_engineering", "PART_OF")

    # People
    for person in people:
        for team_id in person.get("team_ids", []):
            store.create_edge(person["id"], team_id, "MEMBER_OF")
        for tech_id in person.get("technologies", []):
            store.create_edge(person["id"], tech_id, "KNOWS")
        for tech_id in person.get("technologies", [])[:2]:
            store.create_edge(person["id"], tech_id, "EXPERT_IN")
        for skill_id in person.get("skills", []):
            store.create_edge(person["id"], skill_id, "HAS_SKILL")

    # Projects
    for project in projects:
        store.create_edge(project["team_id"], project["id"], "OWNS")
        if project.get("owner_id"):
            store.create_edge(project["owner_id"], project["id"], "OWNS")
        for member_id in project.get("member_ids", []):
            store.create_edge(member_id, project["id"], "WORKS_ON")
        for tech_id in project.get("technologies", []):
            store.create_edge(project["id"], tech_id, "USES")

    # Technologies belong to systems
    for system in company["systems"]:
        if system.get("technology_id"):
            store.create_edge(system["technology_id"], system["id"], "PART_OF")
        if system.get("owner_id"):
            store.create_edge(system["owner_id"], system["id"], "RESPONSIBLE_FOR")
        if system.get("team_id"):
            store.create_edge(system["team_id"], system["id"], "OWNS")

    # Documents
    project_technologies = {p["id"]: p.get("technologies", []) for p in projects}
    for document in documents:
        if document.author_id:
            store.create_edge(document.author_id, document.id, "AUTHORED")
            store.create_edge(document.id, document.author_id, "REFERENCES")
        if document.project_id:
            store.create_edge(document.project_id, document.id, "HAS_DOCUMENT")
            store.create_edge(document.id, document.project_id, "REFERENCES")
        for tech_id in project_technologies.get(document.project_id, []):
            store.create_edge(document.id, tech_id, "REFERENCES")
        for system_id in DOCUMENT_SYSTEM_LINKS.get(document.id, []):
            store.create_edge(document.id, system_id, "RELATED_TO")

    # Tickets
    for ticket in tickets:
        store.create_edge(ticket["project_id"], ticket["id"], "HAS_TICKET")
        store.create_edge(ticket["id"], ticket["project_id"], "RELATED_TO")
        if ticket.get("assignee_id"):
            store.create_edge(ticket["id"], ticket["assignee_id"], "ASSIGNED_TO")
        if ticket.get("reporter_id"):
            store.create_edge(ticket["id"], ticket["reporter_id"], "REPORTED_BY")

    # Meetings
    for meeting in meetings:
        if meeting.get("project_id"):
            store.create_edge(meeting["id"], meeting["project_id"], "RELATED_TO")
        for attendee_id in meeting.get("attendee_ids", []):
            store.create_edge(attendee_id, meeting["id"], "PARTICIPATED_IN")

    # Decisions
    for decision in decisions:
        store.create_edge(decision["id"], decision["project_id"], "ABOUT")
        store.create_edge(decision["project_id"], decision["id"], "HAS_DECISION")
        for maker_id in decision.get("maker_ids", []):
            store.create_edge(decision["id"], maker_id, "MADE_BY")
            store.create_edge(maker_id, decision["id"], "PARTICIPATED_IN")
        for doc_id in decision.get("supporting_document_ids", []):
            store.create_edge(decision["id"], doc_id, "SUPPORTED_BY")
        if decision.get("meeting_id"):
            store.create_edge(decision["id"], decision["meeting_id"], "DISCUSSED_IN")

    stats = store.stats()
    logger.info("Seed complete: %s nodes, %s edges", stats.nodes, stats.edges)
    return stats.as_dict()


def print_statistics(store: GraphStore) -> None:
    """Print a human readable seed summary."""

    stats = store.stats()
    labels = stats.nodes_by_label
    print("Company Brain Seed Complete")
    print()
    print(f"  People:        {labels.get('Person', 0)}")
    print(f"  Teams:         {labels.get('Team', 0)}")
    print(f"  Departments:   {labels.get('Department', 0)}")
    print(f"  Projects:      {labels.get('Project', 0)}")
    print(f"  Documents:     {labels.get('Document', 0)}")
    print(f"  Tickets:       {labels.get('Ticket', 0)}")
    print(f"  Decisions:     {labels.get('Decision', 0)}")
    print(f"  Meetings:      {labels.get('Meeting', 0)}")
    print(f"  Technologies:  {labels.get('Technology', 0)}")
    print(f"  Systems:       {labels.get('System', 0)}")
    print(f"  Skills:        {labels.get('Skill', 0)}")
    print()
    print(f"  Total nodes:         {stats.nodes}")
    print(f"  Graph relationships: {stats.edges}")


def run(settings: Settings | None = None, store: GraphStore | None = None) -> dict[str, Any]:
    """Seed and print statistics. Used by scripts and tests."""

    settings = settings or get_settings()
    store = store or get_store(settings, force=True)
    stats = seed_graph(store, settings)
    print_statistics(store)
    return stats


if __name__ == "__main__":  # pragma: no cover - manual entry point
    logging.basicConfig(level=logging.INFO)
    run()
