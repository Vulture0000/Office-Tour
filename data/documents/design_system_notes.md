---
id: doc_frontend_design_system
title: NovaTech Design System Notes
type: Engineering Guide
author_id: rahul_menon
created_at: 2026-06-05
updated_at: 2026-09-14
project_id: mercury
team_id: team_frontend
source_path: data/documents/design_system_notes.md
---

# NovaTech Design System Notes

**Owner:** Rahul Menon · **Consumers:** Mercury, Nova dashboard, internal tools

## Principles

1. **Information before decoration.** Every pixel either carries meaning or gets removed.
2. **Dark first.** The default theme is dark; light mode is a supported alternative, not an
   afterthought.
3. **Motion with purpose.** Transitions explain state changes, never entertain.

## Foundations

- **Colour:** deep slate surfaces (`#0f1218`, `#161b24`), one accent (cyan `#38bdf8`), semantic
  colours for success, warning and danger. Contrast checked against WCAG AA in both themes.
- **Typography:** system UI stack for product pages; monospace for identifiers, ticket keys and
  code. Numeric data uses tabular figures.
- **Spacing:** 4px base scale. Cards use 16px padding, 12px gaps.
- **Elevation:** two levels only — resting and raised. Raised surfaces get a 1px border plus a soft
  shadow; we avoid large blur radii.

## Components

Buttons (primary, ghost, danger), inputs with inline validation, cards, badges for status
(`healthy`, `degraded`, `blocked`), and a data table with virtualised rows. Status colours are
always paired with a text label; colour alone never conveys state.

## Charts

Axis and grid lines at 12% opacity. Legends use the accessibility palette and sit above the chart
on narrow viewports. Tooltips show exact values, never rounded ones.

## Accessibility

Keyboard reachable controls, visible focus rings, `prefers-reduced-motion` respected. Icons that
carry meaning have text labels.

## Implementation notes

Tokens ship as CSS custom properties plus a TypeScript object. Components are themed by token, never
by conditional classes. New components require a story and an axe check before merge.
