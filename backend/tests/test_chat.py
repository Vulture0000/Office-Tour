"""End-to-end Company Brain chat tests against the graph."""

from __future__ import annotations


def test_person_question(client):
    body = client.post(
        "/api/chat",
        json={"message": "Who is Arun Kumar and what does he work on?"},
    ).json()
    assert body["intent"] == "PERSON_QUERY"
    assert "Arun Kumar" in body["answer"]
    assert body["confidence"] > 0.5
    assert body["sources"]


def test_decision_trace_question(client):
    body = client.post(
        "/api/chat",
        json={
            "message": "Why did we choose PostgreSQL?",
            "context": {"entity_id": "atlas", "entity_type": "Project"},
        },
    ).json()
    assert body["intent"] == "DECISION_TRACE_QUERY"
    assert "ADR-018" in body["answer"]
    assert body["decision_trace"] is not None
    assert body["graph"]["nodes"]


def test_expertise_question(client):
    body = client.post(
        "/api/query",
        json={
            "question": "Who should I talk to about the Atlas database migration?",
            "entity_id": "atlas",
            "entity_type": "Project",
        },
    ).json()
    assert body["intent"] == "EXPERTISE_QUERY"
    assert body["recommended_people"]
    assert body["recommended_people"][0]["id"] == "arun_kumar"


def test_sources_are_cited(client):
    body = client.post(
        "/api/query", json={"question": "What are the current issues with Project Atlas?"}
    ).json()
    assert body["sources"]
    assert all("title" in source and "type" in source for source in body["sources"])


def test_action_request_returns_preview(client):
    body = client.post(
        "/api/query",
        json={
            "question": "Create a task for Arun Kumar to investigate the cache eviction issue.",
            "entity_id": "atlas",
            "entity_type": "Project",
        },
    ).json()
    assert body["intent"] == "ACTION_REQUEST"
    assert body["action"] is not None
    assert body["action"]["status"] == "pending"
    assert body["action"]["kind"] == "create_ticket"
