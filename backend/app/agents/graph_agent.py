"""Graph intelligence agent.

Turns (intent, entities, question) into a structured evidence bundle by running
parameterised traversals through :mod:`app.graph.queries`. No arbitrary Cypher
is ever derived from user input; the agent only selects which whitelisted
query to run.
"""

from __future__ import annotations

from typing import Any

from ..agents import intent_agent
from ..graph import queries
from ..graph.client import GraphStore
from ..workflows.state import (
    INTENT_ACTION,
    INTENT_DECISION,
    INTENT_DECISION_WHY,
    INTENT_DOCUMENT,
    INTENT_EXPERTISE,
    INTENT_GENERAL,
    INTENT_PERSON,
    INTENT_PLACE,
    INTENT_PROJECT,
    INTENT_SYSTEM,
    INTENT_TEAM,
    INTENT_TICKETS,
    INTENT_LIST,
    BrainState,
)


def _first(entities: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    for entity in entities:
        if entity["label"] == label:
            return entity
    return None


def _focus_entities(state: BrainState, store: GraphStore) -> list[dict[str, Any]]:
    """Entities to anchor the traversal, including the nearby entity."""

    entities = list(state.get("entities", []))
    context = state.get("context", {}) or {}
    context_id = context.get("entity_id")
    if context_id and all(e["id"] != context_id for e in entities):
        node = store.get_node(str(context_id))
        if node:
            entities.append(
                {
                    "id": node["id"],
                    "label": node["label"],
                    "name": queries.display_name(node),
                    "subtitle": "",
                    "from_context": True,
                }
            )
    return entities


def run(state: BrainState, store: GraphStore) -> BrainState:
    """LangGraph node: gather graph evidence for the classified intent."""

    question = state.get("question", "")
    intent = state.get("intent", INTENT_GENERAL)
    entities = _focus_entities(state, store)
    terms = intent_agent.extract_terms(question, state.get("entities", []))

    evidence: dict[str, Any] = {
        "intent": intent,
        "focus": [queries.summarise(store.get_node(e["id"])) for e in entities if store.get_node(e["id"])],
        "person": None,
        "project": None,
        "decision": None,
        "technology": None,
        "system": None,
        "document": None,
        "place": None,
        "team": None,
        "decisions": [],
        "documents": [],
        "tickets": [],
        "meetings": [],
        "technologies": [],
        "people_ranked": [],
        "facts": [],
        "related_document_ids": [],
        "graph_node_ids": [e["id"] for e in entities],
        "terms": terms,
    }

    person = _first(entities, "Person")
    project = _first(entities, "Project")
    technology = _first(entities, "Technology")
    decision = _first(entities, "Decision")
    document = _first(entities, "Document")
    system = _first(entities, "System")
    room = _first(entities, "Room")
    office_object = _first(entities, "Object")
    team = _first(entities, "Team")

    if intent == INTENT_PERSON:
        _person_evidence(store, evidence, person, question)
    elif intent == INTENT_PLACE:
        _place_evidence(store, evidence, room, office_object, entities, question)
    elif intent == INTENT_TEAM:
        _team_evidence(store, evidence, team, question)
    elif intent == INTENT_LIST:
        _list_evidence(store, evidence, state.get("list_target", ""), question)
    elif intent == INTENT_PROJECT:
        _project_evidence(store, evidence, project, question)
    elif intent == INTENT_DECISION_WHY:
        _decision_trace_evidence(store, evidence, entities, technology, project, question)
    elif intent == INTENT_DECISION:
        _decision_evidence(store, evidence, entities, decision, project, question)
    elif intent == INTENT_EXPERTISE:
        _expertise_evidence(store, evidence, terms, project)
    elif intent == INTENT_DOCUMENT:
        _document_evidence(store, evidence, document, project, entities)
    elif intent == INTENT_TICKETS:
        _ticket_evidence(store, evidence, project, entities)
    elif intent == INTENT_SYSTEM:
        _system_evidence(store, evidence, system, technology, question)
    elif intent == INTENT_ACTION:
        _action_evidence(store, evidence, entities, question)
    else:
        _general_evidence(store, evidence, terms, project, person)

    state["evidence"] = evidence
    state.setdefault("log", []).append(
        f"graph evidence: {len(evidence['documents'])} docs, "
        f"{len(evidence['decisions'])} decisions, {len(evidence['tickets'])} tickets"
    )
    return state


# ---------------------------------------------------------------------------
# per-intent evidence builders
# ---------------------------------------------------------------------------
def _person_evidence(
    store: GraphStore, evidence: dict[str, Any], person: dict[str, Any] | None, question: str
) -> None:
    if not person:
        _general_evidence(store, evidence, evidence["terms"], None, None)
        return
    profile = queries.person_profile(store, person["id"])
    evidence["person"] = profile
    if not profile:
        return
    evidence["graph_node_ids"].append(person["id"])
    evidence["documents"] = profile["documents"]
    evidence["related_document_ids"].extend(d["id"] for d in profile["documents"])
    evidence["decisions"] = profile["decisions"]
    evidence["meetings"] = profile["meetings"]
    evidence["tickets"] = profile["tickets"]
    evidence["technologies"] = profile["technologies"]
    if profile["projects"]:
        primary = profile["projects"][0]
        project_profile = queries.project_profile(store, primary["id"])
        if project_profile:
            evidence["project"] = project_profile
    evidence["facts"] = _person_facts(profile)


def _person_facts(profile: dict[str, Any]) -> list[str]:
    facts = [f"{profile['name']} is a {profile.get('role') or 'team member'}."]
    if profile.get("team"):
        facts.append(f"Member of the {profile['team']['name']} team.")
    if profile["projects_owned"]:
        facts.append(
            "Owns " + ", ".join(p["name"] for p in profile["projects_owned"]) + "."
        )
    if profile["projects"]:
        facts.append("Works on " + ", ".join(p["name"] for p in profile["projects"]) + ".")
    if profile["technologies"]:
        facts.append(
            "Knows " + ", ".join(t["name"] for t in profile["technologies"]) + "."
        )
    if profile["documents"]:
        facts.append(
            "Authored " + ", ".join(d["name"] for d in profile["documents"]) + "."
        )
    if profile["decisions"]:
        facts.append(
            "Was involved in " + ", ".join(d["name"] for d in profile["decisions"]) + "."
        )
    if profile["collaborators"]:
        facts.append(
            "Collaborates with "
            + ", ".join(c["name"] for c in profile["collaborators"])
            + "."
        )
    if profile["tickets"]:
        facts.append(
            "Assigned tickets include "
            + ", ".join(t["name"] for t in profile["tickets"][:4])
            + "."
        )
    return facts


def _project_evidence(
    store: GraphStore, evidence: dict[str, Any], project: dict[str, Any] | None, question: str
) -> None:
    if not project:
        _general_evidence(store, evidence, evidence["terms"], None, None)
        return
    profile = queries.project_profile(store, project["id"])
    evidence["project"] = profile
    if not profile:
        return
    evidence["graph_node_ids"].append(project["id"])
    evidence["technologies"] = profile["technologies"]
    evidence["documents"] = profile["documents"]
    evidence["related_document_ids"].extend(d["id"] for d in profile["documents"])
    evidence["decisions"] = profile["decisions"]
    evidence["tickets"] = profile["tickets"]
    evidence["meetings"] = profile["meetings"]
    evidence["facts"] = _project_facts(profile)


def _project_facts(profile: dict[str, Any]) -> list[str]:
    facts = [f"{profile['name']} is {profile.get('status', 'in progress')}."]
    if profile.get("health"):
        facts.append(f"Health: {profile['health'].replace('_', ' ')}.")
    if profile.get("owner"):
        facts.append(f"Owned by {profile['owner']['name']}.")
    if profile.get("team"):
        facts.append(f"Delivered by the {profile['team']['name']} team.")
    if profile["members"]:
        facts.append("Members: " + ", ".join(m["name"] for m in profile["members"]) + ".")
    if profile["technologies"]:
        facts.append(
            "Technology stack: " + ", ".join(t["name"] for t in profile["technologies"]) + "."
        )
    if profile["decisions"]:
        facts.append("Decisions include " + ", ".join(d["name"] for d in profile["decisions"]) + ".")
    if profile["open_tickets"]:
        facts.append(
            "Open issues: "
            + "; ".join(t["name"] for t in profile["open_tickets"][:5])
            + "."
        )
    if profile.get("description"):
        facts.append(profile["description"])
    return facts


def _decision_trace_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    entities: list[dict[str, Any]],
    technology: dict[str, Any] | None,
    project: dict[str, Any] | None,
    question: str,
) -> None:
    decisions: list[dict[str, Any]] = []
    tech_decisions: list[dict[str, Any]] = []
    if technology:
        tech_decisions = queries.decisions_about_technology(store, technology["id"])
    if tech_decisions:
        decisions = tech_decisions
    elif project:
        decisions = queries.decisions_for_project(store, project["id"])
    if not decisions:
        # Fall back to any technology or project mentioned in the question.
        for entity in entities:
            if entity["label"] == "Technology":
                decisions.extend(queries.decisions_about_technology(store, entity["id"]))
            elif entity["label"] == "Project":
                decisions.extend(queries.decisions_for_project(store, entity["id"]))
    if not decisions:
        decisions = [queries.summarise(n) for n in store.list_nodes("Decision")]

    traces = []
    for decision in decisions[:2]:
        trace = queries.decision_profile(store, decision["id"])
        if trace:
            traces.append(trace)
    evidence["decision_traces"] = traces
    if traces:
        primary = traces[0]
        evidence["decision"] = primary
        evidence["decisions"] = decisions
        evidence["documents"] = primary["supporting_documents"]
        evidence["related_document_ids"].extend(
            d["id"] for d in primary["supporting_documents"]
        )
        if primary.get("project"):
            project_profile = queries.project_profile(store, primary["project"]["id"])
            if project_profile:
                evidence["project"] = project_profile
                evidence["technologies"] = project_profile["technologies"]
                evidence["related_document_ids"].extend(
                    d["id"] for d in project_profile["documents"]
                )
                if not evidence["documents"]:
                    evidence["documents"] = project_profile["documents"][:4]
        if technology:
            evidence["technology"] = queries.technology_profile(store, technology["id"])
        elif primary.get("project"):
            for tech in (evidence.get("project") or {}).get("technologies", []):
                if tech["name"].lower() in question.lower():
                    evidence["technology"] = queries.technology_profile(store, tech["id"])
                    break
        evidence["meetings"] = primary.get("meetings", [])
        evidence["graph_node_ids"] += [d["id"] for d in traces]
        if primary.get("project"):
            evidence["graph_node_ids"].append(primary["project"]["id"])
        if technology:
            evidence["graph_node_ids"].append(technology["id"])
    evidence["facts"] = _decision_trace_facts(evidence)


