# Implementation Plan: Split Session Resume

## Overview

Restructure the monolithic `session-resume.md` steering file (~4,661 tokens) into a lean phase-1 root file and three concern-specific phase-2 files. Implementation involves extracting content into new files, updating the steering index, and writing property-based tests to validate routing correctness and content completeness.

## Tasks

- [x] 1. Create Phase-2 steering files with extracted content
  - [x] 1.1 Create `session-resume-phase2-mapping.md` with mapping checkpoint recovery logic
    - Extract mapping checkpoint validation procedure (JSON parsing, field checks, MCP status call) from original Step 4
    - Extract mapping resume options presentation (Resume/Restart/Skip) from original Step 3
    - Extract fast-track-through-completed-steps logic for valid checkpoints
    - Extract corrupted checkpoint handling and restart offer
    - Add guard condition block at the top
    - Ensure token count stays at or below 1,000 tokens
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 8.3_

  - [x] 1.2 Create `session-resume-phase2-state-repair.md` with stale/corrupted state handling
    - Extract "Handling Stale or Corrupted State" procedure (artifact scanning, discrepancy reporting, correction)
    - Extract progress reconstruction from artifacts logic (missing/corrupted progress file recovery)
    - Add guard condition block at the top
    - Ensure token count stays at or below 800 tokens
    - _Requirements: 3.1, 3.2, 3.5, 8.3_

  - [x] 1.3 Create `session-resume-phase2-setup-recovery.md` with setup recovery logic
    - Extract hook installation logic (Hook Registry reading, createHook calls, failure handling)
    - Extract Step 2d (MCP Health Check) including probe call, success/failure paths, troubleshooting
    - Extract Step 2e (What's New Notification) including CHANGELOG parsing and display logic
    - Add guard condition block at the top
    - Ensure token count stays at or below 700 tokens
    - _Requirements: 4.1, 4.2, 4.3, 4.8, 8.3_

- [x] 2. Rewrite Phase-1 root file with routing logic
  - [x] 2.1 Rewrite `session-resume.md` as the lean Phase-1 file
    - Preserve `inclusion: manual` YAML frontmatter
    - Retain Fast Path Check (5 boolean conditions + skip-to-Step-3 logic)
    - Retain Step 1 (Read All State Files) for non-fast-path flow
    - Retain Step 2 (Load Language Steering) for non-fast-path flow
    - Retain Step 2b (Behavioral Rules Reload) inline
    - Retain Step 2c (Restore Conversation Style) inline
    - Retain Step 3 (Summarize and Confirm) inline, excluding mapping checkpoint detail
    - Retain Step 4 (Load the Right Module Steering) excluding mapping checkpoint validation
    - Retain Step 5 (Re-establish MCP Context)
    - Add Routing Logic section with conditions evaluated in order: state repair → setup recovery → mapping
    - Remove all content migrated to phase-2 files
    - Replace removed inline content with brief cross-references to phase-2 files
    - Ensure token count stays at or below 2,200 tokens
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 5.1, 5.2, 5.3, 7.2, 8.1, 8.2_

- [x] 3. Checkpoint - Verify content migration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update steering index registration
  - [x] 4.1 Update `steering-index.yaml` with session-resume phase entries
    - Add `session-resume` entry under a top-level key with `root` and `phases` map (following `onboarding` pattern)
    - Register `phase1-fast-path` with `session-resume.md`, measured token count, and size category
    - Register `phase2-mapping` with `session-resume-phase2-mapping.md`, measured token count, and size category
    - Register `phase2-state-repair` with `session-resume-phase2-state-repair.md`, measured token count, and size category
    - Register `phase2-setup-recovery` with `session-resume-phase2-setup-recovery.md`, measured token count, and size category
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 4.2 Update `file_metadata` section in `steering-index.yaml`
    - Add entries for `session-resume-phase2-mapping.md`, `session-resume-phase2-state-repair.md`, `session-resume-phase2-setup-recovery.md` with token counts and size categories
    - Update existing `session-resume.md` entry to reflect reduced token count
    - Verify `keywords` section still maps `resume` to `session-resume.md`
    - _Requirements: 6.4, 6.5, 7.4_

- [x] 5. Write property-based tests for routing correctness and content completeness
  - [x] 5.1 Write property test for routing correctness
    - **Property 1: Routing Correctness**
    - Generate arbitrary session states (combinations of valid/invalid progress JSON, consistent/inconsistent current_module, present/missing preferences, hooks_installed values, MCP probe results, show_whats_new flags, session_log existence, mapping_state file existence)
    - Assert that the set of phase-2 files directed for loading equals exactly the set whose trigger conditions are satisfied
    - **Validates: Requirements 2.5, 3.3, 3.4, 4.4, 4.5, 4.7, 5.1, 5.2, 8.1**

  - [x] 5.2 Write property test for content completeness (no instruction loss)
    - **Property 2: Content Completeness**
    - Parse the original monolithic file and all four split files
    - Assert every instruction block from the original appears in exactly one split file
    - Assert no instruction is duplicated across files
    - **Validates: Requirements 7.1, 7.3**

  - [x] 5.3 Write property test for routing section completeness
    - **Property 3: Routing Section Completeness**
    - For each phase-2 filename, assert the routing logic section in Phase-1 contains at least one explicit loading condition referencing that file by name
    - **Validates: Requirements 1.5, 5.3**

- [x] 6. Write unit tests for token budgets and structural validation
  - [x] 6.1 Write unit tests for token budget compliance and file structure
    - Test Phase-1 file token count ≤ 2,200
    - Test Phase-2 Mapping file token count ≤ 1,000
    - Test Phase-2 State Repair file token count ≤ 800
    - Test Phase-2 Setup Recovery file token count ≤ 700
    - Test `inclusion: manual` frontmatter present in Phase-1 only
    - Test phase-2 files have no frontmatter
    - Test each phase-2 file begins with a guard condition block
    - Test steering-index `session-resume` entry has correct structure with all four files
    - Test `resume` keyword still maps to `session-resume.md`
    - _Requirements: 1.10, 2.6, 3.5, 4.8, 6.1, 6.2, 6.3, 6.4, 6.5, 7.2, 7.4, 8.2_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation language is Python (pytest + Hypothesis) for tests; the feature itself is Markdown steering files and YAML configuration
- Token counting should use the same method as `measure_steering.py` for consistency with CI

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["4.1", "4.2"] },
    { "id": 3, "tasks": ["5.1", "5.2", "5.3", "6.1"] }
  ]
}
```
