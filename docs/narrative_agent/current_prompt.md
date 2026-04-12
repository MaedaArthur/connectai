# Current Prompt

This is the behavior contract currently encoded in `src/agente_narrativa/nos.py`.

## System prompt intent

The agent is framed as a generator of immersive fictional corporate stories for hackathon simulations using a strict `mirror-problem-first` method.

Core requirements:

- The story must show the problem before any solution.
- The story is in third person.
- Minimum length is 1,500 words.
- The protagonist is competent but trapped in a dysfunctional system.
- The root cause must be inferable but never named directly in the narrative.
- Documents are central obstacles, not decorative mentions.

## Input contract used in the user prompt

The user prompt is assembled from:

- `empresa`
- `setor`
- `cargo`
- `dificuldade`
- `sintomas[]`
- `causas_raiz.principal`
- `causas_raiz.secundarias[]`

Prompt shape:

```text
Empresa: <empresa>
Setor: <setor>
Cargo do protagonista: <cargo>
Nível de dificuldade: <dificuldade>

Sintomas a espelhar na superfície da narrativa:
- ...

Causa raiz principal (nunca nomear diretamente na história):
- ...

Causas secundárias (camada intermediária da narrativa):
- ...
```

## Mandatory output structure

The system prompt requires exactly these sections in order:

1. `## SEÇÃO 1 — A HISTÓRIA`
2. `## SEÇÃO 2 — ÍNDICE DE DOCUMENTOS`
3. `## SEÇÃO 3 — MAPA DE INVESTIGAÇÃO`

## Important constraints inside the prompt

- Difficulty controls document count:
  - `baixa`: 3-5 docs
  - `média`: 6-8 docs
  - `alta`: 9-12 docs
- The narrative must include:
  - at least one team meeting transcript
  - at least one spreadsheet investigated across tabs
  - at least one internal non-spreadsheet document
- Every document cited in the narrative must appear in Section 2.
- No document may appear in Section 2 unless it was cited in the narrative.
- Section 2 must include exact planted inconsistencies.
- Section 3 must include:
  - signals classified as `Sintoma`, `Causa secundária`, or `Causa principal`
  - an RPU-style grading table
  - the explicit root cause and supporting evidence list for mentors

## Feedback revision prompt

The feedback loop appends the previous conversation and sends:

```text
Revise a história com base no seguinte feedback:

<feedback>

Mantenha rigorosamente a metodologia mirror-problem-first e todas as regras absolutas.
Retorne apenas a história revisada no mesmo formato Markdown.
```

## Few-shot examples in the system prompt

The system prompt includes four inline few-shot examples that calibrate tone and format. These are significant and must be preserved or replaced during migration:

1. **Example 1 — Opening with a concrete document** — shows how the protagonist interacts with a file without naming specific cells or values
2. **Example 2 — Robust dialogue** — shows how characters reveal symptoms through conflict, not exposition
3. **Example 3 — Transcribed meeting** — shows the format and density expected for team meeting scenes
4. **Example — Correct index format** — shows a complete Section 2 table with all three inconsistency layers (VISÍVEL, CRUZADA, SISTÊMICA) filled in

These examples are the primary mechanism for controlling output tone. Stripping them degrades story quality significantly.

## User prompt format

The system prompt states that input will be a JSON block. The actual user prompt assembled by `_montar_prompt_usuario` sends **plain text** in the format shown above, not a JSON object. The LLM handles both because the field names are consistent, but the mismatch is a minor internal inconsistency.

## Migration recommendation

Treat the current prompt as a behavioral spec, not just a string constant. The migration should preserve:

- section names
- document-count behavior by difficulty
- the prohibition on naming the root cause in the narrative
- the distinction between narrative-only clues and exact inconsistency details reserved for Section 2
- the four few-shot examples (or equivalently strong replacements)
