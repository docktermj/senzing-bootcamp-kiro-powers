# Requirements Document

## Introduction

The Senzing Bootcamp module prerequisite relationships are currently scattered across three files: `module-prerequisites.md` (the quick-reference dependency table), `onboarding-flow.md` (track definitions and validation gates), and individual module steering files (inline prerequisite checks). When a prerequisite changes, all three locations must be updated manually, creating a risk of inconsistency. This feature introduces a single machine-readable dependency graph (`config/module-dependencies.yaml`) as the authoritative source of module relationships, updates the three referencing files to derive their information from this graph, and adds a validation script (`scripts/validate_dependencies.py`) that verifies the graph is consistent with the actual steering files.

## Glossary

- **Dependency_Graph**: The `config/module-dependencies.yaml` file that defines all module prerequisite relationships in a machine-readable YAML format
- **Module_Prerequisites_File**: The `senzing-bootcamp/steering/module-prerequisites.md` steering file containing the quick-reference dependency table
- **Onboarding_Flow_File**: The `senzing-bootcamp/steering/onboarding-flow.md` steering file containing track definitions and validation gates
- **Module_Steering_File**: A steering file named `module-NN-*.md` in `senzing-bootcamp/steering/` that contains the steps for a specific bootcamp module
- **Validation_Script**: The `scripts/validate_dependencies.py` Python script that checks the Dependency_Graph for internal consistency and cross-references it against the steering files
- **Module_Node**: A single module entry in the Dependency_Graph, identified by its module number (1-11)
- **Prerequisite_Edge**: A directed relationship in the Dependency_Graph from a dependent module to a required module
- **Skip_Condition**: A condition defined in the Dependency_Graph under which a module's prerequisites can be bypassed
- **Track_Definition**: A named sequence of modules (Quick Demo, Fast Track, Complete Beginner, Full Production) defined in the Dependency_Graph
- **Validation_Gate**: A set of conditions that must be satisfied before transitioning from one module to the next, defined in the Dependency_Graph
- **Consistency_Violation**: A discrepancy detected by the Validation_Script between the Dependency_Graph and the steering files

## Requirements

### Requirement 1: Dependency Graph Schema

**User Story:** As a power maintainer, I want a single YAML file that defines all module relationships, so that I have one authoritative source to update when prerequisites change.

#### Acceptance Criteria

1. THE Dependency_Graph SHALL be located at `senzing-bootcamp/config/module-dependencies.yaml`
2. THE Dependency_Graph SHALL contain a `modules` section where each Module_Node is keyed by its integer module number (1 through 11)
3. WHEN a Module_Node is defined, THE Dependency_Graph SHALL include the following fields for that node: `name` (string, human-readable module title), `requires` (list of integer module numbers representing Prerequisite_Edges), and `skip_if` (string describing the Skip_Condition, or null if the module cannot be skipped)
4. THE Dependency_Graph SHALL contain a `tracks` section defining each Track_Definition with a `name` (string), `description` (string), and `modules` (ordered list of integer module numbers)
5. THE Dependency_Graph SHALL contain a `gates` section where each Validation_Gate is keyed by the transition pattern `N->M` and contains a `requires` field (list of string conditions that must be satisfied)
6. THE Dependency_Graph SHALL contain a `metadata` section with `version` (semantic version string) and `last_updated` (ISO 8601 date string)

### Requirement 2: Dependency Graph Content Accuracy

**User Story:** As a power maintainer, I want the dependency graph to accurately reflect the current prerequisite relationships, so that the graph is immediately usable without corrections.

#### Acceptance Criteria

1. THE Dependency_Graph `modules` section SHALL contain entries for all 11 modules matching the prerequisite relationships currently documented in the Module_Prerequisites_File
2. THE Dependency_Graph `tracks` section SHALL contain entries for all four tracks (Quick Demo, Fast Track, Complete Beginner, Full Production) matching the track definitions currently documented in the Onboarding_Flow_File
3. THE Dependency_Graph `gates` section SHALL contain entries for all 10 module transitions (1→2 through 10→11) matching the validation gate conditions currently documented in the Onboarding_Flow_File
4. THE Dependency_Graph SHALL encode the implicit rule that Module 2 (SDK Setup) is automatically inserted before any module that requires the SDK, matching the behavior documented in the Onboarding_Flow_File
5. WHEN the Dependency_Graph `requires` list for a module is empty, THE Dependency_Graph SHALL represent the module as having no prerequisites (matching modules 1 and 2 in the current documentation)

### Requirement 3: Dependency Graph Structural Validity

**User Story:** As a power maintainer, I want the dependency graph to be structurally valid, so that automated tools can parse and traverse it without encountering malformed data.

