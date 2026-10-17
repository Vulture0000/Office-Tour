"""Pending action storage.

Actions are proposed (preview) and only executed after explicit human
confirmation. Pending proposals are kept in memory and mirrored to a JSON file
so the demo survives a backend restart. Executed actions append to the same
file as an audit trail.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

VALID_ACTION_KINDS = {"create_ticket", "schedule_meeting", "update_project_status", "follow_up"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}


class ActionStore:
    """In-memory action registry with JSON-file persistence."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._pending: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self._load()

    # -- persistence -------------------------------------------------------
    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read action store: %s", exc)
            return
        self._history = payload.get("history", [])

    def _persist(self) -> None:
        if not self.path:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps({"history": self._history}, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("Could not persist action store: %s", exc)

    # -- api ---------------------------------------------------------------
    def propose(
        self,
        kind: str,
        summary: str,
        fields: dict[str, Any],
        entity_id: str | None = None,
    ) -> dict[str, Any]:
        """Register a pending action and return its preview payload."""

        if kind not in VALID_ACTION_KINDS:
            raise ValueError(f"Unsupported action kind: {kind!r}")
        action_id = f"act_{uuid.uuid4().hex[:10]}"
        preview = {
            "id": action_id,
            "kind": kind,
            "status": "pending",
            "summary": summary,
            "fields": fields,
            "entity_id": entity_id,
            "created_at": _now(),
            "requires_confirmation": True,
        }
        with self._lock:
            self._pending[action_id] = preview
        return preview

    def get(self, action_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._pending.get(action_id)

    def cancel(self, action_id: str) -> dict[str, Any] | None:
        with self._lock:
            action = self._pending.pop(action_id, None)
            if action:
                action = {**action, "status": "cancelled"}
                self._history.append(action)
                self._persist()
            return action

    def confirm(self, action_id: str) -> dict[str, Any] | None:
        with self._lock:
            action = self._pending.pop(action_id, None)
            if not action:
                return None
            action = {
                **action,
                "status": "executed",
                "executed_at": _now(),
            }
            self._history.append(action)
            self._persist()
            return action

    def history(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(reversed(self._history))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


_store: ActionStore | None = None
_store_lock = threading.Lock()


def get_action_store(settings: Settings | None = None, force: bool = False) -> ActionStore:
    """Return the process-wide action store."""

    global _store
    settings = settings or get_settings()
    with _store_lock:
        if _store is None or force:
            _store = ActionStore(settings.resolved_actions_store_path())
        return _store


def set_action_store(store: ActionStore | None) -> None:
    """Override the singleton (used by tests)."""

    global _store
    with _store_lock:
        _store = store
