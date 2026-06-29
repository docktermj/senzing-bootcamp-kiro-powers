# Implementation Plan

## Overview

This plan fixes the empty Module 3 Entity Graph (edge-key mismatch) by updating the
visualization-generation guidance and verification, then locking the change with a
guidance-validation test. The work is test-first: add a failing test, apply the steering
edits, then confirm the suite and CI checks pass. No application/runtime code and no API
schema changes are involved.

## Tasks

- [x] 1. Add the failing guidance-validation test (red)
  - Create `senzing-bootcamp/tests/test_module3_entity_graph_edge_key_mapping.py`, mirroring the structure and helpers of `senzing-bootcamp/tests/test_module3_entity_graph_relationships.py` (module-level path constants, `_read`, section-extraction helpers).
  - Assert the Critical Lessons section of `module-03-phase2-visualization.md` contains an edge-key-mapping lesson mentioning `source`/`target`, `source_entity_id`/`target_entity_id`, and `forceLink`.
  - Assert Step 9.4 contains a smoke/verification check referencing the graph edge-key mapping (`source`/`target` before `forceLink`) located before the bootcamper presentation gate (the `🛑 STOP` marker).
  - Add regression-guard assertions: the edge schema fields (`source_entity_id`, `target_entity_id`, `match_key`, `relationship_type`) remain present in both the Phase 2 file and `module-03-visualization-api-reference.md`, and the original six Critical Lessons remain present.
  - Run the test and confirm the new assertions FAIL against current (unfixed) steering content; confirm the regression-guard assertions PASS.
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2_

- [x] 2. Add the edge-key-mapping Critical Lesson to the Phase 2 steering
  - In `senzing-bootcamp/steering/module-03-phase2-visualization.md`, append a new item 7 to the `## CRITICAL LESSONS FOR VISUALIZATION GENERATION` list using the wording from design Change 1 (map `source_entity_id`/`target_entity_id` → `source`/`target` in `drawGraph` before `forceLink`; note it is a silent failure; preserve node `id`/`entity_id`).
  - Keep the imperative, bold-title style consistent with the existing six lessons.
  - _Requirements: 2.1, 2.2_

- [x] 3. Add the Entity Graph component edge-mapping note (Step 9.3)
  - In the Step 9.3 `Entity_Graph` tab section of `module-03-phase2-visualization.md`, add a short bullet near the "D3.js Code Style Constraints" stating that edges from `/api/graph` must be mapped to expose `source`/`target` before constructing the force simulation.
  - _Requirements: 2.2_

- [x] 4. Add the post-generation smoke check to Step 9.4
  - In Step 9.4 "Start and Verify Web Service" of `module-03-phase2-visualization.md`, add the smoke check described in design Change 4, positioned after `index.html` generation and before the Guided Tour / `🛑 STOP` presentation gate.
  - Specify the generated-code check (inspect generated `index.html` `drawGraph` for the `source`/`target` mapping derived from `source_entity_id`/`target_entity_id` before `forceLink`) and the rendered/data check (when `/api/graph` returns ≥1 node, the rendered graph shows visible node elements).
  - Add the verification-table row from the design and a Fix_Instruction (add edge-key mapping per Critical Lesson 7, regenerate `index.html`, re-verify); do not proceed to the Guided Tour until the graph passes.
  - _Requirements: 2.3_

- [x] 5. Add the API-reference cross-note (schema unchanged)
  - In the `GET /api/graph` section of `senzing-bootcamp/steering/module-03-visualization-api-reference.md`, add a one-line note after the edge schema description: `source_entity_id`/`target_entity_id` are the unchanged API contract; mapping to D3's `source`/`target` is a client-side concern handled in `drawGraph` (see the Critical Lesson in the Phase 2 steering).
  - Confirm the edge schema fields themselves are left unchanged.
  - _Requirements: 3.1_

- [x] 6. Run the test suite and CI checks (green)
  - Re-run `test_module3_entity_graph_edge_key_mapping.py` and confirm all assertions now PASS.
  - Run the existing `test_module3_entity_graph_relationships.py` and `test_visualization_enhancements_properties.py` to confirm no regressions (Req 3.3).
  - Run the CI validators that touch steering: `measure_steering.py --check` (token budget) and `validate_commonmark.py` (CommonMark) for the two edited steering files, then the full `pytest` suite.
  - Fix any token-budget or CommonMark issues introduced by the added guidance before closing the task.
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1"],
      "description": "Add the failing guidance-validation test (red)."
    },
    {
      "wave": 2,
      "tasks": ["2", "3", "4", "5"],
      "description": "Independent steering edits (Critical Lesson, Step 9.3 note, Step 9.4 smoke check, API-ref cross-note); any order, all depend on Task 1."
    },
    {
      "wave": 3,
      "tasks": ["6"],
      "description": "Run the suite and CI checks to turn the tests green; depends on Tasks 2-5."
    }
  ]
}
```

- Task 1 comes first (establishes the red test).
- Tasks 2–5 are independent steering edits and may be done in any order after Task 1.
- Task 6 runs last, once Tasks 2–5 are complete, to turn the suite green and validate CI.

## Notes

- Tests assert steering content (not runtime rendering), consistent with the existing
  `test_module3_entity_graph_relationships.py` lock-in pattern.
- Steering edits must respect the per-file token budgets in `steering-index.yaml`; keep the
  new Critical Lesson and smoke check concise (Task 6 verifies via `measure_steering.py --check`).
- No `/api/graph` schema change and no application code change — the mapping is client-side
  guidance only.
