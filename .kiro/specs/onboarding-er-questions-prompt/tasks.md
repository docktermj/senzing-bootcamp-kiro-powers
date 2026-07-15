# Implementation Plan: Onboarding ER Questions Prompt

## Overview

This plan implements the reordering of the two closing calls-to-action in the
mandatory **Exploration_Gate** of
`senzing-bootcamp/steering/entity-resolution-intro.md`. The rendered closing 👉
becomes the **Open_Questions_Prompt** ("Do you have any questions about Entity
Resolution?"), and the **Illustration_Offer** is deferred to a subsequent
(Phase B) turn, presented only after the open prompt is handled.

The implementation surface is steering-file prose plus HTML-comment AGENT
INSTRUCTION directives — there is no runtime code path. Work proceeds
incrementally: first the steering-file edit (the single source of truth for
behavior), then the repo/CI bookkeeping so the edited file stays valid and within
budget, then updates to the existing test assertions that key off the old
ordering, and finally a new focused test module that validates the seven
correctness properties as example-based steering-content assertions.

Because the design's "PBT applicability" note establishes there is a single fixed
input (one steering file), no Hypothesis/property-based tests are added; the
correctness properties are validated as example-based assertions, consistent with
the peer suites.

## Tasks

- [x] 1. Rework the Exploration_Gate closing calls-to-action in the steering file
  - Edit `senzing-bootcamp/steering/entity-resolution-intro.md`, "Explore Further" section
  - [x] 1.1 Change the rendered closing 👉 to the Open_Questions_Prompt
    - Replace the rendered closing 👉 (currently the two-record Illustration_Offer) with `👉 **Do you have any questions about Entity Resolution?**`
    - Keep it the single rendered 👉 of the gate turn: non-compound, exactly one `?` (One_Question_Rule)
    - Keep the 🛑 STOP line immediately following the closing 👉 unchanged
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2_

  - [x] 1.2 Add the new OPEN_QUESTIONS_PROMPT AGENT INSTRUCTION directive
    - Add an HTML-comment `<!-- AGENT INSTRUCTION: OPEN_QUESTIONS_PROMPT ... -->` block in the "Explore Further" section, ordered before the `ILLUSTRATION_OFFER` directive
    - Mark the Open_Questions_Prompt as the single closing 👉 (non-compound, verbosity-aware) and state the Illustration_Offer is NOT presented in the same turn
    - Defer to the existing gate answer/wait semantics for follow-ups, ambiguity, and MCP failures
    - Specify that once the open prompt is handled (readiness / no questions), the agent presents the Illustration_Offer next turn, and that any asked question is answered before the offer
    - _Requirements: 1.2, 1.5, 1.6, 2.3, 2.4, 2.5, 2.6_

  - [x] 1.3 Rework the ILLUSTRATION_OFFER directive to fire as Phase B
    - Re-sequence the existing `ILLUSTRATION_OFFER` directive so it is presented as the single 👉 of its own later turn, only after the Open_Questions_Prompt is handled
    - Preserve: One_Question_Rule + verbosity-aware, optional (decline/readiness proceeds past gate), ask-once, on-accept render ER_Illustration inline then re-present gate, and the clarify-once path for unrecognized responses
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 1.4 Verify preserved directives (ER_CONCEPTS_BANNER, ER_ILLUSTRATION, wait/answer)
    - Confirm the once-only `ER_Concepts_Banner` directive is unchanged and never re-displayed on re-presentation
    - Confirm the gate answer/wait directive still requires MCP-first (`search_docs`) answering and re-presentation without proceeding
    - Confirm the `ER_ILLUSTRATION` directive still enforces conceptual-only / ≤25 lines / no-graph / no-server / Module 3 forward reference / decline-and-redirect
    - _Requirements: 2.6, 3.6, 4.1, 4.2, 4.3, 4.4_

- [x] 2. Update repo/CI bookkeeping for the edited steering file
  - [x] 2.1 Re-measure and update the token_count in steering-index.yaml
    - Run `python senzing-bootcamp/scripts/measure_steering.py` to get the new token count for `entity-resolution-intro.md`
    - Update `file_metadata.entity-resolution-intro.md.token_count` in `senzing-bootcamp/steering/steering-index.yaml` (currently `1977`) to the measured value
    - Verify `python senzing-bootcamp/scripts/measure_steering.py --check` passes and the file stays under `split_threshold_tokens`
    - _Requirements: (CI constraint — steering token budget)_

  - [x] 2.2 Validate CommonMark and power integrity
    - Run `python senzing-bootcamp/scripts/validate_commonmark.py` to confirm the edited markdown is well-formed
    - Run `python senzing-bootcamp/scripts/validate_power.py` to confirm frontmatter, placement, and naming still pass
    - _Requirements: (CI constraint — CommonMark validity, power validation)_

- [x] 3. Checkpoint - Ensure steering edit and CI checks pass
  - Ensure `measure_steering.py --check`, `validate_commonmark.py`, and `validate_power.py` all pass, ask the user if questions arise.

- [x] 4. Update existing test assertions that assume the old ordering
  - Edit `senzing-bootcamp/tests/test_er_intro_illustration.py`
  - [x] 4.1 Re-point test_exactly_one_leading_question to the Open_Questions_Prompt
    - Update `TestIllustrationOffer.test_exactly_one_leading_question` so the single rendered 👉 is asserted to be the Open_Questions_Prompt, not the Illustration_Offer
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 4.2 Move offer/stop-marker assertions to the directive and open prompt
    - Update `TestIllustrationOffer.test_offer_is_about_two_record_match_and_non_match` so two-record match/non-match assertions target the `ILLUSTRATION_OFFER` directive block rather than the rendered closing 👉
    - Update `TestGatePreservation.test_stop_marker_follows_the_offer` so the 🛑 STOP marker is asserted to follow the Open_Questions_Prompt as the rendered closing line
    - _Requirements: 2.1, 3.1_

- [x] 5. Add new property-verification test module
  - Create `senzing-bootcamp/tests/test_onboarding_er_questions_prompt.py`
  - [x] 5.1 Set up module scaffolding and shared fixture
    - Load `senzing-bootcamp/steering/entity-resolution-intro.md`; add the `scripts/` `sys.path` shim to reuse the canonical `count_leading_questions` rule
    - Use class-based organization (`class TestOnboardingERQuestionsPrompt...`) documenting which requirements each class validates
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 5.2 Write example-based assertion for Property 1
    - **Property 1: Closing call-to-action is the Open_Questions_Prompt only**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - Assert exactly one rendered 👉, it is the Open_Questions_Prompt, non-compound (one `?`), and the Illustration_Offer text is not a rendered 👉

  - [x] 5.3 Write example-based assertion for Property 2
    - **Property 2: Open prompt precedes and gates the illustration offer**
    - **Validates: Requirements 1.5, 1.6, 3.1**
    - Assert the `OPEN_QUESTIONS_PROMPT` directive precedes the `ILLUSTRATION_OFFER` directive and gates the offer on the open prompt being handled / questions answered

  - [x] 5.4 Write example-based assertion for Property 3
    - **Property 3: Gate wait semantics are preserved**
    - **Validates: Requirements 2.1, 2.2**
    - Assert a 🛑 STOP line follows the Open_Questions_Prompt 👉 and the directive forbids fabricating/assuming a response and proceeding

  - [x] 5.5 Write example-based assertion for Property 4
    - **Property 4: MCP-first answering and re-presentation are preserved**
    - **Validates: Requirements 2.3, 2.4, 2.5**
    - Assert the gate directive names `search_docs`, ambiguity handling, failure handling, and "re-present"

  - [x] 5.6 Write example-based assertion for Property 5
    - **Property 5: The concepts banner is shown once per Preface run**
    - **Validates: Requirements 2.6, 3.6**
    - Assert the once-only `ER_Concepts_Banner` directive is preserved and re-present never re-displays it

  - [x] 5.7 Write example-based assertion for Property 6
    - **Property 6: Illustration_Offer regression invariants hold**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.7**
    - Assert the `ILLUSTRATION_OFFER` directive marks the offer single/non-compound/verbosity-aware, optional, ask-once, with the clarify-once path

  - [x] 5.8 Write example-based assertion for Property 7
    - **Property 7: The illustration remains a conceptual preview**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    - Assert the `ER_ILLUSTRATION` directive preserves conceptual-only / ≤25 lines / no-graph / no-server / Module 3 forward reference / decline-and-redirect

- [x] 6. Final checkpoint - Ensure all tests pass
  - Run the full pytest suite including `test_er_intro_illustration.py`, `test_onboarding_er_questions_prompt.py`, `test_entity_resolution_intro_structure.py`, and `test_onboarding_flow_restructuring.py`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; here the new property-verification module (5.1–5.8) is optional test work, while the existing-test updates (4.1, 4.2) are required because the old assertions would otherwise fail against the reordered gate.
- Each task references specific requirements (granular sub-requirements) for traceability.
- Checkpoints ensure incremental validation of the steering edit and the test suite.
- Per the design's PBT applicability note, the correctness properties are validated as example-based steering-content assertions against the single fixed steering file; no Hypothesis/property-based tests are added.
- The steering file (`entity-resolution-intro.md`) is edited by task 1 only; `steering-index.yaml` is edited by task 2.1 only; `test_er_intro_illustration.py` is edited by task 4 only; the new test module is created by task 5 only — so no two waves write the same file.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4"] },
    { "id": 4, "tasks": ["2.1", "2.2"] },
    { "id": 5, "tasks": ["4.1", "5.1"] },
    { "id": 6, "tasks": ["4.2", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8"] }
  ]
}
```
