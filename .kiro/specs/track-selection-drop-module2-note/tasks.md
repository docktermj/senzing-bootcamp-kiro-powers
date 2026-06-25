# Implementation Plan

## Overview

Remove the standalone "Module 2 is automatically inserted before any module that needs the SDK."
line from Section 5 (Track Selection) of
`senzing-bootcamp/steering/onboarding-phase2-track-setup.md`. The auto-insertion behavior and its
later explanation in `onboarding-flow.md` are unchanged.

## Tasks

- [x] 1. Write fix-checking and preservation tests (before the edit)
  - Create `senzing-bootcamp/tests/test_track_selection_drop_module2_note.py` (stdlib + pytest,
    `from __future__ import annotations`, class-based, per `python-conventions.md`)
  - **test_track_selection_omits_auto_insertion_note** (Property 1): assert the Track_Setup_File
    does NOT contain "Module 2 is automatically inserted before any module that needs the SDK."
    — authored to FAIL on unfixed content
  - **test_track_options_present** (Property 2): assert "Core Bootcamp" and "Advanced Topics"
    remain — PASS on unfixed content
  - **test_mandatory_stop_gate_present** (Property 2): assert the ⛔ mandatory stop gate text
    remains — PASS on unfixed content
  - **test_response_interpretation_present** (Property 2): assert the "Interpreting responses:"
    line remains — PASS on unfixed content
  - **test_onboarding_flow_explanation_retained** (Property 2): assert `onboarding-flow.md` still
    contains the "explicitly or auto-inserted" explanation — PASS on unfixed content
  - Run the suite: confirm the fix-checking test FAILS and preservation tests PASS
  - _Requirements: 2.1, 2.2, 3.2, 3.3_

- [x] 2. Remove the auto-insertion note from track selection
  - Edit `senzing-bootcamp/steering/onboarding-phase2-track-setup.md` Section "5. Track Selection"
  - Delete the line `Module 2 is automatically inserted before any module that needs the SDK.` and
    the adjacent redundant blank line so the track options flow into "Interpreting responses:"
  - Leave the track options, "Authoritative source" note, response-interpretation guidance, and
    ⛔ mandatory stop gate intact
  - _Requirements: 2.1, 3.1, 3.2_

- [x] 3. Verify tests, CommonMark, and token budget
  - Run `pytest senzing-bootcamp/tests/test_track_selection_drop_module2_note.py` — all tests PASS
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` — passes
  - Run `python senzing-bootcamp/scripts/measure_steering.py --check` — passes (token count only
    decreases)
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2"] },
    { "id": 2, "tasks": ["3"] }
  ]
}
```

- **Wave 0** — `[1]`: author fix-checking + preservation tests against the unfixed file (fix-check
  FAILS, preservation PASSES).
- **Wave 1** — `[2]`: remove the auto-insertion note from track selection.
- **Wave 2** — `[3]`: verify tests, CommonMark, and the steering token budget.

## Notes

- One-line deletion in `onboarding-phase2-track-setup.md`; no behavioral change — module
  sequencing is driven by `config/module-dependencies.yaml`.
- The auto-insertion explanation in `onboarding-flow.md` (delivered when Module 2 is reached) is
  retained as the single, well-timed place that information appears.
- Token budget only decreases; `measure_steering.py --check` should pass without an index update.
