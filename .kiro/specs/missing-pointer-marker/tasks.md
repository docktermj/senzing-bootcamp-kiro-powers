# Implementation Plan

## Overview

Fix the missing 👉 pointer marker in Step 4c of `senzing-bootcamp/steering/onboarding-flow.md`. The fix restructures the Step 4c instruction to make the 👉 prefix an unambiguous, mandatory part of the output template, adds a paraphrase constraint, and preserves all other onboarding behaviors.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Step 4c Missing Pointer Prefix
  - **IMPORTANT**: Write this property-based test BEFORE implementing the fix
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in the current steering file
  - **Scoped PBT Approach**: Scope the property to the Step 4c section of `senzing-bootcamp/steering/onboarding-flow.md`
  - Parse the Step 4c (Comprehension Check) section from the UNFIXED `onboarding-flow.md`
  - Test property: The Step 4c instruction format SHALL unambiguously require the 👉 prefix as part of the output template (not as an external annotation before a quoted string)
  - Bug condition from design: `isBugCondition(input)` where `input.step == "4c" AND input.markerFormat == "annotation_before_quoted_string"`
  - Assert: Step 4c contains an explicit output format directive with 👉 inside the template text
  - Assert: Step 4c contains a paraphrase constraint requiring 👉 on any reformulation
  - Run test on UNFIXED code - expect FAILURE (this confirms the bug exists: the 👉 marker is outside the quoted string and no explicit format directive exists)
  - Document counterexamples found (e.g., "Step 4c uses `👉 "quoted text"` format where marker is outside quotes", "No explicit output format instruction exists")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Step-4c Content Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Observe: Parse the UNFIXED `senzing-bootcamp/steering/onboarding-flow.md` and record all sections outside Step 4c's question formatting
  - Observe: Record all 👉 markers in Steps 2, 3a, 3b, 4b, and 5 with their positions and surrounding text
  - Observe: Record the Step 4 informational content (overview, module table, track descriptions) and verify no 👉 prefix present
  - Observe: Record acknowledgment handling instructions in Step 4c (proceed to Step 5 on "makes sense")
  - Observe: Record clarification handling instructions in Step 4c (answer using verbosity settings)
  - Observe: Record all 🛑 STOP directives and their positions
  - Write property-based test: for all sections where `NOT isBugCondition(section)`, the content in the fixed file SHALL be identical to the original file
  - Write property-based test: for all 👉 markers outside Step 4c, their count and positions SHALL remain unchanged
  - Write property-based test: Step 4c acknowledgment and clarification handling text SHALL remain unchanged
  - Verify tests pass on UNFIXED code (confirms baseline behavior to preserve)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for missing 👉 pointer marker in Step 4c

  - [x] 3.1 Implement the fix in `senzing-bootcamp/steering/onboarding-flow.md`
    - Restructure Step 4c to add an explicit output format directive requiring the 👉 prefix
    - Change the template from `👉 "That was a lot of ground to cover..."` to an explicit output format block showing the complete expected output including the 👉 prefix inside the template
    - Add a paraphrase constraint: if the agent reformulates the question, the 👉 prefix is still mandatory
    - Preserve the 🛑 STOP instruction in Step 4c
    - Preserve acknowledgment handling (bootcamper says "makes sense" → proceed to Step 5)
    - Preserve clarification handling (bootcamper asks question → answer using verbosity settings → check for more questions)
    - Maintain consistency with how other steps (2, 3a, 3b, 4b, 5) format their 👉 questions
    - _Bug_Condition: isBugCondition(input) where input.step == "4c" AND input.markerFormat == "annotation_before_quoted_string" AND agent_output_lacks_pointer_prefix(input.renderedOutput)_
    - _Expected_Behavior: Step 4c output MUST begin with "👉 " followed by the comprehension check question text, whether verbatim or paraphrased_
    - _Preservation: All other steps' 👉 markers, informational content without 👉, acknowledgment/clarification handling, 🛑 STOP directives, and single-question enforcement remain unchanged_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Step 4c Output Includes Pointer Prefix
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (explicit 👉 format directive, paraphrase constraint)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed — Step 4c now has unambiguous 👉 requirement)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Step-4c Content Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — all other steps, informational content, and response handling unchanged)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full test suite: `pytest senzing-bootcamp/tests/` to verify all property-based tests pass
  - Run CI validation scripts: `python senzing-bootcamp/scripts/validate_commonmark.py` on the fixed `onboarding-flow.md`
  - Verify the fixed file's token count remains within budget defined in `steering-index.yaml`
  - Ensure all tests pass, ask the user if questions arise.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3.1"] },
    { "id": 2, "tasks": ["3.2", "3.3"] },
    { "id": 3, "tasks": ["4"] }
  ]
}
```

## Notes

- Tests use pytest + Hypothesis (property-based testing) in `senzing-bootcamp/tests/`
- The exploration test (task 1) is expected to FAIL on unfixed code — this confirms the bug exists
- The preservation test (task 2) is expected to PASS on unfixed code — this captures baseline behavior
- After the fix (task 3.1), both tests should PASS
- The fix targets only `senzing-bootcamp/steering/onboarding-flow.md`, Step 4c section
- CI validation (`validate_commonmark.py`, `measure_steering.py --check`) must pass after the fix
