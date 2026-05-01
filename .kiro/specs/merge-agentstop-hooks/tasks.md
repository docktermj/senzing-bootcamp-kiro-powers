# Implementation Plan: Merge agentStop Hooks

## Overview

Delete the redundant `enforce-wait-after-question` hook and update all configuration, registry, and test references to reflect 18 hooks instead of 19. The `ask-bootcamper` hook already contains all suppression logic, so no prompt changes are needed — this is purely a deletion + cleanup operation.

## Tasks

- [x] 1. Delete the redundant hook file and update hook categories config
  - [x] 1.1 Delete `senzing-bootcamp/hooks/enforce-wait-after-question.kiro.hook`
    - Remove the file entirely from the hooks directory
    - After deletion, the hooks directory should contain exactly 18 `.kiro.hook` files
    - _Requirements: 2.1, 2.2_
  - [x] 1.2 Remove `enforce-wait-after-question` from `senzing-bootcamp/hooks/hook-categories.yaml`
    - Remove the `- enforce-wait-after-question` line from the `critical` section
    - The `critical` section should list exactly 7 hook IDs after the change
    - The total hook count across all categories should be 18
    - Do not modify the `modules` section
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 2. Regenerate the hook registry
  - [x] 2.1 Run `sync_hook_registry.py --write` to regenerate `senzing-bootcamp/steering/hook-registry.md`
    - Execute: `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write`
    - The regenerated registry should report "All 18 bootcamp hooks" in its introductory paragraph
    - The registry should contain no reference to `enforce-wait-after-question`
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Update test suites to expect 18 hooks
  - [x] 3.1 Update `EXPECTED_HOOK_COUNT` in `tests/test_hook_prompt_standards.py`
    - Change `EXPECTED_HOOK_COUNT = 19` to `EXPECTED_HOOK_COUNT = 18`
    - Update the `test_hook_file_count_is_18` assertion from `== 19` to `== 18`
    - Update the `test_registry_entry_count_is_18` assertion from `== 19` to `== 18`
    - Update docstrings that reference "19" to reference "18" (e.g., "All 19 real hook files" → "All 18 real hook files", "exactly 19" → "exactly 18")
    - _Requirements: 5.1, 5.3_
  - [x] 3.2 Update count assertions in `senzing-bootcamp/tests/test_sync_hook_registry_unit.py`
    - In `test_all_18_hooks_parse_without_errors`: change `len(entries) == 19` to `len(entries) == 18`
    - In `test_load_real_categories`: change `len(mapping) == 19` to `len(mapping) == 18`
    - Update docstrings and comments that reference "19" to reference "18"
    - _Requirements: 5.2, 5.3_

- [x] 4. Checkpoint — Verify sync and run tests
  - [x] 4.1 Run `sync_hook_registry.py --verify` and confirm exit code 0
    - Execute: `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    - The script must exit with code 0, confirming the on-disk registry matches the generated output
    - _Requirements: 4.4, 7.1_
  - [x] 4.2 Run the full test suite and confirm zero failures
    - Execute: `python3 -m pytest tests/ senzing-bootcamp/tests/ -v`
    - All tests must pass with zero failures
    - _Requirements: 5.3, 7.2_
  - [x] 4.3 Grep for stale references to `enforce-wait-after-question` across the repo
    - Execute: `grep -r "enforce-wait-after-question" --include="*.py" --include="*.md" --include="*.yaml" --include="*.yml" --include="*.hook" . | grep -v ".kiro/specs/"`
    - Expect zero matches outside the `.kiro/specs/` directory
    - If any stale references are found, remove or update them
    - _Requirements: 6.1, 6.2_
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- The `ask-bootcamper.kiro.hook` file is NOT modified — it already contains all suppression logic
- The `agent-instructions.md` steering file does NOT reference the deleted hook (verified in design)
- The `sync_hook_registry.py` script is generic and needs no code changes
- No property-based tests apply — this is a configuration cleanup with deterministic, finite changes
