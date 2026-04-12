# Current Prompt

This behavior is currently split across two prompts in `src/agente_documentos/nos.py`.

## 1. Enrichment prompt

Purpose:

- infer or confirm the file type
- classify the document into a taxonomy category
- extract narrative context for each document row

Expected output shape:

```json
{
  "nome_arquivo.ext": {
    "tipo": "xlsx|docx|pdf|pptx|eml",
    "categoria": "...",
    "personagens": ["Nome (papel)"],
    "eventos_chave": ["..."],
    "datas_criticas": ["..."],
    "contexto_do_documento": "...",
    "trecho_inconsistencia": "...",
    "estrutura": "..."
  }
}
```

Important behavior:

- `trecho_inconsistencia` must copy the Section 2 inconsistency text literally.
- `estrutura` must also be copied literally.
- Taxonomy differs by type and includes special log categories.

## 2. Document generation prompt

Purpose:

- generate the full JSON representation of one artifact
- anchor it in the story context and in the exact planted inconsistency text

The prompt enforces:

- strict narrative anchoring
- strict anchoring to critical fields from the index
- exact spreadsheet tab structure
- visible, cross-tab, and systemic inconsistency distribution for spreadsheets
- date consistency with the story
- character-name consistency with the story
- 2 to 4 varied inconsistencies per document

## Supported schemas in the current prompt

- `xlsx`
- `docx`
- `pdf`
- `pptx`
- structured log
- `eml`

## Important migration note

The prompt is doing three jobs at once:

- classification
- context extraction
- content generation

The new architecture should preserve those outputs even if they move into separate typed steps or tools.
