# Implementation Plan

## Overview

This plan fixes the dead-end remediation path in `senzing-bootcamp/hooks/verify-sdk-setup.kiro.hook`. The hook's `then.prompt` recommends `python3 senzing-bootcamp/scripts/preflight.py`, a path that does not resolve in the bootcamper's workspace. The fix is a single-string edit repointing it to `python3 src/scripts/verify_sdk.py`. Following the bug condition methodology, an exploratory bug-condition test surfaces a counterexample on the unfixed hook, preservation tests capture baseline behavior, the fix is applied, and both fix-checking and preservation-checking tests confirm correctness with no regressions.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Remediation Path Resolves In Workspace
  - **CRITICAL**: This test MUST FAIL on the unfixed hook - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the hook when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface a counterexample demonstrating the unresolvable `senzing-bootcamp/scripts/preflight.py` remediation path
  - **Scoped PBT Approach**: This is a deterministic, single-file defect; scope the property to the concrete `then.prompt` of `verify-sdk-setup.kiro.hook` so the counterexample is reproducible
  - Place the test in repo-root `tests/` (e.g., `tests/test_verify_sdk_hook_dead_end_path.py`), class-based (`class TestVerifySdkRemediationPath:`)
  - Load the real hook via `hook_test_helpers.load_hook(Path("senzing-bootcamp/hooks/verify-sdk-setup.kiro.hook"))`
  - Assert `then.prompt` does NOT contain `senzing-bootcamp/scripts/preflight.py` (fails on unfixed code)
  - Assert `then.prompt` contains `src/scripts/verify_sdk.py` (fails on unfixed code)
  - Assert no `senzing-bootcamp/scripts/` substring remains anywhere in `then.prompt` (edge case from design)
  - Use Hypothesis `@settings(max_examples=20)` where a generated input domain applies (e.g., generated path-resolution checks asserting the recommended path never matches the power-relative `senzing-bootcamp/scripts/...` form)
  - Run the test on the UNFIXED hook
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document the counterexample found (e.g., "`then.prompt` contains `python3 senzing-bootcamp/scripts/preflight.py`, which does not resolve in the bootcamper workspace")
  - Mark task complete when the test is written, run, and the failure is documented
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Verification, Gating, and Trigger Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology - observe behavior on the UNFIXED hook, then encode it
  - Place the tests in repo-root `tests/` (same module or a sibling `class TestVerifySdkPreservation:`), class-based
  - Load the real hook via `hook_test_helpers.load_hook` and capture the original `then.prompt` and `when` block before any fix
  - Observe and assert (passes on UNFIXED code):
    - `when.patterns` equals exactly `["config/senzing_config.*", "config/bootcamp_preferences.yaml", "database/*.*"]` (Req 3.4)
    - `when.type` == `fileEdited` (Req 3.4)
    - `then.prompt` contains the Module 2 gating phrase "If the bootcamper is in Module 2 (SDK Setup)" and the "If not in Module 2, produce no output" branch (Req 3.3)
    - `then.prompt` contains "database/G2C.db exists and is accessible" and "the Senzing engine can initialize with the current config" (Req 3.1)
    - `then.prompt` contains "If verification fails, present the error" (Req 3.2)
    - Hook has required fields `name`, `version`, `description`, `when`, `then`; `then.type` == `askAgent`; `then.prompt` is a non-empty string; file parses as valid JSON
  - Use Hypothesis `@settings(max_examples=20)` over generated module-context inputs ("in Module 2" / "not in Module 2") asserting the gating/verification phrases remain present and invariant
  - Run the tests on the UNFIXED hook
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on the unfixed hook
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix the dead-end remediation path in verify-sdk-setup hook

  - [x] 3.1 Repoint the remediation command in `then.prompt`
    - Edit `senzing-bootcamp/hooks/verify-sdk-setup.kiro.hook`, field `then.prompt`
    - Replace `python3 senzing-bootcamp/scripts/preflight.py` with `python3 src/scripts/verify_sdk.py`
    - Preserve all other `then.prompt` text verbatim (Module 2 gating, the `database/G2C.db` accessibility check, the engine-initialization check, the "produce no output" branch, and "If verification fails, present the error and")
    - Leave the `when` block untouched: `when.type` stays `fileEdited`; `when.patterns` stays `["config/senzing_config.*", "config/bootcamp_preferences.yaml", "database/*.*"]`
    - Leave schema fields untouched: `name`, `version`, `description`, `then.type` (`askAgent`); file remains valid JSON conforming to the hook schema
    - No new files, no MCP URL changes, no new dependencies (single-string edit only)
    - _Bug_Condition: isBugCondition(X) where X.recommendedScriptPath = `senzing-bootcamp/scripts/preflight.py` and NOT pathResolvesInBootcamperWorkspace(X.recommendedScriptPath)_
    - _Expected_Behavior: emitFailureGuidance'(X) recommends a command whose script path (`src/scripts/verify_sdk.py`) resolves in the bootcamper workspace_
    - _Preservation: Preservation Requirements from design - trigger patterns, Module 2 gating, verification checks, genuine-failure detection/reporting, and hook JSON schema unchanged_
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Remediation Path Resolves In Workspace
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes, it confirms the workspace-resolvable remediation path
    - Run the bug condition exploration test from task 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms the bug is fixed - `then.prompt` recommends `src/scripts/verify_sdk.py` and no longer references `senzing-bootcamp/scripts/preflight.py`)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Verification, Gating, and Trigger Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from task 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions; the only permitted delta is the remediation path substring)
    - Optionally assert the prompt diff is exactly `senzing-bootcamp/scripts/preflight.py` → `src/scripts/verify_sdk.py` (design Preservation test case 6)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Run CI structural and registry verifications
  - [x] 4.1 Run hook schema and structural suites
    - Run `pytest tests/test_hook_schema_conformance.py` to confirm the edited hook still passes schema conformance
    - Run `pytest tests/test_hook_structural_validation.py` to confirm structural validation passes
    - Run `pytest tests/test_hook_prompt_standards.py` to confirm no regression in prompt standards
    - **EXPECTED OUTCOME**: All suites pass (schema fields, `when` block, and `then.type` are unchanged)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 4.2 Verify hook registry sync
    - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    - **EXPECTED OUTCOME**: Verification passes, since `name`, `version`, and `when` are unchanged
    - _Requirements: 3.4_

