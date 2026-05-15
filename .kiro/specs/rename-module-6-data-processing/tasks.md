# Tasks

## Task 1: Rename Files

- [ ] 1.1 Rename `senzing-bootcamp/steering/module-06-load-data.md` to `senzing-bootcamp/steering/module-06-data-processing.md`
  _Requirements: 1.1, 1.2_
- [ ] 1.2 Rename `senzing-bootcamp/steering/load-data-reference.md` to `senzing-bootcamp/steering/data-processing-reference.md`
  _Requirements: 2.1, 2.2_
- [ ] 1.3 Rename `senzing-bootcamp/docs/modules/MODULE_6_LOAD_DATA.md` to `senzing-bootcamp/docs/modules/MODULE_6_DATA_PROCESSING.md`
  _Requirements: 3.1, 3.2_

## Task 2: Update Renamed File Contents

- [ ] 2.1 In `module-06-data-processing.md`: Update heading from "# Module 6: Load Data" to "# Module 6: Data Processing", update Purpose line, update user reference to new docs filename `MODULE_6_DATA_PROCESSING.md`
  _Requirements: 1.3, 1.4_
- [ ] 2.2 In `data-processing-reference.md`: Update heading from "# Module 6: Load Data — Reference Material" to "# Module 6: Data Processing — Reference Material"
  _Requirements: 2.3_
- [ ] 2.3 In `MODULE_6_DATA_PROCESSING.md`: Update banner from "MODULE 6: LOAD DATA" to "MODULE 6: DATA PROCESSING", update heading from "# Module 6: Load Data" to "# Module 6: Data Processing", update steering reference from `module-06-load-data.md` to `module-06-data-processing.md`
  _Requirements: 3.3, 3.4_

## Task 3: Update Config Files

- [ ] 3.1 In `senzing-bootcamp/steering/steering-index.yaml`: Update `modules.6.root` from `module-06-load-data.md` to `module-06-data-processing.md`, update `file_metadata` keys from `load-data-reference.md` to `data-processing-reference.md` and from `module-06-load-data.md` to `module-06-data-processing.md` (preserve token counts)
  _Requirements: 4.1, 4.2, 4.3, 4.4_
- [ ] 3.2 In `senzing-bootcamp/config/module-dependencies.yaml`: Update `modules.6.name` from "Load Data" to "Data Processing"
  _Requirements: 5.1, 5.2_

## Task 4: Update Scripts

- [ ] 4.1 In `senzing-bootcamp/scripts/validate_module.py`: Replace "Load Data" with "Data Processing" for module 6 (docstring and name dict)
  _Requirements: 6.1_
- [ ] 4.2 In `senzing-bootcamp/scripts/rollback_module.py`: Replace "Load Data" with "Data Processing" in the module names dict
  _Requirements: 6.2_
- [ ] 4.3 In `senzing-bootcamp/scripts/status.py`: Replace "Load Data" with "Data Processing" in the module names dict and hint text
  _Requirements: 6.3_
- [ ] 4.4 In `senzing-bootcamp/scripts/visualize_dependencies.py`: Replace "Load Data" with "Data Processing" in the fallback module names dict
  _Requirements: 6.4_
- [ ] 4.5 In `senzing-bootcamp/scripts/split_steering.py`: Replace `module-06-load-data.md` with `module-06-data-processing.md` in the filename mapping
  _Requirements: 11.4_

## Task 5: Update Tests

- [ ] 5.1 In `senzing-bootcamp/tests/test_track_switcher_properties.py`: Replace "Load Data" with "Data Processing" for module 6
  _Requirements: 7.1_
- [ ] 5.2 In `senzing-bootcamp/tests/test_track_switcher_unit.py`: Replace "Load Data" with "Data Processing" for module 6
  _Requirements: 7.2_
- [ ] 5.3 In `senzing-bootcamp/tests/test_rollback_module.py`: Replace "Load Data" with "Data Processing" in the comment
  _Requirements: 7.3_
