# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Dual Stop Hook Visibility and Narration Leak
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate both bug disjuncts exist
  - **Scoped PBT Approach**: Scope the property to two concrete failing cases: (1) count of Stop-trigger hook files > 1, (2) OUTPUT RULES preamble lacks negative examples preventing narration
  - Test that `hook-categories.yaml` `agentstop_order` contains exactly one entry whose corresponding hook JSON `name` field starts with "to wait" or "to append" that surfaces as a user-facing Stop label (from Bug Condition in design: `countVisibleStopHooks(input.hookRegistry) > 1`)
  - Test that `ask-bootcamper.json` prompt OUTPUT RULES section contains explicit negative examples prohibiting narration like "My last message ends with..." (from Bug Condition in design: `ask_output.allPhasesNoOutput AND ask_output.responseText != "."`)
  - Assert that `module-recap-append.json` does NOT exist as a standalone Stop-trigger hook file (single hook visibility property)
  - Assert that the OUTPUT RULES preamble in `ask-bootcamper.json` contains at least 3 negative example patterns (e.g., lines starting with "✗")
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists: two Stop hooks surface, and OUTPUT RULES lack negative examples)
  - Document counterexamples found: `module-recap-append.json` exists as separate Stop hook file; OUTPUT RULES has no "✗" negative examples
  - Mark task complete when test is written, run, and failure is documented
  - Create test file at `tests/test_stop_hook_ux_bug_condition.py`
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Recap Capture, Precedence, and Hook Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: `hook-categories.yaml` `agentstop_order` has `ask-bootcamper` at order 1, recap before celebration, celebration before gate enforcement, gate before visualization, visualization before critical-artifacts
  - Observe: `module-recap-append.json` prompt contains all recap constraints (ISO 8601 timestamps, no secrets, byte-for-byte preservation, duration from planner only, boundary detection, deferral to `.question_pending`)
  - Observe: `ask-bootcamper.json` prompt contains all four phases (Phase 1 Closing Question, Phase 2 Step Sequencing, Phase 3 MCP-First, Phase 4 Question Format) with their full logic intact
  - Observe: `hooks.lock.yaml` and `hook-categories.yaml` are mutually consistent (all Stop hooks in lock have entries in categories)
  - Write property-based test: for all valid `agentstop_order` configurations after fix, the relative precedence ordering is preserved (ask-bootcamper first, celebration before gate, gate before visualization, visualization before critical-artifacts)
  - Write property-based test: for any module completion scenario, the recap logic (now Phase 0 of `ask-bootcamper`) includes all required constraints from the original `module-recap-append` prompt (boundary detection, `.question_pending` deferral, ISO 8601, no secrets, planner-only durations, backfill verification)
  - Write property-based test: the four original phases of `ask-bootcamper` (Closing Question, Step Sequencing, MCP-First, Question Format) remain present and unaltered in the consolidated prompt
  - Write property-based test: `hooks.lock.yaml` does not contain `module-recap-append` after fix AND all remaining Stop hooks in lock match `agentstop_order` entries
  - Write property-based test: `preToolUse` hooks (`enforce-mandatory-gate`, `gate-module3-visualization`, `write-policy-gate`) are completely unaltered
  - Verify tests PASS on UNFIXED code (preservation baseline)
  - Create test file at `tests/test_stop_hook_ux_preservation.py`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3. Fix for dual Stop hook visibility and narration leak

  - [x] 3.1 Add Phase 0 (Module Recap Append) to `ask-bootcamper.json`
    - Insert the full `module-recap-append` prompt logic as "Phase 0" before existing Phase 1
    - Phase 0 checks `config/.question_pending` first (defer if exists)
    - Phase 0 performs boundary detection on `modules_completed`
    - Phase 0 runs full recap-append workflow (gather, compute duration, append, verify/backfill)
    - Preserve all original constraints: ISO 8601, no secrets, byte-for-byte, planner-only durations
    - Preserve Q&R format rules, Journal subsection format, Duration field rules
    - Update the hook description text to reference "five phases" (Phase 0 through Phase 4)
    - _Bug_Condition: isBugCondition(input) where countVisibleStopHooks > 1_
    - _Expected_Behavior: Single "to wait for your answer" hook surfaces with recap logic internal_
    - _Preservation: All recap constraints from module-recap-append.json preserved in Phase 0_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

  - [x] 3.2 Strengthen OUTPUT RULES preamble in `ask-bootcamper.json`
    - Add explicit prohibition against narrating phase evaluation
    - Add "NEGATIVE EXAMPLES" block with at least 3 "✗" prefixed examples
    - Include: "My last message ends with a 👉 question, and no module was completed."
    - Include: "Phase 1 was silenced because a question is already pending."
    - Include: "No phases produced output, so responding with a period."
    - Include: "All conditions checked — no action needed."
    - Add: "The ONLY acceptable no-output response is the literal single character: ."
    - _Bug_Condition: isBugCondition(input) where ask_output.allPhasesNoOutput AND responseText != "."_
    - _Expected_Behavior: No-output path produces exactly "." with zero narration_
    - _Preservation: All existing OUTPUT RULES semantics preserved, only strengthened_
    - _Requirements: 2.3, 3.5_

  - [x] 3.3 Delete `module-recap-append.json`
    - Remove `senzing-bootcamp/hooks/module-recap-append.json` from the repository
    - Its logic now lives inside `ask-bootcamper.json` as Phase 0
    - _Bug_Condition: Separate hook file = separate UI label_
    - _Expected_Behavior: No standalone recap hook file exists_
    - _Preservation: All recap logic preserved inside ask-bootcamper Phase 0_
    - _Requirements: 2.1, 1.1, 1.2_

  - [x] 3.4 Update `hook-categories.yaml`
    - Remove `module-recap-append` from the `any` list under `modules:`
    - Remove the `module-recap-append` entry from `agentstop_order`
    - Renumber remaining `agentstop_order` entries: ask-bootcamper=1, module-completion-celebration=2, enforce-gate-on-stop=3, enforce-visualization-offers=4, enforce-critical-artifacts=5
    - Update `enforce-critical-artifacts` rationale to remove reference to "must run after module-recap-append"
    - _Bug_Condition: agentstop_order listed module-recap-append as separate hook_
    - _Expected_Behavior: agentstop_order has 5 entries, module-recap-append absent_
    - _Preservation: Relative ordering of all remaining hooks unchanged_
    - _Requirements: 2.1, 2.2, 3.4, 3.7_

  - [x] 3.5 Regenerate `hooks.lock.yaml`
    - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write`
    - Verify output does not contain `module-recap-append` entry
    - Verify all remaining hooks are present with correct categories and event types
    - _Expected_Behavior: Lock file consistent with updated hook-categories.yaml_
    - _Preservation: All non-recap hooks unchanged in lock file_
    - _Requirements: 3.7_

  - [x] 3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Single Stop Hook and No Narration
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (single hook, negative examples present)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.3_

  - [x] 3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Recap Capture and Hook Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest tests/test_stop_hook_ux_bug_condition.py tests/test_stop_hook_ux_preservation.py -v`
  - Verify CI-relevant checks pass: `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
  - Ensure all tests pass, ask the user if questions arise.
