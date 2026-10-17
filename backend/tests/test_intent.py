"""Intent classification and entity extraction tests."""

from __future__ import annotations

from app.agents import intent_agent
from app.workflows.state import new_state


def _classify(store, question, context=None):
    state = intent_agent.run(new_state(question, context), store, None)
    return (state["intent"], state["intent_confidence"]), state["entities"]


def test_intents(store):
    assert _classify(store, "Who is Arun Kumar?")[0][0] == "PERSON_QUERY"
    assert _classify(store, "Who owns Project Atlas?")[0][0] == "PROJECT_QUERY"
    assert _classify(store, "Who knows PostgreSQL?")[0][0] == "EXPERTISE_QUERY"
    assert _classify(store, "Why did we choose PostgreSQL?")[0][0] == "DECISION_TRACE_QUERY"
    assert (
        _classify(store, "Create a task for Arun Kumar to fix the bug")[0][0]
        == "ACTION_REQUEST"
    )


def test_entity_extraction(store):
    _, entities = _classify(store, "Who owns Project Atlas and what does Arun Kumar do?")
    ids = {e["id"] for e in entities}
    assert {"atlas", "arun_kumar"} <= ids


def test_pronoun_uses_context(store):
    catalogue = intent_agent.build_catalogue(store)
    entities = intent_agent.extract_entities(store, "What is he working on?", catalogue)
    resolved = intent_agent.resolve_context(
        store,
        "What is he working on?",
        {"entity_id": "arun_kumar", "entity_type": "Person"},
        entities,
    )
    assert any(e["id"] == "arun_kumar" for e in resolved)
