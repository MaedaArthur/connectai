# Documents Agent

This folder documents the current `src/agente_documentos` agent so it can be migrated without losing document-generation behavior.

## Scope

- Reads the Markdown produced by the narrative agent.
- Extracts the Section 2 document index.
- Enriches each row with narrative context.
- Generates one JSON payload per document.
- Saves `documentos/documentos.json` for the renderer in `gerar_documentos.py`.

## Current source of truth

- Graph: `src/agente_documentos/grafo.py`
- Nodes and prompts: `src/agente_documentos/nos.py`
- State: `src/agente_documentos/estado.py`
- CLI entrypoint: `main_documentos.py`
- File renderer: `gerar_documentos.py`

## Files in this folder

- `current_prompt.md`: current generation and enrichment prompt contracts.
- `workflow.md`: graph flow and node responsibilities.
- `specification.md`: state, parser expectations, and JSON contracts.
- `migration_notes.md`: behavior to preserve, mismatches, and migration risks.
