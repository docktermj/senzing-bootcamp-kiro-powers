# Requirements Document

## Introduction

A Python validation script that checks the top-level key structure of the four authoritative YAML configuration files in the senzing-bootcamp power. The script runs in CI as part of the validate-power workflow and provides terse PASS/FAIL output per file. It validates all four files by default and supports a `--file` flag to target a single file.

## Glossary

- **Validator**: The Python script at `senzing-bootcamp/scripts/validate_yaml_schemas.py`
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` with expected top-level keys: `modules`, `keywords`, `languages`, `deployment`, `file_metadata`, `budget`
- **Module_Dependencies**: The YAML file at `senzing-bootcamp/config/module-dependencies.yaml` with expected top-level keys: `metadata`, `modules`, `tracks`, `gates`
- **Hook_Categories**: The YAML file at `senzing-bootcamp/hooks/hook-categories.yaml` with expected top-level keys: `critical`, `modules`
- **Module_Artifacts**: The YAML file at `senzing-bootcamp/config/module-artifacts.yaml` with expected top-level keys: `version`, `modules`
- **CI_Workflow**: The GitHub Actions workflow at `.github/workflows/validate-power.yml`
- **Top_Level_Keys**: The set of required keys that must exist at the root mapping level of a YAML file

## Requirements

### Requirement 1

**User Story:** As a developer, I want the Validator to check that each YAML file contains exactly the expected top-level keys, so that schema drift is caught before merge.

#### Acceptance Criteria

1. WHEN the Validator processes Steering_Index, THE Validator SHALL verify that the top-level keys are exactly `modules`, `keywords`, `languages`, `deployment`, `file_metadata`, `budget`
2. WHEN the Validator processes Module_Dependencies, THE Validator SHALL verify that the top-level keys are exactly `metadata`, `modules`, `tracks`, `gates`
3. WHEN the Validator processes Hook_Categories, THE Validator SHALL verify that the top-level keys are exactly `critical`, `modules`
4. WHEN the Validator processes Module_Artifacts, THE Validator SHALL verify that the top-level keys are exactly `version`, `modules`
5. WHEN a YAML file contains unexpected top-level keys, THE Validator SHALL report the file as FAIL and list the unexpected keys
6. WHEN a YAML file is missing expected top-level keys, THE Validator SHALL report the file as FAIL and list the missing keys

### Requirement 2

**User Story:** As a developer, I want terse CI output showing PASS or FAIL per file, so that I can quickly identify which file has a schema problem.

#### Acceptance Criteria

1. WHEN a YAML file passes validation, THE Validator SHALL print a single line in the format `PASS: <filename>`
2. WHEN a YAML file fails validation, THE Validator SHALL print a single line in the format `FAIL: <filename>` followed by the reason on the same or subsequent line
3. THE Validator SHALL print one result line per validated file

### Requirement 3

**User Story:** As a developer, I want the Validator to check all four files by default and support a `--file` flag for single-file validation, so that I can run targeted checks locally.

#### Acceptance Criteria

1. WHEN the Validator is invoked without arguments, THE Validator SHALL validate all four YAML files (Steering_Index, Module_Dependencies, Hook_Categories, Module_Artifacts)
2. WHEN the Validator is invoked with `--file <path>`, THE Validator SHALL validate only the specified file
3. IF the `--file` argument references a file not in the known schema registry, THEN THE Validator SHALL exit with a non-zero code and print an error message identifying the unrecognized file

### Requirement 4

**User Story:** As a developer, I want the Validator to exit with a non-zero code on any failure, so that CI treats schema violations as blocking.

#### Acceptance Criteria

1. WHEN all validated files pass, THE Validator SHALL exit with code 0
2. WHEN one or more validated files fail, THE Validator SHALL exit with a non-zero code
3. WHEN a YAML file cannot be parsed, THE Validator SHALL report the file as FAIL with a parse error message and exit with a non-zero code

### Requirement 5

**User Story:** As a developer, I want the Validator integrated into the CI workflow, so that schema checks run automatically on every PR and push.

#### Acceptance Criteria

1. THE CI_Workflow SHALL include a step that runs `python senzing-bootcamp/scripts/validate_yaml_schemas.py`
2. WHEN the Validator step fails, THE CI_Workflow SHALL fail the overall job

### Requirement 6

**User Story:** As a developer, I want the Validator to use only Python stdlib, so that it follows the project convention of no third-party dependencies.

#### Acceptance Criteria

1. THE Validator SHALL parse YAML files using only Python standard library modules
2. THE Validator SHALL implement a `main()` entry point with argparse CLI following the project script conventions
