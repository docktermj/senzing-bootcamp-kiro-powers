# Requirements Document

## Introduction

The module-artifacts.yaml file currently only declares artifacts for Modules 4–11, omitting Modules 1–3. It also lacks a mechanism to represent non-file outcomes (such as "SDK installed and importable"). This feature completes the artifact manifest by adding Modules 1–3, introducing a "sentinel" artifact type for non-file outcomes, and aligning the requires_from dependency graph with module-dependencies.yaml. Existing test suites must be updated to accept the new artifact type.

## Glossary

- **Artifact_Manifest**: The config/module-artifacts.yaml file that declares what each module produces and what it requires from other modules
- **Artifact_Type**: The classification of a produced artifact — one of "file", "directory", or "sentinel"
- **Sentinel_Artifact**: A non-file artifact representing a verifiable system state (e.g., SDK installed and importable) rather than a path on disk
- **Requires_From**: A mapping within a module declaration that lists artifact paths consumed from a specific source module
- **Module_Dependencies**: The config/module-dependencies.yaml file that declares the execution ordering and prerequisite relationships between modules
- **Validation_Script**: The senzing-bootcamp/scripts/validate_module.py script that parses and validates the Artifact_Manifest
- **Chain_Integration_Tests**: The test suite in test_artifact_chain_integration.py that validates internal consistency of the artifact dependency graph
- **Dependency_Tracking_Tests**: The test suite in test_artifact_dependency_tracking.py that validates manifest schema integrity via property-based tests

## Requirements

### Requirement 1: Module 1 Artifact Declaration

**User Story:** As a bootcamp power developer, I want Module 1 artifacts declared in the Artifact_Manifest, so that the dependency graph has complete lineage from the first module.

#### Acceptance Criteria

1. THE Artifact_Manifest SHALL declare Module 1 with a produces list containing "docs/business_problem.md" of type "file"
2. THE Artifact_Manifest SHALL declare Module 1 with a produces list containing "config/data_sources.yaml" of type "file"
3. THE Artifact_Manifest SHALL declare Module 1 with an empty requires_from mapping

### Requirement 2: Module 2 Artifact Declaration

**User Story:** As a bootcamp power developer, I want Module 2 artifacts declared in the Artifact_Manifest, so that downstream modules can formally depend on SDK setup outputs.

#### Acceptance Criteria

1. THE Artifact_Manifest SHALL declare Module 2 with a produces list containing "database/G2C.db" of type "file"
2. THE Artifact_Manifest SHALL declare Module 2 with a produces list containing "config/engine_config.json" of type "file"
3. THE Artifact_Manifest SHALL declare Module 2 with a produces list containing "config/bootcamp_preferences.yaml" of type "file"
4. THE Artifact_Manifest SHALL declare Module 2 with a produces list containing a sentinel artifact with path "sdk_installed" and description indicating the SDK is installed and importable
5. THE Artifact_Manifest SHALL declare Module 2 with an empty requires_from mapping

### Requirement 3: Module 3 Artifact Declaration

**User Story:** As a bootcamp power developer, I want Module 3 artifacts declared in the Artifact_Manifest, so that system verification outputs are tracked in the dependency graph.

#### Acceptance Criteria

1. THE Artifact_Manifest SHALL declare Module 3 with a produces list containing "src/system_verification/" of type "directory"
2. THE Artifact_Manifest SHALL declare Module 3 with a produces list containing "docs/progress/MODULE_3_COMPLETE.md" of type "file"
3. THE Artifact_Manifest SHALL declare Module 3 with a requires_from mapping referencing Module 2 for "database/G2C.db"

### Requirement 4: Sentinel Artifact Type Support

**User Story:** As a bootcamp power developer, I want a "sentinel" artifact type, so that non-file outcomes like SDK installation can be formally tracked in the dependency graph.

#### Acceptance Criteria

1. THE Artifact_Manifest SHALL accept "sentinel" as a valid value for the type field in a produces entry
2. WHEN a produces entry has type "sentinel", THE Artifact_Manifest SHALL treat the path field as a logical identifier rather than a filesystem path
3. THE Validation_Script SHALL recognize "file", "directory", and "sentinel" as the complete set of valid artifact types

### Requirement 5: Requires_From Alignment with Module Dependencies

**User Story:** As a bootcamp power developer, I want the requires_from graph in the Artifact_Manifest to match the lineage declared in Module_Dependencies, so that artifact flow is consistent with module execution order.

#### Acceptance Criteria

1. THE Artifact_Manifest SHALL declare Module 4 requires_from Module 1 for "config/data_sources.yaml"
2. THE Artifact_Manifest SHALL declare Module 6 requires_from Module 2 for "database/G2C.db"
3. WHEN Module 3 declares requires_from, THE Artifact_Manifest SHALL reference only Module 2 as a source
4. WHEN Module 4 declares requires_from, THE Artifact_Manifest SHALL reference Module 1 as a source in addition to any existing sources

### Requirement 6: Test Suite Type Validation Update

**User Story:** As a bootcamp power developer, I want the existing test suites to accept "sentinel" as a valid artifact type, so that adding sentinel artifacts does not break CI.

#### Acceptance Criteria

1. WHEN the Chain_Integration_Tests validate produces item structure, THE Chain_Integration_Tests SHALL accept "file", "directory", and "sentinel" as valid type values
2. WHEN the Dependency_Tracking_Tests validate produces entries, THE Dependency_Tracking_Tests SHALL accept "file", "directory", and "sentinel" as valid type values

### Requirement 7: Chain Continuity for Modules 1–3

**User Story:** As a bootcamp power developer, I want the artifact chain to be connected from Module 1 onward, so that no module is orphaned from the dependency graph.

#### Acceptance Criteria

1. WHEN the Chain_Integration_Tests check chain connectivity, THE Chain_Integration_Tests SHALL verify that Modules 1 through 11 form a connected dependency graph
2. THE Artifact_Manifest SHALL ensure every module except Module 1 and Module 2 has at least one requires_from entry
3. WHEN Module 1 produces "config/data_sources.yaml", THE Artifact_Manifest SHALL ensure at least one downstream module consumes the artifact via requires_from
