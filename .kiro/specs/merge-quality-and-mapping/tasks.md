# Implementation Plan: Merge Data Quality and Data Mapping Modules

## Overview

Merge Module 4 (Data Quality Scoring) and Module 5 (Data Mapping) into a single unified "Data Quality & Mapping" module, then renumber all downstream modules (6→5 through 12→11). This involves creating a merged steering file, deleting old files, renaming downstream files, and updating all cross-references across POWER.md, steering files, documentation, hooks, and diagrams.

## Tasks

- [x] 1. Create the merged steering file and remove old module files
  - [x] 1.1 Create `senzing-bootcamp/steering/module-04-data-quality-mapping.md`
    - Combine the content of `module-04-data-quality.md` (Phase 1 — Quality Assessment) and `module-05-data-mapping.md` (Phase 2 — Data Mapping) into a single continuous steering file
    - Phase 1 covers: list data sources, request samples, understand Entity Specification, compare sources, categorize, assess quality, summarize findings
    - Quality gate preserved inline: ≥80% proceed directly, 70–79% warn and proceed if accepted, <70% strongly recommend fixing before mapping
    - Phase 2 covers: start mapping workflow per source, profile, plan, map, generate, build transformation, test, quality analysis, save and document
    - Seamless transition between phases — no banner, no journey map reset, no module boundary
    - Update all internal references: "Module 5" (mapping) references become "this module" or "Phase 2"; "Module 6" (loading) references become "Module 5"
    - Preserve the mapping state checkpointing section from Module 5
    - _Requirements: 1, 2, 4_
  - [x] 1.2 Delete `senzing-bootcamp/steering/module-04-data-quality.md`
    - Remove the old separate Module 4 steering file
    - _Requirements: 1_
  - [x] 1.3 Delete `senzing-bootcamp/steering/module-05-data-mapping.md`
    - Remove the old separate Module 5 steering file
    - _Requirements: 1_
  - [x] 1.4 Create `senzing-bootcamp/docs/modules/MODULE_4_DATA_QUALITY_AND_MAPPING.md`
    - Create merged documentation file combining content from `MODULE_4_DATA_QUALITY_SCORING.md` and `MODULE_5_DATA_MAPPING.md`
    - Update title, overview, and all internal references to reflect the merged module
    - _Requirements: 1, 4_
  - [x] 1.5 Delete `senzing-bootcamp/docs/modules/MODULE_4_DATA_QUALITY_SCORING.md` and `senzing-bootcamp/docs/modules/MODULE_5_DATA_MAPPING.md`
    - Remove the old separate documentation files
    - _Requirements: 1_

- [x] 2. Rename downstream steering files (6→5 through 12→11)
  - [x] 2.1 Rename `module-06-single-source.md` → `module-05-single-source.md`
    - Update the module number in the file title, banner references, and any internal "Module 6" self-references to "Module 5"
    - _Requirements: 3_
  - [x] 2.2 Rename `module-07-multi-source.md` → `module-06-multi-source.md` and `module-07-reference.md` → `module-06-reference.md`
    - Update module numbers in titles and internal self-references from "Module 7" to "Module 6"
    - _Requirements: 3_
  - [x] 2.3 Rename `module-08-query-validation.md` → `module-07-query-validation.md`
    - Update module number in title and internal self-references from "Module 8" to "Module 7"
    - _Requirements: 3_
  - [x] 2.4 Rename `module-09-performance.md` → `module-08-performance.md`
    - Update module number in title and internal self-references from "Module 9" to "Module 8"
    - _Requirements: 3_
  - [x] 2.5 Rename `module-10-security.md` → `module-09-security.md`
    - Update module number in title and internal self-references from "Module 10" to "Module 9"
    - _Requirements: 3_
  - [x] 2.6 Rename `module-11-monitoring.md` → `module-10-monitoring.md`
    - Update module number in title and internal self-references from "Module 11" to "Module 10"
    - _Requirements: 3_
  - [x] 2.7 Rename `module-12-deployment.md` → `module-11-deployment.md`
    - Update module number in title and internal self-references from "Module 12" to "Module 11"
    - _Requirements: 3_

