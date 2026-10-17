"""Reasoning agent.

Composes the final answer from the evidence bundle. Two paths exist:

* **Deterministic** — the default. Answers are assembled from live graph
  results, so they are always grounded, reproducible, and work without any LLM
  key (DEMO_MODE).
* **LLM-assisted** — when a provider is configured, the model is asked to
  rephrase the *supplied* evidence into a natural answer. It cannot introduce
  facts: if the call fails, the deterministic answer stands.

Every factual answer carries sources and a graph explanation path.
"""

from __future__ import annotations

from typing import Any

from ..graph import queries
from ..graph.client import GraphStore
from ..llm.provider import LLMProvider, safe_complete
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
    INTENT_TICKETS,
    BrainState,
)

OPEN_STATUSES = ("To Do", "In Progress", "In Review", "Blocked")

ANSWER_SYSTEM_PROMPT = (
    "You are Nova, an assistant that answers employee questions about their company "
    "using ONLY the supplied evidence. Rules:\n"
    "1. Never invent facts, names, dates or relationships that are not in the evidence.\n"
    "2. Be concise: at most 120 words.\n"
    "3. Prefer concrete names, ids and dates over vague statements.\n"
    "4. If the evidence does not answer the question, say so plainly.\n"
    "Answer in plain text, no markdown headers."
)


# ---------------------------------------------------------------------------
# sources
# ---------------------------------------------------------------------------
def _build_sources(state: BrainState, store: GraphStore) -> list[dict[str, Any]]:
    """Assemble the citation list shown next to every answer."""

    sources: list[dict[str, Any]] = []
    evidence = state.get("evidence", {}) or {}
    people = {p["id"]: p for p in store.list_nodes("Person")}

    # Document passages from retrieval.
    for chunk in state.get("documents", []):
        doc_id = chunk.get("document_id")
        doc_node = store.get_node(doc_id) if doc_id else None
        props = doc_node["props"] if doc_node else {}
        author_node = people.get(props.get("author_id"))
        author = queries.display_name(author_node) if author_node else props.get("author_id", "")
        sources.append(
            {
                "id": doc_id,
                "type": "document",
                "title": chunk.get("document_title") or props.get("title", doc_id),
                "doc_type": chunk.get("type") or props.get("type", "Document"),
                "author": author,
                "date": props.get("updated_at") or props.get("created_at", ""),
                "excerpt": chunk.get("excerpt") or chunk.get("text", "")[:280],
                "heading": chunk.get("heading", ""),
                "relevance": chunk.get("score", 0.0),
            }
        )

    # Decisions.
    for trace in evidence.get("decision_traces", []) or []:
        sources.append(
            {
                "id": trace["id"],
                "type": "decision",
                "title": trace.get("title") or trace["id"],
                "doc_type": "Decision",
                "author": ", ".join(m["name"] for m in trace.get("makers", [])),
                "date": trace.get("date", ""),
                "excerpt": trace.get("summary", ""),
                "heading": trace.get("status", ""),
                "relevance": 1.0,
            }
        )

    # Meetings.
    for meeting in evidence.get("meetings", []) or []:
        props = meeting.get("props", {})
        attendees = props.get("attendee_ids", [])
        names = [queries.display_name(people[a]) for a in attendees if a in people]
        sources.append(
            {
                "id": meeting["id"],
                "type": "meeting",
                "title": meeting["name"],
                "doc_type": "Meeting",
                "author": ", ".join(names[:4]),
                "date": props.get("date", ""),
                "excerpt": props.get("summary", ""),
                "heading": "",
                "relevance": 0.8,
            }
        )

    # Tickets.
    for ticket in evidence.get("tickets", []) or []:
        props = ticket.get("props", {})
        assignee_node = people.get(props.get("assignee_id"))
        assignee = queries.display_name(assignee_node) if assignee_node else ""
        sources.append(
            {
                "id": ticket["id"],
                "type": "ticket",
                "title": ticket["name"],
                "doc_type": "Ticket",
                "author": assignee,
                "date": props.get("updated_at", ""),
                "excerpt": props.get("description", "")[:240],
                "heading": props.get("status", ""),
                "relevance": 0.6,
            }
        )

    # Graph facts (ownership, membership, expertise).
    if evidence.get("person"):
        profile = evidence["person"]
        sources.append(
            {
                "id": profile["id"],
                "type": "graph",
                "title": f"Company graph · Person: {profile['name']}",
                "doc_type": "Person",
                "author": profile.get("team", {}).get("name", "") if profile.get("team") else "",
                "date": "",
                "excerpt": f"{profile.get('role', '')}. "
                + ", ".join(f"{f}." for f in evidence.get("facts", [])[:2]),
                "heading": "",
                "relevance": 0.9,
            }
        )
    if evidence.get("project"):
        profile = evidence["project"]
        owner = profile.get("owner") or {}
        sources.append(
            {
                "id": profile["id"],
                "type": "graph",
                "title": f"Company graph · Project: {profile['name']}",
                "doc_type": "Project",
                "author": owner.get("name", ""),
                "date": profile.get("target_date", ""),
                "excerpt": (profile.get("description") or "")[:240],
                "heading": "",
                "relevance": 0.9,
            }
        )

    if evidence.get("place"):
        place = evidence["place"]
        sources.append(
            {
                "id": place.get("id"),
                "type": "graph",
                "title": f"Office map · {place.get('type', 'place').title()}: {place.get('name')}",
                "doc_type": place.get("type", "Place"),
                "author": "",
                "date": "",
                "excerpt": place.get("description", ""),
                "heading": "",
                "relevance": 0.95,
            }
        )
    # Deduplicate by (type, id), keeping the highest relevance.
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for source in sources:
        if not source.get("id"):
            continue
        key = (source["type"], str(source["id"]))
        existing = best.get(key)
        if not existing or source.get("relevance", 0) > existing.get("relevance", 0):
            best[key] = source
    ordered = sorted(
        best.values(), key=lambda s: (-s.get("relevance", 0), s.get("type", ""))
    )
    return ordered[:10]


