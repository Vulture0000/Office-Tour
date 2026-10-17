"""Shared workflow state and intent vocabulary.

The state is a plain dictionary that flows between LangGraph nodes. Each agent
reads the fields it needs and writes its own outputs, so nodes remain small and
independently testable.
"""

from __future__ import annotations

from typing import Any, TypedDict


class QueryContext(TypedDict, total=False):
    """Where the question came from in the 2D world."""

    entity_id: str
    entity_type: str
    room: str
    room_id: str
    history: list[dict[str, str]]


class EvidenceEntity(TypedDict, total=False):
    id: str
    label: str
    name: str
    subtitle: str


class Source(TypedDict, total=False):
    id: str
    type: str
    title: str
    author: str
    date: str
    excerpt: str
    relevance: float
    snippet: str


class BrainState(TypedDict, total=False):
    """The Company Brain workflow state."""

    question: str
    context: QueryContext
    intent: str
    intent_confidence: float
    entities: list[dict[str, Any]]
    evidence: dict[str, Any]
    documents: list[dict[str, Any]]
    answer: str
    sources: list[Source]
    confidence: float
    graph_path: list[dict[str, Any]]
    graph: dict[str, Any]
    recommended_people: list[dict[str, Any]]
    decision_trace: dict[str, Any] | None
    action: dict[str, Any] | None
    log: list[str]


# Intent vocabulary -------------------------------------------------------
INTENT_PERSON = "PERSON_QUERY"
INTENT_PROJECT = "PROJECT_QUERY"
INTENT_DOCUMENT = "DOCUMENT_QUERY"
INTENT_DECISION = "DECISION_QUERY"
INTENT_DECISION_WHY = "DECISION_TRACE_QUERY"
INTENT_EXPERTISE = "EXPERTISE_QUERY"
INTENT_TICKETS = "TICKET_QUERY"
INTENT_SYSTEM = "SYSTEM_QUERY"
INTENT_ACTION = "ACTION_REQUEST"
INTENT_GENERAL = "GENERAL_COMPANY_QUERY"

ALL_INTENTS = [
    INTENT_PERSON,
    INTENT_PROJECT,
    INTENT_DOCUMENT,
    INTENT_DECISION,
    INTENT_DECISION_WHY,
    INTENT_EXPERTISE,
    INTENT_TICKETS,
    INTENT_SYSTEM,
    INTENT_ACTION,
    INTENT_GENERAL,
]

#: The labels the intent agent builds its entity catalogue from.
CATALOGUE_LABELS = [
    "Person",
    "Project",
    "Technology",
    "Team",
    "Decision",
    "Document",
    "Meeting",
    "System",
    "Skill",
    "Department",
]


def new_state(question: str, context: QueryContext | None = None) -> BrainState:
    """Create a fresh workflow state."""

    return {
        "question": question,
        "context": context or {},
        "entities": [],
        "log": [],
    }
