---
id: doc_atlas_architecture
title: Atlas System Architecture
type: Technical Design
author_id: arun_kumar
created_at: 2026-04-10
updated_at: 2026-09-30
project_id: atlas
team_id: team_backend
source_path: data/documents/atlas_system_architecture.md
---

# Atlas System Architecture

## Overview

Atlas is NovaTech's customer data platform. It ingests product usage events, joins them with
customer records, and serves analytics to the Mercury dashboard and the Nova knowledge pipeline.

## Current topology

Ingestion workers consume events from the product APIs and write them through a FastAPI ingest
service. Since ADR-018 the system of record is PostgreSQL on AWS RDS, with MongoDB retained only
as a shadow source during the cutover window. Reporting queries run against a PostgreSQL read
replica as approved in ADR-020.

Redis provides the result cache for dashboard aggregates and the durable queue for background
ingest jobs. All services run as containers on AWS EKS (ADR-021) and are deployed through GitHub
Actions pipelines with required checks on main.

## Data model core

Three tables carry most of the load: `customers`, `usage_events` and `plans`. Usage events are
append-only and partitioned monthly. Customer PII columns are encrypted at rest and every read is
audit logged per ATLAS-110.

## Why relational

The reporting use cases are dominated by joins between customers, plans and usage aggregates.
Application-side stitching in the MongoDB era produced inconsistent aggregates and cost 3.4x more
to operate. PostgreSQL gives transactional consistency, window functions for cohort queries, and a
single operational model shared with Orion and Nova.

## Known pressure points

- Connection pooling saturates near 600 RPS (ATLAS-109).
- Reporting latency regressed during write peaks, tracked by ADR-020 and ATLAS-105.
- Dual-write divergence checks are still running (ATLAS-101).

## Owners

Arun Kumar is the technical owner. Meera Krishnan owns the ingestion pipeline. David Wilson
approved the architecture. Sarah Thomas owns the product-facing reporting commitments.
