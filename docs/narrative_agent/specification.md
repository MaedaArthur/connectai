# Specification

## Input schema

Current input shape from `src/agente_narrativa/estado.py`:

```python
{
  "empresa": str,
  "setor": str,
  "cargo": str,
  "dificuldade": "baixa" | "média" | "alta",
  "sintomas": list[str],
  "causas_raiz": {
    "principal": str,
    "secundarias": list[str],
  }
}
```

## State schema

```python
{
  "entrada": EntradaHistoria,
  "historia": str,
  "historico": Annotated[List, add_messages],  # LangGraph reducer — messages are appended, not replaced
  "feedback": str,
}
```

The `historico` field uses LangGraph's `add_messages` reducer. Each `atualizar_historia` call appends the new exchange to the list rather than overwriting it. This means the full conversation history accumulates in state across revisions.

## Output contract

The main output is a Markdown document containing all three sections. The downstream documents agent depends on this output having:

- a recognizable `SEÇÃO 2`
- a pipe-table document index
- consistent file names and types in that table

## Observable behaviors to preserve

- `dificuldade` changes the required number of cited documents.
- The agent can revise the story repeatedly from user feedback.
- Saving is separate from generation.
- Saved files always live under `outputs/<empresa_slug>/...`.
- The output filename format is significant because the documents agent later derives:
  - `caso`
  - `dificuldade`

## `causas_raiz` shape

Although `causas_raiz` is typed as `dict` in `EntradaHistoria`, the expected shape is:

```python
{
  "principal": str,
  "secundarias": List[str],
}
```

The user prompt builder (`_montar_prompt_usuario`) reads `causas_raiz["principal"]` and `causas_raiz["secundarias"]` directly; missing either key will raise a `KeyError` at runtime.

## Hidden coupling with the documents agent

The documents agent expects:

- section headers matching the regex for `SEÇÃO 2`
- table rows starting with `|`
- the filename to follow `<empresa>_<dificuldade>_<nnn>.md`

If the new narrative architecture changes any of those, migration must also update the documents parser.
