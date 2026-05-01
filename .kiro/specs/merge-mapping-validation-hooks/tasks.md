# Implementation Plan: Merge Mapping Validation Hooks

## Overview

Merge two overlapping Module 5 hooks into one: enhance `analyze-after-mapping` (fileCreated) to include Entity Spec conformance checks from `validate-senzing-json` (fileEdited), then delete `validate-senzing-json` and update all references across the power. Net result: 19 hooks → 18 hooks.

**Parallel spec dependency:** The `merge-agentstop-hooks` spec also reduces hook count by 1 (removing `enforce-wait-after-question`). If that spec is applied first, all count values in this plan (19 → 18) must be adjusted to (18 → 17). The tasks below assume this spec is applied against the current baseline of 19 hooks.

## Tasks

- [x] 1. Enhance the analyze-after-mapping hook and delete validate-senzing-json
  - [x] 1.1 Update the `analyze-after-mapping.kiro.hook` prompt and description
    - Update the `description` field to reflect the expanded scope: validation of both quality metrics and Entity Spec conformance
    - Append to the `prompt` field: "Also verify that records conform to the Senzing Generic Entity Specification."
    - Retain the existing `fileCreated` event type with patterns `["data/transformed/*.jsonl", "data/transformed/*.json"]`
    - Retain the `askAgent` action type
    - Ensure the file remains valid JSON
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 1.2 Delete `senzing-bootcamp/hooks/validate-senzing-json.kiro.hook`
    - Remove the file entirely from the hooks directory
    - After deletion, the hooks directory should contain exactly 18 `.kiro.hook` files
    - _Requirements: 2.1, 2.2_

