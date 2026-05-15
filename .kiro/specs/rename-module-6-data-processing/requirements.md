# Requirements Document

## Introduction

Rename Module 6 from "Load Data" to "Data Processing" across the entire senzing-bootcamp Kiro Power codebase. This is a pure naming consistency change — no behavioral modifications. The rename aligns Module 6 with the "Data" prefix pattern used by Module 4 (Data Collection) and Module 5 (Data Quality & Mapping), and better describes the module's scope (loading, redo processing, and validation — not just loading).

## Glossary

- **Module_6**: The sixth module in the senzing-bootcamp curriculum, currently named "Load Data", to be renamed "Data Processing"
- **Steering_File**: A markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that guides agent behavior during the bootcamp
- **Steering_Index**: The machine-readable YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps module numbers to steering file paths and metadata
- **Module_Dependencies_Config**: The YAML file at `senzing-bootcamp/config/module-dependencies.yaml` defining module names, prerequisites, and skip conditions
- **Cross_Reference**: Any link, filename reference, or textual mention of Module 6 by its old name or old filename in any file within the power
- **Atomic_Rename**: A rename operation where all references are updated together so that no intermediate state contains broken links or inconsistent naming

## Requirements

### Requirement 1: Rename Module 6 Steering Root File

**User Story:** As a power maintainer, I want the Module 6 root steering file renamed from `module-06-load-data.md` to `module-06-data-processing.md`, so that the filename reflects the new module name.

#### Acceptance Criteria

1. WHEN the rename is complete, THE Steering_File at path `senzing-bootcamp/steering/module-06-data-processing.md` SHALL exist with the same content structure as the former `module-06-load-data.md`
2. WHEN the rename is complete, THE Steering_File formerly at `senzing-bootcamp/steering/module-06-load-data.md` SHALL no longer exist
3. THE renamed Steering_File SHALL contain the heading "# Module 6: Data Processing" instead of "# Module 6: Load Data"
4. THE renamed Steering_File SHALL contain a Purpose line referencing "Data Processing" instead of "Load Data"

### Requirement 2: Rename Module 6 Reference File

**User Story:** As a power maintainer, I want the Module 6 reference file renamed from `load-data-reference.md` to `data-processing-reference.md`, so that the filename is consistent with the new module name.

#### Acceptance Criteria

1. WHEN the rename is complete, THE Steering_File at path `senzing-bootcamp/steering/data-processing-reference.md` SHALL exist with the same content structure as the former `load-data-reference.md`
2. WHEN the rename is complete, THE Steering_File formerly at `senzing-bootcamp/steering/load-data-reference.md` SHALL no longer exist
3. THE renamed Steering_File SHALL contain the heading "# Module 6: Data Processing — Reference Material" instead of "# Module 6: Load Data — Reference Material"

### Requirement 3: Rename Module 6 Documentation File

**User Story:** As a power maintainer, I want the Module 6 documentation file renamed from `MODULE_6_LOAD_DATA.md` to `MODULE_6_DATA_PROCESSING.md`, so that the filename is consistent with the new module name.

#### Acceptance Criteria

1. WHEN the rename is complete, THE documentation file at path `senzing-bootcamp/docs/modules/MODULE_6_DATA_PROCESSING.md` SHALL exist with the same content structure as the former `MODULE_6_LOAD_DATA.md`
2. WHEN the rename is complete, THE documentation file formerly at `senzing-bootcamp/docs/modules/MODULE_6_LOAD_DATA.md` SHALL no longer exist
3. THE renamed documentation file SHALL contain the heading "# Module 6: Data Processing" instead of "# Module 6: Load Data"
4. THE renamed documentation file SHALL contain the banner text "MODULE 6: DATA PROCESSING" instead of "MODULE 6: LOAD DATA"

### Requirement 4: Update Steering Index

**User Story:** As a power maintainer, I want the steering-index.yaml updated with the new filenames, so that the agent can locate Module 6 files correctly.

#### Acceptance Criteria

1. WHEN the Steering_Index is updated, THE root field for module 6 SHALL reference `module-06-data-processing.md` instead of `module-06-load-data.md`
2. WHEN the Steering_Index is updated, THE file_metadata section SHALL contain an entry for `data-processing-reference.md` instead of `load-data-reference.md`
3. WHEN the Steering_Index is updated, THE file_metadata section SHALL contain an entry for `module-06-data-processing.md` instead of `module-06-load-data.md`
4. THE token_count and size_category values for the renamed entries SHALL remain unchanged from their original values

### Requirement 5: Update Module Dependencies Config

**User Story:** As a power maintainer, I want the module-dependencies.yaml updated with the new module name, so that the dependency graph reflects the correct name.

#### Acceptance Criteria

1. WHEN the Module_Dependencies_Config is updated, THE name field for module 6 SHALL be "Data Processing" instead of "Load Data"
2. THE requires, skip_if, gates, and tracks fields for module 6 SHALL remain unchanged

### Requirement 6: Update Script Module Name Strings

**User Story:** As a power maintainer, I want all Python scripts that contain the module name string "Load Data" updated to "Data Processing", so that script output and internal references are consistent.

#### Acceptance Criteria

