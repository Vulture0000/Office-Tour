---
id: doc_incident_2026_06_21
title: Incident Report INC-042 — Failed Production Deploy
type: Incident Report
author_id: vikram_raj
created_at: 2026-06-21
updated_at: 2026-06-24
project_id: atlas
team_id: team_devops
source_path: data/documents/incident_inc_042.md
---

# INC-042 — Failed Production Deploy (2026-06-21)

**Severity:** 2 · **Duration:** 74 minutes · **Author:** Vikram Raj

## Summary

A production deploy of the Atlas ingest service left the fleet in a mixed state: six of nine EC2
instances ran the new build while three kept the old one. Ingest throughput dropped 40% and
duplicate usage rows appeared for 11 minutes.

## Timeline

- 14:02 — Deploy command issued by hand over SSH to the instance list.
- 14:05 — Three instances rejected the artifact due to a checksum mismatch.
- 14:09 — Mixed-version fleet caused duplicate writes for tenants on both versions.
- 15:16 — Fleet rolled back to the previous artifact; duplication stopped.

## Root cause

Deploys were a hand-rolled script over a hard-coded instance list with no atomicity, no
verification and no rollback path. The checksum mismatch was a symptom; the absence of a release
mechanism was the cause.

## Impact

11 minutes of duplicate usage rows (since deduplicated), 40% ingest degradation for 74 minutes, no
customer data loss.

## Contributing factors

- No staging environment matched production at the time.
- Artifact checksums were computed per host rather than centrally.

## Actions taken

1. Approved ADR-021: move production to AWS EKS with GitOps deployments (approved 2026-07-09).
2. Added artifact checksum verification to the release pipeline.
3. Staging cluster raised to production parity in node count.

## Lessons

Deployment is a system, not a command. Standardise the platform before optimising the process.
This incident is the primary evidence behind ADR-021.
