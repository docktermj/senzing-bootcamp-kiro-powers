# Requirements Document

## Introduction

Rename Module 7 from "Query & Visualize" to "Query, Visualize, and Discover" across the entire senzing-bootcamp Kiro Power codebase. This is a pure rename with no behavioral changes — all references to the old module name, including file names, headings, table entries, YAML keys, and string literals, must be updated atomically to prevent broken cross-references.

## Glossary

- **Module_7**: The seventh module in the senzing-bootcamp curriculum, currently named "Query & Visualize", to be renamed "Query, Visualize, and Discover"
- **Steering_File**: A markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that guides agent behavior during the bootcamp
- **Steering_Index**: The machine-readable YAML file (`steering-index.yaml`) that maps module numbers to steering file names and tracks token budgets
- **Cross_Reference**: Any internal link, filename reference, or string literal that points to a Module 7 artifact by name or filename
- **Rename_Operation**: The atomic update of a module's display name and associated filenames across all locations in the codebase

## Requirements

### Requirement 1: Rename Module 7 Steering File

**User Story:** As a power maintainer, I want the Module 7 steering file renamed from `module-07-query-validation.md` to `module-07-query-visualize-discover.md`, so that the filename reflects the updated module name.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE Steering_File previously named `module-07-query-validation.md` SHALL exist at the path `senzing-bootcamp/steering/module-07-query-visualize-discover.md`
2. WHEN the Rename_Operation is applied, THE Steering_File at `module-07-query-visualize-discover.md` SHALL contain the heading "Module 7: Query, Visualize, and Discover" in place of any previous heading referencing the old name
3. WHEN the Rename_Operation is applied, THE old file path `senzing-bootcamp/steering/module-07-query-validation.md` SHALL no longer exist in the repository

### Requirement 2: Update Steering Index

**User Story:** As a power maintainer, I want the steering-index.yaml updated with the new filename, so that the agent can locate the correct steering file for Module 7.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE Steering_Index SHALL reference `module-07-query-visualize-discover.md` as the steering file for module 7
2. WHEN the Rename_Operation is applied, THE Steering_Index `file_metadata` section SHALL use `module-07-query-visualize-discover.md` as the key for Module 7 metadata

### Requirement 3: Update Module Dependencies Config

**User Story:** As a power maintainer, I want the module-dependencies.yaml updated with the new module name, so that dependency resolution uses the correct display name.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE module-dependencies config SHALL specify the name field for module 7 as "Query, Visualize, and Discover"

### Requirement 4: Update Documentation Module File

**User Story:** As a power maintainer, I want the Module 7 documentation file renamed and updated, so that user-facing documentation reflects the new module name.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE documentation file previously at `docs/modules/MODULE_7_QUERY_VALIDATION.md` SHALL exist at `docs/modules/MODULE_7_QUERY_VISUALIZE_DISCOVER.md`
2. WHEN the Rename_Operation is applied, THE documentation file SHALL contain headings referencing "Query, Visualize, and Discover" in place of the old name
3. WHEN the Rename_Operation is applied, THE old file path `docs/modules/MODULE_7_QUERY_VALIDATION.md` SHALL no longer exist in the repository

### Requirement 5: Update Documentation Index and Cross-References

**User Story:** As a power maintainer, I want all documentation files that reference Module 7 updated, so that no broken links or stale names remain.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE `docs/modules/README.md` SHALL reference the new filename `MODULE_7_QUERY_VISUALIZE_DISCOVER.md` and display name "Query, Visualize, and Discover"
2. WHEN the Rename_Operation is applied, THE `docs/README.md` (top-level docs index) SHALL reference the new filename `MODULE_7_QUERY_VISUALIZE_DISCOVER.md`
3. WHEN the Rename_Operation is applied, THE `docs/diagrams/module-flow.md` SHALL use "Query, Visualize, and Discover" as the Module 7 label
4. WHEN the Rename_Operation is applied, THE `docs/guides/ARCHITECTURE.md` SHALL use "Query, Visualize, and Discover" for Module 7 references
5. WHEN the Rename_Operation is applied, THE `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md` SHALL reference Module 7 as "Query, Visualize, and Discover"
6. WHEN the Rename_Operation is applied, THE `docs/modules/MODULE_6_LOAD_DATA.md` SHALL reference Module 7 as "Query, Visualize, and Discover"

