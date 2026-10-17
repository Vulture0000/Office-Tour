"""Graph query and entity-resolution tests."""

from __future__ import annotations

import pytest

from app.graph import queries


@pytest.fixture
def store():
    """A freshly seeded in-memory graph, isolated from other tests."""

    from app.graph.client import MemoryStore
    from app.graph.seed import seed_graph

    graph = MemoryStore()
    seed_graph(graph)
    return graph


def test_seed_statistics(store):
    stats = store.stats()
    assert stats.nodes == 120
    assert stats.edges == 579
    by_label = stats.nodes_by_label
    assert by_label["Person"] == 8
    assert by_label["Project"] == 4
    assert by_label["Decision"] == 10
    assert by_label["Document"] == 20


def test_person_profile_arun(store):
    profile = queries.person_profile(store, "arun_kumar")
    assert profile is not None
    assert profile["team"]["name"] == "Backend"
    tech_ids = {t["id"] for t in profile["technologies"]}
    assert "postgresql" in tech_ids
    project_ids = {p["id"] for p in profile["projects"]}
    assert {"atlas", "mercury", "nova"} <= project_ids
    assert {p["id"] for p in profile["projects_owned"]} == {"atlas"}


def test_project_profile_atlas(store):
    profile = queries.project_profile(store, "atlas")
    assert profile is not None
    assert profile["owner"]["name"] == "Arun Kumar"
    assert profile["team"]["name"] == "Backend"
    assert profile["tickets"], "Atlas should have tickets"


def test_decision_trace_adr018(store):
    trace = queries.decision_profile(store, "ADR-018")
    assert trace is not None
    maker_ids = {m["id"] for m in trace["makers"]}
    assert {"arun_kumar", "priya_sharma", "david_wilson"} <= maker_ids
    doc_ids = {d["id"] for d in trace["supporting_documents"]}
    assert "doc_atlas_migration_design" in doc_ids


def test_resolve_entity_scoring(store):
    assert queries.resolve_entity(store, "Postgres")["id"] == "postgresql"
    assert queries.resolve_entity(store, "postgresql")["id"] == "postgresql"
    assert queries.resolve_entity(store, "atlas")["id"] == "atlas"
    assert queries.resolve_entity(store, "ATLAS-101")["id"] == "ATLAS-101"
    assert queries.resolve_entity(store, "arun kumar")["id"] == "arun_kumar"


def test_expertise_rank_orders_arun_first(store):
    ranked = queries.expertise_rank(
        store, ["database", "migration", "postgresql"], project_id="atlas"
    )
    assert ranked
    assert ranked[0]["person"]["id"] == "arun_kumar"
    scores = [entry["score"] for entry in ranked]
    assert scores == sorted(scores, reverse=True)


def test_decisions_about_technology(store):
    decisions = queries.decisions_about_technology(store, "postgresql")
    ids = {d["id"] for d in decisions}
    assert "ADR-018" in ids
    titles = " ".join(d["name"] for d in decisions).lower()
    assert "read replicas" in titles


def test_documents_for_technology(store):
    docs = queries.documents_for_technology(store, "postgresql")
    assert docs
