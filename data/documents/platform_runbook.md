---
id: doc_platform_runbook
title: Platform Runbook
type: Runbook
author_id: vikram_raj
created_at: 2026-05-18
updated_at: 2026-10-01
project_id: atlas
team_id: team_devops
source_path: data/documents/platform_runbook.md
---

# Platform Runbook

**Owner:** Vikram Raj · **Platform:** AWS EKS, GitHub Actions, Redis, PostgreSQL RDS

## Deployments

All production deployments go through GitHub Actions with GitOps (ADR-021). A deploy that bypasses
the pipeline is an incident. Rollback is `git revert` plus sync; median rollback time is 4 minutes.

## Cluster operations

- Node groups: `general` (m5.large) and `ai` (g5.xlarge, tainted for AI Services).
- Autoscaling targets CPU 65% / memory 70%. Cluster autoscaler adds nodes within 90 seconds.
- PodDisruptionBudgets are required for anything with more than one replica.

## Database operations

- RDS PostgreSQL 16, multi-AZ, 15-minute automated backups, 7-day PITR window.
- Read replica lag alerts at 30 seconds; page at 120 seconds.
- PgBouncer front-ends all application connections. Pool exhaustion near 600 RPS is tracked by
  ATLAS-109.

## Cache operations

Redis runs as a two-shard cluster with 6GB maxmemory and `allkeys-lru`. Memory pressure above 85%
for five minutes pages the on-call engineer. A cache redesign in September caused AI gateway p99
regression (NOVA-205) from eviction churn; the fix is a dedicated namespace per workload.

## Observability

- Dashboards: service RED metrics, database health, cache pressure, cost.
- Alerts route to the on-call rotation with severity in the page title.
- Every service logs correlation IDs; trace sampling is 10% steady, 100% during incidents.

## On-call

Seven-day rotations, handover notes required, and a blameless postmortem within five business days
for severity 1 or 2 incidents.