#### Acceptance Criteria

1. THE Dependency_Graph SHALL form a directed acyclic graph (no circular dependencies among module prerequisites)
2. THE Dependency_Graph SHALL reference only module numbers that exist in the `modules` section (no dangling references in `requires`, `tracks`, or `gates`)
3. THE Dependency_Graph `tracks` section SHALL list modules in a valid topological order consistent with the Prerequisite_Edges (no track lists a module before its prerequisites)
4. THE Dependency_Graph SHALL be valid YAML parseable by the Python `yaml.safe_load` function without errors

### Requirement 4: Validation Script Core Checks

**User Story:** As a CI pipeline maintainer, I want a validation script that detects inconsistencies between the dependency graph and the steering files, so that drift is caught before it ships.

#### Acceptance Criteria

1. THE Validation_Script SHALL be located at `senzing-bootcamp/scripts/validate_dependencies.py`
2. THE Validation_Script SHALL run as `python scripts/validate_dependencies.py` from the repository root with no third-party dependencies beyond the Python standard library and PyYAML
3. WHEN the Validation_Script detects zero Consistency_Violations, THE Validation_Script SHALL exit with exit code 0
4. WHEN the Validation_Script detects one or more Consistency_Violations, THE Validation_Script SHALL exit with exit code 1
5. THE Validation_Script SHALL print each Consistency_Violation to stdout in the format `{level}: {description}` where level is `ERROR` or `WARNING`
6. THE Validation_Script SHALL print a summary line at the end of output showing the total count of errors and warnings

### Requirement 5: Validation Script Cross-Reference Checks

**User Story:** As a power maintainer, I want the validation script to verify that the dependency graph matches the steering files, so that I am alerted when the graph drifts from the actual documentation.

#### Acceptance Criteria

1. THE Validation_Script SHALL verify that every module number in the Dependency_Graph has a corresponding Module_Steering_File in `senzing-bootcamp/steering/` with the naming pattern `module-NN-*.md`
2. WHEN a module number in the Dependency_Graph has no corresponding Module_Steering_File, THE Validation_Script SHALL report an error Consistency_Violation
3. THE Validation_Script SHALL parse the Module_Prerequisites_File and verify that the prerequisite relationships in its table match the `requires` fields in the Dependency_Graph
4. WHEN a prerequisite relationship in the Module_Prerequisites_File does not match the Dependency_Graph, THE Validation_Script SHALL report an error Consistency_Violation identifying the module and the discrepancy
5. THE Validation_Script SHALL parse the Onboarding_Flow_File track definitions and verify that the module sequences match the `tracks` section of the Dependency_Graph
6. WHEN a track definition in the Onboarding_Flow_File does not match the Dependency_Graph, THE Validation_Script SHALL report an error Consistency_Violation identifying the track and the discrepancy

### Requirement 6: Validation Script Structural Checks

**User Story:** As a power maintainer, I want the validation script to catch structural problems in the dependency graph itself, so that malformed graphs are rejected before they cause runtime issues.

#### Acceptance Criteria

1. THE Validation_Script SHALL verify that the Dependency_Graph contains no circular dependencies by performing a topological sort of the `modules` section
2. WHEN a circular dependency is detected, THE Validation_Script SHALL report an error Consistency_Violation identifying the modules involved in the cycle
3. THE Validation_Script SHALL verify that all module numbers referenced in `requires`, `tracks`, and `gates` exist in the `modules` section
4. WHEN a dangling module reference is detected, THE Validation_Script SHALL report an error Consistency_Violation identifying the referencing section and the missing module number
5. THE Validation_Script SHALL verify that the YAML file is parseable and conforms to the expected schema (all required fields present with correct types)
6. WHEN a schema violation is detected, THE Validation_Script SHALL report an error Consistency_Violation identifying the field and the expected type

### Requirement 7: Steering File Reference Updates

**User Story:** As a power maintainer, I want the three referencing files to acknowledge the dependency graph as the authoritative source, so that future maintainers know where to make changes.

#### Acceptance Criteria

1. THE Module_Prerequisites_File SHALL contain a note at the top of the "Quick Reference: Dependencies" section stating that the authoritative source for prerequisite data is the Dependency_Graph file and referencing its path
2. THE Onboarding_Flow_File SHALL contain a note in the "Track Selection" section stating that track definitions are derived from the Dependency_Graph file and referencing its path
3. THE Onboarding_Flow_File SHALL contain a note in the "Validation Gates" section stating that gate conditions are derived from the Dependency_Graph file and referencing its path
4. WHEN a maintainer updates a prerequisite relationship, THE notes in the referencing files SHALL direct the maintainer to update the Dependency_Graph first and then run the Validation_Script to verify consistency