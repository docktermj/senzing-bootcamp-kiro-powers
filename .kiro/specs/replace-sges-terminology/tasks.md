# Implementation Plan: Replace "SGES" with "Entity Specification"

## Overview

Systematically replace bare "SGES" references across 13 files, applying first-mention expansion ("Senzing Entity Specification (SGES)") and subsequent shortening ("Entity Specification"). Verify no undefined usages remain.

## Tasks

- [x] 1. Replace in steering files
  - [x] 1.1 Update `senzing-bootcamp/steering/onboarding-flow.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - Compound forms: "SGES data" → "Entity Specification data", etc.
    - _Requirements: 1, 2_
  - [x] 1.2 Update `senzing-bootcamp/steering/module-06-single-source.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_

- [x] 2. Replace in POWER.md
  - [x] 2.1 Update `senzing-bootcamp/POWER.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - Cover module table, path B, experienced users, skip-ahead sections
    - _Requirements: 1, 2_

- [x] 3. Replace in docs/guides/ files
  - [x] 3.1 Update `senzing-bootcamp/docs/guides/QUICK_START.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - Cover path table, example phrases, skip-ahead
    - _Requirements: 1, 2_
  - [x] 3.2 Update `senzing-bootcamp/docs/guides/FAQ.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_
  - [x] 3.3 Update `senzing-bootcamp/docs/guides/PROGRESS_TRACKER.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_
  - [x] 3.4 Update `senzing-bootcamp/docs/guides/README.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_
  - [x] 3.5 Update `senzing-bootcamp/docs/guides/COMMON_MISTAKES.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_

- [x] 4. Replace in docs/modules/README.md
  - [x] 4.1 Update `senzing-bootcamp/docs/modules/README.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_

- [x] 5. Replace in docs/diagrams/ files
  - [x] 5.1 Update `senzing-bootcamp/docs/diagrams/module-flow.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_
  - [x] 5.2 Update `senzing-bootcamp/docs/diagrams/module-prerequisites.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_
  - [x] 5.3 Update `senzing-bootcamp/docs/diagrams/data-flow.md`
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_

- [x] 6. Replace in scripts/install_hooks.py
  - [x] 6.1 Update `senzing-bootcamp/scripts/install_hooks.py`
    - Replace bare "SGES" in hook description string
    - First occurrence → "Senzing Entity Specification (SGES)"
    - Subsequent occurrences → "Entity Specification"
    - _Requirements: 1, 2_

- [x] 7. Checkpoint - Verify replacements
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Verify no undefined SGES usages remain
  - [x] 8.1 Grep for remaining bare "SGES" across the repository
    - Run `grep -rn "SGES" senzing-bootcamp/` and confirm every remaining instance is in a post-definition context (GLOSSARY.md, MODULE_5_DATA_MAPPING.md, or after a full-term introduction in the same file)
    - _Requirements: 2, 3_

- [x] 9. Run validate_power.py
  - [x] 9.1 Execute `python senzing-bootcamp/scripts/validate_power.py`
    - Confirm no broken links or structural issues from the terminology changes
    - _Requirements: 4_

- [x] 10. Final checkpoint
  - Ensure all validations pass, ask the user if questions arise.

## Notes

- GLOSSARY.md and MODULE_5_DATA_MAPPING.md are intentionally unchanged (they already define the full term before using the acronym)
- No automated tests needed — this is a documentation-only change
- Each task references specific acceptance criteria from requirements.md
