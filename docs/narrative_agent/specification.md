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
  "historico": list[messages],
  "feedback": str,
}
```

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

## Hidden coupling with the documents agent

The documents agent expects:

- section headers matching the regex for `SEÇÃO 2`
- table rows starting with `|`
- the filename to follow `<empresa>_<dificuldade>_<nnn>.md`

If the new narrative architecture changes any of those, migration must also update the documents parser.
