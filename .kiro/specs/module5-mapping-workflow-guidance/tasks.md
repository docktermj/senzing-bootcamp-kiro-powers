# Implementation Plan

## Overview

This plan fixes the brittle Module 5 (Data Quality & Mapping) Phase 2 mapping-workflow guidance
using the bug-condition methodology. The fix is power-side, steering/documentation only — no
runtime/code changes. Following the exploratory bugfix workflow, bug-demonstrating tests are
written FIRST (task 1) to surface counterexamples, preservation tests capture baseline behavior
(task 2), then the fix is applied to the steering and companion doc (task 3) and validated against
both test suites (tasks 3.4–3.5, 4).

## Tasks

- [x] 1. Write bug condition exploration tests (BEFORE implementing the fix)
  - **Property 1: Bug Condition** - Resilient Validation When Scripts Are Unavailable; **Property 2: Bug Condition** - Forward Guidance After the Step 5 Menu
  - **CRITICAL**: These tests MUST FAIL on the unfixed guidance - failure confirms the bug exists
  - **DO NOT attempt to fix the tests or the guidance when they fail**
  - **NOTE**: These tests encode the expected behavior - they will validate the fix when they pass after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in the current Module 5 Phase 2 steering
  - **Scoped PBT Approach**: The artifact under test is steering/documentation text, so model the bug as a `WorkflowState` (step, scriptAvailability map, menuReturned) and scope the property to the concrete failing cases — Step 4 with `sz_verbatim_check.py`/`sz_routing_report.py` unavailable (HTTP 404), and Step 5 with the `detect_environment` menu returned
  - Create `senzing-bootcamp/tests/test_module5_mapping_workflow_guidance_exploration.py` (pytest + Hypothesis)
  - Assert the Step 4 guidance in `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` contains an "if `sz_verbatim_check.py` unavailable → skip as optional/best-effort, proceed" branch (from Bug Condition Aspect A; expected behavior 2.1)
  - Assert the Step 4 guidance contains an "if `sz_routing_report.py` unavailable → skip as optional/best-effort, proceed" branch (Aspect A; expected behavior 2.2)
  - Assert the guidance names `sz_json_analyzer.py` as the primary validation sufficient to proceed when the other scripts are absent (expected behavior 2.3)
  - Assert the guidance explains the Step 5 `detect_environment` menu — that Steps 5–8 are optional sandbox validation and enumerates the four options (skip / test_load / load+resolve / done) (Aspect B; expected behavior 2.4)
  - Assert the guidance recommends skipping the per-source test load (real load deferred to Module 6) and continuing to the next unmapped source when sources remain (Aspect B; expected behavior 2.5)
  - Run the tests on the UNFIXED guidance
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct - it proves the bug exists: hard-gate framing with no unavailability branch, and no Step 5 menu handling)
  - Document counterexamples found to confirm the root cause (missing degradation branch, missing Step 5 interpretation, missing multi-source continuation logic)
  - Mark task complete when tests are written, run, and the failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Write preservation property tests (BEFORE implementing the fix)
  - **Property 3: Preservation** - Normal Mapping Workflow Unchanged
  - **IMPORTANT**: Follow the observation-first methodology — observe behavior on the UNFIXED guidance for non-bug inputs (cases where `isBugCondition` returns false), then encode it
  - Observe on unfixed guidance: when `sz_json_analyzer.py` is available, structural + Entity-Specification validation runs as the primary mapping validation (3.1)
  - Observe: when the verbatim-fidelity and routing-coverage scripts ARE available (HTTP 200 / working inline fallback), their checks run as before (3.2)
  - Observe: the normal per-source `mapping_workflow` progression and Step 4 approval are present and unchanged (3.3)
  - Observe: explicit `test_load` / `load+resolve` selections at the Step 5 menu enter Phase 3 (Steps 5–8) as before, cross-referenced in `senzing-bootcamp/steering/module-05-phase3-test-load.md` (3.4)
  - Observe: the production/real load remains deferred to Module 6 (3.5)
  - Create `senzing-bootcamp/tests/test_module5_mapping_workflow_guidance_preservation.py` (pytest + Hypothesis)
  - Write property-based tests that generate non-bug `WorkflowState` inputs (all three scripts hosted; every step other than the Step 4 gate and Step 5 menu; and explicit `test_load` / `load+resolve` choices) and assert the captured behavior is present in the guidance
  - Run the tests on the UNFIXED guidance
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior that must be preserved)
  - Mark task complete when tests are written, run, and passing on the unfixed guidance
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix the brittle Module 5 Phase 2 mapping-workflow guidance

  - [x] 3.1 Add an availability-aware validation branch at Step 4 in the Phase 2 steering
    - In `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`, replace the hard "do NOT proceed until verbatim-fidelity passes" framing with conditional guidance
    - If `sz_verbatim_check.py` is available → run the verbatim-fidelity check as before; if unavailable (HTTP 404 / no working inline fallback) → announce it is skipped because the script is unavailable, treat as optional/best-effort, and continue
    - Degrade the routing-coverage report the same way: if `sz_routing_report.py` is available → run it; if unavailable → announce skip, treat as optional/best-effort, continue
    - State explicitly that `sz_json_analyzer.py` (structural + Entity-Specification validation) is the primary mapping validation and is sufficient to proceed when the verbatim/routing scripts are unavailable
    - _Bug_Condition: isBugCondition(input) where input.step == 4 AND (NOT scriptAvailability['sz_verbatim_check.py'] OR NOT scriptAvailability['sz_routing_report.py']) — Aspect A from design_
    - _Expected_Behavior: Property 1 — degrade affected checks to optional/best-effort, inform bootcamper, proceed via sz_json_analyzer.py without blocking_
    - _Preservation: sz_json_analyzer.py validation, verbatim/routing checks when available, normal progression and Step 4 approval (3.1, 3.2, 3.3)_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 Add explicit Step 5 menu handling and multi-source continuation guidance
    - In `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`, when `mapping_workflow` returns the `detect_environment` menu, explain that Steps 5–8 are optional sandbox validation and describe the four options (skip / test_load / load+resolve / done)
    - When one or more unmapped sources remain, recommend skipping the per-source test load (note the real load happens in Module 6) and automatically continue to the next unmapped source
    - Preserve the explicit `test_load` / `load+resolve` paths when the bootcamper chooses them
    - In `senzing-bootcamp/steering/module-05-phase3-test-load.md`, cross-reference the Step 5 menu handling so explicitly chosen `test_load` / `load+resolve` paths still enter Phase 3 (Steps 5–8) unchanged
    - _Bug_Condition: isBugCondition(input) where input.step == 5 AND input.menuReturned == true — Aspect B from design_
    - _Expected_Behavior: Property 2 — state Steps 5–8 are optional, explain choices, recommend skip + continue to next unmapped source when sources remain_
    - _Preservation: explicit test_load / load+resolve Phase 3 paths and deferral of the real load to Module 6 (3.4, 3.5)_
    - _Requirements: 2.4, 2.5_

  - [x] 3.3 Update the companion user doc to match the resilient guidance
    - In `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`, update the Phase 2 validation description and the Step 5 decision so they match the resilient guidance (optional/best-effort checks when scripts are unavailable, optional Steps 5–8, skip recommendation when sources remain)
    - _Expected_Behavior: Property 1 and Property 2 reflected in user-facing documentation_
    - _Preservation: existing description of normal progression, available-script checks, and Module 6 deferral remains accurate (3.1–3.5)_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.4 Verify bug condition exploration tests now pass
    - **Property 1: Expected Behavior** - Resilient Validation When Scripts Are Unavailable; **Property 2: Expected Behavior** - Forward Guidance After the Step 5 Menu
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - The tests from task 1 encode the expected behavior; when they pass, they confirm the expected behavior is satisfied
    - Run the exploration tests from task 1 (`test_module5_mapping_workflow_guidance_exploration.py`)
    - **EXPECTED OUTCOME**: Tests PASS (confirms the bug is fixed for all buggy inputs)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 3: Preservation** - Normal Mapping Workflow Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from task 2 (`test_module5_mapping_workflow_guidance_preservation.py`)
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions for non-buggy inputs)
    - Confirm all tests still pass after the fix
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full Module 5 mapping-workflow guidance test suite (exploration + preservation) plus related existing suites (e.g., `test_mapping_workflow_integration.py`) to confirm no regressions
  - Run `validate_commonmark.py` / `measure_steering.py --check` as appropriate for the edited steering and doc files
  - Ensure all tests pass; ask the user if questions arise

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "description": "Author bug-demonstrating and preservation tests before any fix (run on unfixed guidance)",
      "tasks": ["1", "2"]
    },
    {
      "wave": 2,
      "description": "Apply the steering/documentation fix",
      "tasks": ["3.1", "3.2", "3.3"],
      "dependsOn": ["1", "2"]
    },
    {
      "wave": 3,
      "description": "Verify the fix passes and preservation holds",
      "tasks": ["3.4", "3.5"],
      "dependsOn": ["3.1", "3.2", "3.3"]
    },
    {
      "wave": 4,
      "description": "Final checkpoint - ensure all tests pass",
      "tasks": ["4"],
      "dependsOn": ["3.4", "3.5"]
    }
  ]
}
```

## Notes

- Bug-condition methodology: tasks 1 and 2 MUST be completed before any fix work. Task 1 tests
  encode the expected behavior and MUST FAIL on the unfixed guidance (confirming the bug); task 2
  tests MUST PASS on the unfixed guidance (capturing baseline behavior to preserve).
- The artifact under test is steering/documentation, so tests assert on the presence/absence of
  guidance branches and the conditions under which they apply, rather than executable runtime
  output.
- Property 1 (Requirements 2.1–2.3) and Property 2 (Requirements 2.4–2.5) cover the fix; Property 3
  (Requirements 3.1–3.5) covers preservation.
- Tests use pytest + Hypothesis and live in `senzing-bootcamp/tests/`.
- Do NOT re-write tests in tasks 3.4/3.5 — re-run the same tests authored in tasks 1 and 2.
- Re-hosting the missing scripts is a server-side concern outside this fix's scope.
