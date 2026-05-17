# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Step-Chaining After Final Sub-Step
  - **IMPORTANT**: Write this property-based test BEFORE implementing the fix
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the steering files lack step-chaining instructions
  - **Scoped PBT Approach**: Generate random AgentTurnContext inputs where `currentStep` is the last lettered sub-step (e.g., "7d"), `isLastSubStepInSequence = TRUE`, `undeterminedItemsRemaining = 0`, and `nextNumberedStepExists = TRUE`
  - Test that `module-01-business-problem.md` contains an explicit step-chaining instruction after Step 7d directing the agent to ask Step 8's 👉 question
  - Test that `module-transitions.md` Sub-Step Convention includes a rule for what happens after the last sub-step
  - Test that `conversation-protocol.md` End-of-Turn Protocol addresses sub-step completion (checkpoint is NOT end of turn)
  - Property: for all inputs satisfying `isBugCondition(input)`, the relevant steering text contains an unambiguous instruction to advance to the next numbered step's 👉 question in the same turn
  - Run test on UNFIXED steering files
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the steering lacks step-chaining instructions)
  - Document counterexamples found (e.g., "Step 7d section contains 🛑 STOP but no instruction to proceed to Step 8")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Mid-Sequence Sub-Step and Existing Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Observe on UNFIXED steering: mid-sequence sub-steps (7a, 7b, 7c when undetermined items remain) each contain "ask about only one undetermined item per turn" and 🛑 STOP markers
  - Observe on UNFIXED steering: all existing 🛑 STOP markers in Steps 7a–7d are present
  - Observe on UNFIXED steering: conversation-protocol.md "One Question Rule" is intact
  - Observe on UNFIXED steering: ⛔ gate behavior is unchanged
  - Write property-based tests:
    - For all sub-step positions where `undeterminedItemsRemaining > 0` (non-bug-condition), steering contains "ask about only one undetermined item per turn" instruction and 🛑 STOP
    - All existing 🛑 STOP markers in sub-steps 7a–7d are preserved in the fixed version
    - The "One Question Rule" in conversation-protocol.md is not weakened or removed
    - ⛔ gates continue to block advancement regardless of step-chaining rule
  - Verify tests PASS on UNFIXED steering files
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for leading question not asked after final gap-filling sub-step

  - [x] 3.1 Add step-chaining instruction to `senzing-bootcamp/steering/module-01-business-problem.md`
    - Insert explicit step-chaining instruction after Step 7d checkpoint
    - Add: "**All sub-steps complete?** → Proceed immediately to Step 8 below. Do NOT end your turn here — the bootcamper expects the next question."
    - Ensure the instruction clearly states: once all gap-filling sub-steps are complete (no undetermined items remain), immediately proceed to Step 8 in the same turn — present Step 8's 👉 question as the closing question
    - Verify all existing 🛑 STOP markers in Steps 7a–7d remain intact
    - _Bug_Condition: isBugCondition(input) where input.currentStep is last sub-step AND undeterminedItemsRemaining = 0 AND nextNumberedStepExists = TRUE_
    - _Expected_Behavior: Agent writes checkpoint AND asks next numbered step's 👉 question in same turn_
    - _Preservation: Mid-sequence sub-step 🛑 STOP behavior unchanged; one-question-per-turn rule intact_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2_

  - [x] 3.2 Add "after the last sub-step" rule to `senzing-bootcamp/steering/module-transitions.md`
    - Append a bullet to the Sub-Step Convention section
    - Add: "**After the last sub-step**: When the bootcamper's answer completes the final sub-step (no undetermined items remain), write the checkpoint and immediately proceed to the next numbered step's 👉 question in the same turn. Do not end the turn after writing the last sub-step's checkpoint."
    - Ensure existing Sub-Step Convention rules are not modified or removed
    - _Bug_Condition: Sub-Step Convention is silent on post-final-sub-step behavior_
    - _Expected_Behavior: Convention explicitly defines step-chaining after last sub-step_
    - _Preservation: All existing Sub-Step Convention bullets remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Add sub-step completion clause to `senzing-bootcamp/steering/conversation-protocol.md`
    - Add clarifying paragraph to End-of-Turn Protocol section: "When you complete the LAST sub-step in a gap-filling sequence (all undetermined items resolved): writing the checkpoint is NOT the end of your turn. You must also present the next numbered step's 👉 question. The checkpoint marks sub-step completion; the 👉 question marks turn completion."
    - Add Sub-Step Completion Dead-End example to No Dead-End Responses section showing WRONG (checkpoint only) vs CORRECT (checkpoint + next step's 👉 question)
    - Ensure existing End-of-Turn Protocol rules and One Question Rule are not modified
    - _Bug_Condition: Conversation protocol does not address sub-step-to-next-step transition_
    - _Expected_Behavior: Protocol explicitly states checkpoint is not turn completion for final sub-steps_
    - _Preservation: One Question Rule, ⛔ gate behavior, clarifying question priority all unchanged_
    - _Requirements: 2.1, 2.3, 3.3, 3.4, 3.5_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Step-Chaining After Final Sub-Step
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (steering contains step-chaining instructions)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1 against FIXED steering files
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed — steering now contains step-chaining instructions)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Mid-Sequence Sub-Step and Existing Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2 against FIXED steering files
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — mid-sequence stops, 🛑 markers, One Question Rule, ⛔ gates all preserved)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_leading_question_enforcement.py -v`
  - Ensure all property-based tests pass (both bug condition and preservation)
  - Ensure no other existing tests are broken by the steering file changes
  - Ask the user if questions arise
