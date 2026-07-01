# Implementation Plan: Module 3 First-Visualization Guarantee

## Overview

This plan implements a journey-level guarantee that every bootcamper sees a first
entity-resolution visualization even when they opt out of Module 3. The core is a small,
pure marker helper added to the existing `scripts/progress_utils.py`, a backward-compatible
schema extension, and steering/governance framing that reuses the Module 3 Step 9
web-service pattern and the existing Visualization Offer Protocol. The Step 9 mandatory gate
and the canonical Governing Rule 15 are preserved unchanged.

Implementation language: **Python 3.11+ (stdlib only)**, tests with **pytest + Hypothesis**,
per project conventions. All new code lives in `senzing-bootcamp/scripts/`, steering in
`senzing-bootcamp/steering/`, config in `senzing-bootcamp/config/`, and tests in
`senzing-bootcamp/tests/`.

## Tasks

- [x] 1. Extend progress schema for the `first_visualization` marker
  - [x] 1.1 Add optional `first_visualization` object to `validate_progress_schema` / `ProgressSchema` in `senzing-bootcamp/scripts/progress_utils.py`
    - Accept an optional top-level `first_visualization` dict; absence means "not owed"
    - Validate `status ∈ {"owed", "satisfied"}`; `owed_at`/`satisfied_at` (if non-null) are valid ISO 8601; `satisfied_by` (if non-null) is a non-empty string
    - When `status == "satisfied"`, expect `satisfied_by` and `satisfied_at` non-null
    - Keep all existing fields and legacy files valid (backward compatible)
    - _Requirements: 1.1, 2.3_

  - [x] 1.2 Write unit tests for the schema extension
    - Assert a valid `first_visualization` marker passes and malformed ones (bad `status`, non-ISO timestamps, empty `satisfied_by`) are rejected
    - Assert legacy progress files without the marker still validate
    - _Requirements: 1.1, 2.3, 4.3_

- [x] 2. Implement the `first_visualization` marker helper
  - [x] 2.1 Implement marker functions in `senzing-bootcamp/scripts/progress_utils.py`
    - Implement `mark_first_visualization_owed(reason="module_3_opt_out", progress_path=...)`, `clear_first_visualization_owed(satisfied_by, progress_path=...)`, and `is_first_visualization_owed(progress)`
    - Reuse `_read_progress` / `_write_progress` (2-space indent, trailing newline, parent-dir creation, backward-compatible parse)
    - Enforce monotonic lifecycle: never regress `satisfied` → `owed`; clearing a never-owed/already-satisfied marker is a no-op
    - Handle missing/empty progress file as `{}`; on invalid JSON surface a clear error without a partial write
    - _Requirements: 1.1, 2.2, 2.3_

  - [x] 2.2 Write property test for the owed-on-opt-out invariant
    - **Property 1: Opting out records an owed first visualization (monotonic)**
    - Generate varied valid progress dicts (marker absent / `owed` / `satisfied`); after `mark_first_visualization_owed` assert the marker is present and owed, except when already `satisfied` (unchanged)
    - Tag: `Feature: module3-first-visualization-guarantee, Property 1`
    - **Validates: Requirements 1.1**

  - [x] 2.3 Write property test for clear + idempotence
    - **Property 3: Any generated first visualization clears the owed marker (idempotently)**
    - Generate progress dicts in any marker state; assert `clear_first_visualization_owed` yields `not is_first_visualization_owed` and status `"satisfied"`, and a second clear is a no-op
    - Tag: `Feature: module3-first-visualization-guarantee, Property 3`
    - **Validates: Requirements 2.2, 2.3**

  - [x] 2.4 Write unit tests for marker error handling
    - Cover missing/empty file, invalid JSON, monotonic no-op, and never-owed clear no-op paths
    - _Requirements: 2.3, 4.1_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Wire the owed marker into the Module 3 Opt-Out Gate
  - [x] 4.1 Update the "## Opt-Out Gate" section of `senzing-bootcamp/steering/module-03-phase1-verification.md`
    - On trigger, after recording the module-3 skip, also call `mark_first_visualization_owed(reason="module_3_opt_out")`
    - Present the Standalone Demo Visualization as an offer (not a forced step) using the visualization-guide offer template; declining moves to the deferred guarantee
    - Keep the explicit distinction: Step 9 is unconditional whenever Module 3 runs; this journey-level guarantee covers the opt-out case only
    - _Requirements: 1.1, 2.1, 3.3_

  - [x] 4.2 Write content test for the standalone offer framing
    - Assert the Opt-Out Gate section offers the standalone demo as an offer (not forced) and references the Step 9 web-service constraints (stdlib HTTP server, D3.js v7 CDN, single HTML file, working-directory artifacts)
    - _Requirements: 2.1, 3.1_