def _confidence(state: BrainState, sources: list[dict[str, Any]]) -> float:
    """Transparent confidence heuristic based on evidence quality."""

    if not sources:
        return 0.15
    score = 0.45
    score += min(0.25, 0.05 * len(sources))
    kinds = {s["type"] for s in sources}
    if "decision" in kinds:
        score += 0.12
    if "document" in kinds:
        score += 0.08
    if "graph" in kinds:
        score += 0.1
    if "meeting" in kinds:
        score += 0.03
    if "ticket" in kinds:
        score += 0.02
    # An intent whose evidence bundle was empty is clearly weak.
    evidence = state.get("evidence", {}) or {}
    if not any(
        evidence.get(key)
        for key in ("person", "project", "decision", "documents", "tickets", "people_ranked", "place")
    ):
        score = min(score, 0.3)
    return round(min(0.98, score), 2)


# ---------------------------------------------------------------------------
# deterministic answer composers
# ---------------------------------------------------------------------------
def _has(question: str, *words: str) -> bool:
    lower = question.lower()
    return any(word in lower for word in words)


def _person_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    profile = evidence.get("person")
    question = state.get("question", "")
    if not profile:
        return "I could not find that person in the company graph."
    facts: list[str] = []
    if _has(question, "what do", "know", "skill", "technolog", "expert"):
        if profile["technologies"]:
            facts.append(
                f"{profile['name']} knows "
                + ", ".join(t["name"] for t in profile["technologies"])
                + "."
            )
        if profile["skills"]:
            facts.append(
                "Skills: " + ", ".join(s["name"] for s in profile["skills"]) + "."
            )
    if _has(question, "own", "responsible"):
        if profile["projects_owned"]:
            facts.append(
                f"{profile['name']} owns "
                + ", ".join(p["name"] for p in profile["projects_owned"])
                + "."
            )
        elif profile["projects"]:
            facts.append(
                f"{profile['name']} does not own a project outright but works on "
                + ", ".join(p["name"] for p in profile["projects"])
                + "."
            )
    if _has(question, "work", "on", "doing", "involved"):
        if profile["projects"]:
            facts.append(
                f"{profile['name']} works on "
                + ", ".join(p["name"] for p in profile["projects"])
                + "."
            )
    if _has(question, "collaborat", "with", "team", "who does", "know"):
        if profile["collaborators"]:
            facts.append(
                "Collaborates with "
                + ", ".join(c["name"] for c in profile["collaborators"])
                + "."
            )
    if _has(question, "document", "authored", "wrote"):
        if profile["documents"]:
            facts.append(
                f"{profile['name']} authored "
                + "; ".join(d["name"] for d in profile["documents"])
                + "."
            )
    if _has(question, "decision"):
        if profile["decisions"]:
            facts.append(
                "Involved in "
                + "; ".join(d["name"] for d in profile["decisions"])
                + "."
            )
    if not facts:
        lead = f"{profile['name']} is a {profile.get('role', 'team member')}"
        if profile.get("team"):
            lead += f" on the {profile['team']['name']} team"
        facts.append(lead + ".")
        facts.extend(evidence.get("facts", [])[1:])
    intro = f"{profile['name']} is a {profile.get('role', '')}."
    if profile.get("team"):
        intro = f"{profile['name']} ({profile.get('role', '')}) is on the {profile['team']['name']} team."
    return "\n".join([intro] + facts)


