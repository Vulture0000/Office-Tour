---
id: doc_adr_index
title: Architecture Decision Log — Index
type: Architecture Decision Record
author_id: david_wilson
created_at: 2026-03-20
updated_at: 2026-10-02
project_id: atlas
team_id: team_engineering
source_path: data/documents/architecture_decision_index.md
---

# Architecture Decision Log — Index

Maintained by David Wilson. Every decision that is expensive to reverse gets an ADR with context,
alternatives and consequences.

| ADR | Title | Status | Date | Project | Decision makers |
| --- | --- | --- | --- | --- | --- |
| ADR-006 | Use Redis for caching, sessions and job queues | Approved | 2026-02-10 | Atlas | Arun Kumar, Vikram Raj |
| ADR-009 | Python and FastAPI as the standard backend stack | Approved | 2026-03-18 | Atlas | David Wilson, Arun Kumar |
| ADR-012 | React with Vite and TypeScript for web apps | Approved | 2026-04-28 | Mercury | Rahul Menon, Sarah Thomas |
| ADR-015 | Use FalkorDB as the graph store for Nova | Approved | 2026-06-30 | Nova | Priya Sharma, David Wilson |
| ADR-017 | Replace legacy CI with GitHub Actions | Approved | 2026-05-20 | Mercury | Vikram Raj, Rahul Menon |
| ADR-018 | Move Atlas database from MongoDB to PostgreSQL | Approved | 2026-08-14 | Atlas | Arun Kumar, Priya Sharma, David Wilson |
| ADR-020 | Add read replicas for Atlas reporting workloads | Approved | 2026-09-18 | Atlas | Arun Kumar, Meera Krishnan, David Wilson |
| ADR-021 | Run production workloads on AWS EKS | Approved | 2026-07-09 | Atlas | Vikram Raj, David Wilson |
| ADR-023 | Orchestrate Nova agents with LangGraph | Approved | 2026-09-02 | Nova | Priya Sharma, Arun Kumar |
| ADR-025 | Adopt OIDC with a dedicated Auth Gateway in Orion | Proposed | 2026-10-02 | Orion | Ananya Iyer, Sarah Thomas |

## How to read this index

Each numbered ADR links to its supporting documents, the meeting where it was decided, and the
people accountable for it. In the company knowledge graph these links are traversable
relationships: Decision about Project, made by Person, supported by Document, discussed in Meeting.

## Current open decisions

- **ADR-025** is proposed and awaiting CTO approval. It blocks ORION-404 (logout divergence).
- A future ADR on cold-data archival is expected after ATLAS-108.

## Review

The index is reviewed monthly. If a decision's context changes materially, a superseding ADR is
written rather than editing history.
