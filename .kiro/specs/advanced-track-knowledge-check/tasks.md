# Implementation Plan: Advanced Track Knowledge Check

## Overview

Add a single, light entity-resolution (ER) Knowledge_Check to the onboarding flow, presented **only
for the Advanced track** and inserted after the Step 5 Track Selection gate resolves to Advanced and
before Module 1 begins. This is a **steering-driven** feature: the behavior is authored as a new
sub-step (`5c. Advanced Track Knowledge Check`) in
`senzing-bootcamp/steering/onboarding-phase2-track-setup.md`, not as a runtime script or hook. It
reuses the Step 5b Comprehension_Check tone, the `ask-bootcamper` closing-question note, and the
current verbosity settings, and it never blocks regardless of answer.

Work proceeds authoring-first: add the steering sub-step, then sync the two `steering-index.yaml`
token-count entries and verify with `measure_steering.py --check`, then add the test-only reference
decision model plus Hypothesis property tests (Properties 1–4), and finally the content/flow tests
that read the real steering and keep the model faithful to the authored prose. Tests live in
`senzing-bootcamp/tests/`, follow the project pattern (pytest + Hypothesis, class-based, `sys.path`
import), use the registered Hypothesis profiles (no hand-set `@settings(max_examples=...)`), and use
synthetic, PII-free fixtures only. Steering content references ER concepts via existing steering /
MCP conventions and contains no external URLs.

## Tasks

- [x] 1. Author the Advanced Track Knowledge Check steering sub-step
  - [x] 1.1 Add the `5c. Advanced Track Knowledge Check` section to `onboarding-phase2-track-setup.md`
    - Edit `senzing-bootcamp/steering/onboarding-phase2-track-setup.md` to add a new
      `## 5c. Advanced Track Knowledge Check` section positioned **immediately after** the
      `## 5. Track Selection` section and **before** the `## Switching Tracks` appendix; state that
      the check follows track selection and precedes Module 1
    - Add the **Advanced-only guard**: the step runs only when the persisted `track` is the Advanced
      track (`advanced_topics`) and is skipped for the Core track (`core_bootcamp`) and any
      missing/unknown value, which proceed straight to Module 1 with Core onboarding unchanged
    - Author **exactly one** warm, `👉`-prefixed ER comprehension question drawn from a core concept
      in `entity-resolution-intro.md` (e.g., that ER decides whether records refer to the *same
      real-world entity*), in the non-quiz "gut-check" tone consistent with Step 5b, then stop
    - Document the **affirm-and-proceed** path for correct/understanding answers and the
      **Re_Explanation-and-proceed** path for incorrect/unsure answers, instructing the agent to
      apply the bootcamper's current verbosity settings when giving the Re_Explanation
    - Add the **non-gate note**: Step 5c is NOT a mandatory gate, never prevents continuing
      regardless of answer, and the `ask-bootcamper` hook owns the closing question — mirroring the
      Step 5b note and containing no gate markers, no "MUST stop", no "mandatory gate", no
      "MUST NOT proceed", and no "WAIT"; use no external URLs and source any Senzing/ER facts via
      existing conventions
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.3_

