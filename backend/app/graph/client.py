"""Graph store abstraction.

FalkorDB is the primary store: :class:`FalkorStore` runs real parameterised
Cypher against FalkorDB. :class:`MemoryStore` is an in-process fallback with the
same *operation* surface, used for tests and for offline demos when no FalkorDB
instance is reachable. It is not a general Cypher engine - it implements only
the operations this application uses, so the application logic stays identical
whichever backend is active.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from typing import Any, Iterable, Protocol

from ..config import Settings, get_settings
from . import schema

logger = logging.getLogger(__name__)

MAX_EXPAND_DEPTH = 3


class GraphUnavailable(RuntimeError):
    """Raised when the configured graph backend cannot serve a request."""


class GraphStore(Protocol):
    """Minimal operation surface used by the application."""

    backend: str

    def clear(self) -> None: ...
    def ensure_schema(self) -> None: ...
    def create_node(self, label: str, props: dict[str, Any]) -> None: ...
    def create_edge(self, src_id: str, dst_id: str, rel: str) -> None: ...
    def get_node(self, node_id: str) -> dict[str, Any] | None: ...
    def list_nodes(self, label: str) -> list[dict[str, Any]]: ...
    def expand(
        self, node_id: str, rels: Iterable[str] | None = None, depth: int = 1
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]: ...
    def search_nodes(
        self, text: str, labels: Iterable[str] | None = None
    ) -> list[dict[str, Any]]: ...
    def stats(self) -> schema.GraphStats: ...
    def healthy(self) -> bool: ...


def _node(label: str, props: dict[str, Any]) -> dict[str, Any]:
    return {"id": props.get("id"), "label": label, "props": props}


class FalkorStore:
    """FalkorDB backed graph store executing parameterised Cypher."""

    backend = "falkor"

    def __init__(self, settings: Settings) -> None:
        from falkordb import FalkorDB  # imported lazily so tests avoid the dep

        kwargs: dict[str, Any] = {
            "host": settings.falkordb_host,
            "port": settings.falkordb_port,
        }
        if settings.falkordb_username:
            kwargs["username"] = settings.falkordb_username
        if settings.falkordb_password:
            kwargs["password"] = settings.falkordb_password
        self._client = FalkorDB(**kwargs)
        self._graph = self._client.select_graph(settings.falkordb_graph)

    # -- low level helpers -------------------------------------------------
    def _query(self, cypher: str, params: dict[str, Any] | None = None) -> list[list[Any]]:
        try:
            result = self._graph.query(cypher, params or {})
        except Exception as exc:  # noqa: BLE001 - surface as a domain error
            raise GraphUnavailable(str(exc)) from exc
        return list(result.result_set)

    def _rows_to_nodes(self, rows: list[list[Any]]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for row in rows:
            node_id, labels, props = row[0], row[1], row[2]
            label = labels[0] if labels else "Unknown"
            props = dict(props or {})
            props.setdefault("id", node_id)
            nodes.append({"id": node_id, "label": label, "props": props})
        return nodes

    # -- operations --------------------------------------------------------
    def clear(self) -> None:
        self._query("MATCH (n) DETACH DELETE n")

    def ensure_schema(self) -> None:
        statements = schema.index_statements() + schema.name_index_statements()
        for statement in statements:
            try:
                self._graph.query(statement)
            except Exception as exc:  # noqa: BLE001 - index may already exist
                logger.debug("Index statement skipped: %s (%s)", statement, exc)

    def create_node(self, label: str, props: dict[str, Any]) -> None:
        label = schema.validate_label(label)
        node_id = props.get("id")
        if not node_id:
            raise ValueError("Nodes require an 'id' property")
        self._query(
            f"MERGE (n:{label} {{id: $id}}) SET n += $props",
            {"id": node_id, "props": props},
        )

    def create_edge(self, src_id: str, dst_id: str, rel: str) -> None:
        rel = schema.validate_relationship(rel)
        self._query(
            f"MATCH (a {{id: $src}}), (b {{id: $dst}}) "
            f"MERGE (a)-[:{rel}]->(b)",
            {"src": src_id, "dst": dst_id},
        )

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        rows = self._query(
            "MATCH (n {id: $id}) RETURN n.id AS id, labels(n) AS labels, properties(n) AS props",
            {"id": node_id},
        )
        nodes = self._rows_to_nodes(rows)
        return nodes[0] if nodes else None

    def list_nodes(self, label: str) -> list[dict[str, Any]]:
        label = schema.validate_label(label)
        rows = self._query(
            f"MATCH (n:{label}) RETURN n.id AS id, labels(n) AS labels, properties(n) AS props"
        )
        return self._rows_to_nodes(rows)

    def expand(
        self, node_id: str, rels: Iterable[str] | None = None, depth: int = 1
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        depth = max(1, min(int(depth), MAX_EXPAND_DEPTH))
        rels = [schema.validate_relationship(r) for r in (rels or [])]
        params = {"id": node_id, "rels": rels}
        node_rows = self._query(
            f"MATCH p = (a {{id: $id}})-[*1..{depth}]-(b) "
            "WHERE ALL(r IN relationships(p) WHERE $rels = [] OR type(r) IN $rels) "
            "WITH DISTINCT b RETURN DISTINCT b.id AS id, labels(b) AS labels, "
            "properties(b) AS props",
            params,
        )
        edge_rows = self._query(
            f"MATCH p = (a {{id: $id}})-[*1..{depth}]-(b) "
            "WHERE ALL(r IN relationships(p) WHERE $rels = [] OR type(r) IN $rels) "
            "UNWIND relationships(p) AS r "
            "WITH DISTINCT startNode(r).id AS s, type(r) AS rel, endNode(r).id AS e "
            "RETURN s, rel, e",
            params,
        )
        nodes = self._rows_to_nodes(node_rows)
        start = self.get_node(node_id)
        if start:
            nodes = [start] + [n for n in nodes if n["id"] != node_id]
        edges = [{"source": row[0], "rel": row[1], "target": row[2]} for row in edge_rows]
        return nodes, edges

    def search_nodes(
        self, text: str, labels: Iterable[str] | None = None
    ) -> list[dict[str, Any]]:
        labels = [schema.validate_label(l) for l in (labels or [])]
        needle = (text or "").strip().lower()
        if not needle:
            return []
        where_label = (
            "WHERE any(l IN labels(n) WHERE l IN $labels) " if labels else ""
        )
        rows = self._query(
            "MATCH (n) "
            + where_label
            + ("AND " if labels else "WHERE ")
            + "("
            "toLower(coalesce(n.name, '')) CONTAINS $text OR "
            "toLower(coalesce(n.title, '')) CONTAINS $text OR "
            "toLower(coalesce(n.description, '')) CONTAINS $text OR "
            "toLower(coalesce(n.summary, '')) CONTAINS $text"
            ") RETURN n.id AS id, labels(n) AS labels, properties(n) AS props "
            "LIMIT 50",
            {"text": needle, "labels": labels},
        )
        return self._rows_to_nodes(rows)

    def stats(self) -> schema.GraphStats:
        node_rows = self._query("MATCH (n) RETURN labels(n) AS labels")
        labels = [row[0][0] if row[0] else "Unknown" for row in node_rows]
        counts: dict[str, int] = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        edge_rows = self._query("MATCH ()-[r]->() RETURN count(r)")
        edges = int(edge_rows[0][0]) if edge_rows else 0
        return schema.GraphStats(nodes=len(labels), edges=edges, nodes_by_label=counts)

    def healthy(self) -> bool:
        try:
            self._query("RETURN 1")
            return True
        except GraphUnavailable:
            return False


class MemoryStore:
    """In-process fallback implementing the same operation surface.

    Used by the test suite and when FalkorDB is unreachable so the demo still
    answers from real graph traversals of the seeded data.
    """

    backend = "memory"

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[tuple[str, str, str]] = []
        self._lock = threading.RLock()

    def clear(self) -> None:
        with self._lock:
            self._nodes.clear()
            self._edges.clear()

    def ensure_schema(self) -> None:  # nothing to do in memory
        return None

    def create_node(self, label: str, props: dict[str, Any]) -> None:
        label = schema.validate_label(label)
        node_id = props.get("id")
        if not node_id:
            raise ValueError("Nodes require an 'id' property")
        with self._lock:
            existing = self._nodes.get(node_id)
            merged = dict(existing["props"]) if existing else {}
            merged.update(props)
            self._nodes[node_id] = {"id": node_id, "label": label, "props": merged}

    def create_edge(self, src_id: str, dst_id: str, rel: str) -> None:
        rel = schema.validate_relationship(rel)
        with self._lock:
            if src_id not in self._nodes or dst_id not in self._nodes:
                return
            edge = (src_id, rel, dst_id)
            if edge not in self._edges:
                self._edges.append(edge)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        with self._lock:
            node = self._nodes.get(node_id)
            return _copy(node) if node else None

    def list_nodes(self, label: str) -> list[dict[str, Any]]:
        label = schema.validate_label(label)
        with self._lock:
            return [_copy(n) for n in self._nodes.values() if n["label"] == label]

    def _neighbours(self, node_id: str, rels: set[str], reverse: bool) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for src, rel, dst in self._edges:
            if rels and rel not in rels:
                continue
            if not reverse and src == node_id:
                out.append((dst, rel))
            elif reverse and dst == node_id:
                out.append((src, rel))
        return out

    def expand(
        self, node_id: str, rels: Iterable[str] | None = None, depth: int = 1
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        depth = max(1, min(int(depth), MAX_EXPAND_DEPTH))
        rel_filter = {schema.validate_relationship(r) for r in (rels or [])}
        with self._lock:
            if node_id not in self._nodes:
                return [], []
            visited: set[str] = {node_id}
            collected_edges: set[tuple[str, str, str]] = set()
            queue: deque[tuple[str, int]] = deque([(node_id, 0)])
            while queue:
                current, level = queue.popleft()
                if level >= depth:
                    continue
                for neighbour, rel in self._neighbours(
                    current, rel_filter, reverse=False
                ) + self._neighbours(current, rel_filter, reverse=True):
                    collected_edges.add((current, rel, neighbour))
                    if neighbour not in visited:
                        visited.add(neighbour)
                        queue.append((neighbour, level + 1))
            nodes = [_copy(self._nodes[n]) for n in visited if n in self._nodes]
            edges = [{"source": s, "rel": r, "target": t} for s, r, t in collected_edges]
            return nodes, edges

    def search_nodes(
        self, text: str, labels: Iterable[str] | None = None
    ) -> list[dict[str, Any]]:
        label_filter = {schema.validate_label(l) for l in (labels or [])}
        needle = (text or "").strip().lower()
        if not needle:
            return []
        fields = ("name", "title", "description", "summary")
        out: list[dict[str, Any]] = []
        with self._lock:
            for node in self._nodes.values():
                if label_filter and node["label"] not in label_filter:
                    continue
                haystack = " ".join(
                    str(node["props"].get(f, "")) for f in fields
                ).lower()
                if needle in haystack:
                    out.append(_copy(node))
        return out[:50]

    def stats(self) -> schema.GraphStats:
        with self._lock:
            counts: dict[str, int] = {}
            for node in self._nodes.values():
                counts[node["label"]] = counts.get(node["label"], 0) + 1
            return schema.GraphStats(
                nodes=len(self._nodes), edges=len(self._edges), nodes_by_label=counts
            )

    def healthy(self) -> bool:
        return True


def _copy(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node["id"],
        "label": node["label"],
        "props": dict(node["props"]),
    }


_store: GraphStore | None = None
_store_lock = threading.Lock()


def build_store(settings: Settings) -> tuple[GraphStore, str | None]:
    """Build a store according to ``GRAPH_BACKEND``.

    Returns the store and an optional note explaining a fallback.
    """

    backend = settings.graph_backend
    if backend == "memory":
        return MemoryStore(), "GRAPH_BACKEND=memory: using in-process graph store"
    if backend in {"falkor", "auto"}:
        try:
            store = FalkorStore(settings)
            if store.healthy():
                return store, None
            note = (
                "FalkorDB health check failed for "
                f"{settings.falkordb_host}:{settings.falkordb_port}"
            )
        except Exception as exc:  # noqa: BLE001 - fall back below
            note = f"FalkorDB unavailable ({exc})"
        if backend == "falkor":
            raise GraphUnavailable(note)
        logger.warning("%s - falling back to in-process graph store", note)
        return MemoryStore(), note + ": using in-process graph store"
    raise ValueError(f"Unsupported GRAPH_BACKEND: {backend!r}")


def get_store(settings: Settings | None = None, force: bool = False) -> GraphStore:
    """Return the process-wide graph store singleton."""

    global _store
    settings = settings or get_settings()
    with _store_lock:
        if _store is None or force:
            store, note = build_store(settings)
            if note:
                logger.info(note)
            _store = store
        return _store


def set_store(store: GraphStore) -> None:
    """Override the singleton (used by tests)."""

    global _store
    with _store_lock:
        _store = store
