# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** — Prompt Re-states Pending Question
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the prompt contains a re-statement instruction
  - **Scoped PBT Approach**: For any generated question marker (👉-prefixed string or WAIT pattern), assert the hook prompt does NOT contain "re-state" or "restate" in the context of pending questions
  - Test file: `senzing-bootcamp/tests/test_summarize_on_stop_hook.py` — use the existing `TestBugConditionExploration` class
  - The existing tests in `TestBugConditionExploration` check for detection and reordering instructions; add a new property test `test_hook_prompt_does_not_restate_question` that asserts the prompt does NOT contain "re-state the pending question" or "restate the pending question"
  - Also add `test_registry_prompt_does_not_restate_question` to verify the registry prompt lacks the re-statement instruction
  - Use the existing `question_marker_st` strategy to generate 👉 and WAIT markers
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (the prompt currently contains "re-state the pending question as the very last element")
  - Document counterexample: the prompt literal string "Then re-state the pending question as the very last element so it is the last thing the bootcamper sees." is the defect
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** — No-Question Path and Hook Metadata Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **NOTE**: The existing `TestPreservation` class in `senzing-bootcamp/tests/test_summarize_on_stop_hook.py` already covers preservation
  - Observe on UNFIXED code: `test_no_question_output_prompt_instructs_three_element_summary` passes (for any agent output without 👉/WAIT, prompt instructs accomplished + files + next step)
  - Observe on UNFIXED code: `test_hook_file_is_valid_json_with_required_keys` passes (hook JSON has name, version, description, when, then)
  - Observe on UNFIXED code: `test_hook_event_type_is_agent_stop` passes (when.type == "agentStop")
  - Observe on UNFIXED code: `test_hook_action_type_is_ask_agent` passes (then.type == "askAgent")
  - Observe on UNFIXED code: `test_hook_name_is_correct` passes (name == "Summarize Progress on Stop")
  - Observe on UNFIXED code: `test_prompt_mentions_all_three_summary_elements` passes (accomplished + files + next step)
  - Observe on UNFIXED code: `test_registry_prompt_matches_hook_prompt` passes (hook prompt == registry prompt)
  - Run all `TestPreservation` tests on UNFIXED code
  - **EXPECTED OUTCOME**: All preservation tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are run and all pass on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for duplicate question re-statement in hook prompt

  - [x] 3.1 Update hook prompt to remove re-statement instruction
    - File: `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook`
    - Remove the clause "Then re-state the pending question as the very last element so it is the last thing the bootcamper sees."
    - Replace with instruction to append only the summary (what was accomplished, which files changed) without re-stating the question, since it is already visible
    - Preserve the 👉 and WAIT detection logic at the start of the prompt
    - Preserve the no-question path: "If no pending question is detected, append the summary at the end as usual: (1) What did you accomplish? (2) Which files were created or modified? (3) What is the next step? Keep it concise."
    - _Bug_Condition: isBugCondition(input) where hookPrompt contains "re-state the pending question" AND agentOutput has 👉 or WAIT_
    - _Expected_Behavior: When pending question detected, append only summary without re-stating the question_
    - _Preservation: No-question path three-element summary, hook metadata, registry sync unchanged_
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.4_

  - [x] 3.2 Mirror the prompt change in hook-registry.md
    - File: `senzing-bootcamp/steering/hook-registry.md`
    - Update the Prompt field for `summarize-on-stop` to match the new hook file prompt exactly
    - Verify the registry prompt text is identical to the updated hook file prompt
    - _Preservation: Registry prompt must match hook file prompt (Requirements 3.3)_
    - _Requirements: 2.2, 3.3_

  - [x] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** — Prompt No Longer Re-states Pending Question
    - **IMPORTANT**: Re-run the SAME tests from task 1 — do NOT write new tests
    - The tests from task 1 encode the expected behavior (prompt should NOT contain re-statement instruction)
    - Run `test_hook_prompt_does_not_restate_question` and `test_registry_prompt_does_not_restate_question`
    - **EXPECTED OUTCOME**: Tests PASS (confirms the re-statement instruction has been removed)
    - _Requirements: 2.1, 2.2_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** — No-Question Path and Hook Metadata Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run all `TestPreservation` tests from `senzing-bootcamp/tests/test_summarize_on_stop_hook.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — three-element summary, metadata, registry sync all preserved)
    - Confirm all preservation tests still pass after fix
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint — Ensure all tests pass
  - Run the full test suite: `pytest senzing-bootcamp/tests/test_summarize_on_stop_hook.py -v`
  - Ensure all bug condition exploration tests pass (Property 1)
  - Ensure all preservation tests pass (Property 2)
  - Ensure all existing tests in `TestBugConditionExploration` pass (detection and reordering checks will pass on fixed code since the prompt retains detection logic and the summary-before-question structure)
  - Ask the user if questions arise
