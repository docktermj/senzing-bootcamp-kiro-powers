# Implementation Plan

## Overview

Fix the `write-policy-gate` preToolUse hook to produce zero visible output when the fast path passes. The hook prompt currently instructs the agent to output "policy: pass" text, causing visible clutter in the bootcamper's chat. The fix modifies the prompt in `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` to suppress all visible output on the fast path while preserving all slow-path violation-detection behavior.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Fast Path Produces Visible Output
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the hook prompt instructs visible output on the fast path
  - **Scoped PBT Approach**: Scope the property to the concrete failing patterns: prompt contains "output exactly...policy...pass" or "Just output: policy: pass" reinforcement that instructs the agent to produce visible text when the fast path passes
  - Test file: `tests/test_hook_silent_fast_path_properties.py` class `TestBugConditionExploration`
  - Property test 1a: For any project-relative file path (generated via Hypothesis), assert the prompt does NOT contain an instruction like "output exactly" followed by "policy...pass" that tells the agent to produce visible text on the fast path
  - Property test 1b: For any project-relative file path, assert the prompt does NOT contain "Just output: policy: pass" reinforcement
  - Property test 1c: For any project-relative file path, assert the prompt CONTAINS a genuine silent-processing instruction (e.g., "do not acknowledge.*do not explain.*do not print" or "produce no output at all") without any contradicting "output exactly...policy: pass" instruction
  - Property test 1d: Assert the prompt does NOT contain narration-encouraging patterns like "output.*fast path" or "respond.*policy.*pass" that would cause the agent to summarize its evaluation
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct - it proves the bug exists by showing the prompt instructs visible output)
  - Document counterexamples found (e.g., "prompt contains 'Just output: policy: pass'" or "prompt contains 'output exactly' followed by policy pass instruction")
  - Mark task complete when tests are written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Violation Detection Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Test file: `tests/test_hook_silent_fast_path_properties.py` class `TestPreservationProperties`
  - Observe on UNFIXED code: the SLOW PATH section contains "STOP" and "project-relative equivalents" for external path blocking
  - Observe on UNFIXED code: the prompt contains "⚠️ COMPOUND QUESTION DETECTED" output format for compound question violations
  - Observe on UNFIXED code: the prompt contains "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" redirect for misrouted feedback
  - Observe on UNFIXED code: the prompt contains all Senzing SQL blocking instructions with SDK method alternatives
  - Observe on UNFIXED code: hook JSON has all required fields (name, version, description, when.type=preToolUse, when.toolTypes=["write"], then.type=askAgent, then.prompt non-empty)
  - Property test 2a: For any generated external path prefix (/tmp/, %TEMP%, ~/Downloads), the prompt SLOW PATH section contains "STOP" and blocking instructions
  - Property test 2b: For any non-canonical feedback path, the prompt contains redirect to canonical feedback path
  - Property test 2c: For any required hook JSON field, the structure contains it with valid values
  - Property test 2d: For any project-relative file path, the SLOW PATH section text is identical to the captured baseline from unfixed code
  - Property test 2e: For any Senzing database indicator (G2C.db, RES_ENT, OBS_ENT, etc.), the prompt contains SQL blocking instructions referencing it
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix write-policy-gate hook prompt for silent fast path

  - [x] 3.1 Implement the fix in `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`
    - Remove any "output exactly...policy: pass" instruction from the fast-path section
    - Remove any "Just output: policy: pass" reinforcement line
    - Strengthen the FAST PATH GATE silence directive with explicit zero-output markers (e.g., "OUTPUT: (none)" or "Your response when fast path passes: [empty — produce zero tokens]")
    - Add explicit anti-narration instruction: "Do NOT output phrases like 'Fast path passes', 'Proceeding', 'All checks pass', or any summary of your evaluation. Zero tokens means zero tokens."
    - Consolidate fast-path exit to be the single authoritative silent exit point
    - Preserve ALL slow-path text verbatim (SQL blocking, compound question format, external path blocking, feedback redirect, content check)
    - _Bug_Condition: isBugCondition(input) where input.hook_name = "write-policy-gate" AND target_path IS INSIDE working_directory AND NOT endsWith(target_path, ".question_pending") AND NOT (containsSqlPatterns(content) AND containsSenzingDbIndicators(content))_
    - _Expected_Behavior: output.visible_chat_text = EMPTY AND output.write_operation_proceeds = TRUE_
    - _Preservation: All slow-path sections (SQL blocking, compound question enforcement, external path blocking, feedback redirect, content path checking) remain character-for-character identical_
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Zero Visible Output on Fast Path Pass
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (no "policy: pass" output instruction, genuine silent-processing directive present, no narration-encouraging patterns)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1: `pytest tests/test_hook_silent_fast_path_properties.py::TestBugConditionExploration -v`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Violation Detection Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2: `pytest tests/test_hook_silent_fast_path_properties.py::TestPreservationProperties -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all slow-path sections remain identical after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest tests/test_hook_silent_fast_path_properties.py -v`
  - Verify both bug condition exploration tests and preservation tests pass
  - Run existing related test: `pytest tests/test_suppress_policy_pass_output.py -v` to confirm no conflicts
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tests validate the hook prompt text (the artifact we control) rather than agent runtime behavior (which cannot be deterministically tested)
- The existing `tests/test_suppress_policy_pass_output.py` covers similar ground — the new test file focuses specifically on the silent fast-path property and may share patterns
- All tests use pytest + Hypothesis following the project's PBT conventions with `@settings(max_examples=20)`
- Hook tests validating real hook files go in repo-root `tests/`, not `senzing-bootcamp/tests/`
