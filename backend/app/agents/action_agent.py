"""Action agent.

Proposes write actions (create ticket, schedule meeting, follow-up, project
status update) and executes them **only after explicit human confirmation**.
Proposals are structured data validated against a whitelist; no LLM output is
executed directly.
"""

from __future__ import annotations

import re
from typing import Any

from ..graph import queries
from ..graph.client import GraphStore
from ..services.action_store import ActionStore
from ..workflows.state import INTENT_ACTION, BrainState

TITLE_PATTERNS = [
    re.compile(
        r"(?:task|ticket|issue|to[\s-]?do|follow[\s-]?up)\s+for\s+.+?\s+to\s+(.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:create|open|file|raise|log|add)\s+(?:a\s+)?(?:new\s+)?"
        r"(?:ticket|task|issue|to[\s-]?do)\s+(?:to|about|regarding|for)\s+(.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
    re.compile(r"\bto\s+(investigate|fix|review|look\s+into|check|migrate|resolve)\b(.+?)(?:\.|$)", re.IGNORECASE),
]

PRIORITY_RULES = [
    (re.compile(r"\b(critical|outage|sev\s*1|sev-1|urgent)\b", re.IGNORECASE), "Critical"),
    (re.compile(r"\b(high|asap|blocker|important)\b", re.IGNORECASE), "High"),
    (re.compile(r"\b(low|minor|nice\s+to\s+have|whenever)\b", re.IGNORECASE), "Low"),
]

CLEAN_PREFIX = re.compile(
    r"^(?:please\s+)?(?:can\s+you\s+)?(?:create|open|file|raise|log|add|make|set\s*up|"
    r"schedule|book|plan|draft|assign)\s+",
    re.IGNORECASE,
)


def detect_kind(question: str) -> str:
    """Map the request to a supported action kind."""

    lower = question.lower()
    if "meeting" in lower or "schedule" in lower or "book" in lower:
        return "schedule_meeting"
    if "status" in lower and ("update" in lower or "set" in lower):
        return "update_project_status"
    if "follow" in lower:
        return "follow_up"
    return "create_ticket"


def detect_priority(question: str) -> str:
    for pattern, priority in PRIORITY_RULES:
        if pattern.search(question):
            return priority
    return "Medium"


def extract_title(question: str) -> str:
    """Derive a short, imperative ticket title from the request."""

    for pattern in TITLE_PATTERNS:
        match = pattern.search(question)
        if match:
            groups = [g for g in match.groups() if g]
            title = " ".join(groups).strip()
            if title:
                return _tidy(title)
    cleaned = CLEAN_PREFIX.sub("", question).strip()
    cleaned = re.sub(r"\s+for\s+[A-Z][\w]+.*$", "", cleaned).strip()
    cleaned = re.sub(r"^(?:a\s+)?(?:ticket|task|issue)\s*(?:for\s+[^,.]*)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" .,:;")
    if not cleaned:
        cleaned = question.strip(" .,:;")
    return _tidy(cleaned)


def _tidy(text: str) -> str:
    text = text.strip(" .,:;\"'")
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text[:120]


def _next_ticket_id(store: GraphStore, project_key: str) -> str:
    prefix = (project_key or "TASK").upper()
    highest = 0
    for ticket in store.list_nodes("Ticket"):
        ticket_id = str(ticket["id"])
        match = re.match(rf"^{re.escape(prefix)}-(\d+)$", ticket_id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1}"


def run(
    state: BrainState,
    store: GraphStore,
    action_store: ActionStore,
) -> BrainState:
    """LangGraph node: build an action preview for ACTION_REQUEST intents."""

    if state.get("intent") != INTENT_ACTION:
        state["action"] = None
        return state

    question = state.get("question", "")
    evidence = state.get("evidence", {}) or {}
    context = state.get("context", {}) or {}

    person = evidence.get("person")
    project = evidence.get("project")
    person_entity = _entity_of(state, "Person")
    project_entity = _entity_of(state, "Project")

    # Fall back to the entity the player is standing near.
    if not person and context.get("entity_id"):
        node = store.get_node(str(context["entity_id"]))
        if node and node["label"] == "Person":
            person = queries.person_profile(store, node["id"])
            person_entity = {"id": node["id"], "name": queries.display_name(node)}
    if not project and person:
        owned = person.get("projects_owned") or []
        preferred = owned[0] if owned else (person.get("projects") or [None])[0]
        if preferred:
            project = queries.project_profile(store, preferred["id"])
            project_entity = {"id": preferred["id"], "name": preferred["name"]}

    kind = detect_kind(question)
    title = extract_title(question) if kind == "create_ticket" else _tidy(question)

    fields: dict[str, Any] = {
        "title": title,
        "priority": detect_priority(question),
        "description": f"Created from Company Brain chat: “{question}”",
    }
    if person_entity:
        fields["assignee"] = person_entity["name"]
        fields["assignee_id"] = person_entity["id"]
    else:
        fields["assignee"] = "Unassigned"
    if project_entity:
        fields["project"] = project_entity["name"]
        fields["project_id"] = project_entity["id"]
        project_node = store.get_node(project_entity["id"])
        key = (project_node["props"].get("key") if project_node else None) or project_entity["id"]
        fields["ticket_id"] = _next_ticket_id(store, str(key))
    else:
        fields["project"] = "General"
        fields["ticket_id"] = _next_ticket_id(store, "TASK")

    if kind == "schedule_meeting":
        fields["attendees"] = [person_entity["name"]] if person_entity else []
    if kind == "update_project_status":
        fields["new_status"] = "at risk" if "risk" in question.lower() else "on track"

    summary = (
        f"{kind.replace('_', ' ').title()}: {fields['title']} "
        f"(assignee: {fields['assignee']}, project: {fields['project']})"
    )
    preview = action_store.propose(
        kind=kind,
        summary=summary,
        fields=fields,
        entity_id=fields.get("project_id") or fields.get("assignee_id"),
    )
    state["action"] = preview
    state.setdefault("log", []).append(f"action proposed: {preview['id']} ({kind})")
    return state


def _entity_of(state: BrainState, label: str) -> dict[str, Any] | None:
    for entity in state.get("entities", []):
        if entity["label"] == label:
            return entity
    return None


# ---------------------------------------------------------------------------
# execution (called by the API after confirmation)
# ---------------------------------------------------------------------------
def execute(store: GraphStore, action: dict[str, Any]) -> dict[str, Any]:
    """Execute a confirmed action against the graph.

    Only the ``create_ticket`` kind writes a Node in this prototype; the others
    return a structured record and are stored in the action history so the flow
    is complete without pretending to integrate with external systems.
    """

    kind = action.get("kind")
    fields = dict(action.get("fields", {}))

    if kind != "create_ticket":
        return {
            "kind": kind,
            "status": "recorded",
            "fields": fields,
            "note": "Recorded in the action log (no external system integration in the demo).",
        }

    ticket_id = fields.get("ticket_id") or "TASK-1"
    if store.get_node(ticket_id):
        # Extremely unlikely; keep ids unique.
        ticket_id = _next_ticket_id(store, ticket_id.split("-")[0])

    props: dict[str, Any] = {
        "id": ticket_id,
        "title": fields.get("title", "Untitled task"),
        "description": fields.get("description", ""),
        "status": "To Do",
        "priority": fields.get("priority", "Medium"),
        "created_at": _today(),
        "updated_at": _today(),
        "created_by": "nova_agent",
        "comments_json": "[]",
    }
    if fields.get("assignee_id"):
        props["assignee_id"] = fields["assignee_id"]
    if fields.get("project_id"):
        props["project_id"] = fields["project_id"]

    store.create_node("Ticket", props)
    if fields.get("project_id"):
        store.create_edge(fields["project_id"], ticket_id, "HAS_TICKET")
        store.create_edge(ticket_id, fields["project_id"], "RELATED_TO")
    if fields.get("assignee_id"):
        store.create_edge(ticket_id, fields["assignee_id"], "ASSIGNED_TO")

    return {
        "kind": kind,
        "status": "created",
        "ticket": {
            "id": ticket_id,
            "title": props["title"],
            "status": props["status"],
            "priority": props["priority"],
            "assignee": fields.get("assignee"),
            "project": fields.get("project"),
        },
    }


def _today() -> str:
    from datetime import date

    return date.today().isoformat()