def _project_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    profile = evidence.get("project")
    question = state.get("question", "")
    if not profile:
        return "I could not find that project in the company graph."
    lines: list[str] = []
    owner = profile.get("owner") or {}
    if _has(question, "own", "lead", "who"):
        if owner:
            lines.append(
                f"{profile['name']} is owned by {owner['name']}"
                + (
                    f" ({owner.get('subtitle') or owner.get('props', {}).get('role', '')})"
                    if owner.get("props", {}).get("role")
                    else ""
                )
                + "."
            )
        if profile.get("lead"):
            lines.append(f"Engineering lead: {profile['lead']['name']}.")
        if profile.get("team"):
            lines.append(f"Team: {profile['team']['name']}.")
    if _has(question, "problem", "issue", "blocker", "risk", "status", "health"):
        if profile.get("health"):
            lines.append(
                f"Health: {profile['health'].replace('_', ' ')} "
                f"(status: {profile.get('status', 'in progress')})."
            )
        if profile.get("open_tickets"):
            lines.append("Open issues:")
            lines.extend(
                f"• {t['name']} — {t['props'].get('status', '')} / {t['props'].get('priority', '')}"
                for t in profile["open_tickets"][:5]
            )
    if _has(question, "member", "who works", "team", "people", "involved"):
        if profile.get("members"):
            lines.append(
                "Members: " + ", ".join(m["name"] for m in profile["members"]) + "."
            )
    if _has(question, "stack", "technolog", "using", "depend"):
        if profile.get("technologies"):
            lines.append(
                "Stack: " + ", ".join(t["name"] for t in profile["technologies"]) + "."
            )
    if _has(question, "decision"):
        if profile.get("decisions"):
            lines.append(
                "Decisions: "
                + "; ".join(f"{d['name']}" for d in profile["decisions"])
                + "."
            )
    if _has(question, "document", "spec", "design", "doc"):
        if profile.get("documents"):
            lines.append(
                "Documents: " + "; ".join(d["name"] for d in profile["documents"][:6]) + "."
            )
    if not lines:
        lines.append(f"{profile['name']} — {profile.get('description', '')}")
        if owner:
            lines.append(f"Owner: {owner['name']}.")
        if profile.get("team"):
            lines.append(f"Team: {profile['team']['name']}.")
        if profile.get("technologies"):
            lines.append(
                "Stack: " + ", ".join(t["name"] for t in profile["technologies"]) + "."
            )
        if profile.get("members"):
            lines.append("Members: " + ", ".join(m["name"] for m in profile["members"]) + ".")
        if profile.get("open_tickets"):
            lines.append(f"{len(profile['open_tickets'])} open issues.")
        if profile.get("decisions"):
            lines.append(
                "Key decisions: "
                + "; ".join(d["name"] for d in profile["decisions"][:3])
                + "."
            )
    return "\n".join(lines)


def _decision_trace_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    traces = evidence.get("decision_traces", [])
    if not traces:
        return (
            "I could not trace a decision for that question in the company graph. "
            "Try naming the technology or the project."
        )
    trace = traces[0]
    lines = [
        f"{trace['id']} — {trace.get('title')} "
        f"({trace.get('status', 'unknown')}, {trace.get('date', '')})."
    ]
    if trace.get("summary"):
        lines.append(trace["summary"])
    if trace.get("reason"):
        lines.append(f"Reason: {trace['reason']}")
    if trace.get("makers"):
        lines.append(
            "Decision makers: " + ", ".join(m["name"] for m in trace["makers"]) + "."
        )
    if trace.get("supporting_documents"):
        lines.append(
            "Supporting documents: "
            + "; ".join(d["name"] for d in trace["supporting_documents"])
            + "."
        )
    if trace.get("meetings"):
        lines.append(
            "Discussed in " + ", ".join(m["name"] for m in trace["meetings"]) + "."
        )
    alternatives = trace.get("alternatives") or []
    if alternatives:
        considered = "; ".join(
            f"{a.get('name')} — {a.get('outcome')}" for a in alternatives if a.get("name")
        )
        if considered:
            lines.append(f"Alternatives considered: {considered}.")
    return "\n".join(lines)