- [x] 5. Checkpoint - Ensure all tests pass
  - Run the full hook test set (tasks 1-2 tests plus the CI suites in task 4)
  - Confirm the Property 1 exploration test now passes, Property 2 preservation tests pass, and all structural/registry verifications pass
  - Ensure all tests pass; ask the user if questions arise

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"],
      "description": "Pre-fix tests: task 1 (bug condition exploration) must FAIL on the unfixed hook; task 2 (preservation) must PASS on the unfixed hook. Independent, can run in parallel."
    },
    {
      "wave": 2,
      "tasks": ["3.1"],
      "description": "Apply the fix: repoint the then.prompt remediation path. Depends on tasks 1 and 2."
    },
    {
      "wave": 3,
      "tasks": ["3.2", "3.3"],
      "description": "Re-run task 1 test (now PASSES) and task 2 tests (still PASS). Depend on task 3.1, can run in parallel."
    },
    {
      "wave": 4,
      "tasks": ["4.1", "4.2"],
      "description": "CI structural/schema/prompt-standards suites and hook registry sync verification. Depend on the fix, can run in parallel."
    },
    {
      "wave": 5,
      "tasks": ["5"],
      "description": "Final checkpoint gate, depends on all prior tasks passing."
    }
  ]
}
```

- Tasks 1 and 2 are independent and must both complete before the fix (task 3.1).
- Task 3.1 must precede the verification sub-tasks 3.2 and 3.3.
- Tasks 4.1 and 4.2 run after the fix and can run in parallel.
- Task 5 is the final gate, depending on all prior tasks.

## Notes

- Tasks 1 and 2 are written and run BEFORE the fix: task 1 must FAIL (proving the bug), task 2 must PASS (capturing baseline behavior to preserve).
- The fix is a single-string edit to `then.prompt`; all other hook fields (`name`, `version`, `description`, `when`, `then.type`) stay byte-for-byte identical.
- Hook tests validating the real hook file live in repo-root `tests/`, not `senzing-bootcamp/tests/`, per the workspace structure rule.
- Tests are class-based and use Hypothesis `@settings(max_examples=20)` where a generated input domain applies, loading the hook via `hook_test_helpers.load_hook`.
- No new files, no MCP URL changes, and no new dependencies are introduced.
