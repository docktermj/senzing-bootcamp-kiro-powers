# Implementation Plan: Consolidate preToolUse Hooks

## Overview

Replace three separate preToolUse write hooks with a single consolidated hook to reduce visible noise from 3 interceptions to 1 per write operation.

## Tasks

- [x] 1. Create consolidated write-policy-gate hook
  - [x] 1.1 Read the current `block-direct-sql.kiro.hook`, `enforce-single-question.kiro.hook`, and `enforce-file-path-policies.kiro.hook` prompts to capture their exact logic
  - [x] 1.2 Create `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` with consolidated prompt combining all three policy checks (SQL blocking, single-question enforcement, file path policies) with explicit silent fast-path instructions and verbatim slow-path violation text from the originals
  - [x] 1.3 Verify the new hook file is valid JSON with required keys (`name`, `version`, `when`, `then`)
- [x] 2. Delete old hook files
  - [x] 2.1 Delete `senzing-bootcamp/hooks/block-direct-sql.kiro.hook`
  - [x] 2.2 Delete `senzing-bootcamp/hooks/enforce-single-question.kiro.hook`
  - [x] 2.3 Delete `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook`
- [x] 3. Update hook-categories.yaml
  - [x] 3.1 Replace `block-direct-sql`, `enforce-file-path-policies`, and `enforce-single-question` in the `critical` list with `write-policy-gate` in `senzing-bootcamp/hooks/hook-categories.yaml`
- [x] 4. Update steering registry files
  - [x] 4.1 Update `senzing-bootcamp/steering/hook-registry.md` to remove the three old hook rows and add one row for `write-policy-gate`
  - [x] 4.2 Update `senzing-bootcamp/steering/hook-registry-detail.md` to remove the three old detail sections and add one section for `write-policy-gate`
- [x] 5. Update onboarding and steering references
  - [x] 5.1 Update `senzing-bootcamp/steering/onboarding-flow.md` to replace the three hook installation table rows with one row for `write-policy-gate`
  - [x] 5.2 Update steering references in `senzing-bootcamp/steering/agent-instructions.md`, `senzing-bootcamp/steering/conversation-protocol.md`, and `senzing-bootcamp/steering/conversation-examples.md` to reference `write-policy-gate` instead of the individual hook names
- [x] 6. Update test files
  - [x] 6.1 Update `tests/test_hook_prompt_standards.py`: change `EXPECTED_HOOK_COUNT` from 29 to 27
  - [x] 6.2 Update `tests/test_suppress_policy_pass_output.py`: change `HOOK_PATH` to `Path("senzing-bootcamp/hooks/write-policy-gate.kiro.hook")`
  - [x] 6.3 Update `tests/hook_test_helpers.py`: replace `block-direct-sql`, `enforce-file-path-policies`, `enforce-single-question` in `CRITICAL_HOOKS` with `write-policy-gate`
- [x] 7. Run sync verification
  - [x] 7.1 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` and fix any sync issues
- [x] 8. Run full test suite
  - [x] 8.1 Run `pytest tests/ senzing-bootcamp/tests/ -v` and fix any test failures

## Notes

- The `ORIGINAL_SLOW_PATH_TEXT` constant in `test_suppress_policy_pass_output.py` must still match the file-path-policies slow-path section in the consolidated prompt — preserve that text verbatim.
- The `sync_hook_registry.py` script auto-generates `hook-registry-detail.md` from hook files, so Task 4.2 may be handled automatically by running the script in Task 7.
- Hook count changes from 29 to 27 (net -2: remove 3, add 1).
