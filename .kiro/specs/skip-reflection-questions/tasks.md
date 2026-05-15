# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Reflection Question Present in Steering Files
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the reflection question instructions exist in the steering files
  - **Scoped PBT Approach**: Scope the property to the concrete failing cases: module-completion.md contains "## Reflection Question" section, journal template contains "Bootcamper's takeaway" with reflection placeholder, module-03-system-verification.md step 12 contains "Reflection question:" instruction, and success criteria require "answered the reflection question"
  - Test file: `senzing-bootcamp/tests/test_skip_reflection_questions_bug.py`
  - Parse `senzing-bootcamp/steering/module-completion.md` and assert it does NOT contain a "## Reflection Question" heading (will FAIL on unfixed code)
  - Parse `senzing-bootcamp/steering/module-completion.md` journal template and assert "Bootcamper's takeaway" either does not exist or is auto-filled with "N/A" (will FAIL on unfixed code)
  - Parse `senzing-bootcamp/steering/module-03-system-verification.md` step 12 and assert it does NOT contain "Reflection question:" instruction (will FAIL on unfixed code)
  - Parse `senzing-bootcamp/steering/module-03-system-verification.md` success criteria and assert it does NOT contain "answered the reflection question" (will FAIL on unfixed code)
  - Use Hypothesis with `@given()` to generate module numbers (1-11) and verify that for any module, the completion workflow does not instruct reflection questions
  - Run test on UNFIXED code - expect FAILURE (this confirms the bug exists)
  - Document counterexamples found (e.g., "module-completion.md line N contains '## Reflection Question' heading")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Module Completion Workflow Integrity
  - **IMPORTANT**: Follow observation-first methodology
  - Test file: `senzing-bootcamp/tests/test_skip_reflection_questions_preservation.py`
  - Observe: `module-completion.md` contains "## Bootcamp Journal" section with template fields (module name, date, what we did, what was produced, why it matters)
  - Observe: `module-completion.md` contains "## Module Completion Certificate" section with certificate template
  - Observe: `module-completion.md` contains "## Next-Step Options" section with all five options (Proceed, Iterate, Explore, Undo, Share)
  - Observe: `module-completion.md` contains "⛔ Immediate Execution on Affirmative Response" section with PROHIBITED list
  - Observe: `module-completion.md` contains "## Path Completion Detection" table and "## Path Completion Celebration" section
  - Observe: `module-03-system-verification.md` step 12 contains "Follow the `module-completion.md` workflow" instruction
  - Observe: `module-03-system-verification.md` step 12 contains "Journal entry" instruction
  - Observe: `module-03-system-verification.md` step 12 contains "Transition to Module 4" instruction
  - Write property-based test: for all preserved sections, the structural content remains intact in the steering files
  - Use Hypothesis with `@given()` to generate random subsets of preserved section names and verify each exists with expected content
  - Verify tests PASS on UNFIXED code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix for reflection question removal from steering files

  - [x] 3.1 Remove reflection question from module-completion.md
    - Remove the entire "## Reflection Question" section (the section that instructs the agent to ask about the bootcamper's main takeaway and append the response)
    - Update the journal template: remove `**Bootcamper's takeaway:** [response to reflection question]` line or replace with `**Bootcamper's takeaway:** N/A`
    - Update "## Module Completion Certificate" section header from "After the journal entry and reflection" to "After the journal entry"
    - Update "## Next-Step Options" section header from "After the journal entry and reflection" to "After the journal entry"
    - Preserve flow ordering: journal entry → certificate → next-step options
    - _Bug_Condition: isBugCondition(input) where input.workflowPhase == "module_completion" AND steeringFileContains("module-completion.md", "Reflection Question" section)_
    - _Expected_Behavior: module-completion.md SHALL NOT contain a "## Reflection Question" section; flow proceeds directly from journal to certificate_
    - _Preservation: Journal entry structure (minus takeaway), certificate template, next-step options, immediate execution rules, path completion detection and celebration all remain unchanged_
    - _Requirements: 2.1, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 3.2 Remove reflection question from module-03-system-verification.md
    - Remove item 3 from step 12 ("Reflection question: Present one reflection question to the bootcamper" and the example question)
    - Remove "The bootcamper has answered the reflection question" from the Success Criteria section
    - Renumber step 12 items to remain coherent (items: follow module-completion.md, journal entry, transition to Module 4)
    - _Bug_Condition: isBugCondition(input) where input.moduleNumber == 3 AND step12Contains("Reflection question:")_
    - _Expected_Behavior: step 12 SHALL NOT contain reflection question instruction; success criteria SHALL NOT require reflection answer_
    - _Preservation: All other step 12 items (follow module-completion.md, journal entry, transition to Module 4) and all other success criteria remain unchanged_
    - _Requirements: 2.2, 2.3_

  - [x] 3.3 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Reflection Question Removed
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (no reflection question content in steering files)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1: `pytest senzing-bootcamp/tests/test_skip_reflection_questions_bug.py -v`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2: Preservation** - Module Completion Workflow Integrity
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2: `pytest senzing-bootcamp/tests/test_skip_reflection_questions_preservation.py -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_skip_reflection_questions_bug.py senzing-bootcamp/tests/test_skip_reflection_questions_preservation.py -v`
  - Ensure all tests pass, ask the user if questions arise.
