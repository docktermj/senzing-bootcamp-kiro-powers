# Implementation Plan: Onboarding Comprehension Check

## Overview

Add a comprehension check sub-step (Step 4c) to the onboarding flow steering file, update the steering index token count, and write tests. The implementation follows an observation-first approach: write tests first (so preservation baselines are captured before any edits), then implement the steering file change, then update the index.

## Tasks

- [x] 1. Write tests for the comprehension check feature
  - [x] 1.1 Create `senzing-bootcamp/tests/test_comprehension_check.py` with structural placement tests
    - Create the test file with helpers to read `onboarding-flow.md` and parse step sections
    - Write `TestStepHeadingSequence` class: assert the heading list includes `4c` between `4b` and `5`
    - Write `TestExistingStepPreservation` class: assert steps 0, 1, 1b, 2, 3, 4, 4b, 5 and subsequent sections retain their key content (welcome banner, guided discovery, track descriptions, gate markers on steps 2 and 5, etc.)
    - _Requirements: 1.1, 1.2, 5.1_

  - [x] 1.2 Add content marker tests for Step 4c
    - Write `TestStep4cContentMarkers` class with individual test methods:
      - Prompt contains comprehension check phrasing ("makes sense" / "questions")
      - Prompt references upcoming track selection
      - Section contains acknowledgment handling instructions with example phrases ("looks good," "ready," "no questions," etc.)
      - Section contains clarification handling instructions with check-for-more-questions logic
      - Section references verbosity settings for answering clarifications
      - Section contains note about not being a mandatory gate and hook handling closing questions
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 5.2, 5.3_

  - [x] 1.3 Add non-gate contract test for Step 4c
    - Write `TestStep4cNonGate` class: assert Step 4c section contains no ⛔ markers, no "MUST stop", no "mandatory gate", no "MUST NOT proceed" gate keywords
    - Assert Step 4c section contains no inline 👉 closing questions or WAIT instructions
    - _Requirements: 1.3, 2.4_

  - [x] 1.4 Write Hypothesis property test for non-gate step contract (Property 1)
    - **Property 1: Non-gate step contract**
    - **Validates: Requirements 1.3, 2.4**
    - Write `TestNonGateStepContractProperty` class using Hypothesis
    - Define `st_non_gate_step_id()` strategy sampling from `["0", "1", "1b", "4", "4c"]`
    - `@given(step_id=st_non_gate_step_id())` with `@settings(max_examples=100)`
    - For each sampled step, parse its section from `onboarding-flow.md` and assert: no gate markers (⛔, "MUST stop", "mandatory gate", "MUST NOT proceed") AND no inline 👉 questions or WAIT instructions
    - Tag: `Feature: onboarding-comprehension-check, Property 1: Non-gate step contract`

  - [x] 1.5 Add token count consistency test
    - Write `TestTokenCountConsistency` class: read `steering-index.yaml`, get the `onboarding-flow.md` token count, run `measure_steering.py` programmatically or compare against actual file size to verify the count is not stale
    - _Requirements: 5.4_

- [x] 2. Checkpoint — Run tests to confirm baselines
  - Ensure all tests pass (preservation and content marker tests will initially fail since Step 4c doesn't exist yet — that's expected). Run: `python -m pytest senzing-bootcamp/tests/test_comprehension_check.py -v`
  - Confirm which tests pass (preservation) and which fail (Step 4c content). Ask the user if questions arise.

- [x] 3. Implement the Step 4c section in `onboarding-flow.md`
  - [x] 3.1 Add the `### 4c. Comprehension Check` section to `senzing-bootcamp/steering/onboarding-flow.md`
    - Insert the new section between the `### 4b. Verbosity Preference` section and the `## 5. Track Selection` section
    - Include the warm, conversational comprehension check prompt text that asks if the introduction makes sense and whether the bootcamper has questions before choosing a track
    - Include acknowledgment handling instructions: on responses like "looks good," "makes sense," "no questions," "let's go," "ready," "all clear," "got it" → proceed to Step 5
    - Include clarification handling instructions: answer the question using the bootcamper's current verbosity settings, then check for more questions before proceeding to Step 5
    - Include a note that Step 4c is NOT a mandatory gate and that the `ask-bootcamper` hook handles the closing question
    - Do NOT include inline 👉 closing questions or WAIT instructions (consistent with the onboarding flow note)
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

- [x] 4. Update the steering index token count
  - [x] 4.1 Run `python3 senzing-bootcamp/scripts/measure_steering.py` and update `senzing-bootcamp/steering/steering-index.yaml` with the new token count for `onboarding-flow.md` and recalculated `budget.total_tokens`
    - _Requirements: 5.4_

- [x] 5. Final checkpoint — Run all tests and verify
  - Run `python -m pytest senzing-bootcamp/tests/test_comprehension_check.py -v` and ensure all tests pass
  - Run the existing onboarding question ownership tests to confirm no regressions: `python -m pytest senzing-bootcamp/tests/test_onboarding_question_ownership.py -v`
  - Run the track selection gate preservation tests: `python -m pytest senzing-bootcamp/tests/test_track_selection_gate_preservation.py -v`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- The observation-first approach (tests before implementation) captures preservation baselines from the unfixed state
- Property tests validate universal correctness properties across all non-gate steps
- Unit tests validate specific structural and content properties of Step 4c
