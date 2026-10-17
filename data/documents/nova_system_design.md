---
id: doc_nova_design
title: Nova Knowledge Assistant — System Design
type: Technical Design
author_id: priya_sharma
created_at: 2026-06-20
updated_at: 2026-10-08
project_id: nova
team_id: team_ai_platform
source_path: data/documents/nova_system_design.md
---

# Nova Knowledge Assistant — System Design

## Goal

Nova answers employee questions about people, projects, systems, documents and decisions — with
sources — by walking the company knowledge graph instead of relying on vector similarity alone.

## Why a graph first

Questions like "Who owns Project Atlas?" and "Why did we choose PostgreSQL?" are relationship
questions. Similarity search cannot traverse Person to OWNS to Project to HAS_DECISION to
Decision to SUPPORTED_BY to Document. Per ADR-015 the company graph lives in FalkorDB and every
factual answer must be reachable through a Cypher traversal plus document evidence.

## Pipeline

The workflow is a LangGraph state graph (ADR-023) with five agents:

1. **Intent agent** — classifies the request (person, project, decision, expertise, document,
   action, general) and extracts entities.
2. **Graph intelligence agent** — resolves entities to graph nodes and runs parameterised
   traversals. Arbitrary Cypher is never accepted from users; only whitelisted query templates.
3. **Knowledge retrieval agent** — hybrid retrieval: graph-linked documents first, then vector
   similarity over chunks for long-form detail.
4. **Reasoning agent** — composes the answer from evidence only, attaches sources and a graph
   path, and scores confidence. No evidence, no claim.
5. **Action agent** — proposes write actions (create ticket, assign task, schedule meeting) as a
   preview that requires explicit human confirmation before execution.

## Data model

Nodes: Person, Team, Project, Document, Decision, Ticket, Meeting, Technology, System, Skill,
Department. Relationships include MEMBER_OF, OWNS, WORKS_ON, KNOWS, EXPERT_IN, AUTHORED,
PARTICIPATED_IN, HAS_DOCUMENT, HAS_TICKET, HAS_DECISION, MADE_BY, ABOUT, SUPPORTED_BY,
DISCUSSED_IN, RELATED_TO, REFERENCES, USES and PART_OF.

## Embeddings and chunking

Documents are chunked by heading-aware paragraphs and embedded for hybrid retrieval. The graph
always supplies relationships; embeddings only supply passage-level detail.

## Failure behaviour

DEMO_MODE keeps the assistant usable without an LLM key: answers are composed deterministically
from live graph results. FalkorDB unavailability degrades to a clear service message rather than
a stack trace.