- [x] 3. Rename downstream documentation files (6→5 through 12→11)
  - [x] 3.1 Rename `MODULE_6_SINGLE_SOURCE_LOADING.md` → `MODULE_5_SINGLE_SOURCE_LOADING.md`
    - Update module number in title and internal references
    - _Requirements: 3_
  - [x] 3.2 Rename `MODULE_7_MULTI_SOURCE_ORCHESTRATION.md` → `MODULE_6_MULTI_SOURCE_ORCHESTRATION.md`
    - Update module number in title and internal references
    - _Requirements: 3_
  - [x] 3.3 Rename `MODULE_8_QUERY_VALIDATION.md` → `MODULE_7_QUERY_VALIDATION.md`
    - Update module number in title and internal references
    - _Requirements: 3_
  - [x] 3.4 Rename `MODULE_9_PERFORMANCE_TESTING.md` → `MODULE_8_PERFORMANCE_TESTING.md`
    - Update module number in title and internal references
    - _Requirements: 3_
  - [x] 3.5 Rename `MODULE_10_SECURITY_HARDENING.md` → `MODULE_9_SECURITY_HARDENING.md`
    - Update module number in title and internal references
    - _Requirements: 3_
  - [x] 3.6 Rename `MODULE_11_MONITORING_OBSERVABILITY.md` → `MODULE_10_MONITORING_OBSERVABILITY.md`
    - Update module number in title and internal references
    - _Requirements: 3_
  - [x] 3.7 Rename `MODULE_12_DEPLOYMENT_PACKAGING.md` → `MODULE_11_DEPLOYMENT_PACKAGING.md`
    - Update module number in title and internal references
    - _Requirements: 3_

- [x] 4. Checkpoint - Verify file structure
  - Ensure all new files exist, all old files are deleted, and all renames are complete. Ask the user if questions arise.

- [x] 5. Update POWER.md
  - [x] 5.1 Update the overview section
    - Change "13-module curriculum (Modules 0-12)" to "12-module curriculum (Modules 0-11)"
    - _Requirements: 3_
  - [x] 5.2 Update the module table (What This Bootcamp Does)
    - Merge rows for Module 4 and Module 5 into a single "Data Quality & Mapping" row
    - Renumber all subsequent rows: 6→5, 7→6, 8→7, 9→8, 10→9, 11→10, 12→11
    - _Requirements: 3_
  - [x] 5.3 Update Quick Start paths (A, B, C, D)
    - Update all module numbers in the four learning paths to reflect the new numbering
    - _Requirements: 3_
  - [x] 5.4 Update the Available Steering Files section
    - Update the module workflow list to reflect new filenames and numbers
    - Replace `module-04-data-quality.md` and `module-05-data-mapping.md` with `module-04-data-quality-mapping.md`
    - Renumber all downstream steering file references
    - _Requirements: 3_
  - [x] 5.5 Update the Bootcamp Modules table
    - Merge Module 4 and 5 rows, renumber downstream modules
    - _Requirements: 3_
  - [x] 5.6 Update hook references and all prose references
    - Update any module numbers in hook descriptions and general prose throughout POWER.md
    - _Requirements: 3_

