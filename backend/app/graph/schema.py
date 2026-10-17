"""Graph schema definition for the NovaTech company knowledge graph.

The schema module is the single source of truth for node labels, relationship
types and the whitelist used to sanitise any identifier that ends up inside a
Cypher statement. Labels and relationship types cannot be parameterised in
Cypher, so they are validated against these sets before interpolation.
"""

from __future__ import annotations

from dataclasses import dataclass

LABELS: frozenset[str] = frozenset(
    {
        "Person",
        "Team",
        "Project",
        "Document",
        "Decision",
        "Ticket",
        "Meeting",
        "Technology",
        "System",
        "Skill",
        "Department",
        "Company",
    }
)

RELATIONSHIPS: frozenset[str] = frozenset(
    {
        "MEMBER_OF",
        "OWNS",
        "WORKS_ON",
        "KNOWS",
        "EXPERT_IN",
        "HAS_SKILL",
        "AUTHORED",
        "PARTICIPATED_IN",
        "HAS_DOCUMENT",
        "HAS_TICKET",
        "HAS_DECISION",
        "USES",
        "MADE_BY",
        "ABOUT",
        "SUPPORTED_BY",
        "DISCUSSED_IN",
        "RELATED_TO",
        "REFERENCES",
        "PART_OF",
        "REPORTS_IN",
        "ASSIGNED_TO",
        "REPORTED_BY",
        "RESPONSIBLE_FOR",
        "ATTENDED",
    }
)

#: Human readable labels for API/UI consumption.
LABEL_DISPLAY: dict[str, str] = {
    "Person": "Person",
    "Team": "Team",
    "Project": "Project",
    "Document": "Document",
    "Decision": "Decision",
    "Ticket": "Ticket",
    "Meeting": "Meeting",
    "Technology": "Technology",
    "System": "System",
    "Skill": "Skill",
    "Department": "Department",
    "Company": "Company",
}

#: Which property carries the display name for each label.
NAME_PROPERTY: dict[str, str] = {
    "Person": "name",
    "Team": "name",
    "Project": "name",
    "Document": "title",
    "Decision": "title",
    "Ticket": "title",
    "Meeting": "title",
    "Technology": "name",
    "System": "name",
    "Skill": "name",
    "Department": "name",
    "Company": "name",
}

DISPLAY_NAME = "name"


@dataclass(frozen=True)
class GraphStats:
    """Simple counters describing the loaded graph."""

    nodes: int
    edges: int
    nodes_by_label: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "nodes_by_label": self.nodes_by_label,
        }


def validate_label(label: str) -> str:
    """Return ``label`` if it is part of the schema, else raise ``ValueError``."""

    if label not in LABELS:
        raise ValueError(f"Unknown node label: {label!r}")
    return label


def validate_relationship(rel: str) -> str:
    """Return ``rel`` if it is part of the schema, else raise ``ValueError``."""

    if rel not in RELATIONSHIPS:
        raise ValueError(f"Unknown relationship type: {rel!r}")
    return rel


def index_statements() -> list[str]:
    """Cypher statements creating an index on ``id`` for every label."""

    return [f"CREATE INDEX FOR (n:{label}) ON (n.id)" for label in sorted(LABELS)]


def name_index_statements() -> list[str]:
    """Cypher statements indexing the display-name property where it exists."""

    return [
        f"CREATE INDEX FOR (n:{label}) ON (n.{prop})"
        for label, prop in sorted(NAME_PROPERTY.items())
        if prop != "id"
    ]
