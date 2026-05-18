# Implementation Plan: Rename Module 7

## Overview

Rename Module 7 from "Query & Visualize" to "Query, Visualize, and Discover" across the entire senzing-bootcamp codebase. This is a coordinated find-and-replace plus two file moves, applied atomically. The execution order follows the design: file renames first, then YAML configs, then documentation/steering/scripts/tests, then verification.

## Tasks

- [x] 1. Rename files
  - [x] 1.1 Rename the Module 7 steering file from `senzing-bootcamp/steering/module-07-query-validation.md` to `senzing-bootcamp/steering/module-07-query-visualize-discover.md` and update the internal heading to "Module 7: Query, Visualize, and Discover"
    - Use git mv to preserve history
    - Update the top-level heading inside the file from the old name to "Module 7: Query, Visualize, and Discover"
    - Verify old path no longer exists
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Rename the Module 7 documentation file from `senzing-bootcamp/docs/modules/MODULE_7_QUERY_VALIDATION.md` to `senzing-bootcamp/docs/modules/MODULE_7_QUERY_VISUALIZE_DISCOVER.md` and update internal headings
    - Use git mv to preserve history
    - Update all headings referencing the old name to "Query, Visualize, and Discover"
    - Verify old path no longer exists
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Update YAML configuration files
  - [x] 2.1 Update `senzing-bootcamp/steering/steering-index.yaml` to reference the new steering filename
    - Change the module 7 mapping from `module-07-query-validation.md` to `module-07-query-visualize-discover.md`
    - Change the `file_metadata` key from `module-07-query-validation.md` to `module-07-query-visualize-discover.md`
    - _Requirements: 2.1, 2.2_

  - [x] 2.2 Update `senzing-bootcamp/config/module-dependencies.yaml` to use the new module name
    - Change `modules.7.name` from `"Query & Visualize"` to `"Query, Visualize, and Discover"`
    - _Requirements: 3.1_

- [x] 3. Update POWER.md
  - [x] 3.1 Update all Module 7 references in `senzing-bootcamp/POWER.md`
    - Update the module table to display "Query, Visualize, and Discover" for Module 7
    - Update the steering file list to reference `module-07-query-visualize-discover.md`
    - Update the bootcamp modules table to display "Query, Visualize, and Discover"
    - Update all prose references to Module 7
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 4. Update documentation cross-references
  - [x] 4.1 Update `senzing-bootcamp/docs/modules/README.md` to reference the new filename and display name
    - Change filename link from `MODULE_7_QUERY_VALIDATION.md` to `MODULE_7_QUERY_VISUALIZE_DISCOVER.md`
    - Change display name to "Query, Visualize, and Discover"
    - _Requirements: 5.1_

  - [x] 4.2 Update `senzing-bootcamp/docs/README.md` to reference the new filename
    - Change filename reference from `MODULE_7_QUERY_VALIDATION.md` to `MODULE_7_QUERY_VISUALIZE_DISCOVER.md`
    - _Requirements: 5.2_

  - [x] 4.3 Update `senzing-bootcamp/docs/diagrams/module-flow.md` to use the new Module 7 label
    - Change the Module 7 label to "Query, Visualize, and Discover"
    - _Requirements: 5.3_

  - [x] 4.4 Update `senzing-bootcamp/docs/guides/ARCHITECTURE.md` to use the new Module 7 name
    - Change all Module 7 references to "Query, Visualize, and Discover"
    - _Requirements: 5.4_

  - [x] 4.5 Update `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md` to reference Module 7 with the new name
    - Change Module 7 forward-reference to "Query, Visualize, and Discover"
    - _Requirements: 5.5_

  - [x] 4.6 Update `senzing-bootcamp/docs/modules/MODULE_6_LOAD_DATA.md` to reference Module 7 with the new name
    - Change Module 7 forward-reference to "Query, Visualize, and Discover"
    - _Requirements: 5.6_

- [x] 5. Update steering cross-references
  - [x] 5.1 Update `senzing-bootcamp/steering/module-prerequisites.md` to display the new Module 7 name
    - Change Module 7 display name to "Query, Visualize, and Discover"
    - _Requirements: 7.1_

  - [x] 5.2 Update `senzing-bootcamp/steering/module-transitions.md` to use the new Module 7 name
    - Change Module 7 references in journey map examples to "Query, Visualize, and Discover"
    - _Requirements: 7.2_

  - [x] 5.3 Update `senzing-bootcamp/steering/visualization-guide.md` to reference the new filename
    - Change `module-07-query-validation.md` to `module-07-query-visualize-discover.md`
    - _Requirements: 7.3_

  - [x] 5.4 Update any remaining steering files that reference Module 7 by display name
    - Search all files in `senzing-bootcamp/steering/` for "Query & Visualize" and replace with "Query, Visualize, and Discover"
    - _Requirements: 7.4_

- [x] 6. Checkpoint - Verify configs and docs
  - Ensure all YAML files parse correctly and all Markdown links are valid. Run `python senzing-bootcamp/scripts/validate_power.py` and `python senzing-bootcamp/scripts/validate_commonmark.py`. Ask the user if questions arise.

