# Implementation Plan

## Overview

Fix the compound question enforcement gap by: (1) writing exploration and preservation tests to confirm the bug and baseline behavior, (2) strengthening `conversation-protocol.md` with pre-output validation, (3) adding compound-question validation to `ask-bootcamper.kiro.hook`, and (4) creating a new `question-format-gate.kiro.hook` agentStop hook for mechanical enforcement on all agent output.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Compound Questions Pass Through Unvalidated
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate compound questions in agent output are not caught by current enforcement
  - **Scoped PBT Approach**: Scope the property to concrete failing cases — agent output strings containing 👉 questions with prose-joined alternatives ("or", "Or shall we", "Or would you")
  - Test that `isBugCondition(output)` inputs are detected and reformatted by the enforcement system:
    - "👉 Would you like me to create a one-page executive summary? Or shall we skip that and move on to Module 3?" → must be caught
    - "👉 Does that look right? Or would you like me to adjust it?" → must be caught
    - "👉 Would you like to proceed with Python or Java?" → must be caught (prose-joined alternatives)
  - Use Hypothesis to generate variations: random action text joined by "or"/"Or" patterns within 👉 questions
  - Assert that for all generated compound questions, the enforcement mechanism detects and blocks them
  - Run test on UNFIXED code - expect FAILURE (confirms the enforcement gap exists)
  - Document counterexamples found (e.g., "compound question in direct output passes through with no validation")
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Compound Output Passes Through Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs:
    - Observe: "👉 Ready to move on to Module 3?" passes through unchanged
    - Observe: "Here you can use Python or Java for this step." (informational prose with "or") passes through unchanged
    - Observe: "👉 What would you like to do next?\n1. Share with your team or manager\n2. Move to Module 3" (numbered list with "or" in item) passes through unchanged
    - Observe: "👉 Would you like me to create the summary?" (single yes/no) passes through unchanged
  - Write property-based tests using Hypothesis:
    - Generate random simple yes/no questions (single action, no alternatives) → assert unchanged
    - Generate random informational prose containing "or" but no 👉 question → assert unchanged
    - Generate random questions already formatted as numbered lists → assert not double-reformatted
    - Generate random numbered list items containing "or" in descriptions → assert "or" inside list items is not flagged
    - Generate random non-question content → assert unchanged
  - Verify tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for compound question enforcement gap

  - [x] 3.1 Strengthen `conversation-protocol.md` with pre-output validation and rewrite protocol
    - Add explicit "Pre-Output Validation Checklist" section that the agent must execute before every turn containing a 👉 question
    - Make compound-question check the FIRST item in the checklist (fail-fast)
    - Add "Rewrite Protocol" subsection with step-by-step instructions for converting compound questions to numbered list format or single yes/no format
    - Include concrete before/after examples for each violation pattern (either/or, appended alternative, sentence-starter "Or")
    - _Bug_Condition: isBugCondition(output) where output.contains👉Question() AND multipleAlternatives() AND alternativesJoinedByProse() AND NOT formattedAsNumberedList()_
    - _Expected_Behavior: compound questions reformatted as numbered list preceded by neutral question, OR single yes/no with no appended alternatives_
    - _Preservation: simple yes/no questions stay inline prose; informational prose unchanged; "or" inside list items allowed_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.5_

  - [x] 3.2 Add compound-question validation to `ask-bootcamper.kiro.hook` Phase 1
    - Modify the Phase 1 prompt in `ask-bootcamper.kiro.hook` to include compound-question validation before outputting a closing question
    - Add instruction: "Before outputting the closing question, verify it does not contain prose-joined alternatives. If it does, reformat as a numbered list."
    - Include the detection patterns: "[action A], or [action B]", "[question]? Or [alternative]?", "[question], or would you [alternative]?"
    - _Bug_Condition: ask-bootcamper generates closing question with multipleAlternatives() joined by prose_
    - _Expected_Behavior: closing questions with multiple alternatives are formatted as numbered lists_
    - _Preservation: single yes/no closing questions remain in simple "👉 [question]?" format_
    - _Requirements: 2.1, 2.3, 3.1, 3.5_

  - [x] 3.3 Create `question-format-gate.kiro.hook` as agentStop enforcement hook
    - Create new hook file at `senzing-bootcamp/hooks/question-format-gate.kiro.hook`
    - Hook type: `agentStop` — fires after every agent response before it reaches the bootcamper
    - Hook prompt inspects the agent's most recent output for 👉 questions containing prose-joined alternatives
    - Detection logic: scan for 👉 prefix, then check if question text matches compound patterns (multipleAlternatives + alternativesJoinedByProse + NOT formattedAsNumberedList)
    - If compound question detected: instruct agent to rewrite using numbered list format preceded by neutral question
    - If no compound question detected: pass through unchanged (no interference)
    - This closes the enforcement gap on the output path that currently has no validation
    - _Bug_Condition: isBugCondition(output) — compound 👉 questions in direct agent response text_
    - _Expected_Behavior: mechanical enforcement catches compound questions that slip past steering compliance_
    - _Preservation: non-compound outputs pass through with zero modification_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.5_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Compound Questions Are Reformatted
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (compound questions must be detected and blocked)
    - When this test passes, it confirms the enforcement gap is closed
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms compound questions are now caught by enforcement)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Compound Output Passes Through Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — simple questions, prose, and list-internal "or" are unaffected)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/ tests/ -v`
  - Verify Property 1 (bug condition) test passes on fixed code
  - Verify Property 2 (preservation) tests pass on fixed code
  - Verify existing `write-policy-gate` Check 2 tests still pass (requirement 3.4)
  - Ensure no other test regressions introduced
  - Ask the user if questions arise

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 2, "tasks": ["3.4", "3.5"] },
    { "id": 3, "tasks": ["4"] }
  ]
}
```

## Notes

- Tasks 1 and 2 are independent and can be written in parallel (both run on unfixed code)
- Tasks 3.1, 3.2, and 3.3 are the implementation tasks and can be done in parallel
- Tasks 3.4 and 3.5 are verification tasks that depend on both the tests (tasks 1, 2) and the implementation (tasks 3.1–3.3)
- Task 4 is the final checkpoint that depends on all verification passing
- Tests use pytest + Hypothesis per project conventions; test files go in `tests/` (repo-level, since they validate hook prompts)