- [x] 5. Implement the Standalone Demo Visualization
  - [x] 5.1 Create a minimal TruthSet-backed standalone demo reusing the Step 9 web-service pattern
    - Add a `write_html.py` generator + stdlib `http.server` runner under the working directory (`src/system_verification/web_service/`), matching `module-03-phase2-visualization.md` constraints (D3.js v7 CDN, single self-contained HTML file)
    - On successful generation call `clear_first_visualization_owed(satisfied_by="standalone_demo")`; on failure reuse Step 9 fallback and leave the marker `owed`
    - _Requirements: 2.1, 2.3, 3.1_

- [x] 6. Wire the deferred guarantee into the Visualization Offer Protocol
  - [x] 6.1 Update `senzing-bootcamp/steering/visualization-guide.md` and Module 6/7 steering for the deferred path
    - In the Decline/Generate handling, when a visualization is generated at the Module 6 results-dashboard or Module 7 (`m7_exploratory_queries`) checkpoint AND `first_visualization` is `owed`, also call `clear_first_visualization_owed(satisfied_by="module_6_deferred" | "module_7_deferred")`
    - Reuse the existing `config/visualization_tracker.json` offer flow; do not add a new offer template, tracker, or checkpoint map
    - _Requirements: 2.2, 2.3, 3.2_

  - [x] 6.2 Write content test for deferred reuse
    - Assert the deferred wiring references the existing `visualization-guide.md` Module 6/7 checkpoints and reuses `visualization_tracker.json` without a new parallel offer template
    - _Requirements: 2.2, 3.2_

- [x] 7. Add journey-level governance rule (Rule 15 untouched)
  - [x] 7.1 Add a new, separate entry to `senzing-bootcamp/config/governance-rules.yaml`
    - Describe the journey-level first-visualization guarantee with assertions pinning (a) the owed marker is set at the opt-out point and (b) the two satisfaction paths exist in steering
    - Leave `rule-15-module3-visualization-gate` and its assertions byte-stable
    - _Requirements: 1.3, 3.3_

  - [x] 7.2 Write preservation tests for the Step 9 gate and Rule 15 pin
    - **Property 2: The Step 9 in-module gate remains unconditional**
    - Reuse `validate_mandatory_gates._check_gate` against the real Step 9 gate; generate progress past `3.9` with varied checkpoint/skip combos and assert a violation whenever both checkpoints are not `"passed"` (a `skipped_steps["3.9"]` entry never satisfies the gate)
    - Also assert `governance-rules.yaml` `rule-15-module3-visualization-gate` retains its pinned assertions and `validate_mandatory_gates.NON_SKIPPABLE_GATES == {"3.9"}`
    - Tag: `Feature: module3-first-visualization-guarantee, Property 2`
    - **Validates: Requirements 1.2, 1.3**

- [x] 8. Add explicit-distinction content coverage
  - [x] 8.1 Write content test for the explicit distinction framing
    - Assert steering/governance framing states both that Step 9 is unconditional when Module 3 runs and that the journey-level guarantee covers the opt-out case separately
    - _Requirements: 3.3, 4.2_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific requirements (granular clauses) for traceability.
- Property tests use the repo Hypothesis profiles (`fast`=5 local, `thorough`=100 CI) via
  `hypothesis_profiles.py` / `conftest.py`; do not hand-set `max_examples`.
- Tests are class-based and import scripts via the `sys.path` pattern in
  `senzing-bootcamp/tests/`, per `python-conventions.md`.
- Tasks 1.1 and 2.1 both modify `progress_utils.py` and are intentionally sequenced in
  separate waves to avoid write conflicts.
- This feature does not weaken the Step 9 gate or modify Governing Rule 15.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "4.1", "7.1"] },
    { "id": 3, "tasks": ["4.2", "5.1", "6.1", "7.2", "8.1"] },
    { "id": 4, "tasks": ["6.2"] }
  ]
}
```
