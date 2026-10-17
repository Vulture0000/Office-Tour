"""Company Brain workflow.

A LangGraph state graph orchestrating five agents:

    intent -> graph -> action -> retrieval -> reasoning

* **intent** — classify the question and resolve entities.
* **graph** — gather relationship evidence from FalkorDB.
* **action** — propose a write action when the user asks for one.
* **retrieval** — hybrid graph + vector passage retrieval.
* **reasoning** — compose the grounded answer, sources and graph path.

The graph is compiled once per process. A dependency-free sequential runner is
used as a fallback if LangGraph is unavailable, so the API never breaks.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from ..agents import action_agent, graph_agent, intent_agent, reasoning_agent, retrieval_agent
from ..config import Settings, get_settings
from ..graph import queries
from ..graph.client import GraphStore, get_store
from ..llm.provider import LLMProvider, get_llm
from ..rag.retriever import VectorStore, get_vector_store
from ..services.action_store import ActionStore, get_action_store
from .state import BrainState, QueryContext, new_state

logger = logging.getLogger(__name__)


class CompanyBrain:
    """Runs the query pipeline against a fixed set of dependencies."""

    def __init__(
        self,
        store: GraphStore | None = None,
        vector_store: VectorStore | None = None,
        llm: LLMProvider | None = None,
        action_store: ActionStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.store = store or get_store(self.settings)
        self.vector_store = vector_store or get_vector_store(self.settings)
        self.llm = llm or get_llm(self.settings)
        self.action_store = action_store or get_action_store(self.settings)
        self._app = self._compile()

    # -- graph construction ------------------------------------------------
    def _compile(self) -> Any:
        try:
            from langgraph.graph import END, START, StateGraph
        except Exception as exc:  # noqa: BLE001 - optional dependency
            logger.warning("LangGraph unavailable (%s); using sequential runner", exc)
            return None

        graph = StateGraph(BrainState)
        graph.add_node("intent", self._intent_node)
        graph.add_node("graph", self._graph_node)
        graph.add_node("action", self._action_node)
        graph.add_node("retrieval", self._retrieval_node)
        graph.add_node("reasoning", self._reasoning_node)
        graph.add_edge(START, "intent")
        graph.add_edge("intent", "graph")
        graph.add_edge("graph", "action")
        graph.add_edge("action", "retrieval")
        graph.add_edge("retrieval", "reasoning")
        graph.add_edge("reasoning", END)
        try:
            return graph.compile()
        except Exception as exc:  # noqa: BLE001 - fall back to the runner
            logger.warning("LangGraph compile failed (%s); using sequential runner", exc)
            return None

    # -- nodes -------------------------------------------------------------
    def _intent_node(self, state: BrainState) -> BrainState:
        return intent_agent.run(state, self.store, self.llm)

    def _graph_node(self, state: BrainState) -> BrainState:
        return graph_agent.run(state, self.store)

    def _action_node(self, state: BrainState) -> BrainState:
        return action_agent.run(state, self.store, self.action_store)

    def _retrieval_node(self, state: BrainState) -> BrainState:
        return retrieval_agent.run(state, self.store, self.vector_store)

    def _reasoning_node(self, state: BrainState) -> BrainState:
        return reasoning_agent.run(state, self.store, self.llm)

    # -- public API --------------------------------------------------------
    def run(self, question: str, context: QueryContext | None = None) -> dict[str, Any]:
        """Run the full pipeline for a question and return a serialisable result."""

        state = new_state(question, context)
        if self._app is not None:
            final = self._app.invoke(state)
        else:
            final = self._run_sequential(state)
        return self._format(final)

    def _run_sequential(self, state: BrainState) -> BrainState:
        for node in (
            self._intent_node,
            self._graph_node,
            self._action_node,
            self._retrieval_node,
            self._reasoning_node,
        ):
            state = node(state)
        return state

    def _format(self, state: BrainState) -> dict[str, Any]:
        evidence = state.get("evidence", {}) or {}
        graph = queries.subgraph(
            self.store,
            [i for i in evidence.get("graph_node_ids", []) if self.store.get_node(i)][:10],
            depth=2,
        )
        return {
            "answer": state.get("answer", ""),
            "intent": state.get("intent"),
            "intent_confidence": state.get("intent_confidence", 0.0),
            "entities": state.get("entities", []),
            "confidence": state.get("confidence", 0.0),
            "sources": state.get("sources", []),
            "graph_path": state.get("graph_path", []),
            "graph": graph,
            "relationships": graph.get("edges", []),
            "recommended_people": state.get("recommended_people", []),
            "decision_trace": state.get("decision_trace"),
            "action": state.get("action"),
            "focus": evidence.get("focus", []),
            "log": state.get("log", []),
        }


_brain: CompanyBrain | None = None
_brain_lock = threading.Lock()


def get_brain(settings: Settings | None = None, force: bool = False) -> CompanyBrain:
    """Return the process-wide Company Brain singleton."""

    global _brain
    settings = settings or get_settings()
    with _brain_lock:
        if _brain is None or force:
            _brain = CompanyBrain(settings=settings)
        return _brain


def set_brain(brain: CompanyBrain | None) -> None:
    """Override the singleton (used by tests)."""

    global _brain
    with _brain_lock:
        _brain = brain


def run_query(
    question: str, context: QueryContext | None = None, settings: Settings | None = None
) -> dict[str, Any]:
    """Convenience wrapper used by the API layer."""

    return get_brain(settings).run(question, context)