def _decision_trace_facts(evidence: dict[str, Any]) -> list[str]:
    facts: list[str] = []
    for trace in evidence.get("decision_traces", []):
        facts.append(
            f"{trace['id']} — {trace['title']} ({trace.get('status')}, {trace.get('date')})."
        )
        if trace.get("summary"):
            facts.append(trace["summary"])
        if trace.get("reason"):
            facts.append(f"Reason: {trace['reason']}")
        if trace.get("makers"):
            facts.append(
                "Decision makers: " + ", ".join(m["name"] for m in trace["makers"]) + "."
            )
        if trace.get("supporting_documents"):
            facts.append(
                "Supported by "
                + ", ".join(d["name"] for d in trace["supporting_documents"])
                + "."
            )
        if trace.get("meetings"):
            facts.append(
                "Discussed in " + ", ".join(m["name"] for m in trace["meetings"]) + "."
            )
    return facts


def _decision_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    entities: list[dict[str, Any]],
    decision: dict[str, Any] | None,
    project: dict[str, Any] | None,
    question: str,
) -> None:
    if decision:
        trace = queries.decision_profile(store, decision["id"])
        evidence["decision"] = trace
        evidence["decision_traces"] = [trace] if trace else []
        if trace:
            evidence["documents"] = trace["supporting_documents"]
            evidence["related_document_ids"].extend(
                d["id"] for d in trace["supporting_documents"]
            )
            evidence["meetings"] = trace.get("meetings", [])
            evidence["graph_node_ids"].append(decision["id"])
            if trace.get("project"):
                project_profile = queries.project_profile(store, trace["project"]["id"])
                evidence["project"] = project_profile
                evidence["technologies"] = project_profile["technologies"] if project_profile else []
        evidence["facts"] = _decision_trace_facts(evidence)
        return

    if project:
        decisions = queries.decisions_for_project(store, project["id"])
    else:
        decisions = [queries.summarise(n) for n in store.list_nodes("Decision")]
    traces = [queries.decision_profile(store, d["id"]) for d in decisions]
    traces = [t for t in traces if t]
    evidence["decisions"] = decisions
    evidence["decision_traces"] = traces
    evidence["documents"] = [
        doc
        for trace in traces
        for doc in trace.get("supporting_documents", [])
    ][:8]
    evidence["related_document_ids"].extend(d["id"] for d in evidence["documents"])
    evidence["graph_node_ids"].extend(d["id"] for d in decisions[:6])
    if project:
        evidence["project"] = queries.project_profile(store, project["id"])
        evidence["graph_node_ids"].append(project["id"])
    evidence["facts"] = [
        "Company decisions:",
        *(
            f"{t['id']} — {t['title']} ({t.get('status')}, {t.get('date')})"
            for t in traces
        ),
    ]


