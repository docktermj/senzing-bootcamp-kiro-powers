# Implementation Plan: Split Verbosity Steering

## Overview

Split the monolithic `verbosity-control.md` (248 lines, 4,152 tokens, `inclusion: always`) into a lean core file (≤80 lines, always-loaded) and a detailed reference file (~170 lines, manually-loaded). Update the steering index to reflect the new two-file structure and update smoke tests to check the correct file for moved content. This is a pure content reorganization — no Python scripts change.

## Tasks

- [x] 1. Add new smoke tests for the reference file
  - [x] 1.1 Add `_read_reference_file()` helper and reference file smoke tests to `TestSteeringFileSmokeTests`
    - Add a `_read_reference_file()` helper method to `TestSteeringFileSmokeTests` that reads `verbosity-control-reference.md`
    - Add `test_reference_file_exists` — asserts `verbosity-control-reference.md` exists at `senzing-bootcamp/steering/verbosity-control-reference.md`
    - Add `test_reference_file_frontmatter_contains_inclusion_manual` — asserts the reference file contains `inclusion: manual`
    - Add `test_core_file_line_count_within_limit` — asserts `verbosity-control.md` has ≤80 lines
    - Add `test_core_file_contains_file_reference_directive` — asserts the core file contains `#[[file:` pointing to `verbosity-control-reference.md`
    - _Requirements: 1.2, 1.4, 3.2, 5.1_

  - [x] 1.2 Add content placement smoke tests for the reference file
    - Add `test_reference_file_contains_full_category_definitions` — asserts all five category definition paragraphs are in the reference file (check for "Definition:" under each category)
    - Add `test_reference_file_contains_content_rules_by_level` — asserts content rules for all three levels appear in the reference file
    - Add `test_reference_file_contains_all_framing_patterns` — asserts "What and Why", "Code Execution Framing", and "Step Recap Framing" sections are in the reference file
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2. Create the reference file
  - [x] 2.1 Create `verbosity-control-reference.md` with extracted detailed content
    - Create `senzing-bootcamp/steering/verbosity-control-reference.md` with `inclusion: manual` frontmatter
    - Extract from the current `verbosity-control.md` into the reference file:
      - Full output category definitions (the "Definition:", "Examples of content in this category:", and "Content rules by level:" subsections for all five categories: `explanations`, `code_walkthroughs`, `step_recaps`, `technical_details`, `code_execution_framing`)
      - All framing pattern examples (the "What and Why" framing at levels 1–3, "Code Execution Framing" at levels 1–3, "Step Recap Framing" at levels 1–3)
    - Add a brief intro stating this is the detailed reference companion to the core file
    - Preserve all original content exactly — no rewording, no omissions
    - _Requirements: 1.2, 1.3, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1_

- [x] 3. Rewrite the core file
  - [x] 3.1 Rewrite `verbosity-control.md` as the lean core file (≤80 lines)
    - Rewrite `senzing-bootcamp/steering/verbosity-control.md` keeping only:
      - `inclusion: always` frontmatter (unchanged)
      - Title and a condensed one-paragraph intro
      - Output Categories — compact list of all five category names with a one-line description each (not the full definitions, not the content rules by level)
      - Preset Definitions — the table mapping `concise`/`standard`/`detailed` to per-category levels, plus one-line description of each preset
      - Natural Language Term Mapping — the table mapping common terms to categories, plus the "no match" fallback instruction
      - Adjustment Instructions — preset changes (4 steps), NL adjustments (7 steps), custom preset definition, session-start reading instructions
      - A `#[[file:verbosity-control-reference.md]]` reference directive with instruction to load the reference file when applying level-specific content rules for the first time in a session
    - The file MUST be ≤80 lines total (including frontmatter and blank lines)
    - _Requirements: 1.1, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3_

- [x] 4. Checkpoint — Verify core and reference files
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update the steering index
  - [x] 5.1 Update `steering-index.yaml` for the two-file structure
    - Update the `file_metadata` entry for `verbosity-control.md` with the new (reduced) `token_count` and `size_category`
    - Add a new `file_metadata` entry for `verbosity-control-reference.md` with its `token_count` and `size_category`
    - Add keyword entries in the `keywords` section that map to `verbosity-control-reference.md` (e.g., `verbosity reference`, `verbosity levels`, `content rules`)
    - Update `budget.total_tokens` to reflect the combined token counts of both files (should be approximately equal to the original 85,098 total since no content is added or removed, just redistributed)
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 6. Update existing smoke tests to check the correct file
  - [x] 6.1 Update three framing smoke tests in `TestSteeringFileSmokeTests` to read from the reference file
    - Update `test_what_why_framing_all_levels` to read from the reference file (via `_read_reference_file()`) instead of the core file
    - Update `test_code_execution_framing_all_levels` to read from the reference file instead of the core file
    - Update `test_step_recap_framing_all_levels` to read from the reference file instead of the core file
    - All other existing smoke tests remain unchanged (they check content that stays in the core file)
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 7. Final checkpoint — Run full test suite
  - Run `pytest senzing-bootcamp/tests/test_verbosity_unit.py senzing-bootcamp/tests/test_verbosity_properties.py -v` and ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 7.1, 7.2_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- No property-based tests needed — this is deterministic file reorganization with no variable input spaces
- The existing property tests in `test_verbosity_properties.py` exercise `verbosity.py` (Python script), not steering file content, and require zero changes
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Core file must be ≤80 lines — count carefully including frontmatter and blank lines
- All original content must be preserved across both files — nothing removed, only reorganized
