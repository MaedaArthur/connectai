# Workflow

## Runtime flow

Current CLI flow in `main_documentos.py`:

1. Receive the path to the narrative Markdown file.
2. Build the initial state.
3. Invoke the compiled LangGraph app once.

## Current graph shape

Defined in `src/agente_documentos/grafo.py`:

```text
extrair_secao2
  -> enriquecer_documentos     if any rows were parsed
  -> salvar_saida              if no rows were parsed

enriquecer_documentos
  -> gerar_todos_documentos
  -> salvar_saida
  -> END
```

## Node roles

### `extrair_secao2`

- Opens the Markdown file produced by the narrative agent.
- Parses the filename to derive:
  - `caso`
  - `dificuldade`
- Extracts Section 2 with regex.
- Parses the pipe table into `documentos_tabela`.

Parsed columns:

- `numero`
- `nome`
- `tipo`
- `papel`
- `estrutura`
- `inconsistencia`
- `docs_relacionados` if a seventh column exists, otherwise `-`

### `enriquecer_documentos`

- Reads the full Markdown from state.
- Extracts Section 1 for narrative context.
- Extracts `causa raiz principal` from the Markdown if present.
- Sends one batch enrichment request for all parsed documents.
- Builds `contextos_documentos` keyed by document name.
- Falls back to table values when enrichment fields are missing.

### `gerar_todos_documentos`

- Uses a `ThreadPoolExecutor(max_workers=5)`.
- For each document:
  - builds a per-document prompt
  - calls the shared LLM
  - attempts to parse JSON
- On parse failure, emits a fallback object with:
  - `arquivo`
  - `erro`
  - `raw`

### `salvar_saida`

- Creates `documentos/documentos_gerados/` under the case folder.
- Saves:

```json
{
  "caso": "...",
  "dificuldade": "...",
  "documentos": [...]
}
```

to `documentos/documentos.json`.

## Renderer coupling

`gerar_documentos.py` consumes the saved JSON and creates real files.

Current renderer expectations:

- `xlsx`: `abas[]` or `colunas + entradas[]`
- `docx`: `secoes[]`, optional `campos_criticos`
- `pdf`: `secoes[]`, optional `assinatura` and `data_emissao`
- `pptx`: `slides[]`
- `eml`: `cabecalho`, `corpo`, optional `anexos`