- [x] 6. Update cross-references in steering files
  - [x] 6.1 Update `senzing-bootcamp/steering/agent-instructions.md`
    - Update the module steering table (0→`module-00-sdk-setup.md` through 11→`module-11-deployment.md`)
    - Update gate references and any module number mentions
    - _Requirements: 3_
  - [x] 6.2 Update `senzing-bootcamp/steering/onboarding-flow.md`
    - Update path definitions, validation gates table, and hook registry module associations
    - _Requirements: 3_
  - [x] 6.3 Update `senzing-bootcamp/steering/session-resume.md`
    - Update references to Module 5 mapping checkpoints (now part of Module 4)
    - Update all downstream module number references
    - _Requirements: 3_
  - [x] 6.4 Update `senzing-bootcamp/steering/module-prerequisites.md`
    - Update the prerequisites table and common blockers table with new module numbers
    - _Requirements: 3_
  - [x] 6.5 Update `senzing-bootcamp/steering/module-completion.md`
    - Update path completion table (Path D completes after Module 11 instead of Module 12)
    - Update all module number references
    - _Requirements: 3_
  - [x] 6.6 Update `senzing-bootcamp/steering/steering-index.yaml`
    - Update the module number → filename mapping to reflect new numbering (0–11) and new filenames
    - _Requirements: 3_
  - [x] 6.7 Update `senzing-bootcamp/steering/cloud-provider-setup.md`
    - Update gate references (e.g., 7→8 becomes 6→7)
    - _Requirements: 3_
  - [x] 6.8 Update `senzing-bootcamp/steering/visualization-guide.md`
    - Update Module 8 references to Module 7
    - _Requirements: 3_

- [x] 7. Update documentation cross-references
  - [x] 7.1 Update `senzing-bootcamp/docs/diagrams/module-flow.md`
    - Update all module boxes, paths, dependencies, and outputs in the diagram
    - _Requirements: 3_
  - [x] 7.2 Update `senzing-bootcamp/docs/diagrams/module-prerequisites.md`
    - Update the module dependency diagram with new numbering
    - _Requirements: 3_
  - [x] 7.3 Update `senzing-bootcamp/docs/modules/README.md`
    - Update the module index to reflect merged module and new numbering
    - _Requirements: 3_
  - [x] 7.4 Update `senzing-bootcamp/docs/guides/QUICK_START.md`
    - Update path module numbers throughout the guide
    - _Requirements: 3_
  - [x] 7.5 Update `senzing-bootcamp/docs/guides/PROGRESS_TRACKER.md`
    - Update module tracking references
    - _Requirements: 3_
  - [x] 7.6 Update `senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md`
    - Update module references throughout the checklist
    - _Requirements: 3_

- [x] 8. Update hooks referencing module numbers
  - [x] 8.1 Update hook files in `senzing-bootcamp/hooks/` that reference module numbers
    - Scan all `.kiro.hook` files for module number references
    - Update any references to modules 5–12 to use the new numbering (5→4 for mapping, 6→5, 7→6, 8→7, 9→8, 10→9, 11→10, 12→11)
    - Pay special attention to `module12-phase-gate.kiro.hook` (should become module 11 reference), `analyze-after-mapping.kiro.hook`, and `data-quality-check.kiro.hook`
    - _Requirements: 3_

- [x] 9. Checkpoint - Validate all cross-references
  - Run `python senzing-bootcamp/scripts/validate_power.py` to verify cross-reference integrity
  - Grep for stale references to old module numbers ("Module 12" as deployment, "module-12-deployment", "MODULE_12_DEPLOYMENT") — these should now be Module 11
  - Grep for any remaining references to "Module 5" meaning "Data Mapping" (should now be part of Module 4) vs. "Module 5" meaning "Single Source Loading" (correct new usage)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Final checkpoint - Full validation
  - Run `python senzing-bootcamp/scripts/validate_power.py` one final time
  - Verify the merged steering file contains all workflow steps from both old Module 4 and old Module 5
  - Verify the quality gate (≥70%) is preserved in the merged flow
  - Verify all module numbers in POWER.md are consistent (0–11)
  - Verify the steering-index.yaml maps all 12 modules (0–11) correctly
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This is a documentation/configuration restructuring task — no runtime code changes
- All file operations for the merge should be treated as atomic: create the new merged file before deleting the old ones
- The quality gate (≥70% to proceed) must be preserved as an internal checkpoint within the merged module
- After all changes, the total module count drops from 13 (0–12) to 12 (0–11)
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
