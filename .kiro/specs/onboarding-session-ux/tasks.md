# Implementation Plan: Onboarding Session UX

## Overview

This plan implements two UX improvements through steering Markdown edits and supporting tests:
1. Add a setup-complete statement to the WELCOME banner section in `onboarding-phase1b-intro-language.md` (Requirement 2.4)
2. Add Rule 6 (bold question convention) to `session-resume.md` Step 2b Core Rules (Requirements 4.1–4.4)
3. Update token counts in `steering-index.yaml` for modified files (Requirement 6.1)
4. Write property-based tests validating the bold formatting logic (Requirements 3.x, 5.x)

No changes needed to `onboarding-flow.md` (§ 0 already contains the preamble) or `write-policy-gate.json` (CHECK 2 already strips bold markers).

## Tasks

- [x] 1. Edit steering files for onboarding and session-resume improvements
  - [x] 1.1 Add setup-complete statement to WELCOME banner section in `onboarding-phase1b-intro-language.md`
    - In the `## 5. Bootcamp Introduction` section, add an instruction line immediately before the banner display directing the agent to state that administrative setup is complete and the bootcamp is now starting
    - The statement must clearly communicate: "Administrative setup is complete. The bootcamp is starting."
    - _Requirements: 2.4_

  - [x] 1.2 Add Rule 6 (bold question convention) to `session-resume.md` Step 2b Core Rules
    - In the `### Core Rules` numbered list under `## Step 2b: Behavioral Rules Reload`, add a sixth rule after rule 5
    - Rule 6 text: `6. **Bold question text** — Every 👉 leading question's text is wrapped in CommonMark bold (`**...**`). The 👉 pointer is outside the bold span. Explanatory context before the question stays plain. Numbered option lines stay plain. Enforcement: if a 👉 question's text lacks bold emphasis, wrap it before sending.`
    - Update the "re-assert the five core conversation rules" phrasing to "six core conversation rules"
    - The rule must be self-contained (not solely a reference to conversation-protocol.md) so it persists through context compaction
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 1.3 Update token counts in `steering-index.yaml`
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get new token counts for `session-resume.md` and `onboarding-phase1b-intro-language.md`
    - Update the `token_count` values in `steering-index.yaml` under the `session-resume` section (phase1-fast-path) and the `onboarding` section (phase1b-intro-language), and in `file_metadata`
    - Verify neither file exceeds `split_threshold_tokens` (5000). Per the design, both remain well under threshold.
    - _Requirements: 6.1, 6.2_

- [x] 2. Checkpoint - Verify steering edits
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement formatting helper functions and tests
  - [x] 3.1 Create the bold question formatting module at `senzing-bootcamp/tests/helpers/bold_format.py`
    - Implement `format_bold_question(text: str) -> str` — wraps question text in `👉 **{text}**` format (idempotent: applying twice yields same result)
    - Implement `format_choice_question(lead: str, options: list[str]) -> str` — formats lead in bold, numbered options in plain text
    - Implement `strip_bold_markers(text: str) -> str` — removes all `**` markers for validation equivalence
    - These functions codify the formatting logic described in the design's correctness properties
    - _Requirements: 3.1, 3.2, 3.3, 3.6_

  - [x] 3.2 Write property test for question formatting idempotence
    - **Property 1: Question formatting idempotence**
    - Test that applying `format_bold_question` produces output with (a) text inside `**...**`, (b) `👉` outside bold, and (c) re-applying is idempotent
    - Use Hypothesis `st.text()` strategy filtered to non-empty strings
    - Minimum 100 iterations
    - **Validates: Requirements 3.1, 3.2, 3.6**

  - [x] 3.3 Write property test for choice question lead/option bold separation
    - **Property 2: Choice question formatting separates lead from options**
    - Test that `format_choice_question` produces bold on lead line and no `**` on option lines
    - Use `st.text()` for lead + `st.lists(st.text(), min_size=1)` for options
    - Minimum 100 iterations
    - **Validates: Requirements 3.3, 3.4**

  - [x] 3.4 Write property test for bold-marker-transparent validation
    - **Property 3: Bold-marker-transparent validation**
    - Test that `strip_bold_markers` applied before a mock compound-question validator gives the same verdict as validating after stripping
    - Use `st.text()` with injected `**` markers at random positions
    - Minimum 100 iterations
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 4. Write structural unit tests for steering file content
  - [x] 4.1 Create `senzing-bootcamp/tests/test_onboarding_session_ux.py` with structural validation tests
    - Test: WELCOME banner section in `onboarding-phase1b-intro-language.md` contains a setup-complete statement
    - Test: `session-resume.md` Step 2b contains a rule about bold `👉` question text stated inline (not solely by reference)
    - Test: `onboarding-flow.md` § 0 Setup Preamble precedes § 1 Directory Structure and § 2 Prerequisite Check
    - Test: `onboarding-flow.md` preamble content contains "project directory", "hooks", "environment", and "WELCOME"
    - Test: `write-policy-gate.json` CHECK 2 contains the "STRIP BOLD MARKERS" instruction
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 4.2, 4.3, 5.1_

  - [x] 4.2 Write token budget validation test
    - Run `measure_steering.py --check` in a subprocess and verify exit code 0
    - Confirms no file exceeds split threshold without allowlist entry
    - _Requirements: 6.1, 6.2_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (Hypothesis, Python 3.11+)
- Unit tests validate specific structural requirements and edge cases
- The formatting helper module (`bold_format.py`) is placed in the test helpers directory since it codifies the logic for testing purposes — the actual formatting is enforced by steering, not code
- `onboarding-flow.md` and `write-policy-gate.json` require no edits (validated by unit tests)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "3.1"] },
    { "id": 2, "tasks": ["3.2", "3.3", "3.4", "4.1"] },
    { "id": 3, "tasks": ["4.2"] }
  ]
}
```