def _expertise_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    terms: list[str],
    project: dict[str, Any] | None,
) -> None:
    ranked = queries.expertise_rank(store, terms, project_id=project["id"] if project else None)
    evidence["people_ranked"] = ranked
    if project:
        evidence["project"] = queries.project_profile(store, project["id"])
        evidence["graph_node_ids"].append(project["id"])
    # Technology-specific evidence for "who knows X".
    if not ranked and terms:
        for term in terms:
            tech = queries.resolve_entity(store, term, ["Technology"])
            if tech:
                ranked = queries.expertise_rank(store, [queries.display_name(tech)], None)
                evidence["people_ranked"] = ranked
                evidence["technology"] = queries.technology_profile(store, tech["id"])
                evidence["graph_node_ids"].append(tech["id"])
                break
    evidence["graph_node_ids"].extend(
        person["person"]["id"] for person in evidence["people_ranked"][:3]
    )
    evidence["facts"] = [
        f"{entry['person']['name']} (score {entry['score']}): " + "; ".join(entry["reasons"])
        for entry in evidence["people_ranked"][:5]
    ]


def _document_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    document: dict[str, Any] | None,
    project: dict[str, Any] | None,
    entities: list[dict[str, Any]],
) -> None:
    if document:
        profile = queries.document_profile(store, document["id"])
        evidence["document"] = profile
        evidence["documents"] = [queries.summarise(store.get_node(document["id"]))]
        evidence["related_document_ids"].append(document["id"])
        evidence["graph_node_ids"].append(document["id"])
        if profile and profile.get("project"):
            evidence["project"] = queries.project_profile(store, profile["project"]["id"])
        evidence["facts"] = [f"{profile['title']} ({profile.get('type')})."] if profile else []
        return

    if project:
        documents = queries.documents_for_project(store, project["id"])
        evidence["project"] = queries.project_profile(store, project["id"])
        evidence["graph_node_ids"].append(project["id"])
    else:
        documents = queries.documents_index(store)
    evidence["documents"] = documents
    evidence["related_document_ids"].extend(d["id"] for d in documents)
    evidence["facts"] = [f"{d['title']} ({d['type']})" for d in documents[:10]]


