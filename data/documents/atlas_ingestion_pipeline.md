---
id: doc_data_pipeline_design
title: Atlas Ingestion Pipeline Design
type: Technical Design
author_id: meera_krishnan
created_at: 2026-07-15
updated_at: 2026-10-07
project_id: atlas
team_id: team_data
source_path: data/documents/atlas_ingestion_pipeline.md
---

# Atlas Ingestion Pipeline Design

**Author:** Meera Krishnan · **Owner:** Arun Kumar · **Related:** ADR-018, ATLAS-102, ATLAS-107

## Overview

The ingestion pipeline turns raw product API events into the canonical `usage_events` table that
powers reporting and billing.

## Stages

1. **Collect.** FastAPI ingest endpoints accept batched events, validate against the event schema
   and write to a Redis stream.
2. **Normalise.** Workers consume the stream, coerce types, resolve tenant and plan identifiers,
   and emit normalised rows.
3. **Load.** Rows are written to PostgreSQL in 5k-row transactions with `ON CONFLICT DO NOTHING`
   for idempotency.
4. **Aggregate.** Hourly materialised views roll usage up by tenant, plan and region.

## Backfill

Historical backfill from MongoDB runs in resumable 50k-row chunks with checkpoints in Redis. Chunk
size was chosen so replica lag stays under two seconds, which is the threshold the reporting
staleness badge tolerates (ATLAS-102).

## Data quality

- Event schema version is enforced at ingest; unknown versions are rejected with a metric.
- A nightly reconciliation job compares hourly aggregates against raw counts and alerts on
  divergence above 0.05%.
- Contract tests compare ingest output to the API model, added after ATLAS-107 found a
  `plan_tier` vs `planTier` mismatch.

## Failure modes

| Failure | Behaviour |
| --- | --- |
| Redis stream full | Ingest sheds load with 429 and a retry hint |
| Postgres primary failover | Workers retry with exponential backoff, stream retains events |
| Schema drift | Rows quarantined to `usage_events_quarantine` and alerted |

## Open work

Cold-data archival to S3 (ATLAS-108) and a schema registry to remove the manual contract tests.