- [x] 7. Update Python scripts
  - [x] 7.1 Update `senzing-bootcamp/scripts/validate_module.py` to use the new Module 7 name string
    - Replace `"Query & Visualize"` with `"Query, Visualize, and Discover"` in the module name mapping
    - _Requirements: 8.1_

  - [x] 7.2 Update `senzing-bootcamp/scripts/rollback_module.py` to use the new Module 7 name string
    - Replace `"Query & Visualize"` with `"Query, Visualize, and Discover"` in the module name mapping
    - _Requirements: 8.2_

  - [x] 7.3 Update `senzing-bootcamp/scripts/status.py` to use the new Module 7 name string and hint text
    - Replace `"Query & Visualize"` with `"Query, Visualize, and Discover"` in the module name mapping and any hint text
    - _Requirements: 8.3_

  - [x] 7.4 Update `senzing-bootcamp/scripts/visualize_dependencies.py` to use the new Module 7 name string
    - Replace `"Query & Visualize"` with `"Query, Visualize, and Discover"` in the module name mapping
    - _Requirements: 8.4_

- [x] 8. Update test files
  - [x] 8.1 Update `senzing-bootcamp/tests/test_track_switcher_properties.py` to use the new Module 7 name string
    - Replace `"Query & Visualize"` with `"Query, Visualize, and Discover"`
    - _Requirements: 9.1_

  - [x] 8.2 Update `senzing-bootcamp/tests/test_track_switcher_unit.py` to use the new Module 7 name string
    - Replace `"Query & Visualize"` with `"Query, Visualize, and Discover"`
    - _Requirements: 9.2_

  - [x] 8.3 Update `senzing-bootcamp/tests/test_visualization_web_service.py` to reference the new filename
    - Replace `module-07-query-validation.md` with `module-07-query-visualize-discover.md`
    - _Requirements: 9.3_

  - [x] 8.4 Update `senzing-bootcamp/tests/test_self_answering_questions_bug.py` to reference the new filename
    - Replace `module-07-query-validation.md` with `module-07-query-visualize-discover.md`
    - _Requirements: 9.4_

  - [x] 8.5 Update `senzing-bootcamp/tests/test_self_answering_questions_preservation.py` to reference the new filename
    - Replace `module-07-query-validation.md` with `module-07-query-visualize-discover.md`
    - _Requirements: 9.5_

  - [x] 8.6 Update `senzing-bootcamp/tests/test_mapping_workflow_integration.py` to reference the new filename
    - Replace `module-07-query-validation.md` with `module-07-query-visualize-discover.md`
    - _Requirements: 9.6_

  - [x] 8.7 Update `senzing-bootcamp/tests/test_module_closing_question_ownership.py` to reference the new filename
    - Replace `module-07-query-validation.md` with `module-07-query-visualize-discover.md`
    - _Requirements: 9.7_

  - [x] 8.8 Update `senzing-bootcamp/tests/test_er_quality_evaluation.py` to reference the new filename
    - Replace `module-07-query-validation.md` with `module-07-query-visualize-discover.md`
    - _Requirements: 9.8_

- [x] 9. Checkpoint - Run test suite
  - Ensure all tests pass. Run `pytest senzing-bootcamp/tests/` and verify no failures. Ask the user if questions arise.

- [x] 10. Final verification
  - [x] 10.1 Run grep verification to confirm no old references remain
    - Run `grep -r "Query & Visualize" senzing-bootcamp/` — should return zero matches
    - Run `grep -r "module-07-query-validation" senzing-bootcamp/` — should return zero matches
    - Run `grep -r "MODULE_7_QUERY_VALIDATION" senzing-bootcamp/` — should return zero matches
    - _Requirements: 10.1, 10.2_

  - [x] 10.2 Run the full CI validation pipeline
    - Run `python senzing-bootcamp/scripts/validate_power.py`
    - Run `python senzing-bootcamp/scripts/measure_steering.py --check`
    - Run `python senzing-bootcamp/scripts/validate_commonmark.py`
    - Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    - Run `pytest`
    - All commands must pass with zero failures
    - _Requirements: 10.2, 10.3_

- [x] 11. Final checkpoint - Ensure all checks pass
  - Ensure all verification steps pass with no errors. Ask the user if questions arise.

## Notes

- This is a pure rename operation — no behavioral changes, gate conditions, or workflow logic should be modified
- All changes should be committed atomically in a single commit to prevent broken cross-references
- The execution order (file renames → YAML → docs → steering → scripts → tests → verification) minimizes risk of intermediate broken states
- Checkpoints ensure incremental validation before proceeding to the next phase
- Property-based testing does not apply to this feature (pure string replacement, no algorithmic logic)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3", "5.4"] },
    { "id": 5, "tasks": ["7.1", "7.2", "7.3", "7.4"] },
    { "id": 6, "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8"] },
    { "id": 7, "tasks": ["10.1", "10.2"] }
  ]
}
```
