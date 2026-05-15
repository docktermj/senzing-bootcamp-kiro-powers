# Implementation Plan: Mapping Regression Testing

## Overview

Implement a lightweight Python comparison script and steering integration that lets bootcampers see the impact of mapping changes on entity resolution results during Module 5 Phase 3. The implementation uses stdlib-only Python, JSON baseline files, and integrates into the existing test-load steering workflow.

## Tasks

- [x] 1. Create comparison script with core data models and CLI
  - [x] 1.1 Create `senzing-bootcamp/scripts/compare_results.py` with ERStatistics dataclass and load_statistics function
    - Define `ERStatistics` dataclass with fields: datasource, entity_count, record_count, match_count, possible_match_count, relationship_count, captured_at
    - Implement `load_statistics(path)` function that reads a JSON file, validates required fields, and returns an `ERStatistics` instance
    - Handle error cases: missing file, invalid JSON, missing required fields, with appropriate error messages and exit codes
    - _Requirements: 1, 2_

  - [x] 1.2 Implement `compare()` function and `ComparisonResult` dataclass
    - Define `ComparisonResult` dataclass with delta fields: entity_delta, record_delta, match_delta, possible_match_delta, relationship_delta, quality_assessment
    - Implement `compare(baseline, current)` as a pure function computing deltas (current - baseline) for each metric
    - _Requirements: 1, 3_

  - [x] 1.3 Implement `assess_quality()` function
    - Implement quality assessment heuristic: "improved" if match_count increased OR entity_count decreased (with no decrease in match_count), "degraded" if match_count decreased OR entity_count increased (with no increase in match_count), "unchanged" otherwise
    - _Requirements: 3_

  - [x] 1.4 Implement `format_report()` function
    - Format `ComparisonResult` as human-readable text showing entities gained/lost, matches gained/lost, possible matches gained/lost, relationships gained/lost, and net quality assessment
    - Use +/- notation for deltas (e.g., "+5 matches", "-3 entities")
    - _Requirements: 3_

  - [x] 1.5 Implement `baseline_path()` and `accept_baseline()` functions
    - `baseline_path(datasource)` returns `config/er_baseline_{datasource_lower}.json`
    - `accept_baseline(current_path, datasource)` copies current stats file to the canonical baseline path
    - _Requirements: 7, 8_

  - [x] 1.6 Implement `main()` CLI entry point with argparse
    - Accept `--baseline <file>` and `--current <file>` arguments
    - If baseline file missing, print informative message and save current as baseline (exit 0)
    - If baseline exists, run comparison and print formatted report
    - Exit 0 on success, exit 1 on error
    - _Requirements: 1, 2_

- [x] 2. Checkpoint - Ensure comparison script works end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Write tests for comparison script
  - [x] 3.1 Write property test for comparison delta correctness
    - **Property 1: Comparison produces correct deltas with complete output**
    - Generate random pairs of ERStatistics with non-negative integer counts
    - Assert each delta equals current - baseline for every metric
    - Assert quality_assessment is one of "improved", "degraded", "unchanged"
    - **Validates: Requirements 1, 3**

  - [x] 3.2 Write property test for baseline path construction
    - **Property 2: Baseline path construction**
    - Generate random datasource name strings (alphanumeric + underscores)
    - Assert output matches pattern `config/er_baseline_{datasource_lower}.json`
    - **Validates: Requirements 7**

  - [x] 3.3 Write property test for incremental baseline update
    - **Property 3: Incremental baseline update preserves last accepted state**
    - Generate random sequences of (ERStatistics, accept: bool) pairs
    - Assert stored baseline equals most recently accepted snapshot
    - **Validates: Requirements 8**

  - [x] 3.4 Write property test for quality assessment consistency
    - **Property 4: Quality assessment consistency**
    - Generate constrained ERStatistics pairs where match/entity deltas have known direction
    - Assert "improved" when match_count increased and entity_count did not increase
    - Assert "degraded" when match_count decreased and entity_count did not decrease
    - **Validates: Requirements 3**

  - [x] 3.5 Write example-based unit tests for comparison scenarios
    - Test identical baselines → all deltas zero, assessment "unchanged"
    - Test improved results → more matches, fewer entities → assessment "improved"
    - Test degraded results → fewer matches, more entities → assessment "degraded"
    - Test missing baseline file → graceful handling with informative message
    - Test invalid JSON → clear error message
    - Test CLI arg parsing → verify --baseline and --current flags work
    - _Requirements: 10_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Integrate into steering and documentation
  - [x] 5.1 Update Module 5 Phase 3 test-load steering with baseline capture and comparison steps
    - Add a sub-step after ER evaluation (step 24) that captures statistics to a JSON file using the Senzing SDK
    - Add baseline detection logic: if no baseline exists, save current stats as baseline
    - Add comparison trigger: if baseline exists, run `compare_results.py` and present diff
    - Add accept/reject gate: ask bootcamper whether to accept new results as baseline
    - _Requirements: 4, 5, 6, 8_

  - [x] 5.2 Add compare_results.py to POWER.md "Useful Commands" section
    - Document the script usage with `--baseline` and `--current` flags
    - Include a brief description of what the script does
    - _Requirements: 9_

  - [x] 5.3 Write structural tests for steering and POWER.md integration
    - Test that Module 5 Phase 3 steering contains baseline capture step
    - Test that POWER.md Useful Commands section lists compare_results.py
    - _Requirements: 4, 9_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The script uses stdlib-only Python (no third-party dependencies) per project conventions
- Tests use pytest + Hypothesis (already available in the project)
- All paths are relative to `senzing-bootcamp/` as per project structure conventions

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.5"] },
    { "id": 2, "tasks": ["1.3", "1.4", "1.6"] },
    { "id": 3, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5"] },
    { "id": 4, "tasks": ["5.1", "5.2"] },
    { "id": 5, "tasks": ["5.3"] }
  ]
}
```
