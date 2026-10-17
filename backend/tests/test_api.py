"""REST API endpoint tests."""

from __future__ import annotations


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["graph_backend"] == "memory"
    assert body["graph_healthy"] is True
    assert body["stats"]["nodes"] >= 120


def test_company_overview(client):
    body = client.get("/api/company").json()
    assert body["counts"]["people"] == 8
    assert body["counts"]["projects"] == 4
    assert body["company"]["name"] == "NovaTech"


def test_world_objects(client):
    body = client.get("/api/world").json()
    labels = {obj["label"] for obj in body["objects"]}
    assert {"Room", "Person", "Project", "System"} <= labels
    assert body["demo_questions"]


def test_people_listing_and_profile(client):
    people = client.get("/api/people").json()
    assert len(people) == 8
    arun = client.get("/api/people/arun_kumar").json()
    assert arun["name"] == "Arun Kumar"
    assert arun["team"]["name"] == "Backend"


def test_missing_person_returns_404(client):
    assert client.get("/api/people/does_not_exist").status_code == 404


def test_projects_and_decisions(client):
    assert client.get("/api/projects").json()
    atlas = client.get("/api/projects/atlas").json()
    assert atlas["owner"]["name"] == "Arun Kumar"
    decision = client.get("/api/decisions/ADR-018").json()
    assert "makers" in decision
    assert any(m["id"] == "priya_sharma" for m in decision["makers"])


def test_documents_and_filters(client):
    assert len(client.get("/api/documents").json()) == 20
    filtered = client.get("/api/documents", params={"project_id": "atlas"}).json()
    assert filtered


def test_systems_and_tickets(client):
    assert client.get("/api/systems").json()
    tickets = client.get("/api/tickets", params={"project_id": "atlas"}).json()
    assert tickets


def test_search(client):
    body = client.get("/api/search", params={"q": "postgres"}).json()
    assert body["count"] >= 1
    assert any(r["id"] == "postgresql" for r in body["results"])


def test_graph_endpoints(client):
    graph = client.get("/api/graph/entity/atlas").json()
    assert graph["nodes"] and graph["edges"]
    assert any(n["id"] == "atlas" for n in graph["nodes"])
    explanation = client.get("/api/graph/explain", params={"ids": "atlas,arun_kumar"}).json()
    assert explanation
    assert any(step["focus"] for step in explanation)