def _ticket_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    project: dict[str, Any] | None,
    entities: list[dict[str, Any]],
) -> None:
    ticket_entity = _first(entities, "Ticket")
    if project:
        tickets = queries.tickets_for_project(store, project["id"])
        evidence["project"] = queries.project_profile(store, project["id"])
        evidence["graph_node_ids"].append(project["id"])
    else:
        tickets = [queries.summarise(n) for n in store.list_nodes("Ticket")]
    if ticket_entity:
        profile = queries.ticket_profile(store, ticket_entity["id"])
        evidence["ticket"] = profile
        tickets = [queries.summarise(store.get_node(ticket_entity["id"]))]
        evidence["graph_node_ids"].append(ticket_entity["id"])
    evidence["tickets"] = tickets
    evidence["facts"] = [
        f"{t['name']} — {t['props'].get('status', '')} / {t['props'].get('priority', '')}"
        for t in tickets[:12]
    ]


def _system_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    system: dict[str, Any] | None,
    technology: dict[str, Any] | None,
    question: str,
) -> None:
    if system:
        system_profile = queries.system_profile(store, system["id"])
        evidence["system"] = system_profile
        evidence["graph_node_ids"].append(system["id"])
        if system_profile:
            evidence["documents"] = system_profile.get("documents", [])
            evidence["related_document_ids"].extend(
                d["id"] for d in system_profile.get("documents", [])
            )
            if system_profile.get("technology"):
                tech_id = system_profile["technology"]["id"]
                tech_profile = queries.technology_profile(store, tech_id)
                evidence["technology"] = tech_profile
                evidence["graph_node_ids"].append(tech_id)
                evidence["decisions"] = queries.decisions_about_technology(store, tech_id)
        evidence["facts"] = _system_facts(evidence)
        return

    # No specific system: list systems, optionally filtered by a technology.
    systems = [queries.summarise(n) for n in store.list_nodes("System")]
    evidence["systems"] = systems
    if technology:
        tech_profile = queries.technology_profile(store, technology["id"])
        evidence["technology"] = tech_profile
        evidence["decisions"] = queries.decisions_about_technology(store, technology["id"])
        related_docs = queries.documents_for_technology(store, technology["id"])
        evidence["documents"] = related_docs
        evidence["related_document_ids"].extend(d["id"] for d in related_docs)
        evidence["facts"] = [
            f"{technology['name']} is part of "
            + ", ".join(s["name"] for s in (tech_profile or {}).get("systems", []))
            + ".",
            "Projects depending on it: "
            + ", ".join(p["name"] for p in (tech_profile or {}).get("projects", [])),
        ]
        evidence["graph_node_ids"].append(technology["id"])
    else:
        evidence["facts"] = [
            f"{s['name']} — {s['props'].get('status', '')}" for s in systems
        ]
    evidence["graph_node_ids"].extend(s["id"] for s in systems[:6])


