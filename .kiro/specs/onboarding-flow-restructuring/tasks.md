# Implementation Plan: Onboarding Flow Restructuring

## Overview

This plan restructures the `onboarding-flow.md` steering file to reorder steps (ER intro before language selection), adds a production reuse hint, adds git accessibility guidance to `module-01-business-problem.md`, and updates the internal comment in `entity-resolution-intro.md`. Property-based tests validate structural invariants of the produced files.

## Tasks

- [x] 1. Restructure `onboarding-flow.md` step ordering
  - [x] 1.1 Move Prerequisite Check from Step 3 to Step 2 and renumber sub-steps
    - Move the current "## 3. Prerequisite Check" section (including sub-steps 3a–3d) to become "## 2. Prerequisite Check" with sub-steps 2a–2d
    - Update all internal references to step numbers within the section
    - _Requirements: 1.1, 1.4_

  - [x] 1.2 Move Entity Resolution Introduction to new Step 3 as a top-level step
    - Remove the current "### 4a. What Is Entity Resolution?" sub-step from under Bootcamp Introduction
    - Create a new "## 3. Entity Resolution Introduction" top-level section containing the `#[[file:senzing-bootcamp/steering/entity-resolution-intro.md]]` directive
    - Ensure the mandatory gate in `entity-resolution-intro.md` serves as the gate for this step
    - _Requirements: 1.1, 1.2, 1.3, 1.5_

  - [x] 1.3 Move Programming Language Selection to Step 4 and add Production Reuse Hint
    - Move the current "## 2. Programming Language Selection" section to become "## 4. Programming Language Selection"
    - Insert the Production Reuse Hint as a blockquote after the language list presentation instruction and before the mandatory gate marker
    - Verbatim hint text: "Tip: If you plan to use these bootcamp artifacts in production, consider choosing the language your team already uses — the code we generate here is designed to be your starting point for real-world use."
    - _Requirements: 1.1, 1.4, 3.1, 3.2, 3.3, 3.4_

  - [x] 1.4 Move Bootcamp Introduction to Step 5 with sub-steps 5a and 5b
    - Move the current "## 4. Bootcamp Introduction" section to become "## 5. Bootcamp Introduction"
    - Renumber "### 4b. Verbosity Preference" to "### 5a. Verbosity Preference"
    - Renumber "### 4c. Comprehension Check" to "### 5b. Comprehension Check"
    - Remove the old "### 4a." sub-step (already moved to Step 3)
    - Update the trailing instruction to reference loading `onboarding-phase2-track-setup.md` after Step 5b
    - _Requirements: 1.4, 1.5_

  - [x] 1.5 Update cross-references and flow description in `onboarding-flow.md`
    - Update the file's opening description line to reflect the new sequence: directory creation → prerequisites → entity resolution → language selection → introduction → track selection
    - Verify no prose references to old step numbers remain
    - _Requirements: 1.4_

- [x] 2. Update `entity-resolution-intro.md` internal comment
  - [x] 2.1 Update the step reference comment from "Step 4a" to "Step 3"
    - Change the line "Loaded via `#[[file:]]` from `onboarding-flow.md` during Step 4a." to reference "Step 3"
    - _Requirements: 1.4_

  - [x] 2.2 Add fallback handling rule for search_docs failures
    - In the "Explore Further" agent instruction comment block, add a handling rule: "If search_docs returns no relevant results or the tool call fails: inform the bootcamper that no documentation was found for their specific question, suggest they rephrase or ask a different question, then re-present this gate."
    - _Requirements: 2.6_