- [x] 2. Sync the steering index token counts
  - [x] 2.1 Update `steering-index.yaml` and verify with `measure_steering.py --check`
    - Edit `senzing-bootcamp/steering/steering-index.yaml` to refresh the measured token counts for
      the modified file: `onboarding.phases.phase2-track-setup.token_count` (was `991`) and
      `file_metadata."onboarding-phase2-track-setup.md".token_count` (was `972`); widen the
      phase2 `step_range` to include the new sub-step if appropriate
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` and confirm the recorded
      counts match the file (still under the `split_threshold_tokens` budget of 5000)
    - _Requirements: 3.2_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Add the reference decision model and property tests
  - [x] 4.1 Create the test module and the test-only reference decision model
    - Create `senzing-bootcamp/tests/test_advanced_track_knowledge_check.py` mirroring the structure
      of `test_comprehension_check.py` (module docstring, `sys.path` insertion where needed,
      class-based organization, helpers that read the real steering files under
      `senzing-bootcamp/steering/`)
    - Define the pure reference model in the test module (not shipped in the power runtime path):
      `presents_knowledge_check(track)`, the frozen `CheckOutcome` dataclass, and
      `resolve_knowledge_check(track, answer)` exactly as specified in the design's Components section
    - Add the `st_track()` strategy (draws `advanced_topics`, `core_bootcamp`, arbitrary/unknown
      strings, and the empty string) and the `st_answer_class()` strategy (draws `correct`,
      `incorrect`, `unsure`, and `None`); use synthetic, PII-free values only
    - _Requirements: 4.2_

  - [x] 4.2 Write property test for Advanced-only presentation
    - **Property 1: Advanced-only presentation** — for any `st_track()`,
      `presents_knowledge_check(track)` is true iff `track == "advanced_topics"`
    - **Validates: Requirements 1.1, 1.2**

  - [x] 4.3 Write property test for correct answers affirming and proceeding
    - **Property 2: Correct answers affirm and proceed** — for any correct answer on the Advanced
      track, the outcome selects the `affirm` branch, `re_explanation is False`, and
      `proceeds_to_module_1 is True`
    - **Validates: Requirements 2.2**

  - [x] 4.4 Write property test for incorrect/unsure answers triggering Re_Explanation
    - **Property 3: Incorrect or unsure answers trigger a Re_Explanation and proceed** — for any
      incorrect / unsure / no answer on the Advanced track, `re_explanation is True` and
      `proceeds_to_module_1 is True`
    - **Validates: Requirements 2.3**

  - [x] 4.5 Write property test for the never-blocks contract
    - **Property 4: The Knowledge_Check never blocks** — for any `(st_track(), st_answer_class())`
      pair (including Core, unknown tracks, wrong answers, "unsure", and no answer),
      `proceeds_to_module_1 is True`
    - **Validates: Requirements 2.4**

- [x] 5. Add content / flow tests against the real steering
  - [x] 5.1 Write placement and Advanced-only guard content tests
    - Assert the `5c. Advanced Track Knowledge Check` heading exists in
      `onboarding-phase2-track-setup.md`, appears **after** `## 5. Track Selection` and **before**
      `## Switching Tracks`, and states the check precedes Module 1
    - Assert the section explicitly scopes the check to the Advanced track (`advanced_topics`) and
      states the Core track skips it / is unchanged
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 5.2 Write single-question, tone, and branch-documentation content tests
    - Assert the section contains exactly one `👉`-prefixed question, references a core ER concept,
      and carries non-quiz framing consistent with Step 5b
    - Assert the section documents the affirm-and-proceed path for correct answers and the
      Re_Explanation-and-proceed path for incorrect/unsure answers
    - _Requirements: 2.1, 2.2, 2.3, 3.1_

  - [x] 5.3 Write non-gate contract and hook + verbosity content tests
    - Assert the section contains **no** gate markers — no ⛔, no "MUST stop", no "mandatory gate",
      no "MUST NOT proceed", and no "WAIT" — mirroring the Step 5b non-gate contract test
    - Assert the section references the `ask-bootcamper` closing-question note and instructs the
      agent to apply the bootcamper's current verbosity settings when giving the Re_Explanation
    - _Requirements: 2.4, 3.1, 3.3_

  - [x] 5.4 Write steering index sync test
    - Assert the `steering-index.yaml` entries for `onboarding-phase2-track-setup.md` exist for both
      the `phase2-track-setup` phase entry and the `file_metadata` entry for the modified file
    - _Requirements: 3.2_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, run `python3 senzing-bootcamp/scripts/measure_steering.py --check`, and
    ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/test_advanced_track_knowledge_check.py`, are class-based, and
  import scripts via the `sys.path` convention; the reference decision model is defined in the test
  module and is not shipped in the distributed power path.
- Content/flow tests keep the reference model faithful to the authored steering, so the properties
  cannot pass against a model that has drifted from the flow.
- All fixtures are synthetic and PII-free; steering content uses no external URLs and sources Senzing
  facts via existing MCP conventions.
- Each property task references its property number and the requirement clause it validates for
  traceability.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "4.1"] },
    { "id": 2, "tasks": ["4.2", "4.3", "4.4", "4.5", "5.1", "5.2", "5.3", "5.4"] }
  ]
}
```
