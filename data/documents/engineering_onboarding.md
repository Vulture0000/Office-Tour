---
id: doc_onboarding_handbook
title: Engineering Onboarding Handbook
type: Onboarding
author_id: sarah_thomas
created_at: 2026-02-15
updated_at: 2026-07-01
project_id: mercury
team_id: team_product
source_path: data/documents/engineering_onboarding.md
---

# Engineering Onboarding Handbook

Welcome to NovaTech. This handbook gets you from laptop to first pull request in a day.

## Week one

1. **Accounts.** SSO through the identity provider, then ask your team lead for repository access.
2. **Local environment.** Docker Desktop, Python 3.12, Node 20, and `uv` or `poetry`. Every service
   has a `docker compose` file that boots it with dependencies.
3. **Read these first.** Engineering Guidelines v3, the Security Policy, and the architecture
   document for the project you joined.

## How we work

We develop in trunk-based style with short-lived branches and required checks on main. Every
change needs one review. We use ADRs for decisions that are expensive to reverse: if you are
choosing a database, an auth model, or a deployment platform, write an ADR.

## Who to ask

- Backend, data platform, database migrations: **Arun Kumar**
- AI platform, agent orchestration, retrieval quality: **Priya Sharma**
- Frontend, design system, performance: **Rahul Menon**
- Kubernetes, CI/CD, cloud cost: **Vikram Raj**
- Security reviews, threat modelling, access: **Ananya Iyer**
- Data pipelines and warehouse modelling: **Meera Krishnan**
- Roadmap, priorities, customer context: **Sarah Thomas**
- Architecture escalations: **David Wilson**

## Your first task

Pick a "good first issue" from your team's backlog. Your mentor reviews it with you. Team leads own
the backlog grooming, so ask them if the issue is unclear.

## Where knowledge lives

Documents, decisions and meeting notes are indexed in the company knowledge graph. Ask Nova in the
dashboard: it answers with sources, and walking the virtual office to a desk or room gives you the
same graph with context.
