---
id: doc_access_review_q3
title: Q3 2026 Access Review Report
type: Security Policy
author_id: ananya_iyer
created_at: 2026-09-30
updated_at: 2026-10-02
project_id: orion
team_id: team_security
source_path: data/documents/access_review_q3_2026.md
---

# Q3 2026 Access Review

**Author:** Ananya Iyer · **Scope:** Production systems, repositories, cloud accounts
**Cadence:** Quarterly (Security Policy v2.1)

## Method

Reviewed every human principal with production access against their current team and project
assignment. Repository access was reconciled from the identity provider against team membership in
the company directory.

## Findings

| # | Finding | Severity | Status |
| --- | --- | --- | --- |
| 1 | Two former contractors retained AWS console access | High | Revoked |
| 2 | Atlas production database access granted to a rotated-off engineer | Medium | Revoked |
| 3 | Shared service account used interactively by three engineers | High | Rotated, per-user creds issued |
| 4 | Audit trail for one legacy session service incomplete | Medium | Open — superseded by ADR-025 |
| 5 | Repository admin rights on 3 orgs wider than policy allows | Low | Remaining 2 owners confirmed |

14 of 16 findings closed; 2 remain open and are tracked to Orion sign-in rework.

## Recommendation

Finding 4 is structural, not a process lapse: the legacy session service did not log token events.
Rather than patch it, complete ADR-025 so all sessions are issued and logged by the Orion gateway.
This is the strongest evidence in favour of the central gateway and is referenced in the ADR-025
supporting material.

## Follow-up

- Q4 review scheduled for 2026-12-30.
- Per-workload service accounts migrating to short-lived credentials via the gateway.
- Customer PII reads added to the audit trail under ATLAS-110.
