---
id: doc_atlas_status_report
title: Atlas Status Report — Q3 2026
type: Status Report
author_id: sarah_thomas
created_at: 2026-09-30
updated_at: 2026-10-12
project_id: atlas
team_id: team_product
source_path: data/documents/atlas_status_report_q3.md
---

# Project Atlas — Q3 2026 Status Report

**Overall health:** At risk (yellow)
**Owner:** Arun Kumar · **Lead:** David Wilson · **Product:** Sarah Thomas

## Summary

The PostgreSQL migration is functionally complete for new writes and backfill is 92% done. The
project is flagged at risk for schedule, not for correctness: reporting latency and connection
pooling both need work before we can decommission MongoDB.

## Progress this quarter

- ADR-018 approved and implemented for primary workloads.
- ADR-020 approved: read replica added for reporting.
- ATLAS-102 backfill at 92% of historical usage events.
- ATLAS-104 index tuning closed with a 6x improvement on customer lookups.

## Risks

1. **Connection pool exhaustion (ATLAS-109).** PgBouncer saturates at 600 RPS in load tests.
   Mitigation under investigation by Arun with Vikram's load harness.
2. **Reporting latency (ATLAS-105).** Dashboard p95 hit 2.8s during ingest peaks. The read replica
   work moves reporting off the primary.
3. **Schema drift (ATLAS-107).** Ingest and API disagree on `planTier` casing; a contract test is
   being added.

## Next quarter

- Finish backfill and shadow-read validation, then retire MongoDB (ATLAS-106).
- Complete audit logging for PII reads (ATLAS-110) ahead of the security review.
- Hand stable reporting views to the Mercury beta.

## Budget note

Infrastructure spend is down 19% quarter over quarter, driven by the MongoDB reduction. No new
headcount requested.
