---
id: doc_mercury_frontend_architecture
title: Mercury Frontend Architecture
type: Technical Design
author_id: rahul_menon
created_at: 2026-05-30
updated_at: 2026-09-22
project_id: mercury
team_id: team_frontend
source_path: data/documents/mercury_frontend_architecture.md
---

# Mercury Frontend Architecture

**Author:** Rahul Menon · **Stack:** React 18, Vite, TypeScript (ADR-012)

## Structure

Feature-sliced layout: `features/reports`, `features/account`, `features/shared`. Each feature owns
its components, hooks and API client. Cross-feature imports go through the shared design system,
never sideways into another feature.

## Data layer

A thin typed client wraps the Atlas Reports API. Response types are generated from the OpenAPI
schema so contract drift fails at compile time — the same class of bug as MERCURY-304 but caught in
CI instead of production.

Caching uses stale-while-revalidate: the dashboard renders cached data with a freshness badge while
refetching. The freshness badge reads `staleness_seconds` from the API, tolerating up to 120s before
warning.

## Rendering performance

The usage table is windowed and virtualised (MERCURY-302). Above 10k rows we render only visible
rows plus a 20-row overscan; sorting and filtering are memoised over a normalised index.

Charts render to canvas with a shared theme object. Legend colours come from the accessibility-safe
palette; ADR for dark mode contrast is tracked in MERCURY-303.

## State

Server state lives in the query cache; UI state lives in local component state. There is no global
store, deliberately: the dashboard has no cross-feature client state worth centralising.

## Testing

Vitest for units, Playwright for the three critical journeys (login, view report, export CSV).
Accessibility checked with axe on every component story.

## Known debt

Charts re-render on window resize without debounce, and the export path duplicates formatting
logic that lives in the shared package.