def _system_facts(evidence: dict[str, Any]) -> list[str]:
    system = evidence.get("system") or {}
    facts = [f"{system.get('name')} is {system.get('status', 'unknown')}."]
    if system.get("description"):
        facts.append(system["description"])
    if system.get("owner"):
        facts.append(f"Owned by {system['owner']['name']}.")
    if system.get("technology"):
        facts.append(f"Built on {system['technology']['name']}.")
    if system.get("projects"):
        facts.append(
            "Projects depending on it: "
            + ", ".join(p["name"] for p in system["projects"])
            + "."
        )
    if evidence.get("technology"):
        experts = evidence["technology"].get("experts") or []
        if experts:
            facts.append("People with expertise: " + ", ".join(e["name"] for e in experts) + ".")
    return facts


def _action_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    entities: list[dict[str, Any]],
    question: str,
) -> None:
    person = _first(entities, "Person")
    project = _first(entities, "Project")
    if person:
        evidence["person"] = queries.person_profile(store, person["id"])
        evidence["graph_node_ids"].append(person["id"])
    if project:
        evidence["project"] = queries.project_profile(store, project["id"])
        evidence["graph_node_ids"].append(project["id"])
    # If the user is standing next to a person but did not name them, use them.
    if not person and not project:
        evidence["facts"] = ["No explicit target found for the requested action."]


