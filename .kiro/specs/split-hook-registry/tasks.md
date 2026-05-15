# Implementation Plan: Split hook-registry.md Below Token Threshold

## Overview

Split the monolithic `hook-registry.md` (8,307 tokens) into a summary file (hook IDs + descriptions in tables) and a detail file (full prompts for `createHook`). Update `sync_hook_registry.py` to generate both, update `steering-index.yaml`, fix references, and update tests.

## Tasks

- [x] 1. Update sync_hook_registry.py to generate both files
  - [x] 1.1 Add a `generate_registry_summary()` function to `senzing-bootcamp/scripts/sync_hook_registry.py` that produces a table-based summary with columns: Hook ID, Event Type, Description for critical hooks and Hook ID, Module, Event Type, Description for module hooks — target under 2,500 tokens
  - [x] 1.2 Rename the existing `generate_registry()` function to `generate_registry_detail()` and update its title/intro to say "Hook Registry — Full Prompts" with a cross-reference to the summary file
  - [x] 1.3 Add a `REGISTRY_DETAIL_PATH` constant pointing to `senzing-bootcamp/steering/hook-registry-detail.md`
  - [x] 1.4 Update `main()` to generate and write both files: summary to `REGISTRY_PATH` and detail to `REGISTRY_DETAIL_PATH`
  - [x] 1.5 Update `--verify` mode to verify both files against their generated content
  - [x] 1.6 Add `--output-detail` CLI argument (default: `REGISTRY_DETAIL_PATH`) for the detail file path
    - _Requirements: 1, 2, 3, 8_

- [x] 2. Generate the split files
  - [x] 2.1 Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write` to generate both `hook-registry.md` (summary) and `hook-registry-detail.md` (detail)
  - [x] 2.2 Verify the summary file is under 2,500 tokens by running `python3 senzing-bootcamp/scripts/measure_steering.py` and checking the output
  - [x] 2.3 Verify the detail file is under 7,000 tokens (acceptable for manual-inclusion files loaded once per session)
    - _Requirements: 1, 2, 3, 5_

- [x] 3. Update steering-index.yaml
  - [x] 3.1 In `senzing-bootcamp/steering/steering-index.yaml`, update the `file_metadata` entry for `hook-registry.md` with the new (lower) token count and size_category
  - [x] 3.2 Add a new `file_metadata` entry for `hook-registry-detail.md` with its token count and size_category
  - [x] 3.3 Verify the `keywords` section still has `hook: hook-registry.md` and `hooks: hook-registry.md` (pointing to the summary)
    - _Requirements: 4, 5, 6_

- [x] 4. Update file references
  - [x] 4.1 In `senzing-bootcamp/steering/onboarding-flow.md`, change the `#[[file:]]` reference from `hook-registry.md` to `hook-registry-detail.md` (onboarding needs full prompts for createHook)
  - [x] 4.2 In `senzing-bootcamp/docs/guides/HOOKS_INSTALLATION_GUIDE.md`, update the reference to mention both files (summary for overview, detail for full prompts)
  - [x] 4.3 In `senzing-bootcamp/hooks/README.md`, update references to mention both `hook-registry.md` (summary) and `hook-registry-detail.md` (full prompts)
    - _Requirements: 7_

- [x] 5. Update tests referencing hook-registry.md
  - [x] 5.1 In `senzing-bootcamp/tests/test_silent_hook_architecture.py`, update the registry path from `hook-registry.md` to `hook-registry-detail.md` (this test checks prompt content)
  - [x] 5.2 In `senzing-bootcamp/tests/test_silent_hook_processing.py`, update `_HOOK_REGISTRY` path from `hook-registry.md` to `hook-registry-detail.md` (this test checks prompt content)
  - [x] 5.3 In `senzing-bootcamp/tests/test_conversational_hook_names.py`, update `_REGISTRY_PATH` from `hook-registry.md` to `hook-registry-detail.md` (this test checks name matching against prompts)
  - [x] 5.4 In `senzing-bootcamp/tests/test_track_selection_gate_bug.py`, update `_HOOK_REGISTRY` path from `hook-registry.md` to `hook-registry-detail.md` (this test checks prompt content)
  - [x] 5.5 In `senzing-bootcamp/scripts/test_hooks.py`, update `REGISTRY_PATH` from `hook-registry.md` to `hook-registry-detail.md` (this test validates hook IDs against registry)
  - [x] 5.6 In `senzing-bootcamp/scripts/lint_steering.py`, update the `check_hook_consistency` function to read from `hook-registry-detail.md` instead of `hook-registry.md` for hook ID extraction
    - _Requirements: 11_

- [x] 6. Run validation suite
  - [x] 6.1 Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` and verify exit code 0 (both files in sync)
  - [x] 6.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` and verify both new files pass
  - [x] 6.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` and verify no budget violations
  - [x] 6.4 Run `python3 -m pytest senzing-bootcamp/tests/test_silent_hook_architecture.py senzing-bootcamp/tests/test_silent_hook_processing.py senzing-bootcamp/tests/test_conversational_hook_names.py senzing-bootcamp/tests/test_track_selection_gate_bug.py -v` and verify all pass
  - [x] 6.5 Run `python3 -m pytest senzing-bootcamp/scripts/test_hooks.py -v` and verify all pass
    - _Requirements: 9, 10, 11_

## Notes

- The detail file (~6,500 tokens) exceeds the 5,000-token split threshold but is acceptable because it uses manual inclusion and is loaded only during hook creation (once per session). Further splitting would fragment hook definitions across 3+ files.
- The summary file targets ~2,000 tokens — well under the threshold and efficient for keyword-routed loading.
- `sync_hook_registry.py` remains the single source of truth — both files are generated from `.kiro.hook` JSON files.
- The `#[[file:]]` reference in `onboarding-flow.md` must point to the detail file since the agent needs full prompts to call `createHook`.
- Tests that check prompt content must read the detail file; tests that only check hook IDs can use either file.
- No new test files are needed — existing tests are updated to point to the correct file.
