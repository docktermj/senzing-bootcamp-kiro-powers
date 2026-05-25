# Implementation Plan: Steering Optimization

## Overview

Implement `optimize_steering.py` — a single Python script that splits always-on steering files, compresses large manual files using Refine-style optimization, and synchronizes `steering-index.yaml`. The script uses Python 3.11+ stdlib only (no third-party deps). Tests use pytest + Hypothesis.

## Tasks

- [x] 1. Set up project structure and core interfaces
  - [x] 1.1 Create `optimize_steering.py` with CLI skeleton and data models
    - Create `senzing-bootcamp/scripts/optimize_steering.py`
    - Implement `main()` with argparse: `--steering-dir`, `--index-path`, `--dry-run`
    - Define all dataclasses: `ExtractionRule`, `SplitResult`, `CompressTarget`, `CompressResult`, `RuleInventory`, `OptimizeResult`
    - Implement `token_count()` and `size_category()` utility functions
    - Wire `optimize()` function that calls split → compress → index update phases (stubs for now)
    - _Requirements: 1.1, 1.2, 3.8, 4.4, 5.1_

  - [x] 1.2 Define extraction and compression configuration constants
    - Add `AGENT_INSTRUCTIONS_EXTRACTIONS` list with all `ExtractionRule` instances per design
    - Add `TRANSITIONS_KEEP` and `TRANSITIONS_EXTRACT` section lists
    - Add `COMPRESSION_TARGETS` list with all `CompressTarget` instances
    - _Requirements: 1.3, 1.4, 1.5, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_

- [x] 2. Implement RulePreserver (behavioral correctness validator)
  - [x] 2.1 Implement `extract_rule_inventory()` and `verify_preservation()`
    - Parse files for ⛔ gate markers, 👉 question markers, SHALL/NEVER/MUST/ALWAYS directives, hook definitions, file placement rules
    - Implement `verify_preservation()` that compares original vs optimized inventories
    - Return list of missing rules on mismatch
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.8_

  - [x] 2.2 Write property test for rule preservation (Property 1)
    - **Property 1: Behavioral rule preservation across optimization**
    - **Validates: Requirements 1.2, 1.6, 2.5, 3.5, 6.1, 6.2, 6.8**

  - [x] 2.3 Write property test for gate/question marker verbatim preservation (Property 7)
    - **Property 7: Gate and question marker verbatim preservation**
    - **Validates: Requirements 3.7, 6.1, 6.2**

- [x] 3. Implement SplitEngine (section extraction)
  - [x] 3.1 Implement `split_always_on_file()` for agent-instructions.md
    - Parse markdown into sections by H2/H3 headings
    - Extract sections matching `ExtractionRule.source_heading`
    - Write extracted content to destination files (create with YAML frontmatter if new, append if existing)
    - Insert dispatch pointers at extraction points in source file
    - Verify resulting core file ≤ 80 non-blank lines
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 3.2 Implement module-transitions.md split logic
    - Keep only `TRANSITIONS_KEEP` sections in always-on file
    - Extract `TRANSITIONS_EXTRACT` sections to new `module-transitions-detail.md`
    - Create `module-transitions-detail.md` with `inclusion: auto` frontmatter and keywords
    - Verify resulting always-on file ≤ 60 non-blank lines
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.3 Write property test for YAML frontmatter validity (Property 5)
    - **Property 5: YAML frontmatter validity for new files**
    - **Validates: Requirements 7.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement CompressEngine (Refine-style optimization)
  - [x] 5.1 Implement `compress_file()` core logic
    - Identify compressible regions (prose paragraphs of 3+ sentences, repeated WHEN/THEN patterns, verbose lists)
    - Preserve all markers verbatim (⛔, 👉, hook names, step numbers)
    - Convert prose to tables/bullets using regex-based pattern matching
    - Remove filler words, transitional phrases, redundant context
    - Calculate token reduction and verify against target ratio
    - Report if target cannot be achieved without semantic loss (do NOT discard content)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.9_

  - [x] 5.2 Implement always-on file Refine optimization
    - Apply compression to `agent-instructions.md` post-split (prose → tables/bullets)
    - Apply compression to `module-transitions.md` post-split (banners → compact notation)
    - Verify ≥ 15% token reduction for each always-on file
    - Reject optimization and retain original if any behavioral rule is omitted
    - _Requirements: 4.1, 4.2, 4.3, 4.7_

  - [x] 5.3 Write property test for token reduction (Property 2)
    - **Property 2: Token reduction for always-on files**
    - **Validates: Requirements 4.3**

- [x] 6. Implement IndexUpdater (steering-index.yaml synchronization)
  - [x] 6.1 Implement `update_index()` function
    - Call `measure_steering.py` in update mode as subprocess to regenerate `file_metadata` and `budget`
    - Add keyword mappings for all new files to the `keywords` section
    - Verify `budget.total_tokens` equals sum of all `token_count` values
    - Add new files to `modules` section with correct `phases` mapping where applicable
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 6.2 Write property test for index completeness (Property 3)
    - **Property 3: Steering index completeness**
    - **Validates: Requirements 5.1, 5.2**

  - [x] 6.3 Write property test for budget consistency (Property 4)
    - **Property 4: Budget total consistency**
    - **Validates: Requirements 5.5**

  - [x] 6.4 Write property test for index referential integrity (Property 6)
    - **Property 6: Index referential integrity**
    - **Validates: Requirements 7.5**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Wire orchestrator and CI integration
  - [x] 8.1 Wire `optimize()` to call all phases in sequence
    - Execute: RulePreserver (extract original inventory) → SplitEngine → CompressEngine → IndexUpdater → RulePreserver (verify preservation)
    - Implement dry-run mode (report changes without writing files)
    - Report results: files modified, token savings per file, total savings, any failures
    - Exit code 0 on success, 1 on marker count mismatch or critical failure
    - _Requirements: 4.4, 4.5, 6.6, 6.8, 7.1_

  - [x] 8.2 Add CI validation integration
    - After index update, run `measure_steering.py --check` and verify exit 0
    - Run `validate_commonmark.py` and verify exit 0
    - Run `validate_power.py` and verify exit 0
    - Handle subprocess errors with clear error messages
    - _Requirements: 4.5, 4.6, 7.1, 7.2, 7.3, 7.6_

- [x] 9. Write unit tests
  - [x] 9.1 Create `test_steering_optimization_unit.py` with example-based tests
    - Test line count constraints (agent-instructions.md ≤ 80, module-transitions.md ≤ 60)
    - Test token count targets for each compressed file (hook-registry-critical ≤ 5718, hook-registry-modules ≤ 5521, module-03 ≤ 4814, onboarding-flow ≤ 3950)
    - Test specific section extraction (SDK Method Discovery → mcp-usage-reference.md)
    - Test dispatch pointer presence in core files
    - Test new file frontmatter structure (inclusion + description fields)
    - Test keyword mappings in steering-index.yaml for new files
    - Test dry-run mode produces no file changes
    - _Requirements: 1.1, 1.3, 2.3, 3.1, 3.2, 3.3, 3.4, 5.6, 7.4_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All code is Python 3.11+ stdlib only (except pytest + Hypothesis for tests)
- The script delegates to existing `measure_steering.py` for token counting and index updates

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3"] },
    { "id": 4, "tasks": ["5.1"] },
    { "id": 5, "tasks": ["5.2", "5.3"] },
    { "id": 6, "tasks": ["6.1"] },
    { "id": 7, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 8, "tasks": ["8.1"] },
    { "id": 9, "tasks": ["8.2", "9.1"] }
  ]
}
```