def _decision_list_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    traces = evidence.get("decision_traces") or []
    decisions = evidence.get("decisions") or []
    if traces:
        lines = [f"{t['id']} — {t.get('title')} ({t.get('status')}, {t.get('date')})" for t in traces]
        return "\n".join(lines)
    if decisions:
        lines = [
            f"{d['name']} ({d['props'].get('status', '')}, {d['props'].get('date', '')})"
            for d in decisions
        ]
        return "\n".join(lines)
    return "I could not find any decisions for that question in the company graph."


def _expertise_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    ranked = evidence.get("people_ranked", [])
    question = state.get("question", "").lower()
    if not ranked:
        return (
            "I could not find anyone in the company graph connected to that topic. "
            "Try naming a technology or a project."
        )
    top = ranked[0]
    people = ranked[:5]
    lines: list[str] = []
    if _has(question, "who should", "talk", "contact", "help", "best", "right person"):
        lines.append(
            f"Start with {top['person']['name']}"
            + (f" ({top.get('role')})" if top.get("role") else "")
            + "."
        )
    else:
        lines.append(
            "People connected to this topic, ranked by graph relationships:"
        )
    for entry in people:
        person = entry["person"]
        detail = "; ".join(entry["reasons"][:3])
        lines.append(f"• {person['name']} (score {entry['score']}) — {detail}.")
    if top.get("team"):
        lines.append(
            f"Top recommendation: {top['person']['name']} on the {top['team']} team."
        )
    return "\n".join(lines)


def _document_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    profile = evidence.get("document")
    passages = state.get("documents", [])
    if profile:
        lines = [
            f"{profile['title']} ({profile.get('type')})",
        ]
        if profile.get("author"):
            lines.append(f"Author: {profile['author']['name']}.")
        if profile.get("updated_at"):
            lines.append(f"Updated {profile['updated_at']}.")
        if profile.get("project"):
            lines.append(f"Related project: {profile['project']['name']}.")
        if passages:
            lines.append(f"\nExcerpt — {passages[0].get('heading', '')}:")
            lines.append(passages[0].get("excerpt", ""))
        return "\n".join(lines)
    documents = evidence.get("documents", [])
    if not documents:
        return "I could not find that document in the company library."
    lines = [f"I found {len(documents)} documents:"]
    lines.extend(f"• {d['name']} ({d['subtitle'] or d['props'].get('type', 'Document')})" for d in documents[:8])
    return "\n".join(lines)


def _ticket_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    tickets = evidence.get("tickets", [])
    if not tickets:
        return "I could not find any tickets for that question."
    by_status: dict[str, list[dict[str, Any]]] = {}
    for ticket in tickets:
        status = str(ticket["props"].get("status", "Unknown"))
        by_status.setdefault(status, []).append(ticket)
    lines: list[str] = []
    for status in OPEN_STATUSES + ("Done",):
        group = by_status.get(status)
        if not group:
            continue
        lines.append(f"{status} ({len(group)}):")
        lines.extend(f"• {t['name']} [{t['props'].get('priority', '')}]" for t in group[:6])
    return "\n".join(lines) or "No tickets found."


def _system_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    facts = evidence.get("facts", [])
    if evidence.get("system") or facts:
        return "\n".join(facts) if facts else "No system information found."
    systems = evidence.get("systems", [])
    if systems:
        lines = ["Company systems:"]
        lines.extend(f"• {s['name']} — {s['props'].get('status', '')}" for s in systems)
        return "\n".join(lines)
    return "I could not find that system in the company graph."


def _place_answer(state: BrainState) -> str:
    evidence = state.get("evidence", {}) or {}
    facts = evidence.get("facts", [])
    # Drop the generic "graph holds N nodes" filler if we have real place facts.
    real = [f for f in facts if "knowledge graph holds" not in f]
    if real:
        return "\n".join(real)
    if facts:
        return "\n".join(facts)
    return "I could not find that place or object on the office map."


def _general_answer(state: BrainState) -> str:
    evidence = state["evidence"]
    facts = evidence.get("facts", [])
    matches = evidence.get("search_matches", [])
    if matches:
        names = ", ".join(m["name"] for m in matches[:5])
        facts = facts + [f"Closest matches in the graph: {names}."]
    if not facts:
        return (
            "I could not find that in the company graph. Try asking about a person, "
            "project, decision, document or system."
        )
    return "\n".join(facts)


