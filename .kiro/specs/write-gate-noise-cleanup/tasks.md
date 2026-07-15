# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - No Stale/Unwanted Write-Gate Output
  - **CRITICAL**: This test MUST FAIL on fixed code — failure confirms the stale content has been removed and the new rule added
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the *defective* state — it will FAIL after the fix is applied (confirming the bug is gone)
  - **GOAL**: Surface counterexamples that demonstrate the bug exists on UNFIXED code
  - **Test file**: `tests/test_write_gate_noise_cleanup.py`
  - **Test class**: `class TestBugConditionExploration`
  - **Scoped PBT Approach**: Two concrete property assertions:
    - Parse `senzing-bootcamp/steering/onboarding-flow.md` and assert section heading `## 0a. Why You May See "Rejected"/"Accepted" Messages` exists (confirms Defect 1 — stale content present)
    - Parse `senzing-bootcamp/steering/agent-behavior-rules.md` and assert NO rule explicitly prohibits narration/visible tokens on internal-file pass-through re-invokes (confirms Defect 2 — steering gap)
  - Bug condition from design: `isBugCondition(input)` where `staleOnboardingNote := input.note_present = TRUE` OR `narratedSilentReinvoke := input.emitted_tokens != EMPTY`
  - Run test on UNFIXED code — expect PASS (confirms both defects exist)
  - After fix: tests FAIL (confirms stale section removed and new rule present)
  - Document counterexamples found (e.g., "Section '0a' found at line N describing behavior that no longer occurs")
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Legitimate Gate Behavior and Other Onboarding Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **Test file**: `tests/test_write_gate_noise_cleanup.py`
  - **Test class**: `class TestPreservation`
  - Observe on UNFIXED code then write property-based tests:
    - **Onboarding sections preserved**: All non-0a sections in `onboarding-flow.md` (0. Setup Preamble, 0b. MCP Health Check, 0c. Version Display, 1. Directory Structure, 1b. Team Detection, 2. Prerequisite Check) exist and their content is unchanged
    - **Hook file integrity**: `senzing-bootcamp/hooks/write-policy-gate.json` is byte-for-byte unchanged (SHA-256 or content comparison)
    - **Agent behavior rules additive-only**: Rules 1–4 in `agent-behavior-rules.md` are unchanged; only a new Rule 5 is appended
    - **Hypothesis strategy**: Generate random indices into the list of preserved onboarding section headings and verify each is present with unchanged content
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for write-gate noise cleanup (steering edits + test updates)

  - [x] 3.1 Remove stale onboarding section from `senzing-bootcamp/steering/onboarding-flow.md`
    - Delete the entire `## 0a. Why You May See "Rejected"/"Accepted" Messages` section (heading + all body content through end of section, stopping before `## 0b. MCP Health Check`)
    - Approximately 12 lines of stale content to remove
    - _Bug_Condition: isBugCondition(input) where input.note_present = TRUE_
    - _Expected_Behavior: onboarding_content SHALL NOT contain the stale "Rejected/Accepted" reassurance note_
    - _Preservation: All other onboarding content (0, 0b, 0c, 1, 1b, 2) unchanged_
    - _Requirements: 2.1, 3.4_

  - [x] 3.2 Add Rule 5 to `senzing-bootcamp/steering/agent-behavior-rules.md`
    - Append a new Rule 5 section after Rule 4
    - Rule explicitly prohibits the agent from emitting any visible tokens (narration, acknowledgment, explanation) when re-invoking a write after the `write-policy-gate` INTERNAL-FILE PASS-THROUGH applies
    - Reinforces the hook's "ZERO tokens" mandate at the agent steering level
    - _Bug_Condition: isBugCondition(input) where input.emitted_tokens != EMPTY on pass-through_
    - _Expected_Behavior: agent SHALL produce zero visible tokens on internal-file pass-through re-invoke_
    - _Preservation: Rules 1–4 unchanged; Rule 5 is purely additive_
    - _Requirements: 2.2, 3.3_

  - [x] 3.3 Remove stale test methods from `tests/test_write_policy_gate_integration.py`
    - Remove test methods (lines ~372–456) that assert section "0a" exists, appears before later sections, is near the start, follows the setup preamble, and contains reassuring content
    - These tests validate content being intentionally removed — they would now fail
    - Methods to remove: `test_explanation_section_exists`, `test_explanation_appears_before_later_sections`, `test_explanation_is_near_the_start`, `test_explanation_follows_setup_preamble`, `test_explanation_content_reassures_bootcamper`
    - If these methods are the only members of their test class, remove the entire class and its `_load_doc` helper
    - _Requirements: 2.1_

  - [x] 3.4 Update `_EXPECTED_HEADINGS` in `senzing-bootcamp/tests/test_onboarding_question_ownership.py`
    - Remove the entry `'0a. Why You May See "Rejected"/"Accepted" Messages'` from the `_EXPECTED_HEADINGS` list (around line 290)
    - Remove the associated comment explaining the entry (the 3-line comment block above it)
    - _Requirements: 2.1_

  - [x] 3.5 Verify bug condition exploration test now fails (confirming fix works)
    - **Property 1: Expected Behavior** - No Stale/Unwanted Write-Gate Output
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 asserts the defective state exists; after the fix, those assertions fail
    - When the exploration test FAILS, it confirms the stale section is gone and the new rule is present
    - Run `pytest tests/test_write_gate_noise_cleanup.py::TestBugConditionExploration`
    - **EXPECTED OUTCOME**: Test FAILS (confirms bug is fixed — stale content removed, rule added)
    - _Requirements: 2.1, 2.2_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Legitimate Gate Behavior and Other Onboarding Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run `pytest tests/test_write_gate_noise_cleanup.py::TestPreservation`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation properties hold: non-0a sections unchanged, hook file unchanged, Rules 1–4 unchanged

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `python -m pytest senzing-bootcamp/tests/ tests/`
  - Verify no regressions in existing test files
  - Confirm `write-policy-gate.json` was NOT modified (security constraint)
  - Ask the user if questions arise
