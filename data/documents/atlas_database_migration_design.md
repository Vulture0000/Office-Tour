---
id: doc_atlas_migration_design
title: Atlas Database Migration Design
type: Technical Design
author_id: arun_kumar
created_at: 2026-07-28
updated_at: 2026-10-09
project_id: atlas
team_id: team_backend
source_path: data/documents/atlas_database_migration_design.md
---

# Atlas Database Migration Design (MongoDB to PostgreSQL)

## Purpose

This document is the supporting design for ADR-018, which moved Atlas from MongoDB to PostgreSQL.

## Problem statement

Three forces drove the migration:

1. **Consistency.** Reporting aggregates built in application code disagreed with operational
   counts under concurrent writes. MongoDB multi-document transactions existed but were slow and
   rarely used by the legacy repository layer.
2. **Join cost.** Cohort reporting needs joins across customers, plans and usage. Stitching in
   application code made every report a bespoke query.
3. **Cost.** Managed MongoDB spend grew 3.4x year over year while our Postgres footprint stayed flat.

## Target design

PostgreSQL 16 on AWS RDS with multi-AZ. Monthly partitioned `usage_events`, encrypted PII columns,
PgBouncer for pooling, and a read replica for reporting (ADR-020).

## Migration strategy

Three phases:

- **Phase 1 — Dual write.** Writes go to MongoDB first, then PostgreSQL, with divergence logging (ATLAS-101).
- **Phase 2 — Shadow reads.** Reads still served by MongoDB while PostgreSQL responses are compared (ATLAS-101).
- **Phase 3 — Cutover and decommission.** Reads flip to PostgreSQL, then MongoDB is retired (ATLAS-106).

Backfill runs in resumable 50k-row chunks to keep replica lag under two seconds (ATLAS-102).
Index tuning for customer-by-region and customer-by-plan lookups landed in ATLAS-104.

## Rollback

If divergence exceeds 0.1% of sampled queries, reads revert to MongoDB for one release cycle.

## Decision context

Reviewed with Priya Sharma and Meera Krishnan, approved by David Wilson in the Database
Architecture Review meeting on 2026-08-12 (ADR-018).
