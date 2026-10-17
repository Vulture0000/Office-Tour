"""Intent agent.

Determines what the user wants and which company entities the question refers
to. Entity extraction is graph-backed: the agent builds a catalogue of real
node names from the store, so it only ever resolves to entities that exist.

Deterministic rules run first (fast, offline, testable). When an LLM is
configured it is used only to break ties for low-confidence classifications.
"""

from __future__ import annotations

import re
from typing import Any

from ..graph import queries
from ..graph.client import GraphStore
from ..llm.provider import LLMProvider, safe_complete
from ..workflows.state import (
    CATALOGUE_LABELS,
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

PRONOUNS = {"he", "she", "him", "her", "his", "they", "them", "it", "this", "that", "its"}

#: Id fragments too generic to be meaningful aliases (``it_room`` -> "room").
GENERIC_ID_PARTS = {"room", "hall", "area", "floor", "level", "section", "wing", "desk"}

#: Office labels matched only by exact id/name (no id-fragment aliases).
OFFICE_LABELS = {"Room", "Object"}

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are",
    "was", "were", "be", "been", "it", "this", "that", "these", "those", "as", "at",
    "by", "from", "we", "our", "us", "i", "me", "my", "you", "your", "they", "their",
    "he", "she", "him", "her", "his", "what", "which", "who", "whom", "whose", "how",
    "why", "when", "where", "do", "does", "did", "can", "could", "should", "would",
    "will", "shall", "not", "no", "yes", "but", "if", "then", "than", "so", "such",
    "into", "about", "over", "under", "after", "before", "between", "there", "here",
    "know", "knows", "knowing", "should", "talk", "speak", "contact", "ask", "tell",
    "show", "give", "get", "find", "work", "works", "working", "worked", "own", "owns",
    "owner", "handle", "handles", "use", "uses", "using", "used", "run", "runs",
    "help", "need", "want", "please", "explain", "summarize", "summarise", "summar",
    "summary", "related", "issue", "issues", "problem", "problems", "current",
    "currently", "has", "have", "had", "there", "any", "more", "much", "many", "some",
    "he", "she", "they", "person", "people", "someone", "anyone", "everyone", "project",
    "projects", "team", "teams", "company", "tell", "details", "info", "information",
    "status", "depend", "depends", "involved", "responsible", "responsible", "collab",
    "collaborate", "collaborates", "collaborates", "part", "made", "make", "makes",
}

ACTION_VERB_RE = re.compile(
    r"\b(create|open|file|raise|log|add|assign|schedule|book|set(?:\s+up)?|plan|"
    r"kick\s*off|start|draft|note)\b",
    re.IGNORECASE,
)
ACTION_NOUN_RE = re.compile(
    r"\b(ticket|task|issue|meeting|follow[\s-]?up|action|todo|to[\s-]?do|reminder|"
    r"investigation|review|spike)\b",
    re.IGNORECASE,
)
EXPERTISE_RE = re.compile(
    r"\b(who\s+(?:should|can|could|do|does|would|to)\b|who\s+knows|best\s+person|"
    r"right\s+person|subject\s+matter\s+expert|expert|expertise|talk\s+to|speak\s+to|"
    r"reach\s+out|go\s+to|contact)\b",
    re.IGNORECASE,
)
WHY_RE = re.compile(r"\bwhy\b", re.IGNORECASE)
DECISION_CHOICE_RE = re.compile(
    r"\b(choose|chose|chosen|pick|picked|select|selected|decide|decided|decision|adr|"
    r"rationale|reason|migrat\w*|adopt\w*|switch\w*)\b",
    re.IGNORECASE,
)
DECISION_RE = re.compile(r"\b(decision|decisions|adr|adrs|approved|approved)\b", re.IGNORECASE)
DOCUMENT_RE = re.compile(
    r"\b(document|documents|docs|doc|design|spec|specification|policy|policies|"
    r"requirements|prd|report|reports|read|guide|guidelines|notes|runbook|adr)\b",
    re.IGNORECASE,
)
TICKET_RE = re.compile(r"\b(ticket|tickets|backlog|sprint|blocker|blockers)\b", re.IGNORECASE)
PERSON_RE = re.compile(
    r"\b(who|whom|whose|person|people|engineer|works?\s+on|owns?|collaborat\w*|"
    r"knows?|expertise|team\s+of|reports?\s+to|manager|colleague|desk)\b",
    re.IGNORECASE,
)
PROJECT_RE = re.compile(
    r"\b(project|status|progress|health|milestone|roadmap|deadline|timeline|blocker|"
    r"deliverable|scope|owns?|owner|depend\w*|using|stack)\b",
    re.IGNORECASE,
)
SYSTEM_RE = re.compile(
    r"\b(system|service|server|infrastructure|infra|cluster|database\s+server|"
    r"production|uptime|outage|downtime|deploy\w*|architecture)\b",
    re.IGNORECASE,
)

