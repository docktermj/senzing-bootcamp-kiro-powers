# Implementation Plan: Per-Source Mapping Workflow

## Overview

Update Module 5 documentation and Module 4 steering to explicitly require a separate `mapping_workflow` run per user-supplied data source, with each run producing its own mapping specification markdown file. All changes are documentation and steering file edits — no application code is modified.

## Tasks

- [x] 1. Update Module 5 Quick Test Path for per-source mapping
  - [x] 1.1 Add per-source mapping agent instruction to the Quick Test Path section in `senzing-bootcamp/docs/modules/MODULE_5_SINGLE_SOURCE_LOADING.md`
    - Insert a new agent instruction block after the existing Quick Test Path agent instruction
    - State that `mapping_workflow` must be run separately for each user-supplied source file
    - Each run must produce its own mapping specification markdown (e.g., `scripts/toyworld_mapper.md`, `scripts/funtoys_mapper.md`)
    - Mapper code may be shared across sources if schemas are identical, but mapping documentation is always per-source
    - _Requirements: 1, 3_
  - [x] 1.2 Add repeat-for-each-source guidance to Module 5 Quick Test Path
    - After the new agent instruction from 1.1, add a numbered workflow guiding the user through mapping the first source, then explicitly repeating for each additional source
    - Include a verification note: the user should confirm each per-source mapping spec exists before proceeding to loading
    - _Requirements: 4_

- [x] 2. Checkpoint — Review Module 5 changes
  - Ensure the Module 5 Quick Test Path section clearly requires per-source mapping workflow runs and per-source mapping specification markdown output. Ask the user if questions arise.

- [x] 3. Update Module 4 steering to enforce per-source mapping specification output
  - [x] 3.1 Add per-source mapping emphasis to Phase 2 step 1 in `senzing-bootcamp/steering/module-04-data-quality-mapping.md`
    - Add an agent instruction box in step 1 (Start mapping workflow) emphasizing that each data source must complete its own full `mapping_workflow` run
    - Explicitly prohibit reusing one source's mapping output for another source
    - _Requirements: 1, 3_
  - [x] 3.2 Add per-source mapping specification markdown requirement to Phase 2 step 11
    - In step 11 (Save and document), add a requirement to save a per-source mapping specification markdown to `scripts/{source_name}_mapper.md`
    - Document the expected structure: field mappings table, entity type, mapping decisions, quality notes
    - _Requirements: 2_
  - [x] 3.3 Add per-source mapping completion check to Phase 2 step 12
    - In step 12 (Repeat for remaining data sources), add a checkpoint verifying that each completed source has its own `scripts/{source_name}_mapper.md` file before marking the source as done
    - _Requirements: 2, 4_

- [x] 4. Final checkpoint — Verify all acceptance criteria
  - Ensure all changes are consistent between Module 5 doc and Module 4 steering. Verify all four acceptance criteria are addressed: (1) separate `mapping_workflow` per source, (2) per-source mapping spec markdown, (3) shared mapper code allowed but docs always per-source, (4) guide through first source then repeat. Ask the user if questions arise.

## Notes

- All tasks are documentation and steering file edits — no application code is created or modified
- No property-based tests apply since there are no functions or data transformations to test
- Each task references specific requirements from the requirements document for traceability
- Checkpoints ensure incremental validation of the documentation changes
