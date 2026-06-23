# Implementation Plan: Graduation Artifact Inventory

## Overview

Implement a stdlib-only Python CLI script that generates a "Complete Artifact Inventory" Markdown
section from `config/bootcamp_progress.json` and the files present in the bootcamper's project,
grouped by phase and annotated with why-it-matters notes and carry-forward / leave-behind
classifications. Then wire the `graduation.md` steering file to run the script and embed its
output into `GRADUATION_REPORT.md` (non-blocking). Tests use pytest + Hypothesis.

## Tasks

- [x] 1. Create script skeleton with CLI, data model, and catalog
  - [x] 1.1 Create `senzing-bootcamp/scripts/generate_artifact_inventory.py` with shebang, module
    docstring, `from __future__ import annotations`, the `CatalogArtifact` dataclass, `PHASE_ORDER`,
    a stub `ARTIFACT_CATALOG`, `parse_args(argv)` (`--progress-file`, `--project-root`, `--output`,
    `--show-missing`), and a `main(argv=None)` that returns 0/1 and the `if __name__ == "__main__"`
    guard
    - _Requirements: 1.1, 1.2_
  - [x] 1.2 Populate `ARTIFACT_CATALOG` with all module artifacts from `config/module-artifacts.yaml`
    plus the bootcamp-record entries (recap, journal, progress, completion summary, certificate),
    each with phase, module, classification, and a concise why-it-matters note
    - _Requirements: 2.1, 3.1, 3.2, 3.3, 3.4_
  - [x] 1.3 Write unit tests for argument parsing (defaults and overrides for each flag)
    - _Requirements: 1.1_

- [x] 2. Implement progress loading
  - [x] 2.1 Implement `load_modules_completed(path)` returning `(modules_completed, complete)`,
    treating missing/malformed JSON as empty with `complete=False`
    - _Requirements: 1.2, 4.2_
  - [x] 2.2 Write unit tests for `load_modules_completed` with valid, missing, and malformed JSON
    - _Requirements: 1.2, 4.2_

- [x] 3. Implement artifact scanning
  - [x] 3.1 Implement `artifact_exists(root, art)` (files must be regular files; directories must
    exist and be non-empty) and `collect_present_artifacts(root, catalog)` preserving catalog order,
    skipping any path that errors during the check
    - _Requirements: 1.3, 2.3, 4.3_
  - [x] 3.2 Write unit tests for `artifact_exists` (present file, absent file, empty dir, non-empty
    dir) and `collect_present_artifacts`
    - _Requirements: 1.3, 2.3_
  - [x] 3.3 Write property test: only existing artifacts are listed (Property 1)
    - **Property 1: Only existing artifacts are listed**
    - Materialize a random subset of catalog paths in a temp root; assert collected artifacts equal
      the materialized subset and exclude absent paths
    - **Validates: Requirements 1.3, 2.3**
  - [x] 3.4 Write property test: no fabrication for incomplete modules (Property 5)
    - **Property 5: No fabrication for incomplete modules**
    - For random `modules_completed` sets, assert no absent-on-disk artifact ever appears
    - **Validates: Requirements 2.2, 2.3**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the renderer
  - [x] 5.1 Implement `render_inventory(present, *, progress_complete, modules_completed,
    show_missing)` — always emit the `## Complete Artifact Inventory` heading, group by phase in
    `PHASE_ORDER`, omit empty groups, render each artifact with path + note + classification tag
    (`_(carry-forward)_` vs `_(bootcamp record)_`), and prepend an incompleteness note when
    `progress_complete` is False
    - _Requirements: 1.1, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 4.2_
  - [x] 5.2 Write unit tests for rendering (heading present, phase sub-headings in order, tag text,
    incompleteness note when progress incomplete, no empty groups)
    - _Requirements: 1.1, 2.1, 3.2, 3.3, 4.2_
  - [x] 5.3 Write property test: every listed artifact is fully annotated (Property 2)
    - **Property 2: Every listed artifact is fully annotated**
    - Assert every rendered artifact line contains its path, a non-empty note, and a classification
      tag
    - **Validates: Requirements 3.1, 3.4**
  - [x] 5.4 Write property test: classification matches artifact role (Property 3)
    - **Property 3: Classification matches artifact role**
    - Assert carry-forward entries render the carry-forward tag and leave-behind entries render the
      learning/record tag
    - **Validates: Requirements 3.2, 3.3**
  - [x] 5.5 Write property test: artifacts are grouped by phase (Property 4)
    - **Property 4: Artifacts are grouped by phase**
    - Assert each listed artifact appears under exactly one phase sub-heading, sub-headings follow
      `PHASE_ORDER`, and no empty group is emitted
    - **Validates: Requirements 2.1, 2.2**
  - [x] 5.6 Write property test: inventory never duplicates the production-subset tables (Property 7)
    - **Property 7: Inventory never duplicates the production-subset tables**
    - Assert the rendered output contains the inventory heading and does not emit files-generated or
      files-excluded tables
    - **Validates: Requirements 1.4, 4.4**