#: "listing" questions ("what are all the projects", "list teams", ...).
LIST_QUERY_RE = re.compile(
    r"\b(all|list|every|each|which|what|name|names|show|overview|many|count)\b",
    re.IGNORECASE,
)
LIST_TARGETS: dict[str, str] = {
    "project": "Project", "projects": "Project",
    "team": "Team", "teams": "Team",
    "system": "System", "systems": "System", "services": "System",
    "decision": "Decision", "decisions": "Decision", "adrs": "Decision",
    "technology": "Technology", "technologies": "Technology", "tech": "Technology",
    "document": "Document", "documents": "Document", "docs": "Document",
    "ticket": "Ticket", "tickets": "Ticket",
    "person": "Person", "people": "Person", "employee": "Person", "employees": "Person",
    "room": "Room", "rooms": "Room",
}


def detect_list_target(question: str) -> str | None:
    """Return the node label a "list everything" question is asking about."""

    if not LIST_QUERY_RE.search(question):
        return None
    for token in re.findall(r"[a-z]+", question.lower()):
        if token in LIST_TARGETS:
            return LIST_TARGETS[token]
    return None


def build_catalogue(store: GraphStore) -> list[dict[str, Any]]:
    """Build the set of resolvable entities with their aliases."""

    catalogue: list[dict[str, Any]] = []
    for label in CATALOGUE_LABELS:
        for node in store.list_nodes(label):
            name = queries.display_name(node)
            aliases = {str(node["id"]).lower(), name.lower()}
            props = node["props"]
            for extra in (props.get("key"), props.get("title")):
                if extra:
                    aliases.add(str(extra).lower())
            # Split compound ids like team_ai_platform into words, but never for
            # office Room/Object nodes: their full ids/names are descriptive and
            # fragments would collide with real business entities (atlas_doc -> "atlas").
            if label not in OFFICE_LABELS:
                aliases.update(
                    part
                    for part in str(node["id"]).lower().split("_")
                    if len(part) > 3 and part not in GENERIC_ID_PARTS
                )
            catalogue.append(
                {
                    "id": node["id"],
                    "label": label,
                    "name": name,
                    "aliases": sorted(a for a in aliases if len(a) >= 3),
                }
            )
    return catalogue