1. WHEN the scripts are updated, THE `validate_module.py` script SHALL reference "Data Processing" for module 6 instead of "Load Data"
2. WHEN the scripts are updated, THE `rollback_module.py` script SHALL reference "Data Processing" for module 6 instead of "Load Data"
3. WHEN the scripts are updated, THE `status.py` script SHALL reference "Data Processing" for module 6 instead of "Load Data"
4. WHEN the scripts are updated, THE `visualize_dependencies.py` script SHALL reference "Data Processing" for module 6 instead of "Load Data"

### Requirement 7: Update Test Module Name Strings

**User Story:** As a power maintainer, I want all test files that contain the module name string "Load Data" updated to "Data Processing", so that tests validate against the correct name.

#### Acceptance Criteria

1. WHEN the tests are updated, THE `test_track_switcher_properties.py` file SHALL reference "Data Processing" for module 6 instead of "Load Data"
2. WHEN the tests are updated, THE `test_track_switcher_unit.py` file SHALL reference "Data Processing" for module 6 instead of "Load Data"
3. WHEN the tests are updated, THE `test_rollback_module.py` file SHALL reference "Data Processing" for module 6 instead of "Load Data"

### Requirement 8: Update Cross-References in Steering Files

**User Story:** As a power maintainer, I want all steering files that reference Module 6 by its old name or old filename updated, so that no broken links or inconsistent naming remains.

#### Acceptance Criteria

1. WHEN the steering files are updated, THE `module-prerequisites.md` file SHALL reference "Data Processing" for module 6 instead of "Load Data"
2. WHEN the steering files are updated, THE `module-transitions.md` file SHALL reference "Data Processing" for module 6 in any example journey maps instead of "Load Data"
3. WHEN the steering files are updated, THE `common-pitfalls.md` file SHALL reference "Module 6: Data Processing" instead of "Module 6: Load Data" in its section heading
4. WHEN the steering files are updated, THE `module-06-phaseD-validation.md` file SHALL reference `data-processing-reference.md` instead of `load-data-reference.md` in its file include directive

### Requirement 9: Update POWER.md

**User Story:** As a power maintainer, I want POWER.md updated with the new module name and filename, so that the power's primary documentation is consistent.

#### Acceptance Criteria

1. WHEN POWER.md is updated, THE module table SHALL list "6 — Data Processing" instead of "6 — Load Data"
2. WHEN POWER.md is updated, THE steering file list SHALL reference `module-06-data-processing.md` instead of `module-06-load-data.md`
3. WHEN POWER.md is updated, THE bootcamp modules table SHALL list "Data Processing" for module 6 instead of "Load Data"

### Requirement 10: Update docs/modules/README.md

**User Story:** As a power maintainer, I want the module documentation index updated with the new module name, filename, and steering reference, so that the documentation index is consistent.

#### Acceptance Criteria

1. WHEN the README is updated, THE Module 6 section heading SHALL be "### Module 6: Data Processing" instead of "### Module 6: Load Data"
2. WHEN the README is updated, THE File reference SHALL link to `MODULE_6_DATA_PROCESSING.md` instead of `MODULE_6_LOAD_DATA.md`
3. WHEN the README is updated, THE Steering reference SHALL reference `module-06-data-processing.md` instead of `module-06-load-data.md`

### Requirement 11: Update Remaining Cross-References

**User Story:** As a power maintainer, I want all remaining files that reference Module 6 by its old name or old filename updated atomically, so that no broken links or inconsistent naming remains anywhere in the codebase.

#### Acceptance Criteria

1. WHEN the update is complete, THE `hooks/README.md` file SHALL reference "Module 6 (Data Processing)" instead of "Module 6 (Load Data)"
2. WHEN the update is complete, THE `docs/guides/ARCHITECTURE.md` file SHALL reference "Data Processing" for module 6 instead of "Load Data"
3. WHEN the update is complete, THE `test_module_closing_question_ownership.py` file SHALL reference the new heading "# Module 6: Data Processing" and the new filename `module-06-data-processing.md`
4. WHEN the update is complete, THE `split_steering.py` script SHALL reference `module-06-data-processing.md` instead of `module-06-load-data.md`
5. WHEN the update is complete, THE `test_split_steering.py` file SHALL reference `module-06-data-processing.md` instead of `module-06-load-data.md`
6. WHEN the update is complete, THE `test_mapping_workflow_integration.py` file SHALL reference `module-06-data-processing.md` instead of `module-06-load-data.md`
7. IF any file in the codebase (excluding `.hypothesis/constants/` cached data) still contains the string "Load Data" in reference to Module 6, THEN THE rename SHALL be considered incomplete

### Requirement 12: Preserve Behavioral Integrity

**User Story:** As a power maintainer, I want the rename to be purely cosmetic with no behavioral changes, so that the module workflow continues to function identically.

#### Acceptance Criteria

1. THE module 6 phase sub-files (`module-06-phaseA-build-loading.md`, `module-06-phaseB-load-first-source.md`, `module-06-phaseC-multi-source.md`, `module-06-phaseD-validation.md`) SHALL retain their existing filenames
2. THE module 6 workflow steps, gate conditions, prerequisites, and skip conditions SHALL remain unchanged
3. WHEN the test suite is run after the rename, THE tests SHALL pass with no failures attributable to the rename
4. THE `.hypothesis/constants/` directory contents SHALL be allowed to regenerate on the next test run without manual intervention