def _llm_answer(state: BrainState, llm: LLMProvider) -> str | None:
    """Ask the model to rephrase the evidence bundle. Returns None on failure."""

    evidence = state.get("evidence", {}) or {}
    facts = "\n".join(f"- {fact}" for fact in evidence.get("facts", [])[:20])
    sources = "\n".join(
        f"- [{s['type']}] {s['title']} ({s.get('date', '')})" for s in state.get("sources", [])
    )
    user = (
        f"Evidence (facts from the company knowledge graph):\n{facts or '- (none)'}\n\n"
        f"Sources:\n{sources or '- (none)'}\n\n"
        f"Question: {state.get('question', '')}\n\n"
        "Write the answer using only this evidence."
    )
    return safe_complete(llm, ANSWER_SYSTEM_PROMPT, user, temperature=0.0)


# ---------------------------------------------------------------------------
# node entry point
# ---------------------------------------------------------------------------
def run(state: BrainState, store: GraphStore, llm: LLMProvider | None = None) -> BrainState:
    """LangGraph node: compose answer, sources, confidence and graph path."""

    intent = state.get("intent", INTENT_GENERAL)
    composers = {
        INTENT_PERSON: _person_answer,
        INTENT_PROJECT: _project_answer,
        INTENT_DECISION: lambda s: _decision_trace_answer(s)
        if s.get("evidence", {}).get("decision_traces")
        and s.get("evidence", {}).get("decision")
        else _decision_list_answer(s),
        INTENT_DECISION_WHY: _decision_trace_answer,
        INTENT_EXPERTISE: _expertise_answer,
        INTENT_DOCUMENT: _document_answer,
        INTENT_TICKETS: _ticket_answer,
        INTENT_SYSTEM: _system_answer,
        INTENT_PLACE: _place_answer,
        INTENT_GENERAL: _general_answer,
    }
    composer = composers.get(intent, _general_answer)
    answer = composer(state)

    # LLM refinement is optional and best effort.
    if llm is not None and getattr(llm, "available", False):
        refined = _llm_answer(state, llm)
        if refined and len(refined.strip()) > 40:
            answer = refined.strip()

    if intent == INTENT_ACTION:
        action = state.get("action")
        if action:
            fields = action.get("fields", {})
            answer = (
                f"I can do that. Proposed {action['kind'].replace('_', ' ')}:\n"
                f"• {fields.get('title', action.get('summary', ''))}\n"
                f"• Assignee: {fields.get('assignee', '—')}\n"
                f"• Project: {fields.get('project', '—')}\n"
                f"• Priority: {fields.get('priority', 'Medium')}\n\n"
                "Confirm to execute, or ignore to cancel."
            )
        else:
            answer = "I could not build an action for that request. Try naming a person or project."

    state["answer"] = answer
    state["sources"] = _build_sources(state, store)
    state["confidence"] = _confidence(state, state["sources"])
    state["graph_path"] = _graph_path(state, store)
    state["recommended_people"] = _recommended_people(state)
    state["decision_trace"] = _decision_trace(state)
    state.setdefault("log", []).append(
        f"answer composed: {len(state['sources'])} sources, confidence {state['confidence']}"
    )
    return state


def _recommended_people(state: BrainState) -> list[dict[str, Any]]:
    ranked = (state.get("evidence", {}) or {}).get("people_ranked", [])
    return [
        {
            "id": entry["person"]["id"],
            "name": entry["person"]["name"],
            "role": entry.get("role"),
            "team": entry.get("team"),
            "score": entry.get("score"),
            "reasons": entry.get("reasons", []),
        }
        for entry in ranked[:3]
    ]


def _decision_trace(state: BrainState) -> dict[str, Any] | None:
    traces = (state.get("evidence", {}) or {}).get("decision_traces", [])
    if not traces:
        return None
    trace = traces[0]
    return {
        "id": trace["id"],
        "title": trace.get("title"),
        "status": trace.get("status"),
        "date": trace.get("date"),
        "reason": trace.get("reason"),
        "summary": trace.get("summary"),
        "makers": [m["name"] for m in trace.get("makers", [])],
        "supporting_documents": [d["name"] for d in trace.get("supporting_documents", [])],
        "meetings": [m["name"] for m in trace.get("meetings", [])],
        "alternatives": trace.get("alternatives", []),
        "path": trace.get("path", []),
        "confidence": trace.get("confidence"),
    }


def _graph_path(state: BrainState, store: GraphStore) -> list[dict[str, Any]]:
    """Ordered, human readable explanation of the traversed graph."""

    evidence = state.get("evidence", {}) or {}
    ids: list[str] = []
    for entity in evidence.get("focus", []):
        ids.append(str(entity["id"]))
    for node_id in evidence.get("graph_node_ids", []):
        if node_id and str(node_id) not in ids:
            ids.append(str(node_id))
    ids = [i for i in ids if store.get_node(i)][:8]
    if not ids:
        return []
    steps = queries.explain_path(store, ids, depth=2)
    return steps[:14]
