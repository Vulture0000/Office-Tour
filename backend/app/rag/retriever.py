"""Hybrid retrieval.

The graph supplies the candidate set (documents connected to the entities in
the question); the vector store ranks passages inside that set. If the graph
gives no candidates, retrieval falls back to a full-corpus vector search so the
system still answers general questions.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Iterable

from ..config import Settings, get_settings
from .chunker import Chunk, chunk_documents
from .embeddings import Embedder, get_embedder
from .loader import CompanyDocument, load_documents

logger = logging.getLogger(__name__)


class VectorStore:
    """Brute-force cosine vector store persisted as JSON.

    The corpus is small (tens of documents), so an in-process store is both
    simpler and faster than a separate service, and keeps the deployment story
    to a single container.
    """

    def __init__(self, embedder: Embedder | None = None) -> None:
        self.embedder = embedder or get_embedder()
        self.chunks: list[Chunk] = []
        self.vectors: list[list[float]] = []
        self.documents: dict[str, CompanyDocument] = {}

    # -- construction ------------------------------------------------------
    def build(self, documents: list[CompanyDocument]) -> None:
        self.documents = {doc.id: doc for doc in documents}
        self.chunks = chunk_documents(documents)
        texts = [self._embed_text(chunk) for chunk in self.chunks]
        self.vectors = self.embedder.embed(texts) if texts else []

    def _embed_text(self, chunk: Chunk) -> str:
        document = self.documents.get(chunk.document_id)
        prefix = ""
        if document:
            prefix = f"{document.title}. {document.type}. "
        return f"{prefix}{chunk.heading}. {chunk.text}"

    # -- persistence -------------------------------------------------------
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "embedder": self.embedder.name,
            "documents": {doc_id: doc.as_node_props() for doc_id, doc in self.documents.items()},
            "chunks": [
                {**chunk.as_dict(), "vector": [round(v, 5) for v in vector]}
                for chunk, vector in zip(self.chunks, self.vectors)
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def load(self, path: Path) -> bool:
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read vector store at %s: %s", path, exc)
            return False
        if payload.get("embedder") != self.embedder.name:
            logger.info("Vector store embedder mismatch; rebuilding")
            return False
        self.chunks = [
            Chunk(
                id=item["id"],
                document_id=item["document_id"],
                text=item["text"],
                index=item["index"],
                heading=item.get("heading", ""),
            )
            for item in payload.get("chunks", [])
        ]
        self.vectors = [item.get("vector", []) for item in payload.get("chunks", [])]
        self.documents = {
            doc_id: _document_from_props(props)
            for doc_id, props in payload.get("documents", {}).items()
        }
        return bool(self.chunks)

    # -- search ------------------------------------------------------------
    def search(
        self,
        query: str,
        k: int = 5,
        document_ids: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        if not self.chunks:
            return []
        allowed = {str(d) for d in document_ids} if document_ids else None
        query_vector = self.embedder.embed([query])[0]
        scored: list[tuple[float, int]] = []
        for index, vector in enumerate(self.vectors):
            if allowed is not None and self.chunks[index].document_id not in allowed:
                continue
            scored.append((_cosine(query_vector, vector), index))
        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, index in scored[:k]:
            if score <= 0:
                continue
            chunk = self.chunks[index]
            document = self.documents.get(chunk.document_id)
            results.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "document_title": document.title if document else chunk.document_id,
                    "type": document.type if document else "Document",
                    "author_id": document.author_id if document else "",
                    "heading": chunk.heading,
                    "text": chunk.text,
                    "score": round(score, 4),
                }
            )
        return results


def _document_from_props(props: dict[str, Any]) -> CompanyDocument:
    return CompanyDocument(
        id=props.get("id", ""),
        title=props.get("title", ""),
        type=props.get("type", "Document"),
        author_id=props.get("author_id", ""),
        created_at=props.get("created_at", ""),
        updated_at=props.get("updated_at", ""),
        project_id=props.get("project_id", ""),
        team_id=props.get("team_id", ""),
        source_path=props.get("source_path", ""),
        content=props.get("content", ""),
        body=props.get("content", ""),
    )


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


_store: VectorStore | None = None


def get_vector_store(settings: Settings | None = None, force: bool = False) -> VectorStore:
    """Return the process-wide vector store, loading or building as needed."""

    global _store
    settings = settings or get_settings()
    if _store is not None and not force:
        return _store
    store = VectorStore()
    path = settings.resolved_vector_store_path()
    if not force and store.load(path):
        _store = store
        return store
    store.build(load_documents())
    try:
        store.save(path)
    except OSError as exc:
        logger.warning("Could not persist vector store: %s", exc)
    _store = store
    return store


def set_vector_store(store: VectorStore | None) -> None:
    """Override the singleton (used by tests)."""

    global _store
    _store = store
