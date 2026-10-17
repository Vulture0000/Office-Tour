---
id: doc_engineering_guidelines
title: NovaTech Engineering Guidelines v3
type: Engineering Guide
author_id: david_wilson
created_at: 2026-03-01
updated_at: 2026-08-20
project_id: atlas
team_id: team_engineering
source_path: data/documents/engineering_guidelines_v3.md
---

# NovaTech Engineering Guidelines v3

These guidelines are the default for every repository. Deviations require an ADR.

## Language and framework defaults

- **Backend:** Python 3.12 with FastAPI (ADR-009). Typed Pydantic request/response models and a
  generated OpenAPI schema are mandatory for every service.
- **Frontend:** React with Vite and TypeScript (ADR-012). Shared components live in the internal
  design system.
- **Ephemeral state:** Redis for caches, sessions and queues (ADR-006).
- **Graph and relationship data:** FalkorDB with parameterised Cypher (ADR-015).

## Data

PostgreSQL is the system of record (ADR-018). Schema changes ship as versioned migrations and are
reviewed by a second engineer. No service writes to another service's tables; use its API.

## Delivery

- Trunk-based development, short-lived branches, required checks on main (ADR-017).
- Every change to production infrastructure goes through GitOps; no manual deploys (ADR-021).
- Tests required for new behaviour: unit tests for logic, API tests for endpoints, an integration
  test for anything touching two services.

## Observability

Structured JSON logs with correlation IDs, RED metrics for every service, and dashboards that
answer "is the customer affected" before "which box is hot".

## Code review

Reviewers check for: typed interfaces at boundaries, explicit error handling, no secrets in the
repo, and documentation for any non-obvious decision. Reviews are about the code, never the
person who wrote it.

## AI features

Any AI feature must (1) cite its sources, (2) degrade gracefully when a model provider is
unavailable, and (3) require human confirmation before performing write actions. Prompt and
evaluation changes are reviewed like code.
