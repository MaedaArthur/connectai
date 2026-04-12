# Narrative Agent

This folder documents the current `src/agente_narrativa` agent so it can be migrated without losing behavior.

## Scope

- Generates the case narrative in Markdown.
- Produces the three required sections:
  - `Seção 1 — A história`
  - `Seção 2 — Índice de documentos`
  - `Seção 3 — Mapa de investigação`
- Supports an interactive feedback loop before saving.

## Current source of truth

- Graph: `src/agente_narrativa/grafo.py`
- Nodes and prompts: `src/agente_narrativa/nos.py`
- State: `src/agente_narrativa/estado.py`
- Input loading: `src/agente_narrativa/entrada.py`
- CLI entrypoint: `main.py`

## Files in this folder

- `current_prompt.md`: distilled prompt contract, user prompt shape, and feedback prompt.
- `workflow.md`: current runtime workflow and node responsibilities.
- `specification.md`: state, I/O contracts, and observable behavior.
- `migration_notes.md`: what must be preserved, what is fragile, and what can be improved safely.
