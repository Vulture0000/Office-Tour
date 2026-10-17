---
id: doc_meeting_db_architecture_2026_08_12
title: Meeting Notes — Database Architecture Review (2026-08-12)
type: Meeting Notes
author_id: arun_kumar
created_at: 2026-08-12
updated_at: 2026-08-14
project_id: atlas
team_id: team_backend
source_path: data/documents/meeting_db_architecture_2026_08_12.md
---

# Database Architecture Review — 2026-08-12

**Attendees:** Arun Kumar, Priya Sharma, David Wilson, Meera Krishnan
**Outcome:** ADR-018 approved

## Agenda

1. MongoDB to PostgreSQL migration proposal for Atlas
2. Reporting join strategy
3. Cutover phasing and rollback criteria

## Discussion

Arun presented the cost and consistency analysis: MongoDB spend had grown 3.4x year over year,
and reporting aggregates built in application code disagreed with operational counts under
concurrent writes. Meera showed that cohort reporting requires joins across customers, plans and
usage events, which the document store could not express efficiently.

Priya confirmed that Nova ingestion also needs relational guarantees: the knowledge graph seed
pipeline reads canonical project and decision data, and inconsistent aggregates would poison
retrieval quality. She supported PostgreSQL as the system of record.

David asked about rollback. Arun described the three-phase plan with divergence logging at 0.1%
threshold from the migration design document. David approved ADR-018 with that rollback clause.

## Decisions

- **ADR-018 approved:** move Atlas from MongoDB to PostgreSQL on AWS RDS.
- Dual-write shadow reads proceed under ATLAS-101.
- Backfill sized at 50k-row resumable chunks (ATLAS-102).

## Actions

| Action | Owner | Due |
| --- | --- | --- |
| Dual-write divergence logging | Arun Kumar | 2026-08-22 |
| Backfill scripts with checkpoints | Meera Krishnan | 2026-08-29 |
| Reporting view rewrite | Arun Kumar | 2026-09-12 |
