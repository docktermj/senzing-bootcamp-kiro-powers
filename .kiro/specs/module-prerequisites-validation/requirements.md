# Requirements Document

## Introduction

The senzing-bootcamp Kiro power defines module prerequisites and transition gates in `config/module-dependencies.yaml`. Gates specify conditions like "SDK installed, DB configured, test passes" that must be met before transitioning between modules. However, there is no automated check that the source module's steering file actually contains checkpoint instructions or content corresponding to those gate requirements. Similarly, module numbers referenced in `requires` fields are validated against the `modules` section of the dependency graph but not against `steering-index.yaml` to confirm a steering file actually exists for each prerequisite. This feature adds a CI validation step that detects drift between the dependency configuration and actual steering file content.

## Glossary

- **Dependency_Graph**: The YAML file at `config/module-dependencies.yaml` containing module definitions, prerequisites, tracks, and gates.
- **Gate**: An entry in the `gates` section of the Dependency_Graph keyed as `"N->M"` with a `requires` list of human-readable conditions that must be satisfied before transitioning from module N to module M.
- **Gate_Requirement**: A single string entry in a Gate's `requires` list describing one or more conditions (e.g., "SDK installed, DB configured, test passes").
- **Steering_Index**: The YAML file at `steering/steering-index.yaml` mapping module numbers to their steering file paths.
- **Steering_File**: A Markdown file in `steering/` that guides the agent through a module's workflow, containing steps, checkpoints, and success criteria.
- **Checkpoint_Instruction**: A line in a Steering_File matching the pattern `**Checkpoint:**` that records completion of a step to the progress file.
- **Success_Criteria**: A section in a Steering_File (typically headed "Success Criteria" or containing `✅` markers) listing the outcomes that indicate module completion.
- **Gate_Keyword**: A normalized token extracted from a Gate_Requirement string by splitting on commas and common delimiters, used for fuzzy matching against Steering_File content.
- **Prerequisites_Validator**: The Python script that performs all validation checks defined in this document.
- **Drift_Report**: The structured output produced by the Prerequisites_Validator listing all mismatches between the Dependency_Graph and steering content.

## Requirements

### Requirement 1: Parse Dependency Graph

**User Story:** As a CI pipeline, I want to parse `module-dependencies.yaml` and extract all gates, module prerequisites, and track definitions, so that I can validate them against steering content.

#### Acceptance Criteria

1. WHEN the Dependency_Graph file exists and is valid YAML, THE Prerequisites_Validator SHALL parse it and extract all modules, gates, and tracks without error.
2. IF the Dependency_Graph file does not exist, THEN THE Prerequisites_Validator SHALL exit with a non-zero exit code and print an error message identifying the missing file path.
3. IF the Dependency_Graph file contains invalid YAML, THEN THE Prerequisites_Validator SHALL exit with a non-zero exit code and print a parse error message.
4. THE Prerequisites_Validator SHALL extract each Gate's source module number, destination module number, and requires list from the `gates` section.
5. THE Prerequisites_Validator SHALL extract each module's `requires` list of prerequisite module numbers from the `modules` section.

### Requirement 2: Validate Module References Against Steering Index

**User Story:** As a maintainer, I want to verify that every module number referenced in `requires` fields has a corresponding entry in `steering-index.yaml`, so that prerequisites point to modules that actually have steering content.

#### Acceptance Criteria

1. WHEN a module's `requires` list contains a module number, THE Prerequisites_Validator SHALL verify that module number exists as a key in the Steering_Index `modules` section.
2. IF a referenced module number does not exist in the Steering_Index, THEN THE Prerequisites_Validator SHALL report an ERROR identifying the referencing module and the missing prerequisite module number.
3. WHEN all referenced module numbers exist in the Steering_Index, THE Prerequisites_Validator SHALL report no errors for this check.
4. THE Prerequisites_Validator SHALL also verify that gate source and destination module numbers exist in the Steering_Index.

### Requirement 3: Validate Gate Requirements Against Steering Content

**User Story:** As a maintainer, I want to verify that each gate's requirements correspond to actual content in the source module's steering file, so that gates do not reference conditions the steering file never addresses.

#### Acceptance Criteria

1. WHEN a Gate specifies requirements for a transition from module N to module M, THE Prerequisites_Validator SHALL locate the Steering_File for module N using the Steering_Index.
2. THE Prerequisites_Validator SHALL extract Gate_Keywords from each Gate_Requirement by splitting on commas and normalizing to lowercase tokens.
3. FOR EACH Gate_Keyword, THE Prerequisites_Validator SHALL search the source module's Steering_File content (including all phase files for multi-phase modules) for the presence of that keyword.
4. IF a Gate_Keyword is not found in the source module's Steering_File content, THEN THE Prerequisites_Validator SHALL report a WARNING identifying the gate, the missing keyword, and the steering file searched.
5. WHEN all Gate_Keywords for a gate are found in the source module's Steering_File, THE Prerequisites_Validator SHALL report no warnings for that gate.

