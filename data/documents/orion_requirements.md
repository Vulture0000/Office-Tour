---
id: doc_orion_requirements
title: Orion Identity & Billing Requirements
type: Requirements Document
author_id: sarah_thomas
created_at: 2026-08-22
updated_at: 2026-09-30
project_id: orion
team_id: team_product
source_path: data/documents/orion_requirements.md
---

# Orion — Identity & Billing Requirements

**Owner:** Ananya Iyer (security) · **Product lead:** Sarah Thomas · **Status:** Planning

## Problem

Authentication is implemented three times: the legacy session service, the Mercury frontend
session cookie, and a partial SSO bridge. Logout behaviour differs across all three, and the Q3
access review could not reconstruct a complete audit trail. Billing is calculated from a nightly
batch with no event-level lineage.

## Goals

1. One identity gateway for all products, enforcing OIDC, MFA and RBAC (ADR-025, proposed).
2. Event-level billing with lineage back to Atlas usage events.
3. Complete audit trail: who acted, on what, under which policy.

## Requirements

- **R1 — OIDC:** authorization code flow with PKCE, JWKS rotation every 30 days (ORION-403).
- **R2 — MFA:** hardware-backed for production access, TOTP for customers.
- **R3 — RBAC:** role claims consumed by Mercury for report gating (MERCURY-301).
- **R4 — Billing events:** schema agreed with Atlas ingestion (ORION-402); every billed unit maps
  to a usage event ID.
- **R5 — Logout:** single gateway-mediated logout across all products (ORION-404, blocked on
  ADR-025).
- **R6 — Audit:** every token issue, refresh and revoke is written to the audit log with actor and
  purpose.

## Non-goals

Social login, SAML for enterprise customers, and anything that changes the Atlas data model.

## Risks

ADR-025 is still proposed; ORION-404 is blocked until it is approved. Migration of live sessions
needs a dual-run window to avoid forcing every user to reauthenticate at once.

## Success metrics

Zero divergent logout reports, 100% audit coverage of token lifecycle events, MFA adoption above
95% for internal users.
