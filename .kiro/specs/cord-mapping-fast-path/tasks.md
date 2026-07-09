# Implementation Plan: CORD Mapping Fast-Path

## Overview

This plan implements the CORD mapping fast-path feature across steering files, a helper script, registry schema documentation, and a property-based test suite. The implementation is primarily steering Markdown changes with an optional Python stdlib-only helper script and comprehensive Hypothesis tests.

## Tasks

- [x] 1. Implement Module 4 provenance recording and registry schema extension
  - [x] 1.1 Add CORD Provenance Recording instruction to Module 4 steering
    - Insert the "Agent instruction — CORD Provenance Recording" block in `senzing-bootcamp/steering/module-04-data-collection.md` after the existing "CORD Metadata Capture" agent instruction in Step 2
    - The block defines provenance values: `cord`, `own`, `free_data`, `synthesized`, `unknown`
    - Includes ISO 8601 `updated_at` timestamp requirement
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_

  - [x] 1.2 Update `config/data_sources.yaml.example` with new optional fields
    - Add `provenance`, `senzing_ready`, and `fast_pathed` fields to the example registry entry in `senzing-bootcamp/config/data_sources.yaml.example` (or create it if not present)
    - Document that these fields are additive and optional — absence does not break existing behavior
    - _Requirements: 1.3, 6.6, 2.6_

- [x] 2. Implement Module 5 Phase 1 readiness check and fast-path offer
  - [x] 2.1 Insert Step 5a into Module 5 Phase 1 steering
    - Add the "CORD Readiness Check and Fast-Path Offer" step in `senzing-bootcamp/steering/module-05-phase1-quality-assessment.md` between Step 5 (Categorize) and Step 6 (Assess quality)
    - Step obtains Senzing schema from MCP via `download_resource`, performs bounded structural check (≤100 records), records `senzing_ready` in registry, presents bold 👉 offer with 🛑 STOP gate
    - Handles both confirmed and declined paths, plus non-ready and non-CORD fallbacks
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 2.2 Write property test for readiness classification correctness
    - **Property 2: Readiness classification correctness**
    - **Validates: Requirements 2.3, 2.4**

  - [x] 2.3 Write property test for bounded sample invariant
    - **Property 3: Bounded sample invariant**
    - **Validates: Requirements 2.5**

  - [x] 2.4 Write property test for unavailable schema defaults to not-ready
    - **Property 4: Unavailable schema defaults to not-ready**
    - **Validates: Requirements 2.7, 8.5**

- [x] 3. Implement Module 5 Phase 2 skip guard and hub update
  - [x] 3.1 Add fast-path skip guard to Module 5 Phase 2 steering
    - Insert the "Agent instruction — Skip fast-pathed sources" block at the top of `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`, before the "Mapping Verbosity Check" section
    - Guard checks `fast_pathed: true` and `mapping_status: complete` in registry before starting mapping for a source
    - _Requirements: 4.1, 5.1, 6.1, 6.2_

  - [x] 3.2 Update Module 5 hub file with fast-path mention
    - In `senzing-bootcamp/steering/module-05-data-quality-mapping.md`, update the Phase 1 bullet in the "Phase Sub-Files" section to include the note: *(Includes CORD readiness check and fast-path offer for eligible sources)*
    - _Requirements: 3.1, 3.3_

- [x] 4. Checkpoint — Ensure all steering changes are valid
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the readiness check helper script
  - [x] 5.1 Create `check_cord_readiness.py` helper script
    - Create `senzing-bootcamp/scripts/check_cord_readiness.py` with full implementation
    - Implements `ReadinessResult` dataclass, `check_readiness()` function, and `main()` CLI entry point
    - Uses only Python stdlib (`argparse`, `json`, `sys`, `pathlib`, `dataclasses`)
    - CLI accepts `--file`, `--schema-keys`, `--max-records` arguments
    - Outputs machine-readable JSON to stdout, human-readable summary to stderr
    - Exit code 0 = ready, 1 = not ready or error
    - ALL sampled records must pass for "ready" classification
    - _Requirements: 2.3, 2.4, 2.5, 2.8, 8.3_

  - [x] 5.2 Write unit tests for helper script CLI and conventions
    - Test `main()` entry point, argparse interface, exit codes 0/1
    - Verify script imports only stdlib modules
    - Test with valid CORD-like JSONL, legacy structure JSONL, and mixed records
    - _Requirements: 2.8, 8.3_

- [x] 6. Implement data lineage entry handling
  - [x] 6.1 Add lineage entry instructions to Step 5a steering
    - Ensure the Step 5a instruction (added in task 2.1) includes the lineage recording clause: when fast-path is confirmed, record a data-lineage entry with `source_file == output_file`, `records_in == records_out`, `records_rejected: 0`, `transformation_script: null`, `fast_pathed: true`
    - Non-blocking: if lineage write fails, fast-path still proceeds
    - _Requirements: 6.3, 6.4, 6.7, 6.8_

  - [x] 6.2 Write property test for fast-path lineage entry invariant
    - **Property 5: Fast-path lineage entry invariant**
    - **Validates: Requirements 6.4**

- [x] 7. Implement registry schema backward compatibility test and remaining property test
  - [x] 7.1 Write property test for registry schema backward compatibility
    - **Property 1: Registry schema backward compatibility**
    - **Validates: Requirements 1.3, 6.6**

  - [x] 7.2 Write example-based unit tests for provenance and readiness scenarios
    - Test valid provenance values (`cord`, `own`, `free_data`, `synthesized`, `unknown`)
    - Test `provenance: unknown` not eligible for fast-path
    - Test readiness check with valid CORD file → ready
    - Test readiness check with legacy structure → not ready
    - Test readiness check with mixed records → not ready
    - Test lineage failure is non-blocking
    - _Requirements: 1.1, 1.2, 1.5, 2.3, 2.4, 6.4, 6.8_

- [x] 8. Update token budgets in steering-index.yaml
  - [x] 8.1 Run `measure_steering.py` and update `steering-index.yaml`
    - Run `python senzing-bootcamp/scripts/measure_steering.py --check` to get updated token counts
    - Update token counts in `senzing-bootcamp/steering/steering-index.yaml` for all modified steering files: `module-04-data-collection.md`, `module-05-phase1-quality-assessment.md`, `module-05-phase2-data-mapping.md`, `module-05-data-quality-mapping.md`
    - Verify all files remain within their size categories
    - _Requirements: 8.4_

- [x] 9. Final checkpoint — Ensure all tests pass and CI checks are green
  - Run `python senzing-bootcamp/scripts/measure_steering.py --check` to confirm token budgets
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` to confirm steering files parse correctly
  - Run `pytest senzing-bootcamp/tests/test_cord_mapping_fast_path.py` to confirm all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The steering changes are the core deliverable; the helper script and tests provide supporting infrastructure
- Token budgets must be updated last since they depend on the final content of all modified steering files
- All Senzing schema facts come from MCP — never hardcoded in steering or scripts

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "5.1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "3.2"] },
    { "id": 2, "tasks": ["5.2", "6.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "6.2", "7.1", "7.2"] },
    { "id": 4, "tasks": ["8.1"] }
  ]
}
```
