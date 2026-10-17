---
id: doc_nova_guardrails
title: Nova Prompting and Grounding Guide
type: Engineering Guide
author_id: priya_sharma
created_at: 2026-09-10
updated_at: 2026-10-14
project_id: nova
team_id: team_ai_platform
source_path: data/documents/nova_grounding_guide.md
---

# Nova Prompting and Grounding Guide

**Owner:** Priya Sharma · **Related:** NOVA-203, NOVA-207, ADR-023

## Principle

Nova is a grounding system first and a language model second. The model is allowed to phrase an
answer; it is not allowed to originate a fact.

## Evidence contract

Every answer is assembled from an evidence bundle:

- **Graph facts** — parameterised traversals that produced nodes and relationships.
- **Document passages** — chunks retrieved from graph-linked documents, then vector-ranked.
- **Tickets and meetings** — operational context, always cited.

If the evidence bundle is empty, Nova must respond that it found no supporting information and
return a confidence below 0.3. There is no "best guess" path.

## Prompt structure

1. System: role, refusal policy, and the instruction to cite only supplied sources.
2. Context: the evidence bundle, each item tagged with a citation key.
3. Question: the user's question with resolved entities.
4. Output contract: a short answer, a list of citation keys used, and a confidence value.

## Confidence

Confidence combines source count, source type weight (decision and design documents weigh more than
tickets), and traversal depth. It is a communication aid, not a calibrated probability.

## Actions

The model may propose an action, never perform one. Proposals are rendered as a preview with the
target entity, the field values and a confirm control. Server-side code validates the proposal
against the whitelist before executing anything.

## Evaluation

A golden set of 40 questions with expected graph paths runs on every prompt change. A change that
lowers path accuracy below 95% blocks merge.
