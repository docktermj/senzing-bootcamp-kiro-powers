# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - v1 JSON Hooks Reported as Missing
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to hooks directory states where at least one capture-critical hook exists ONLY as `<id>.json` (not as `<id>.kiro.hook`) — the concrete failing cases where `isBugCondition` returns true
  - Write a property-based test in `senzing-bootcamp/tests/test_capture_hook_safeguard.py` that:
    - Creates a new strategy `st_v1_only_hooks_dir_state` drawing `HooksDirState`-like objects where at least one capture-critical hook exists only as `<id>.json` (no corresponding `<id>.kiro.hook`)
    - Materializes the hooks directory with `<id>.json` files for v1-only hooks
    - Calls `detect_missing_capture_hooks()` on the materialized directory
    - Asserts that hook ids present as `<id>.json` are NOT in the returned missing list (expected behavior from design)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists because the current code only checks `.kiro.hook` files)
  - Document counterexamples found (e.g., "detect_missing_capture_hooks() returns 'ask-bootcamper' even though ask-bootcamper.json exists in .kiro/hooks/")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.3, 2.1_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Legacy and True-Absence Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Write a property-based test in `senzing-bootcamp/tests/test_capture_hook_safeguard.py` that:
    - Creates a strategy `st_non_bug_condition_hooks_dir_state` drawing hooks directory states where the bug condition does NOT hold: every capture-critical hook either exists as `<id>.kiro.hook` or does not exist in either format (no hook exists only as `<id>.json`)
    - Materializes the hooks directory accordingly
    - Calls `detect_missing_capture_hooks()` on the UNFIXED code
    - Asserts that hooks present as `<id>.kiro.hook` are recognized as present (not in missing list)
    - Asserts that hooks absent in both formats are reported as missing
    - Asserts the return value is a sorted list
  - Observe behavior on UNFIXED code:
    - Observe: `detect_missing_capture_hooks(dir_with_ask-bootcamper.kiro.hook)` does NOT include "ask-bootcamper" in result
    - Observe: `detect_missing_capture_hooks(empty_dir)` returns all CAPTURE_CRITICAL ids sorted
    - Observe: `detect_missing_capture_hooks(nonexistent_dir)` returns all CAPTURE_CRITICAL ids sorted (OSError path)
  - Property: for all hooks directory states where NO hook exists only as `<id>.json`, the function correctly identifies missing hooks based on `.kiro.hook` presence (from Preservation Requirements in design)
  - Verify test passes on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for v1 JSON hooks falsely reported as missing

  - [x] 3.1 Implement the fix
    - Update the list comprehension in `detect_missing_capture_hooks()` (line ~133 of `senzing-bootcamp/scripts/capture_hook_safeguard.py`) to check for BOTH formats:
      ```python
      if not (hooks_dir / f"{hook_id}.json").is_file()
          and not (hooks_dir / f"{hook_id}.kiro.hook").is_file()
      ```
    - A hook is only considered missing when NEITHER `<id>.json` NOR `<id>.kiro.hook` exists
    - Update the function's docstring to document both filename patterns: replace references to only `<id>.kiro.hook` with documentation that both `<id>.json` (v1 format) and `<id>.kiro.hook` (legacy format) are checked
    - Update Args/Returns descriptions to reflect detection of either format
    - _Bug_Condition: isBugCondition(input) where EXISTS hook_id IN CAPTURE_CRITICAL WHERE (hooks_dir / f"{hook_id}.json").is_file() AND NOT (hooks_dir / f"{hook_id}.kiro.hook").is_file()_
    - _Expected_Behavior: For all hook_id where (hooks_dir / f"{hook_id}.json").is_file(), hook_id NOT IN detect_missing_capture_hooks(hooks_dir)_
    - _Preservation: For all inputs where NOT isBugCondition(input), detect_missing_capture_hooks(hooks_dir) produces identical results before and after fix_
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - v1 JSON Hooks Recognized as Present
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior: hook ids present as `<id>.json` should NOT appear in the missing list
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Legacy and True-Absence Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions): legacy `.kiro.hook` detection unchanged, true-absence reporting unchanged, OSError handling unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full test suite: `python -m pytest senzing-bootcamp/tests/test_capture_hook_safeguard.py`
  - Ensure all existing Property 1–5 tests from the original safeguard spec still pass (no regressions to detection, no-op, soft-block, acknowledgment, or recurrence behavior)
  - Ensure the new bug condition and preservation tests pass
  - Ask the user if questions arise
