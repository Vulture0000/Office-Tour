"""Confirm-before-execute action workflow tests."""

from __future__ import annotations


def _propose(client, question: str = "Create a task for Arun Kumar to fix the atlas latency."):
    body = client.post(
        "/api/query",
        json={"question": question, "entity_id": "atlas", "entity_type": "Project"},
    ).json()
    assert body["action"], "expected an action preview"
    return body["action"]


def test_confirm_executes_action(client):
    action = _propose(client)
    assert client.get(f"/api/actions/{action['id']}").status_code == 200

    response = client.post("/api/actions/confirm", json={"action_id": action["id"]})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "executed"
    assert body["result"]["kind"] == "create_ticket"
    assert body["result"]["status"] == "created"

    ticket_id = body["result"]["ticket"]["id"]
    assert client.get(f"/api/tickets/{ticket_id}").status_code == 200

    # Confirming twice is rejected.
    assert client.post("/api/actions/confirm", json={"action_id": action["id"]}).status_code == 404


def test_cancel_discards_action(client):
    action = _propose(client, "Create a task to review the reporting aggregates.")
    response = client.post("/api/actions/cancel", json={"action_id": action["id"]})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    # Cancelled actions can no longer be confirmed.
    assert client.post("/api/actions/confirm", json={"action_id": action["id"]}).status_code == 404


def test_history_records_actions(client):
    history = client.get("/api/actions").json()
    assert isinstance(history, list)
    assert any(item["kind"] == "create_ticket" for item in history)


def test_unknown_action_returns_404(client):
    assert client.post("/api/actions/confirm", json={"action_id": "act_nope"}).status_code == 404