- [ ] 5.4 In `senzing-bootcamp/tests/test_module_closing_question_ownership.py`: Replace "# Module 6: Load Data" with "# Module 6: Data Processing" in the headings list, and update the filename from `module-06-load-data.md` to `module-06-data-processing.md`
  _Requirements: 11.3_
- [ ] 5.5 In `senzing-bootcamp/tests/test_split_steering.py`: Replace `module-06-load-data.md` with `module-06-data-processing.md` in all parametrize decorators and test methods
  _Requirements: 11.5_
- [ ] 5.6 In `senzing-bootcamp/tests/test_mapping_workflow_integration.py`: Replace `module-06-load-data.md` with `module-06-data-processing.md` in the path constant and comments
  _Requirements: 11.6_

## Task 6: Update Steering Cross-References

- [ ] 6.1 In `senzing-bootcamp/steering/module-prerequisites.md`: Replace "6 — Load Data" with "6 — Data Processing" in the prerequisites table
  _Requirements: 8.1_
- [ ] 6.2 In `senzing-bootcamp/steering/module-transitions.md`: Replace "Load Data" with "Data Processing" in any Module 6 journey map examples
  _Requirements: 8.2_
- [ ] 6.3 In `senzing-bootcamp/steering/common-pitfalls.md`: Replace "## Module 6: Load Data" with "## Module 6: Data Processing" in the section heading
  _Requirements: 8.3_
- [ ] 6.4 In `senzing-bootcamp/steering/module-06-phaseD-validation.md`: Replace `load-data-reference.md` with `data-processing-reference.md` in the `#[[file:]]` include directive
  _Requirements: 8.4_

## Task 7: Update Top-Level Documentation

- [ ] 7.1 In `senzing-bootcamp/POWER.md`: Replace all "Load Data" references for Module 6 with "Data Processing", update `module-06-load-data.md` to `module-06-data-processing.md` in the steering file list
  _Requirements: 9.1, 9.2, 9.3_
- [ ] 7.2 In `senzing-bootcamp/docs/modules/README.md`: Update Module 6 section heading, file link to `MODULE_6_DATA_PROCESSING.md`, and steering reference to `module-06-data-processing.md`
  _Requirements: 10.1, 10.2, 10.3_
- [ ] 7.3 In `senzing-bootcamp/hooks/README.md`: Replace "Module 6 (Load Data)" with "Module 6 (Data Processing)"
  _Requirements: 11.1_
- [ ] 7.4 In `senzing-bootcamp/docs/guides/ARCHITECTURE.md`: Replace all "Load Data" references for Module 6 with "Data Processing"
  _Requirements: 11.2_

## Task 8: Verification

- [ ] 8.1 Run `grep -r "Load Data" senzing-bootcamp/ --include="*.md" --include="*.py" --include="*.yaml" | grep -v ".hypothesis" | grep -v ".history"` and confirm no Module 6 references remain (note: "Re-load Data" in DATABASE_MIGRATION.md and "LOAD DATA" step in MODULE_5 are action descriptions, not Module 6 references)
  _Requirements: 11.7_
- [ ] 8.2 Run `grep -r "module-06-load-data" senzing-bootcamp/ | grep -v ".hypothesis" | grep -v ".history"` and confirm zero results
  _Requirements: 11.7_
- [ ] 8.3 Run `grep -r "load-data-reference" senzing-bootcamp/ | grep -v ".hypothesis" | grep -v ".history"` and confirm zero results
  _Requirements: 11.7_
- [ ] 8.4 Run `grep -r "MODULE_6_LOAD_DATA" senzing-bootcamp/ | grep -v ".hypothesis" | grep -v ".history"` and confirm zero results
  _Requirements: 11.7_
- [ ] 8.5 Run `pytest senzing-bootcamp/tests/ -x` and confirm all tests pass (delete `.hypothesis/constants/` first if needed)
  _Requirements: 12.3_
- [ ] 8.6 Verify phase sub-files still exist: `module-06-phaseA-build-loading.md`, `module-06-phaseB-load-first-source.md`, `module-06-phaseC-multi-source.md`, `module-06-phaseD-validation.md`
  _Requirements: 12.1_
