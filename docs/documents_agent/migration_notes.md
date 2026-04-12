# Migration Notes

## Preserve these behaviors

- Continue accepting the narrative agent output as the upstream source, unless both agents are migrated together and a stronger typed contract replaces Markdown parsing.
- Preserve the ability to recover from a single bad LLM response without failing the full run.
- Preserve spreadsheet-specific inconsistency semantics:
  - visible inconsistency
  - cross-tab inconsistency
  - systemic inconsistency
- Preserve exact anchoring to names, dates, and planted inconsistency text.

## Current fragilities

- Section 2 parsing is regex and table-format dependent.
- `caso` and `dificuldade` are inferred from the filename, not metadata.
- `docs_relacionados` is parsed if present, but the narrative prompt does not currently guarantee such a column.
- `main_documentos.py` seeds an `indice_atual` field that is not part of the typed state and is unused.
- The generation prompt and renderer are slightly out of sync in places.

## Notable code/documentation mismatches

- `README.md` describes a `classificar_todos` node that no longer exists.
- `README.md` describes a per-document graph loop that no longer exists; generation is now parallelized inside one node.
- The prompt shows one PDF-style schema example, but the renderer expects top-level `secoes[]`, not `paginas[]`.
- PPTX JSON may include `dados`, but the renderer silently discards it.

## Safe improvements during migration

- Replace Markdown table reparsing with a typed document-index artifact from the narrative agent.
- Store `caso` and `dificuldade` explicitly in metadata instead of inferring them from filenames.
- Split the current workflow into explicit phases:
  - parse upstream artifact
  - enrich document context
  - generate typed document payload
  - validate schema
  - render files
- Add schema validation before writing `documentos.json`.

## Risks if behavior changes

- If spreadsheet structure is relaxed, rendered `.xlsx` files may stop matching the intended investigation flow.
- If literal inconsistency text is normalized or paraphrased, the planted clue can move or disappear.
- If batch enrichment is removed without a replacement, document-level generations may drift apart in names, dates, and causality.
- If parse failures start aborting the run, the migration will reduce robustness relative to current behavior.

## Recommended migration target

Use explicit typed artifacts between steps:

1. `NarrativeCase`
2. `DocumentIndex[]`
3. `DocumentContext[]`
4. `GeneratedDocument[]`
5. rendered files

That removes the fragile regex coupling while preserving the existing functionality and investigation design.
