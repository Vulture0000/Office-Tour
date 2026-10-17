---
id: doc_incident_inc_047
title: Incident Report INC-047 — AI Gateway Latency Regression
type: Incident Report
author_id: vikram_raj
created_at: 2026-09-22
updated_at: 2026-09-26
project_id: nova
team_id: team_devops
source_path: data/documents/incident_inc_047.md
---

# INC-047 — AI Gateway Latency Regression (2026-09-22)

**Severity:** 3 · **Duration:** 6 days (regression, not outage) · **Author:** Vikram Raj

## Summary

After the September cache redesign, AI Services p99 latency rose from 1.9s to 4.7s. No requests
failed, but interactive Nova sessions felt sluggish and the team's own usage dropped.

## Timeline

- Sep 16 — Cache redesign deployed, moving all workloads onto one Redis keyspace.
- Sep 18 — AI gateway p99 crosses 3s; alert threshold not yet breached.
- Sep 22 — Weekly incident triage (meet_012) confirms the correlation.
- Sep 26 — Dedicated Redis namespace for AI workloads restores p99 to 2.0s.

## Root cause

The shared Redis keyspace let high-churn report caches evict the AI gateway's prompt-cache entries
under `allkeys-lru`. Eviction churn increased upstream model calls, which dominate latency.

## Impact

Elevated latency for six days. No data loss, no failed requests, no customer-visible errors.

## Actions taken

- Dedicated Redis namespace per workload class.
- Cache hit ratio dashboard added; alert at below 60% for AI workloads.
- NOVA-205 tracks the permanent fix and verification.

## Lessons

Caching is a shared resource with a fairness problem. Per-workload isolation should have been part
of the cache redesign review. Triage cadence caught this, but two days later than an alert would
have.
