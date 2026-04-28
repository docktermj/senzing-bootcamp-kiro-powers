# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** — Prompt Lacks Pending-Question Detection and Reordering
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in the current prompt text
  - **Scoped PBT Approach**: The bug is deterministic — scope the property to the concrete prompt text in `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook`
  - Create test file `senzing-bootcamp/tests/test_summarize_on_stop_hook.py`
  - Read the current `then.prompt` value from `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook` (parse as JSON)
  - Read the `summarize-on-stop` Prompt field from `senzing-bootcamp/steering/hook-registry.md`
  - Write a property-based test using Hypothesis that generates random question markers (`👉` prefixed strings, `WAIT` pattern strings) and asserts the prompt text contains:
    - Instructions to detect `👉` prefix or `WAIT` pattern in previous output
    - Conditional reordering logic (summary before question when question detected)
    - Instruction to re-state the pending question as the final element
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the prompt lacks detection/reordering instructions)
  - Document counterexamples found (e.g., "prompt contains no mention of 👉, WAIT, pending question, or reorder")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** — No-Question Behavior and Hook Metadata Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **IMPORTANT**: Write these tests in the SAME test file `senzing-bootcamp/tests/test_summarize_on_stop_hook.py`
  - Observe on UNFIXED code: the prompt instructs a three-element summary (accomplished, files changed, next step) appended at end
  - Observe on UNFIXED code: the hook JSON has `"type": "agentStop"` and `"type": "askAgent"`, name is `"Summarize Progress on Stop"`
  - Observe on UNFIXED code: the hook JSON is valid JSON with required keys (`name`, `version`, `description`, `when`, `then`)
  - Write property-based test (Hypothesis): generate random agent output strings WITHOUT `👉` or `WAIT` markers, assert the prompt still instructs the standard three-element summary (accomplished, files, next step) — this validates the no-question path is present in the prompt
  - Write example-based tests:
    - Assert the hook file is valid JSON with all required keys
    - Assert `when.type` is `"agentStop"` and `then.type` is `"askAgent"`
    - Assert the prompt mentions all three summary elements (accomplished, files, next step)
    - Assert the prompt text in `hook-registry.md` matches the prompt in the hook file
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for summarize-on-stop hook prompt missing pending-question detection and reordering

  - [x] 3.1 Update the prompt in `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook`
    - Replace the `then.prompt` value with the updated prompt that includes:
    - Pending question detection: instruct the agent to check if its previous output ended with a pending question identified by `👉` prefix or `WAIT` pattern
    - Conditional reordering: if a pending question is detected, present the summary (accomplished, files changed) FIRST, then re-state the pending question as the very last element
    - Default behavior preserved: if no pending question is detected, append the summary at the end as usual (accomplished, files changed, next step)
    - All three summary elements retained: (1) what was accomplished, (2) files created/modified, (3) next step or re-stated question
    - Ensure the file remains valid JSON after the edit
    - _Bug_Condition: isBugCondition(input) where input.agentOutput ends with `👉` prefix or `WAIT` pattern_
    - _Expected_Behavior: summary appears before pending question; question re-stated as final element_
    - _Preservation: when no pending question, summary appended at end with next step as final element_
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Update the `summarize-on-stop` entry in `senzing-bootcamp/steering/hook-registry.md`
    - Replace the Prompt field for the `summarize-on-stop` entry with the exact same updated prompt text from task 3.1
    - Do NOT change the `id`, `name`, `description`, event type (`agentStop`), or action type (`askAgent`)
    - Ensure the markdown remains well-formed after the edit
    - _Requirements: 2.2, 3.3_

  - [x] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** — Prompt Contains Detection and Reordering Logic
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (prompt contains `👉`/`WAIT` detection and reordering instructions)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** — No-Question Behavior and Hook Metadata Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint — Ensure all tests pass
  - Run the full test suite: `pytest senzing-bootcamp/tests/test_summarize_on_stop_hook.py -v`
  - Ensure all tests pass, ask the user if questions arise
