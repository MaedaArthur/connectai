# Specification

## State schema

Current typed state in `src/agente_documentos/estado.py`:

```python
{
  "caminho_md": str,
  "caso": str,
  "dificuldade": str,
  "historia": str,
  "documentos_tabela": list[DocumentoTabela],
  "documentos_json": list[dict],
  "contextos_documentos": dict[str, ContextoDocumento],
}
```

`DocumentoTabela`:

```python
{
  "numero": int,
  "nome": str,
  "tipo": str,
  "papel": str,
  "estrutura": str,
  "inconsistencia": str,
  "docs_relacionados": str,
}
```

`ContextoDocumento`:

```python
{
  "personagens": list[str],
  "eventos_chave": list[str],
  "datas_criticas": list[str],
  "contexto_do_documento": str,
  "trecho_inconsistencia": str,
  "estrutura": str,
  "tipo": str,
  "categoria": str,
}
```

## Input assumptions

The parser assumes:

- the input is a Markdown file from the narrative agent
- the filename format is `<caso>_<dificuldade>_<nnn>.md`
- Section 2 exists and is headed with a string matching `SEÇÃO 2`
- the document index is a Markdown pipe table

## Output contract

The output file is `documentos/documentos.json`.

Each generated document object is expected to include at least:

- `arquivo`
- `tipo`
- `categoria`
- `inconsistencias[]` — list of objects describing each planted inconsistency (always present across all types)
- schema-specific content matching the selected type

On parse failure the object is `{"arquivo": "...", "erro": "...", "raw": "<first 500 chars>"}` instead.

### `indice_atual` field

`main_documentos.py` seeds `"indice_atual": 0` in the initial state. This field is **not** declared in `EstadoAgente2` and is not read by any node. It is a dead field left over from an earlier design. Migration can drop it safely.

## Behavioral details worth preserving

- Batch enrichment happens before per-document generation.
- Missing enrichment fields fall back to Section 2 values.
- Generation is parallelized at document level.
- Parse failure does not abort the run; it is serialized into the output JSON.

## Downstream file-generation contract

The renderer does not validate aggressively. It mostly trusts shape. That means the documents agent currently owns schema quality.

Important real contracts from `gerar_documentos.py`:

- PDF rendering consumes `secoes[]`, not `paginas[]`.
- PPTX rendering ignores slide-level `dados`.
- Structured logs are rendered as:
  - one-tab Excel sheet named `Log`, or
  - one-page PDF table

If the migrated architecture changes schemas, the renderer must be updated too.