- [x] 2. Update hook categories and regenerate the registry
  - [x] 2.1 Remove `validate-senzing-json` from `senzing-bootcamp/hooks/hook-categories.yaml`
    - Remove the `- validate-senzing-json` line from the `modules.5` section
    - The Module 5 section should list exactly 2 hook IDs after the change: `analyze-after-mapping` and `data-quality-check`
    - Do not modify any other section
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 2.2 Run `sync_hook_registry.py --write` to regenerate `senzing-bootcamp/steering/hook-registry.md`
    - Execute: `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write`
    - The regenerated registry should report "All 18 bootcamp hooks" in its introductory paragraph
    - The registry should contain `analyze-after-mapping` with the enhanced prompt
    - The registry should contain no reference to `validate-senzing-json`
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Checkpoint — Verify registry sync
  - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` and confirm exit code 0
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update documentation files
  - [x] 4.1 Update `senzing-bootcamp/hooks/README.md`
    - Remove the entire section for hook #4 (`Validate Senzing JSON`)
    - Renumber all subsequent hook sections to maintain a sequential, gap-free list (1 through 17)
    - Update the `Analyze After Mapping` section description to reflect the enhanced scope (quality checks + Entity Spec conformance)
    - In the "Recommended Hooks by Module" → "Module 5" list, remove `Validate Senzing JSON` and keep `Analyze After Mapping`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 4.2 Update `senzing-bootcamp/scripts/install_hooks.py`
    - Remove the `("validate-senzing-json.kiro.hook", "Validate Senzing JSON", ...)` tuple from the `HOOKS` list
    - Update the `("analyze-after-mapping.kiro.hook", "Analyze After Mapping", ...)` tuple's description to reflect the enhanced validation scope (quality checks + Entity Spec conformance)
    - _Requirements: 6.1, 6.2_
  - [x] 4.3 Update `senzing-bootcamp/POWER.md`
    - In the "Recommended Hooks" section's `Available:` list, remove `validate-senzing-json`
    - Keep `analyze-after-mapping` in the list
    - _Requirements: 7.1, 7.2_

- [x] 5. Update test files
  - [x] 5.1 Update `senzing-bootcamp/tests/test_silent_hook_processing.py`
    - Remove `"validate-senzing-json"` from the `_NON_AFFECTED_HOOK_IDS` list
    - Verify `"analyze-after-mapping"` remains in the list
    - _Requirements: 8.1, 8.2_
  - [x] 5.2 Update count assertions in `senzing-bootcamp/tests/test_sync_hook_registry_unit.py`
    - In `test_all_18_hooks_parse_without_errors`: change `len(entries) == 19` to `len(entries) == 18`
    - In `test_load_real_categories`: change `len(mapping) == 19` to `len(mapping) == 18`
    - Update docstrings and comments that reference "19" to reference "18"
    - _Requirements: 8.3_
  - [x] 5.3 Update `EXPECTED_HOOK_COUNT` in `tests/test_hook_prompt_standards.py`
    - Change `EXPECTED_HOOK_COUNT = 19` to `EXPECTED_HOOK_COUNT = 18`
    - Update the `test_hook_file_count_is_18` assertion from `== 19` to `== 18`
    - Update the `test_registry_entry_count_is_18` assertion from `== 19` to `== 18`
    - Update docstrings that reference "19" to reference "18" (e.g., "All 19 real hook files" → "All 18 real hook files", "exactly 19" → "exactly 18")
    - _Requirements: 8.3_

- [x] 6. Checkpoint — Run full test suite
  - [x] 6.1 Run `sync_hook_registry.py --verify` and confirm exit code 0
    - Execute: `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    - _Requirements: 4.4, 9.1_
  - [x] 6.2 Run the full test suite and confirm zero failures
    - Execute: `python3 -m pytest tests/ senzing-bootcamp/tests/ -v`
    - All tests must pass with zero failures
    - _Requirements: 8.3, 9.2_
  - [x] 6.3 Grep for stale references to `validate-senzing-json` across the repo
    - Execute: `grep -r "validate-senzing-json" --include="*.py" --include="*.md" --include="*.yaml" --include="*.yml" --include="*.hook" . | grep -v ".kiro/specs/"`
    - Expect zero matches outside the `.kiro/specs/` directory
    - If any stale references are found, remove or update them
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Write property-based tests for correctness properties
  - [x] 7.1 Create `senzing-bootcamp/tests/test_merge_mapping_validation_hooks.py` with test scaffolding
    - Import Hypothesis, pytest, Path, json, re, and yaml parsing utilities
    - Define constants for hooks directory, categories path, registry path, and README path
    - Define the set of hook IDs that should be preserved (all 18 non-removed hooks)
    - _Requirements: 3.3, 4.3, 5.4_
  - [ ]* 7.2 Write property test for category preservation (Property 1)
    - **Property 1: Category preservation for non-removed hooks**
    - For any hook ID that existed in `hook-categories.yaml` before the merge and is not `validate-senzing-json`, that hook ID is still present with the same category and module assignment
    - Use `@given(hook_id=st.sampled_from(preserved_hook_ids))` with `@settings(max_examples=100)`
    - Parse `hook-categories.yaml` and verify the sampled hook retains its category (`critical` or `module`) and module number
    - **Validates: Requirements 3.3**
  - [ ]* 7.3 Write property test for registry preservation (Property 2)
    - **Property 2: Registry entry preservation for non-removed hooks**
    - For any hook ID that existed in `hook-registry.md` before the merge and is not `validate-senzing-json`, that hook's registry section is present and contains the expected id, name, and description
    - Use `@given(hook_id=st.sampled_from(preserved_hook_ids))` with `@settings(max_examples=100)`
    - Parse `hook-registry.md` and verify the sampled hook's entry exists with correct metadata
    - **Validates: Requirements 4.3**
  - [ ]* 7.4 Write example-based test for sequential README numbering (Property 3)
    - **Property 3: README hook numbering is sequential**
    - Parse all `### N.` section headers from `hooks/README.md`
    - Verify the numbers form a contiguous sequence from 1 to N with no gaps
    - Verify N equals the total number of hook sections (17 after removal)
    - **Validates: Requirements 5.4**
  - [ ]* 7.5 Write example-based tests for validate-senzing-json absence
    - Verify `validate-senzing-json.kiro.hook` file does not exist
    - Verify `hook-categories.yaml` does not contain `validate-senzing-json`
    - Verify `hook-registry.md` does not contain `validate-senzing-json`
    - Verify `hooks/README.md` does not contain `validate-senzing-json` section
    - Verify `install_hooks.py` does not contain `validate-senzing-json`
    - Verify `POWER.md` does not contain `validate-senzing-json`
    - **Validates: Requirements 2.1, 3.2, 4.2, 5.2, 6.2, 7.2**

- [x] 8. Final checkpoint — Run full test suite including PBT
  - Execute: `python3 -m pytest tests/ senzing-bootcamp/tests/ -v`
  - All tests must pass with zero failures, including the new property-based tests
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The `sync_hook_registry.py` script is generic and needs no code changes — it regenerates from source-of-truth hook files
- **Parallel spec dependency:** If `merge-agentstop-hooks` is applied first, adjust all hook counts: 19 → 18 becomes 18 → 17, and EXPECTED_HOOK_COUNT targets 17 instead of 18