def extract_entities(
    store: GraphStore,
    question: str,
    catalogue: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Find graph entities explicitly mentioned in the question."""

    catalogue = catalogue if catalogue is not None else build_catalogue(store)
    text = " " + re.sub(r"[^a-z0-9_ ]", " ", question.lower()) + " "
    found: dict[str, dict[str, Any]] = {}
    for entry in catalogue:
        for alias in entry["aliases"]:
            if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text):
                existing = found.get(entry["id"])
                strength = len(alias)
                if not existing or strength > existing["_strength"]:
                    found[entry["id"]] = {
                        "id": entry["id"],
                        "label": entry["label"],
                        "name": entry["name"],
                        "subtitle": "",
                        "_strength": strength,
                    }
                break
    results = list(found.values())
    # Strongest alias match first (an explicit name beats a loose fragment),
    # then longer names, then label for stability.
    results.sort(
        key=lambda item: (-item.get("_strength", 0), -len(item["name"]), item["label"])
    )
    for entry in results:
        entry.pop("_strength", None)
    return results


def _has_pronoun(question: str) -> bool:
    tokens = set(re.findall(r"[a-z]+", question.lower()))
    return bool(tokens & PRONOUNS)


def resolve_context(
    store: GraphStore,
    question: str,
    context: dict[str, Any],
    entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Resolve pronouns against the entity the user is standing near."""

    if entities or context.get("entity_id") is None:
        return entities
    if not _has_pronoun(question):
        return entities
    node = store.get_node(str(context["entity_id"]))
    if not node:
        return entities
    return [
        {
            "id": node["id"],
            "label": node["label"],
            "name": queries.display_name(node),
            "subtitle": "",
            "resolved_from_context": True,
        }
    ]


#: Questions that are about the place the player is standing in.
PLACE_CONTEXT_RE = re.compile(
    r"\b(here|herein|room|location|where|around|nearby|near|stand)\b"
    r"|\bin\s+this\s+(room|place|area)\b|\bthis\s+(room|place|area)\b",
    re.IGNORECASE,
)


def _resolve_room_context(
    store: GraphStore,
    question: str,
    context: dict[str, Any],
    entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Anchor "what is in this room?" to the room the player currently occupies."""

    if entities:
        return entities
    room_key = context.get("room_id") or context.get("room")
    if not room_key or not PLACE_CONTEXT_RE.search(question):
        return entities
    node = store.get_node(str(room_key))
    if not node or node.get("label") != "Room":
        return entities
    return [
        {
            "id": node["id"],
            "label": node["label"],
            "name": queries.display_name(node),
            "subtitle": "",
            "resolved_from_context": True,
        }
    ]


def extract_terms(question: str, entities: list[dict[str, Any]]) -> list[str]:
    """Content words of the question, used for expertise ranking and search."""

    tokens = re.findall(r"[a-z0-9]+", question.lower())
    terms = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    for entity in entities:
        terms.append(entity["name"].lower())
        terms.append(str(entity["id"]).lower())
    # De-duplicate preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            unique.append(term)
    return unique


def classify_intent(
    question: str, entities: list[dict[str, Any]], context: dict[str, Any]
) -> tuple[str, float]:
    """Rule-based intent classification with a confidence estimate."""

    labels = {entity["label"] for entity in entities}
    lower = question.lower()

    if ACTION_VERB_RE.search(question) and ACTION_NOUN_RE.search(question):
        return INTENT_ACTION, 0.9
    if EXPERTISE_RE.search(question):
        return INTENT_EXPERTISE, 0.88
    # A concrete office place/object is the focus of the question when named.
    if "Room" in labels or "Object" in labels:
        return INTENT_PLACE, 0.82
    # A team is the focus when named and no person is the subject.
    if "Team" in labels and "Person" not in labels:
        return INTENT_TEAM, 0.8
    if WHY_RE.search(question) and DECISION_CHOICE_RE.search(question):
        return INTENT_DECISION, 0.9  # refined to trace when a technology is present
    if DECISION_RE.search(question) or "Decision" in labels:
        return INTENT_DECISION, 0.85
    if TICKET_RE.search(question) or "Ticket" in labels:
        return INTENT_TICKETS, 0.8
    if "System" in labels and SYSTEM_RE.search(question):
        return INTENT_SYSTEM, 0.8
    if "Person" in labels and (PERSON_RE.search(question) or len(labels) == 1):
        return INTENT_PERSON, 0.85
    if "Project" in labels and PROJECT_RE.search(question):
        return INTENT_PROJECT, 0.85
    if "Project" in labels:
        return INTENT_PROJECT, 0.7
    if "Person" in labels:
        return INTENT_PERSON, 0.7
    if DOCUMENT_RE.search(question):
        return INTENT_DOCUMENT, 0.75
    if PROJECT_RE.search(question):
        return INTENT_PROJECT, 0.6
    if PERSON_RE.search(question):
        return INTENT_PERSON, 0.6
    if "Technology" in labels:
        return INTENT_EXPERTISE, 0.6
    if context.get("entity_type") in {"npc", "item", "furniture", "Room", "Object"}:
        return INTENT_PLACE, 0.6
    if context.get("entity_type") == "Person":
        return INTENT_PERSON, 0.55
    if context.get("entity_type") == "Project":
        return INTENT_PROJECT, 0.55
    if context.get("entity_type") == "Decision":
        return INTENT_DECISION, 0.55
    if context.get("entity_type") == "Document":
        return INTENT_DOCUMENT, 0.55
    if context.get("entity_type") == "System":
        return INTENT_SYSTEM, 0.55
    if context.get("room") and "decision" in str(context.get("room")).lower():
        return INTENT_DECISION, 0.45
    if "Document" in labels:
        return INTENT_DOCUMENT, 0.6
    if "Meeting" in labels:
        return INTENT_DECISION, 0.4
    return INTENT_GENERAL, 0.4


def run(
    state: BrainState,
    store: GraphStore,
    llm: LLMProvider | None = None,
) -> BrainState:
    """LangGraph node: classify intent and extract entities."""

    question = state.get("question", "").strip()
    context = state.get("context", {}) or {}
    catalogue = build_catalogue(store)
    entities = extract_entities(store, question, catalogue)
    entities = resolve_context(store, question, context, entities)
    entities = _resolve_room_context(store, question, context, entities)
    intent, confidence = classify_intent(question, entities, context)

    # "List everything" questions ("what are all the projects") become a LIST.
    list_target = detect_list_target(question)
    if (
        list_target
        and intent not in (INTENT_ACTION, INTENT_EXPERTISE, INTENT_DECISION_WHY)
        and not any(e["label"] == list_target for e in entities)
    ):
        intent = INTENT_LIST
        confidence = max(confidence, 0.75)
        state["list_target"] = list_target

    # A "why" question about a technology is a decision trace.
    if intent == INTENT_DECISION and WHY_RE.search(question):
        if "Technology" in {e["label"] for e in entities} or _technology_hint(
            store, question
        ):
            intent = INTENT_DECISION_WHY
            confidence = 0.9

    # Low confidence with an LLM available: ask the model to pick an intent.
    if confidence < 0.5 and llm is not None and getattr(llm, "available", False):
        chosen = _llm_intent(llm, question, entities)
        if chosen:
            intent, confidence = chosen, 0.6

    state["entities"] = entities
    state["intent"] = intent
    state["intent_confidence"] = confidence
    state.setdefault("log", []).append(f"intent={intent} ({confidence:.2f})")
    return state


def _technology_hint(store: GraphStore, question: str) -> bool:
    lower = question.lower()
    for tech in store.list_nodes("Technology"):
        if queries.display_name(tech).lower() in lower:
            return True
    return False


def _llm_intent(llm: LLMProvider, question: str, entities: list[dict[str, Any]]) -> str | None:
    from ..workflows.state import ALL_INTENTS

    entity_text = ", ".join(f"{e['name']} ({e['label']})" for e in entities) or "none"
    prompt = (
        "Classify the employee's question about their company into exactly one label.\n"
        f"Labels: {', '.join(ALL_INTENTS)}\n"
        f"Detected entities: {entity_text}\n"
        f"Question: {question}\n"
        "Answer with the single label only."
    )
    text = safe_complete(llm, "You are an intent classifier.", prompt)
    if not text:
        return None
    token = text.strip().split()[0].strip(".,:;\"'").upper()
    for intent in ALL_INTENTS:
        if intent.upper() in token or intent.split("_")[0] in token:
            return intent
    return None
