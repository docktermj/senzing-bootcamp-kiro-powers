# Design: Replace "SGES" with "Entity Specification"

## Overview

Replace bare "SGES" references with "Entity Specification" (or "Senzing Entity Specification (SGES)" on first mention) in user-facing content where the term appears before being defined. Leave technical contexts where the full name is already introduced.

## Files Requiring Changes

| File | Context | Action |
|------|---------|--------|
| `senzing-bootcamp/steering/onboarding-flow.md` | Welcome message, path B, gate 4→5 | Replace |
| `senzing-bootcamp/POWER.md` | Module table, path B, experienced users, skip-ahead | Replace |
| `senzing-bootcamp/docs/guides/QUICK_START.md` | Path table, example phrases, skip-ahead | Replace |
| `senzing-bootcamp/docs/guides/FAQ.md` | Skip modules, glossary reference | Replace |
| `senzing-bootcamp/docs/guides/PROGRESS_TRACKER.md` | Skip-ahead options | Replace |
| `senzing-bootcamp/docs/guides/README.md` | Glossary description | Replace |
| `senzing-bootcamp/docs/guides/COMMON_MISTAKES.md` | Mapping mistake explanation | Replace |
| `senzing-bootcamp/docs/modules/README.md` | Module 5 key topics | Replace |
| `senzing-bootcamp/docs/diagrams/module-flow.md` | Skip path, dependency notes | Replace |
| `senzing-bootcamp/docs/diagrams/module-prerequisites.md` | Skip points | Replace |
| `senzing-bootcamp/docs/diagrams/data-flow.md` | Diagram labels | Replace |
| `senzing-bootcamp/scripts/install_hooks.py` | Hook description string | Replace |
| `senzing-bootcamp/steering/module-06-single-source.md` | Data source bullet points | Replace |

### Unchanged Files

- `senzing-bootcamp/docs/guides/GLOSSARY.md` — canonical definition; stays as-is
- `senzing-bootcamp/docs/modules/MODULE_5_DATA_MAPPING.md` — already introduces the full term "Senzing Generic Entity Specification (SGES)" before using the acronym

## Replacement Rules

1. First occurrence per file → "Senzing Entity Specification (SGES)"
2. Subsequent occurrences in same file → "Entity Specification"
3. Compound forms: "SGES data" → "Entity Specification data", "SGES-compliant" → "Entity Specification-compliant", "SGES format" → "Entity Specification format"
4. Files that already define the full term before using the acronym (MODULE_5, GLOSSARY) → no change

## Error Handling

Not applicable — all changes are static markdown text edits with no runtime behavior.

## Testing Strategy

Manual review: grep for remaining bare "SGES" after changes and confirm each is in a post-definition context. No automated tests needed — this is a documentation-only change.