def _team_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    team: dict[str, Any] | None,
    question: str,
) -> None:
    """Describe a team: its members, owning department and systems."""

    if not team:
        _general_evidence(store, evidence, evidence["terms"], None, None)
        return
    node = store.get_node(team["id"])
    if not node:
        return
    name = queries.display_name(node)
    nodes, _ = store.expand(team["id"], depth=1)

    members = sorted(
        (n for n in nodes if n["label"] == "Person"),
        key=lambda n: queries.display_name(n),
    )
    systems = [n for n in nodes if n["label"] == "System"]
    departments = [n for n in nodes if n["label"] == "Department"]
    projects = [n for n in nodes if n["label"] == "Project"]

    facts = [f"{name} is a team at NovaTech."]
    if departments:
        facts.append(f"Part of the {queries.display_name(departments[0])} department.")
    if members:
        member_text = ", ".join(
            queries.display_name(m)
            + (f" ({m['props']['role']})" if m["props"].get("role") else "")
            for m in members
        )
        facts.append(f"Members: {member_text}.")
    else:
        facts.append("No members are recorded for this team.")
    if systems:
        facts.append("Owns systems: " + ", ".join(queries.display_name(s) for s in systems) + ".")
    if projects:
        facts.append("Works on: " + ", ".join(queries.display_name(p) for p in projects) + ".")

    evidence["team"] = {
        "id": node["id"],
        "name": name,
        "members": [queries.summarise(m) for m in members],
        "systems": [queries.summarise(s) for s in systems],
        "department": queries.summarise(departments[0]) if departments else None,
    }
    evidence["facts"] = facts
    evidence["graph_node_ids"].append(team["id"])
    evidence["graph_node_ids"].extend(m["id"] for m in members)


def _list_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    target: str,
    question: str,
) -> None:
    """Enumerate every node of a label for "list all X" questions."""

    if not target:
        _general_evidence(store, evidence, evidence["terms"], None, None)
        return
    nodes = sorted(store.list_nodes(target), key=lambda n: queries.display_name(n))
    if not nodes:
        _general_evidence(store, evidence, evidence["terms"], None, None)
        return

    plural = {
        "Person": "people",
        "Project": "projects",
        "Team": "teams",
        "System": "systems",
        "Decision": "decisions",
        "Technology": "technologies",
        "Document": "documents",
        "Ticket": "tickets",
        "Room": "rooms",
        "Object": "objects",
    }.get(target, f"{target.lower()}s")

    facts = [f"NovaTech has {len(nodes)} {plural}:"]
    facts.extend(_list_line(store, target, node) for node in nodes)
    evidence["facts"] = facts
    evidence["listing"] = {
        "label": target,
        "count": len(nodes),
        "items": [queries.summarise(n) for n in nodes],
    }
    evidence["graph_node_ids"].extend(n["id"] for n in nodes)


def _list_line(store: GraphStore, label: str, node: dict[str, Any]) -> str:
    name = queries.display_name(node)
    props = node.get("props", {})

    def pretty(value: Any) -> str:
        return str(value).replace("_", " ")

    extra: list[str] = []
    if label == "Project":
        if props.get("key"):
            extra.append(str(props["key"]))
        if props.get("status"):
            extra.append(pretty(props["status"]))
        if props.get("health"):
            extra.append(f"health {pretty(props['health'])}")
        owner = props.get("owner_id")
        if owner:
            owner_node = store.get_node(owner)
            if owner_node:
                extra.append(f"owner {queries.display_name(owner_node)}")
    elif label == "System":
        if props.get("status"):
            extra.append(pretty(props["status"]))
    elif label == "Decision":
        if props.get("status"):
            extra.append(pretty(props["status"]))
        if props.get("date"):
            extra.append(str(props["date"])[:10])
    elif label == "Ticket":
        if props.get("status"):
            extra.append(pretty(props["status"]))
    elif label in ("Document", "Technology", "Person", "Team", "Room", "Object"):
        if props.get("description"):
            extra.append(str(props["description"])[:110])

    return f"• {name} — " + ", ".join(extra) if extra else f"• {name}"


