# Company Brain — WeMakeDevs × FalkorDB Hackathon

A production-quality hackathon prototype: a 2D top-down company environment backed by a FalkorDB knowledge graph, LangGraph agents, graph-aware RAG, source-cited answers, decision traceability, and a **confirm-before-execute** action workflow.

## What Was Built

- **Company dataset (NovaTech)**: 120 graph nodes / 579 edges across 12 labels (Company, Department, Team, Technology, System, Skill, Person, Project, Document, Ticket, Meeting, Decision). Includes 20 markdown knowledge documents parsed with frontmatter.
- **Graph layer**: `GraphStore` protocol with two backends (`FalkorStore` for FalkorDB; `MemoryStore` in-process fallback). Parameterised Cypher, whitelist-based schema for labels/relationships. Domain queries cover profiles, expertise ranking, entity resolution (scored), subgraph/paths, decisions-by-tech, and technology/document linkage.
- **Graph-aware RAG**: Markdown loader (frontmatter-aware), heading-aware chunker, pluggable embeddings (deterministic `HashingEmbedder` default; OpenAI/Google optional). Brute-force cosine vector store persisted to JSON.
- **LangGraph agents**: `intent → graph → action → retrieval → reasoning` pipeline. Deterministic first; LLM only rephrases grounded evidence via `safe_complete` (never fabricates facts). Sequential fallback if LangGraph unavailable.
- **Confirm-before-execute actions**: `ActionStore` (proposed/pending/confirmed/cancelled with history + persistence). Supported kinds: `create_ticket`, `schedule_meeting`, `update_project_status`, `follow_up`. Confirmation required before writing to the graph.
- **REST API (FastAPI)**: Endpoints for company/world/demo/entities/graph/chat/actions/search. Includes CORS, structured errors (404/422/503), startup seeding in demo mode.
- **2D company world (Phaser + React + Vite)**: Top-down map with interactive objects (rooms, people desks, projects, server room systems), room-based exploration, proximity prompts (E), and UI panels (Chat, Graph, People, Projects, Documents, Decisions, Actions, Search).
- **CLI scripts**: `scripts/seed_company.py`, `scripts/ingest_documents.py`, `scripts/reset_demo.py`.
- **Tests**: 30 passing pytest tests covering graph queries, intent, chat, actions and API flows (memory backend).
- **Docker**: `docker/docker-compose.yml` with FalkorDB, backend, frontend + healthchecks and Nginx proxy.


## Quick Start (Local, Memory Backend)



Frontend: cd frontend && npm ci && npm run dev (http://localhost:5173)

## Tests



## Demo Highlights

- Why did we choose PostgreSQL? → ADR-018 with full decision trace + cited sources
- Who should I talk to about the Atlas database migration? → Expertise ranking (Arun Kumar top)
- Confirm-before-execute action: propose → preview → confirm → executed; ticket created
