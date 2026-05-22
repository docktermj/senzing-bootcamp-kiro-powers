# Implementation Plan: Token Budget Optimization

## Overview

Split the oversized `module-07-phase2-discover.md` (6,428 tokens) into two files at the step 4c/4d boundary, update `steering-index.yaml` and the root module file, then validate consistency. The split has already been performed — remaining work is validation testing.

## Tasks

- [x] 1. Split the steering file at the step 4c/4d boundary
  - [x] 1.1 Create Part A file (`module-07-phase2-discover.md`) with steps 4a–4c
    - Retain frontmatter (`inclusion: manual`), introduction, opt-in section, steps 4a–4c with checkpoints
    - Add navigation footer directing agent to load `module-07-phase2b-discover.md`
    - Include session resumption instruction
    - _Requirements: 1.1, 1.3, 1.5, 5.2, 5.3_

  - [x] 1.2 Create Part B file (`module-07-phase2b-discover.md`) with steps 4d–4e
    - Add frontmatter (`inclusion: manual`) and continuation header
    - Include steps 4d–4e and Discover Phase Completion section with checkpoints
    - Include session resumption instruction
    - Include note about returning to root file on completion
    - _Requirements: 1.2, 1.4, 1.6, 5.2, 5.3_

- [x] 2. Update steering-index.yaml
  - [x] 2.1 Replace single `phase2-discover` entry with `phase2a-discover` and `phase2b-discover`
    - Set `phase2a-discover`: file `module-07-phase2-discover.md`, step_range `["4a", "4c"]`
    - Set `phase2b-discover`: file `module-07-phase2b-discover.md`, step_range `["4d", "4e"]`
    - _Requirements: 2.1_

  - [x] 2.2 Update `file_metadata` section with both file entries and measured token counts
    - `module-07-phase2-discover.md`: token_count 3436, size_category large
    - `module-07-phase2b-discover.md`: token_count 3162, size_category large
    - _Requirements: 2.2_

  - [x] 2.3 Update `budget.total_tokens` to reflect new aggregate
    - _Requirements: 2.3_

- [x] 3. Update root file reference
  - [x] 3.1 Update step 4 phase file reference in `module-07-query-visualize-discover.md`
    - Reference both `module-07-phase2-discover.md` (steps 4a–4c) and `module-07-phase2b-discover.md` (steps 4d–4e)
    - Preserve all other content unchanged
    - _Requirements: 3.1, 3.2_

- [x] 4. Checkpoint — Validate consistency
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` and confirm exit code 0
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write validation tests for the split
  - [x] 5.1 Write property test for content preservation
    - **Property 1: Content preservation across split**
    - Verify Part A + Part B combined contain all agent instructions, checkpoints, and success criteria from the original
    - **Validates: Requirements 5.1**

  - [x] 5.2 Write property test for token budget compliance
    - **Property 2: Token budget compliance**
    - Verify each produced file has measured token count < 5,000 (split_threshold_tokens)
    - **Validates: Requirements 1.5, 1.6**

  - [x] 5.3 Write property test for steering index consistency
    - **Property 3: Steering index consistency**
    - Verify stored token_count within 10% of measured value, and budget.total_tokens equals sum of file_metadata counts
    - **Validates: Requirements 2.3, 2.4**

  - [x] 5.4 Write unit tests for the actual split files
    - Verify Part A contains steps 4a–4c headings and navigation footer
    - Verify Part B contains steps 4d–4e headings and continuation header
    - Verify both files have `inclusion: manual` frontmatter
    - Verify no `.kiro.hook` or `hook-categories.yaml` files were modified
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 4.1, 4.2**

- [x] 6. Final checkpoint — Ensure all tests pass
  - Run `python3 -m pytest senzing-bootcamp/tests/test_token_budget_optimization.py -v`
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks 1–4 have already been completed (the file split is done and validated)
- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- The existing `test_split_steering.py` already covers the generic split infrastructure; task 5 tests are specific to the module-07 split
- No hook files are modified (Requirement 4) — verified by absence of changes

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2", "3.1"] },
    { "id": 2, "tasks": ["2.3"] },
    { "id": 3, "tasks": ["5.1", "5.2", "5.3", "5.4"] }
  ]
}
```