- [x] 6. Wire the pipeline and file output
  - [x] 6.1 Wire `main()`: parse args → load progress → collect present artifacts → render → write
    to `--output` or stdout; wrap in a top-level exception handler that prints to stderr and exits 1
    - _Requirements: 1.1, 4.1, 4.3_
  - [x] 6.2 Write property test: robust, non-blocking generation (Property 6)
    - **Property 6: Robust, non-blocking generation**
    - Feed valid/missing/malformed/binary progress content; assert `main()` never raises, output
      always begins with the inventory heading, and an incompleteness note appears when progress is
      unreadable
    - **Validates: Requirements 4.1, 4.2, 4.3**
  - [x] 6.3 Write the catalog drift-guard unit test
    - Extract every `path:` value under `modules:` in `config/module-artifacts.yaml` (line-based, no
      PyYAML) and assert each appears in `ARTIFACT_CATALOG`
    - _Requirements: 1.2, 2.1_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Steering and documentation integration
  - [x] 8.1 Update `senzing-bootcamp/steering/graduation.md` "Graduation Report" section to run
    `generate_artifact_inventory.py` and embed its output as a "Complete Artifact Inventory" section
    placed after the files-excluded table and before Next Steps; make it non-blocking (note failures
    under "⚠️ Issues Encountered") and instruct not to duplicate/contradict the files tables
    - _Requirements: 1.1, 1.4, 4.1, 4.3, 4.4_
  - [x] 8.2 Add a one-line entry for `generate_artifact_inventory.py` to `senzing-bootcamp/scripts/README.md`
    and `senzing-bootcamp/docs/guides/SCRIPT_REFERENCE.md`
    - _Requirements: 1.1_

- [x] 9. Final checkpoint - Ensure all tests pass and CI validators succeed
  - Ensure all tests pass and `validate_commonmark.py` accepts the steering edit; ask the user if
    questions arise.

## Notes

- Each task references specific requirements for traceability.
- Property tests validate the universal correctness properties from the design document.
- Unit tests validate specific examples and edge cases.
- The script uses only Python 3.11+ stdlib (no third-party dependencies).
- Tests use pytest + Hypothesis and live in `senzing-bootcamp/tests/`.
- The in-code `ARTIFACT_CATALOG` is the single source for inventory annotations; the drift-guard
  test keeps it aligned with `config/module-artifacts.yaml`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["1.3", "2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4"] },
    { "id": 4, "tasks": ["5.1"] },
    { "id": 5, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6"] },
    { "id": 6, "tasks": ["6.1", "6.3"] },
    { "id": 7, "tasks": ["6.2"] },
    { "id": 8, "tasks": ["8.1", "8.2"] }
  ]
}
```