def _place_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    room: dict[str, Any] | None,
    office_object: dict[str, Any] | None,
    entities: list[dict[str, Any]],
    question: str,
) -> None:
    """Describe an office room or object and its immediate surroundings."""

    facts: list[str] = []

    if office_object:
        node = store.get_node(office_object["id"])
        if node:
            props = node["props"]
            name = queries.display_name(node)
            kind = str(props.get("type", "object")).replace("_", " ")
            desc = str(props.get("description", "")).strip()
            facts.append(f"{name} ({kind}) — {desc}" if desc else f"{name} ({kind}).")
            evidence["place"] = {
                "id": node["id"],
                "name": name,
                "type": kind,
                "description": desc,
            }
            room_id = props.get("room_id") or _find_related_room(store, office_object["id"])
            if room_id:
                room_node = store.get_node(str(room_id))
                if room_node:
                    facts.append(f"Located in the {queries.display_name(room_node)}.")
                    evidence["focus"].append(queries.summarise(room_node))
                    evidence["graph_node_ids"].append(room_node["id"])
                    facts.append(
                        "Also in this room: "
                        + _list_objects(store, str(room_id), exclude=office_object["id"])
                        + "."
                    )
            evidence["graph_node_ids"].append(office_object["id"])

    if room:
        node = store.get_node(room["id"])
        if node:
            props = node["props"]
            desc = str(props.get("description", "")).strip()
            name = queries.display_name(node)
            facts.append(f"{name} — {desc}" if desc else f"{name}.")
            if not evidence.get("place"):
                evidence["place"] = {
                    "id": node["id"],
                    "name": name,
                    "type": "room",
                    "description": desc,
                }
            inside = _object_nodes(store, room["id"])
            if inside:
                facts.append(
                    "You can find: " + ", ".join(queries.display_name(o) for o in inside) + "."
                )
            linked = _list_connected_rooms(store, room["id"])
            if linked:
                facts.append(f"Connects to: {linked}.")
            evidence["graph_node_ids"].append(room["id"])

    if not facts:
        _general_evidence(store, evidence, evidence["terms"], None, None)
        return
    evidence["facts"] = facts


def _find_related_room(store: GraphStore, object_id: str) -> str | None:
    nodes, _ = store.expand(object_id, rels=["FOUND_IN", "IN_ROOM"], depth=1)
    for node in nodes:
        if node["label"] == "Room" and node["id"] != object_id:
            return str(node["id"])
    return None


def _object_nodes(store: GraphStore, room_id: str) -> list[dict[str, Any]]:
    nodes, _ = store.expand(room_id, rels=["FOUND_IN", "IN_ROOM"], depth=1)
    return [
        n
        for n in nodes
        if n["label"] == "Object" and n["id"] != room_id
    ]


def _list_objects(store: GraphStore, room_id: str, exclude: str | None = None) -> str:
    names = [
        queries.display_name(n)
        for n in _object_nodes(store, room_id)
        if n["id"] != exclude
    ]
    return ", ".join(names) if names else "nothing else"


def _list_connected_rooms(store: GraphStore, room_id: str) -> str:
    nodes, _ = store.expand(room_id, rels=["CONNECTS_TO"], depth=1)
    return ", ".join(
        queries.display_name(n) for n in nodes if n["label"] == "Room" and n["id"] != room_id
    )


def _general_evidence(
    store: GraphStore,
    evidence: dict[str, Any],
    terms: list[str],
    project: dict[str, Any] | None,
    person: dict[str, Any] | None,
) -> None:
    stats = store.stats()
    evidence["stats"] = stats.as_dict()
    search_text = " ".join(terms[:4])
    matches = store.search_nodes(search_text) if search_text else []
    evidence["search_matches"] = [queries.summarise(n) for n in matches[:8]]
    evidence["graph_node_ids"].extend(n["id"] for n in matches[:6])
    if project:
        evidence["project"] = queries.project_profile(store, project["id"])
    if person:
        evidence["person"] = queries.person_profile(store, person["id"])
    evidence["facts"] = [
        f"NovaTech knowledge graph holds {stats.nodes} nodes and {stats.edges} relationships "
        "across people, teams, projects, documents, decisions, tickets and systems."
    ]
    if evidence["search_matches"]:
        evidence["facts"].append(
            "Closest graph entities: "
            + ", ".join(m["name"] for m in evidence["search_matches"])
            + "."
        )
