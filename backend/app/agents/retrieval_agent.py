"""Knowledge retrieval agent.

Graph-first hybrid retrieval: the graph supplies candidate documents (those
connected to the entities in the question), and the vector store ranks passages
*inside* that candidate set. When the graph yields nothing, retrieval falls
back to a full-corpus search so general questions still work.
"""

from __future__ import annotations

from typing import Any

from ..graph import queries
from ..graph.client import GraphStore
from ..rag.retriever import VectorStore
from ..workflows.state import INTENT_ACTION, INTENT_PLACE, BrainState

#: Intents that rarely benefit from document passages.
LOW_DOCUMENT_INTENTS = {INTENT_ACTION, INTENT_PLACE}

EXCERPT_LENGTH = 320


def _enriched_query(state: BrainState) -> str:
    """Question plus entity names, so vector search is anchored to the entities."""

    question = state.get("question", "")
    names = [e["name"] for e in state.get("entities", [])[:3]]
    if names:
        return f"{question} {' '.join(names)}"
    return question


def _linked_documents(evidence: dict[str, Any], store: GraphStore) -> list[str]:
    """Document ids connected to the focus entities via the graph."""

    linked: list[str] = [str(d) for d in evidence.get("related_document_ids", [])]

    # Pull in decision supporting docs and project docs when present.
    for trace in evidence.get("decision_traces", []) or []:
        for doc in trace.get("supporting_documents", []):
            linked.append(str(doc["id"]))
    for doc in evidence.get("documents", []):
        linked.append(str(doc["id"]))

    # Deduplicate preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for doc_id in linked:
        if doc_id and doc_id not in seen and store.get_node(doc_id):
            seen.add(doc_id)
            unique.append(doc_id)
    return unique


def run(
    state: BrainState,
    store: GraphStore,
    vector_store: VectorStore,
) -> BrainState:
    """LangGraph node: retrieve supporting passages for the answer."""

    evidence = state.get("evidence", {}) or {}
    intent = state.get("intent", "")

    if intent in LOW_DOCUMENT_INTENTS:
        state["documents"] = []
        state.setdefault("log", []).append("retrieval skipped for action intent")
        return state

    query = _enriched_query(state)
    linked = _linked_documents(evidence, store)

    results: list[dict[str, Any]] = []
    if linked:
        results = vector_store.search(query, k=6, document_ids=linked)

    # Hybrid fallback: graph candidates gave nothing useful, search the corpus.
    if len(results) < 2:
        fallback = vector_store.search(query, k=6)
        seen = {r["chunk_id"] for r in results}
        for item in fallback:
            if item["chunk_id"] not in seen:
                results.append(item)
                seen.add(item["chunk_id"])
        results.sort(key=lambda item: item["score"], reverse=True)

    for item in results:
        item["excerpt"] = _excerpt(item.get("text", ""), query)

    state["documents"] = results[:6]
    state.setdefault("log", []).append(
        f"retrieval: {len(linked)} graph-linked docs, {len(results)} passages"
    )
    return state


def _excerpt(text: str, query: str, length: int = EXCERPT_LENGTH) -> str:
    """Return the most relevant sentence window of a passage."""

    if not text:
        return ""
    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    if not sentences:
        return text[:length]
    terms = [t for t in query.lower().split() if len(t) > 3]

    def score(sentence: str) -> int:
        lower = sentence.lower()
        return sum(lower.count(term) for term in terms)

    best = max(sentences, key=score) if terms else sentences[0]
    if len(best) > length:
        return best[: length - 1].rstrip() + "…"
    return best
