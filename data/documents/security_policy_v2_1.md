---
id: doc_security_policy
title: NovaTech Security Policy v2.1
type: Security Policy
author_id: ananya_iyer
created_at: 2026-06-10
updated_at: 2026-09-28
project_id: orion
team_id: team_security
source_path: data/documents/security_policy_v2_1.md
---

# NovaTech Security Policy v2.1

**Owner:** Ananya Iyer, Security Engineering
**Scope:** All product and internal systems

## Access control

All human access to production requires SSO with hardware-backed MFA. Access reviews run
quarterly; the Q3 review closed 14 of 16 findings. Per ADR-025 (proposed) all product sessions
move behind an Orion-managed OIDC gateway so that MFA, RBAC and audit logging are enforced in one
place rather than three.

## Data protection

Customer PII is encrypted at rest and in transit. Every read of customer data must be attributable
to an actor and a purpose (ATLAS-110). Secrets live in AWS Secrets Manager; committing a secret to
a repository is treated as a security incident.

## AI systems

Nova may not send customer PII to third-party model providers. Model calls are logged with prompt
hash, model identifier and token counts. Any AI feature that writes to company systems must
present a preview and receive explicit human confirmation (ADR-023, NOVA-207). Ungrounded answers
must be refused or returned with reduced confidence.

## Incident response

Severity 1 incidents page the on-call engineer within five minutes and require a written
postmortem within five business days. Postmortems are blameless and focus on system causes.

## Application security

Dependency scanning and SAST run on every pull request. High findings block merge. Threat modelling
is required for new external interfaces and for anything that changes authentication or
authorization behaviour.

## Review cadence

The policy is reviewed every six months or after any severity 1 security incident.