### Requirement 6: Update POWER.md

**User Story:** As a power maintainer, I want POWER.md updated with the new module name, so that the power's primary documentation is accurate.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE POWER.md module table SHALL display "Query, Visualize, and Discover" for Module 7
2. WHEN the Rename_Operation is applied, THE POWER.md steering file list SHALL reference `module-07-query-visualize-discover.md` for Module 7
3. WHEN the Rename_Operation is applied, THE POWER.md bootcamp modules table SHALL display "Query, Visualize, and Discover" for Module 7
4. WHEN the Rename_Operation is applied, THE POWER.md SHALL use "Query, Visualize, and Discover" in all prose references to Module 7

### Requirement 7: Update Steering Cross-References

**User Story:** As a power maintainer, I want all steering files that reference Module 7 by name or filename updated, so that agent navigation remains correct.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE `module-prerequisites.md` SHALL display "Query, Visualize, and Discover" as the Module 7 name
2. WHEN the Rename_Operation is applied, THE `module-transitions.md` SHALL use "Query, Visualize, and Discover" in journey map examples referencing Module 7
3. WHEN the Rename_Operation is applied, THE `visualization-guide.md` SHALL reference `module-07-query-visualize-discover.md` instead of the old filename
4. WHEN the Rename_Operation is applied, ALL steering files that reference Module 7 by display name SHALL use "Query, Visualize, and Discover"

### Requirement 8: Update Python Scripts

**User Story:** As a power maintainer, I want all Python scripts updated with the new module name string, so that CLI output and validation logic use the correct name.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE `validate_module.py` script SHALL use "Query, Visualize, and Discover" as the Module 7 name string
2. WHEN the Rename_Operation is applied, THE `rollback_module.py` script SHALL use "Query, Visualize, and Discover" as the Module 7 name string
3. WHEN the Rename_Operation is applied, THE `status.py` script SHALL use "Query, Visualize, and Discover" as the Module 7 name string and in hint text
4. WHEN the Rename_Operation is applied, THE `visualize_dependencies.py` script SHALL use "Query, Visualize, and Discover" as the Module 7 name string

### Requirement 9: Update Test Files

**User Story:** As a power maintainer, I want all test files updated with the new module name and filename references, so that the test suite passes after the rename.

#### Acceptance Criteria

1. WHEN the Rename_Operation is applied, THE `test_track_switcher_properties.py` SHALL use "Query, Visualize, and Discover" as the Module 7 name string
2. WHEN the Rename_Operation is applied, THE `test_track_switcher_unit.py` SHALL use "Query, Visualize, and Discover" as the Module 7 name string
3. WHEN the Rename_Operation is applied, THE `test_visualization_web_service.py` SHALL reference `module-07-query-visualize-discover.md` instead of the old filename
4. WHEN the Rename_Operation is applied, THE `test_self_answering_questions_bug.py` SHALL reference `module-07-query-visualize-discover.md` instead of the old filename
5. WHEN the Rename_Operation is applied, THE `test_self_answering_questions_preservation.py` SHALL reference `module-07-query-visualize-discover.md` instead of the old filename
6. WHEN the Rename_Operation is applied, THE `test_mapping_workflow_integration.py` SHALL reference `module-07-query-visualize-discover.md` instead of the old filename
7. WHEN the Rename_Operation is applied, THE `test_module_closing_question_ownership.py` SHALL reference `module-07-query-visualize-discover.md` instead of the old filename
8. WHEN the Rename_Operation is applied, THE `test_er_quality_evaluation.py` SHALL reference `module-07-query-visualize-discover.md` instead of the old filename

### Requirement 10: Preserve Behavioral Integrity

**User Story:** As a power maintainer, I want the rename to introduce no behavioral changes, so that the module workflow continues to function identically.

#### Acceptance Criteria

1. THE Rename_Operation SHALL modify only display names, headings, filename references, and file paths — no workflow logic, gate conditions, or prerequisite rules SHALL change
2. WHEN the Rename_Operation is complete, THE full pytest test suite SHALL pass with no new failures attributable to the rename
3. WHEN the Rename_Operation is complete, THE CI validation pipeline (`validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, pytest) SHALL pass