### Requirement 4: Validate Checkpoint Coverage for Gates

**User Story:** As a maintainer, I want to verify that the source module's steering file contains checkpoint instructions that cover the gate's requirements, so that progress tracking aligns with transition conditions.

#### Acceptance Criteria

1. THE Prerequisites_Validator SHALL count the number of Checkpoint_Instructions in the source module's Steering_File (including phase files).
2. IF the source module's Steering_File contains zero Checkpoint_Instructions, THEN THE Prerequisites_Validator SHALL report an ERROR indicating the module has no checkpoints but has an outgoing gate.
3. THE Prerequisites_Validator SHALL verify that the source module's Steering_File contains a Success_Criteria section or success indicator markers.
4. IF the source module's Steering_File lacks both a Success_Criteria section and success indicator markers, THEN THE Prerequisites_Validator SHALL report a WARNING indicating the module has no success criteria but has an outgoing gate.

### Requirement 5: Drift Report Output

**User Story:** As a developer reviewing CI output, I want a clear structured report of all validation findings, so that I can quickly identify and fix drift between the dependency config and steering content.

#### Acceptance Criteria

1. THE Prerequisites_Validator SHALL categorize findings as ERROR (blocks CI) or WARNING (informational).
2. THE Prerequisites_Validator SHALL print each finding on a separate line in the format `LEVEL: description`.
3. WHEN the Prerequisites_Validator completes, THE Prerequisites_Validator SHALL print a summary line showing the count of errors and warnings.
4. IF one or more ERRORs are found, THEN THE Prerequisites_Validator SHALL exit with exit code 1.
5. WHEN zero ERRORs are found, THE Prerequisites_Validator SHALL exit with exit code 0 regardless of warning count.
6. WHERE the `--warnings-as-errors` flag is provided, THE Prerequisites_Validator SHALL treat WARNINGs as ERRORs for exit code determination.

### Requirement 6: CI Integration

**User Story:** As a maintainer, I want the prerequisites validation to run automatically in CI on every pull request that touches bootcamp files, so that drift is caught before merge.

#### Acceptance Criteria

1. WHEN the CI workflow runs, THE CI pipeline SHALL execute the Prerequisites_Validator as a named step.
2. IF the Prerequisites_Validator exits with a non-zero exit code, THEN THE CI pipeline SHALL fail the workflow and display the Drift_Report in the job output.
3. THE CI pipeline step SHALL run after the existing `validate_power.py` step and before the pytest step.
4. THE Prerequisites_Validator SHALL complete execution within 10 seconds for the current module set (11 modules).

### Requirement 7: Property-Based Tests for Gate Parsing

**User Story:** As a developer, I want property-based tests that verify the gate parsing and keyword extraction logic handles arbitrary valid inputs correctly, so that I have confidence the validator works for any well-formed dependency graph.

#### Acceptance Criteria

1. FOR ALL valid Dependency_Graph structures generated by a Hypothesis strategy, THE Prerequisites_Validator's gate parser SHALL extract the correct source module, destination module, and requires list without raising exceptions.
2. FOR ALL valid Gate_Requirement strings generated by a Hypothesis strategy, THE keyword extraction function SHALL produce a non-empty list of lowercase tokens with no leading or trailing whitespace.
3. FOR ALL valid gate key strings matching the pattern `"N->M"` where N and M are positive integers, THE gate key parser SHALL correctly extract both module numbers.
4. THE property-based tests SHALL use `@settings(max_examples=100)` to balance coverage and execution time.

### Requirement 8: Integration with Existing Validation

**User Story:** As a developer, I want the new prerequisites validation to complement the existing `validate_dependencies.py` script without duplicating its checks, so that the validation suite remains cohesive.

#### Acceptance Criteria

1. THE Prerequisites_Validator SHALL NOT duplicate checks already performed by `validate_dependencies.py` (schema validation, cycle detection, dangling module references within the graph, topological ordering).
2. THE Prerequisites_Validator SHALL focus exclusively on cross-referencing the Dependency_Graph against steering file content and the Steering_Index.
3. WHEN both `validate_dependencies.py` and the Prerequisites_Validator are run in CI, THE combined validation SHALL cover: graph internal consistency (existing) and graph-to-steering-content alignment (new).
