"""Pydantic request/response models for the REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryContext(BaseModel):
    """Context describing where in the 2D world the question was asked."""

    entity_id: str | None = None
    entity_type: str | None = None
    room: str | None = None
    room_id: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    context: QueryContext | None = None
    session_id: str | None = Field(default=None, max_length=64)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    entity_id: str | None = None
    entity_type: str | None = None
    room: str | None = None


class SourceModel(BaseModel):
    id: str | None = None
    type: str
    title: str
    doc_type: str | None = None
    author: str | None = None
    date: str | None = None
    excerpt: str | None = None
    heading: str | None = None
    relevance: float | None = None


class GraphNodeModel(BaseModel):
    id: str
    label: str
    name: str
    subtitle: str | None = ""
    props: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeModel(BaseModel):
    id: str | None = None
    source: str
    target: str
    rel: str


class GraphModel(BaseModel):
    nodes: list[GraphNodeModel] = Field(default_factory=list)
    edges: list[GraphEdgeModel] = Field(default_factory=list)


class RecommendedPerson(BaseModel):
    id: str
    name: str
    role: str | None = None
    team: str | None = None
    score: float | None = None
    reasons: list[str] = Field(default_factory=list)


class ActionFields(BaseModel):
    title: str | None = None
    assignee: str | None = None
    assignee_id: str | None = None
    project: str | None = None
    project_id: str | None = None
    priority: str | None = None
    description: str | None = None
    ticket_id: str | None = None
    attendees: list[str] | None = None
    new_status: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ActionPreview(BaseModel):
    id: str
    kind: str
    status: str
    summary: str
    fields: dict[str, Any] = Field(default_factory=dict)
    entity_id: str | None = None
    created_at: str | None = None
    requires_confirmation: bool = True


class ChatResponse(BaseModel):
    answer: str
    intent: str | None = None
    intent_confidence: float = 0.0
    confidence: float = 0.0
    entities: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[SourceModel] = Field(default_factory=list)
    graph_path: list[dict[str, Any]] = Field(default_factory=list)
    graph: GraphModel = Field(default_factory=GraphModel)
    relationships: list[GraphEdgeModel] = Field(default_factory=list)
    recommended_people: list[RecommendedPerson] = Field(default_factory=list)
    decision_trace: dict[str, Any] | None = None
    action: ActionPreview | None = None
    focus: list[dict[str, Any]] = Field(default_factory=list)
    log: list[str] = Field(default_factory=list)


class ActionConfirmRequest(BaseModel):
    action_id: str = Field(..., min_length=1, max_length=64)


class ActionConfirmResponse(BaseModel):
    status: str
    action: dict[str, Any] | None = None
    result: dict[str, Any] | None = None


class SearchResult(BaseModel):
    id: str
    label: str
    name: str
    subtitle: str | None = ""
    score: float | None = None
    snippet: str | None = None


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    graph_backend: str
    graph_healthy: bool
    llm_provider: str
    llm_available: bool
    embedding_provider: str
    stats: dict[str, Any] = Field(default_factory=dict)


class CompanyOverview(BaseModel):
    company: dict[str, Any] = Field(default_factory=dict)
    stats: dict[str, Any] = Field(default_factory=dict)
    teams: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    technologies: list[dict[str, Any]] = Field(default_factory=list)
    systems: list[dict[str, Any]] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)


class WorldInteractiveObject(BaseModel):
    id: str
    label: str
    name: str
    subtitle: str | None = ""
    prompt: str
    room: str | None = None
    root: bool = False


class WorldResponse(BaseModel):
    objects: list[WorldInteractiveObject] = Field(default_factory=list)
    demo_questions: list[str] = Field(default_factory=list)


class DemoResetResponse(BaseModel):
    status: str
    message: str
    stats: dict[str, Any] = Field(default_factory=dict)
