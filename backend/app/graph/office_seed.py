"""Seed the explorable office into the knowledge graph.

The office layout lives in ``data/office_layout.json`` — the single source of
truth shared with the frontend, so the walkable map and the graph always agree.

Every room becomes a ``Room`` node and every object (NPCs, items, furniture)
becomes an ``Object`` node carrying its description, so graph-aware RAG can
answer "what is this?" / "what is in this room?" about anything on the map.
"""

from __future__ import annotations

import json
from typing import Any

from ..config import get_settings
from .client import GraphStore, get_store

#: Edge types linking office entities.
OBJ_ROOM_EDGE = "FOUND_IN"   # object lives in a room
NPC_ROOM_EDGE = "IN_ROOM"    # a person stands in a room
ROOM_EDGE = "CONNECTS_TO"    # room-to-room adjacency


def _layout_path() -> Any:
    return get_settings().data_dir / "office_layout.json"


def load_layout() -> dict[str, Any]:
    path = _layout_path()
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def seed_office(store: GraphStore | None = None) -> dict[str, int]:
    """Create Room/Object nodes and their edges. Idempotent (MERGE-style)."""

    store = store or get_store()
    layout = load_layout()
    if not layout:
        return {"rooms": 0, "objects": 0, "edges": 0}

    rooms = layout.get("rooms", [])
    objects = 0
    edges = 0

    for room in rooms:
        store.create_node(
            "Room",
            {
                "id": room["id"],
                "name": room["name"],
                "type": room.get("type") or room.get("id"),
                "description": room.get("desc", ""),
            },
        )
        edges += 1
        for obj in room.get("objects", []):
            store.create_node(
                "Object",
                {
                    "id": obj["id"],
                    "name": obj["name"],
                    "type": obj.get("type", "object"),
                    "description": obj.get("info", ""),
                    "room_id": room["id"],
                    "room_name": room["name"],
                },
            )
            objects += 1
            rel = NPC_ROOM_EDGE if obj.get("type") == "npc" else OBJ_ROOM_EDGE
            store.create_edge(obj["id"], room["id"], rel)
            edges += 1

    for src, dst in layout.get("connections", []):
        store.create_edge(src, dst, ROOM_EDGE)
        store.create_edge(dst, src, ROOM_EDGE)
        edges += 2

    return {"rooms": len(rooms), "objects": objects, "edges": edges}
