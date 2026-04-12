# Migration Notes

## Preserve these behaviors

- Keep the output as Markdown with the same three-section structure.
- Keep Section 2 machine-readable by simple regex and table parsing unless the documents agent is migrated in lockstep.
- Keep difficulty-driven document-count rules.
- Keep the revision loop semantics: revise the full story, not a partial patch.
- Keep root-cause concealment in Section 1 and explicit reveal in Section 3.

## Current fragilities

- The compiled graph is not the real end-to-end workflow; feedback and saving are outside the graph.
- The thread id is hardcoded to `sessao_1`.
- Case numbering is directory-count based, so deletions can affect future numbering.
- The downstream parser depends on filename format and exact Markdown structure.

## Safe improvements during migration

- Make revision and save proper graph transitions.
- Replace regex-only section parsing with structured output validation if both agents migrate together.
- Introduce explicit output schemas for:
  - narrative markdown
  - document index rows
  - investigation map tables
- Separate prompt text from node logic.

## Risks if behavior changes

- If section titles change, the documents agent may fail to extract Section 2.
- If document table columns change, downstream generation may silently degrade.
- If the narrative starts naming exact spreadsheet cells or values, it breaks the current separation between story clues and planted inconsistencies.
- If save-path naming changes, the documents agent may infer `caso` and `dificuldade` incorrectly.

## Recommended migration target

Move toward explicit contracts:

1. Generate a typed internal structure for story, index, and mentor map.
2. Render Markdown from that structure.
3. Pass the structured index directly to the documents agent instead of reparsing Markdown when possible.

That preserves functionality while removing the most brittle coupling in the current design.