- [x] 3. Update `module-01-business-problem.md` git prompt
  - [x] 3.1 Add accessibility guidance phrase to the git initialization prompt
    - Change the prompt from: `"This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp."`
    - To: `"If you don't know what 'git' is, just skip this. This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp."`
    - Preserve the pointing marker, STOP instruction, and response-handling logic unchanged
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 4. Checkpoint - Ensure all steering file changes are valid
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write property-based tests for structural invariants
  - [x] 5.1 Write property test for ER Introduction preceding Programming Language Selection
    - **Property 1: Entity Resolution Introduction precedes Programming Language Selection**
    - Parse `onboarding-flow.md` to extract step numbers for the `#[[file:senzing-bootcamp/steering/entity-resolution-intro.md]]` directive, the Programming Language Selection mandatory gate, and the Prerequisite Check; assert ER intro step number < language selection step number, and both > prerequisite check step number
    - **Validates: Requirements 1.1**

  - [x] 5.2 Write property test for contiguous step number sequence
    - **Property 2: Step numbers form a contiguous sequence**
    - Parse all `## N.` headings from `onboarding-flow.md`; assert they form a contiguous integer sequence starting from 0 with no duplicates and no gaps
    - **Validates: Requirements 1.4**

  - [x] 5.3 Write property test for Verbosity and Comprehension sub-step placement
    - **Property 3: Verbosity Preference and Comprehension Check are sub-steps of Bootcamp Introduction**
    - Parse `onboarding-flow.md` to verify "Verbosity Preference" and "Comprehension Check" appear as `###` sub-step headings under the `##` heading for "Bootcamp Introduction", not under Entity Resolution Introduction or Programming Language Selection
    - **Validates: Requirements 1.5**

  - [x] 5.4 Write property test for Production Reuse Hint placement
    - **Property 4: Production Reuse Hint is correctly placed in Programming Language Selection**
    - Parse the Programming Language Selection section of `onboarding-flow.md`; assert the verbatim hint text appears after the language list presentation instruction and before the mandatory gate marker
    - **Validates: Requirements 3.1, 3.2**

  - [x] 5.5 Write property test for git accessibility phrase placement
    - **Property 5: Git accessibility phrase precedes the existing explanation sentence**
    - Parse `module-01-business-problem.md`; assert "If you don't know what 'git' is, just skip this." appears in the same prompt block as, and immediately before, the sentence "This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp."
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 6. Write unit tests for content presence checks
  - [x] 6.1 Write unit tests for `entity-resolution-intro.md` content integrity
    - Test that the mandatory gate pattern (stop marker + STOP instruction) exists in the file
    - Test that the discussion offer has at least 2 example questions
    - Test that acknowledgment phrases are listed in gate instructions
    - Test that search_docs instruction is present in gate handling rules
    - Test that fallback instruction is present for failed search
    - _Requirements: 1.3, 2.1, 2.2, 2.4, 2.5, 2.6_

  - [x] 6.2 Write unit tests for Production Reuse Hint behavior
    - Test that no STOP instruction appears between the hint and the mandatory gate
    - Test that the hint is unconditional (not wrapped in IF/condition)
    - _Requirements: 3.3, 3.4_

  - [x] 6.3 Write unit tests for git prompt preservation
    - Test that the existing explanation sentence is preserved verbatim
    - Test that the STOP instruction is preserved after the git prompt
    - _Requirements: 4.2, 4.4_

- [x] 7. Update `steering-index.yaml` token counts
  - [x] 7.1 Re-measure token counts and update `steering-index.yaml`
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get updated token counts for `onboarding-flow.md` and `module-01-business-problem.md`
    - Update the corresponding entries in `senzing-bootcamp/steering/steering-index.yaml`
    - _Requirements: 1.4_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation language is Python 3.11+ for tests; steering file changes are Markdown
- Test file location: `senzing-bootcamp/tests/test_onboarding_flow_restructuring.py`
- CI pipeline validates: `validate_commonmark.py`, `measure_steering.py --check`, `validate_power.py`, then `pytest`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "2.2", "3.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["1.4", "1.5"] },
    { "id": 3, "tasks": ["7.1"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3", "5.4", "5.5", "6.1", "6.2", "6.3"] }
  ]
}
```
