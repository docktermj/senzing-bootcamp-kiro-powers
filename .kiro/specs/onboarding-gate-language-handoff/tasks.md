# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Gate-Active Closing Question Previews Upcoming Content
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in `senzing-bootcamp/hooks/ask-bootcamper.json` and `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`
  - **Scoped PBT Approach**: Scope the property to the concrete failing cases: Phase 1 fires at the entity-resolution-intro mandatory gate (Step 3) with various session contexts
  - Test file: `senzing-bootcamp/tests/test_onboarding_gate_language_handoff_exploration.py`
  - Use pytest + Hypothesis following project conventions (class-based organization, `st_` prefixed strategies)
  - **Scenario 1 - Phase 1 Preview Leak**: Parse the `ask-bootcamper.json` hook prompt text and verify that Phase 1 (Closing_Question_Phase) contains a gate-awareness constraint that prevents referencing specific upcoming content when a mandatory gate is active. Assert that the prompt contains instructions to genericize forward-looking references at gates. On unfixed code, this constraint is ABSENT — test will FAIL.
  - **Scenario 2 - Gate Transition Directive**: Parse `onboarding-phase1b-intro-language.md` and verify an explicit transition directive exists between Step 3 and Step 4 that routes readiness signals directly to Step 4. On unfixed code, this directive is ABSENT — test will FAIL.
  - Property: For all generated session contexts where `isBugCondition(input)` holds (mandatory gate active + hook fires on Stop), the hook prompt MUST contain gate-awareness constraint text AND the steering file MUST contain a readiness-signal transition directive
  - Generate strategies: `st_readiness_signals()` producing variations like "ready", "let's go", "continue", "next", "move on", "yes", "sure", "yep", "what's next"
  - Generate strategies: `st_gate_active_context()` producing assistant messages containing "⛔ **MANDATORY GATE**" and "🛑 **STOP"
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists: no gate-awareness constraint in Phase 1, no transition directive in steering)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Gate Phase 1 Behavior and Follow-Up Question Handling
  - **IMPORTANT**: Follow observation-first methodology
  - Test file: `senzing-bootcamp/tests/test_onboarding_gate_language_handoff_preservation.py`
  - Use pytest + Hypothesis following project conventions (class-based organization, `st_` prefixed strategies)
  - **Observe on UNFIXED code first**:
    - Observe: Phase 1 prompt text for non-gate steps allows natural references to upcoming content (no gate constraint interferes)
    - Observe: The steering file's Step 3 loads entity-resolution-intro.md via `#[[file:]]` reference
    - Observe: Phase 1 suppresses output when `config/.question_pending` exists (condition 1 of Phase 1)
    - Observe: Follow-up questions at the gate are handled by re-presenting the gate (not treated as readiness signals)
  - **Property 2A - Non-Gate Phase 1 Preservation**: For all generated non-gate step contexts (where no mandatory gate is active), verify that Phase 1's existing conditions and behavior logic remain intact in the hook prompt — the prompt still produces contextual closing questions with full session awareness (Requirements 3.1, 3.3)
  - **Property 2B - Follow-Up Question Handling Preservation**: For all generated follow-up questions at the gate (questions that are NOT readiness signals, e.g., "How does Senzing match records?", "Can you explain entity resolution?"), verify the steering file still instructs the agent to answer and re-present the gate (Requirement 3.2)
  - **Property 2C - Question Pending Suppression Preservation**: Verify that Phase 1's condition checking for `config/.question_pending` existence remains unchanged in the hook prompt (Requirement 3.5)
  - **Property 2D - Non-Gate Transition Preservation**: For all non-gate steps in the steering file, verify existing routing logic (Step 4 → Step 5, Step 5 → track selection) remains unchanged (Requirement 3.4)
  - Generate strategies: `st_non_gate_contexts()` producing contexts without mandatory gate markers
  - Generate strategies: `st_followup_questions()` producing actual questions (contain "?", start with "how", "what", "why", "can you", etc.)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for gate-active closing question preview and missing transition directive

  - [x] 3.1 Add gate-awareness constraint to Phase 1 in `ask-bootcamper.json`
    - In the Phase 1 (Closing_Question_Phase) section of the hook prompt, insert a gate-awareness check at the beginning of the "SECOND — Recap and closing question" block
    - Add detection criteria: the most recent assistant message contains "⛔ **MANDATORY GATE**" AND "🛑 **STOP" — indicating the gate was just presented and is awaiting bootcamper input
    - Add constraint text: "When a mandatory gate is detected as active, your closing question MUST NOT name, preview, or reference specific content from any step beyond the current gate. Use generic forward-looking language only, such as 'we'll continue when you're ready' or 'we'll move on to the next setup step.' Do NOT mention programming language selection, track selection, or any other specific upcoming topic."
    - Preserve all existing Phase 1 conditions and behavior for non-gate contexts
    - _Bug_Condition: isBugCondition(input) where trigger == "Stop" AND currentStepHasMandatoryGate() AND mandatoryGateNotCleared() AND phase1ClosingQuestionReferencesSpecificUpcomingContent()_
    - _Expected_Behavior: Phase 1 closing question keeps forward-looking references generic when gate is active_
    - _Preservation: Non-gate Phase 1 behavior unchanged, question_pending suppression unchanged_
    - _Requirements: 1.1, 1.3, 2.1, 2.3, 3.1, 3.3, 3.5_

  - [x] 3.2 Add explicit transition directive in `onboarding-phase1b-intro-language.md`
    - Insert a transition directive between the Step 3 `#[[file:]]` reference comment block and the Step 4 heading
    - Directive content: instruct the agent that when the bootcamper signals readiness to proceed at the entity-resolution-intro mandatory gate (words like "ready," "let's go," "continue," "next," "move on," or similar acknowledgments, affirmatives like "yes," "sure," "yep," and forward-looking statements like "what's next," "let's keep going"), immediately proceed to Step 4 below without re-presenting the entity-resolution-intro gate content
    - Include contrast guidance: follow-up questions (contain "?", ask for explanation, request clarification about ER concepts) should still trigger the answer-then-re-present-gate flow as defined in entity-resolution-intro.md
    - _Bug_Condition: isBugCondition(input) where trigger == "UserPromptSubmit" AND bootcamperSignaledReadiness(input.userMessage) AND agentResponseRePresentsCurrentGate()_
    - _Expected_Behavior: Readiness signals at entity-resolution-intro gate immediately advance to Step 4_
    - _Preservation: Follow-up questions still answered via search_docs and gate re-presented; non-gate transitions unchanged_
    - _Requirements: 1.2, 2.2, 3.2, 3.4_

  - [x] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Gate-Active Closing Question Genericization
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (gate-awareness constraint exists, transition directive exists)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run: `python -m pytest senzing-bootcamp/tests/test_onboarding_gate_language_handoff_exploration.py --run`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed — gate-awareness constraint now present in hook, transition directive now present in steering)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Gate Phase 1 Behavior and Follow-Up Question Handling
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run: `python -m pytest senzing-bootcamp/tests/test_onboarding_gate_language_handoff_preservation.py --run`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — non-gate behavior unchanged, follow-up handling preserved, question_pending suppression intact)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `python -m pytest senzing-bootcamp/tests/test_onboarding_gate_language_handoff_exploration.py senzing-bootcamp/tests/test_onboarding_gate_language_handoff_preservation.py --run`
  - Ensure all tests pass, ask the user if questions arise.
