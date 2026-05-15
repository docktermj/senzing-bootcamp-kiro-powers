# Implementation Plan: Split onboarding-flow.md Below Token Threshold

## Overview

Split the monolithic `onboarding-flow.md` (6,451 tokens) into two phase files at the natural boundary between Step 4c and Step 5. The root file retains Phase 1 content plus routing logic; a new file contains Phase 2 content. Update all cross-references, the steering index, and affected tests.

## Tasks

- [x] 1. Create Phase 2 file and trim root file
  - [x] 1.1 Create `onboarding-phase2-track-setup.md` with Phase 2 content
    - Extract Step 5 (Track Selection), Switching Tracks, Changing Language, Validation Gates, and Hook Registry `#[[file:]]` reference from `onboarding-flow.md`
    - Add YAML frontmatter (`inclusion: manual`)
    - Place in `senzing-bootcamp/steering/onboarding-phase2-track-setup.md`
    - _Requirements: 1, 3, 5_

  - [x] 1.2 Trim `onboarding-flow.md` to Phase 1 only and add routing
    - Remove Phase 2 content (Step 5 onward) from the root file
    - Add phase routing instruction at the end: "After Step 4c, load `onboarding-phase2-track-setup.md` for track selection."
    - Verify root file retains: frontmatter, opening paragraph, ask-bootcamper note, Steps 0–4c
    - Target under 3,500 tokens
    - _Requirements: 1, 2, 5_

- [x] 2. Update steering-index.yaml
  - [x] 2.1 Add onboarding phases map to `steering-index.yaml`
    - Add `onboarding` entry with `root` and `phases` map (phase1-setup-intro, phase2-track-setup)
    - Include `file`, `token_count` (placeholder), `size_category`, and `step_range` for each phase
    - _Requirements: 4_

  - [x] 2.2 Update `file_metadata` section in `steering-index.yaml`
    - Replace single `onboarding-flow.md` entry with entries for both files
    - Ensure `onboarding-phase2-track-setup.md` is listed with correct metadata
    - _Requirements: 4_

  - [x] 2.3 Verify keyword routing in `steering-index.yaml`
    - Confirm `onboard` and `start` keywords still point to `onboarding-flow.md` (root entry point)
    - No changes needed if already correct
    - _Requirements: 4, 8_

- [x] 3. Update cross-references in other steering files
  - [x] 3.1 Update `session-resume.md` references
    - Change "load the Hook Registry from onboarding-flow.md" to reference `onboarding-phase2-track-setup.md`
    - Change "follow Switching Tracks section in onboarding-flow.md" to reference `onboarding-phase2-track-setup.md`
    - Keep "load onboarding-flow.md" (start over) unchanged — root remains entry point
    - _Requirements: 7_

  - [x] 3.2 Review `agent-instructions.md` references
    - Verify references to `onboarding-flow.md` still make sense (root remains entry point)
    - Update only if a reference specifically points to content that moved to Phase 2
    - _Requirements: 6_

- [x] 4. Checkpoint - Validate file structure
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Run validation scripts
  - [x] 5.1 Run `validate_commonmark.py` on both files
    - Execute `python senzing-bootcamp/scripts/validate_commonmark.py` targeting both `onboarding-flow.md` and `onboarding-phase2-track-setup.md`
    - Fix any CommonMark validation errors
    - _Requirements: 10_

  - [x] 5.2 Run `measure_steering.py` to update token counts
    - Execute `python senzing-bootcamp/scripts/measure_steering.py`
    - Verify both files are under the 5,000-token threshold
    - Update `steering-index.yaml` token counts with measured values
    - _Requirements: 5, 9_

- [x] 6. Update test files for the split
  - [x] 6.1 Update `test_remove_duplicate_module_table.py`
    - Change path reference from `onboarding-flow.md` to `onboarding-phase2-track-setup.md` for Step 5 content assertions
    - _Requirements: 11_

  - [x] 6.2 Update `test_module_flow_integration.py`
    - Change path reference for Step 5 track bullet assertions to `onboarding-phase2-track-setup.md`
    - _Requirements: 11_

  - [x] 6.3 Update `test_hook_consolidation.py`
    - Update to check both `onboarding-flow.md` and `onboarding-phase2-track-setup.md` for hook references
    - _Requirements: 11_

  - [x] 6.4 Update `test_self_answering_questions_preservation.py`
    - Update to test stop markers in both files if assertions reference onboarding content
    - _Requirements: 11_

  - [x] 6.5 Update `test_self_answering_reinforcement.py`
    - Update to check 🛑 STOP markers after 👉 questions in both files
    - _Requirements: 11_

- [x] 7. Final checkpoint - Run full test suite
  - Run `pytest senzing-bootcamp/tests/` to verify no regressions
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- No tasks are marked optional because property-based testing is not applicable for this feature (structural markdown refactoring with no algorithmic logic)
- Each task references specific requirements for traceability
- The split boundary is between Step 4c (Comprehension Check) and Step 5 (Track Selection)
- The pattern follows existing module phase splits (e.g., module-01 → module-01-phase2)
- Token target per file is ≤3,500 with a hard limit of 5,000

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1", "2.2", "2.3", "3.1", "3.2"] },
    { "id": 3, "tasks": ["5.1", "5.2"] },
    { "id": 4, "tasks": ["6.1", "6.2", "6.3", "6.4", "6.5"] }
  ]
}
```
