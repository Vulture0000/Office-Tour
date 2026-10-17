---
id: doc_mercury_requirements
title: Mercury Product Requirements Document
type: Requirements Document
author_id: sarah_thomas
created_at: 2026-04-02
updated_at: 2026-09-12
project_id: mercury
team_id: team_product
source_path: data/documents/mercury_requirements.md
---

# Mercury — Product Requirements Document

**Owner:** Sarah Thomas · **Engineering owner:** Rahul Menon · **Status:** In development

## Problem

Customers see their NovaTech usage only through monthly emailed PDFs. Support tickets about
"missing usage" average 40 per month, and the top churn reason in exit interviews is "we cannot
see what we are paying for".

## Goals

1. Give customers a self-serve, role-aware usage dashboard.
2. Cut "missing usage" tickets by 60% within two quarters.
3. Ship on the standard React, Vite and TypeScript stack (ADR-012).

## Requirements

- **R1 — Reports:** usage by plan, region and period with CSV export. Data from the Atlas reports
  API, served from the PostgreSQL read replica (ADR-020).
- **R2 — Roles:** report tabs are gated by the Orion role claim; the frontend must not decide
  authorization on its own.
- **R3 — Performance:** first meaningful paint under 1.5s on a mid-tier laptop; the usage table
  must stay smooth above 10k rows (MERCURY-302).
- **R4 — Accessibility:** charts must meet WCAG AA contrast in both themes (MERCURY-303).
- **R5 — Resilience:** if the reports API is slow, the dashboard shows cached data with a
  staleness badge instead of a spinner.

## Out of scope

Billing transactions, invoice download, and write operations of any kind.

## Success metrics

Monthly active dashboards, ticket volume tagged "missing usage", and time-to-first-report after
signup. Target: 300 active dashboards and 60% ticket reduction by end of Q4 2026.

## Dependencies

Atlas reports API contract (MERCURY-304, resolved), Orion role claims (ORION-401).
