# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power has 25 hooks distributed across its 11 modules, but Modules 1 (Business Problem) and 3 (Quick Demo) have zero hooks while every other module has at least one. This creates an inconsistency in automation coverage and means these two modules lack the automated validation gates that other modules benefit from.

This feature adds two hooks:
- `validate-business-problem` for Module 1 — validates the problem statement before allowing transition to Module 2
- `verify-demo-results` for Module 3 — confirms the demo produced entity resolution output before marking the module complete

## Glossary

- **Hook**: A JSON file (`.kiro.hook` extension) that maps an IDE event to an automated agent action, following the schema with `name`, `version`, `description`, `when`, and `then` fields.
- **Hook_Registry**: The generated registry file produced by `sync_hook_registry.py` that catalogs all hooks and their metadata.
- **Hook_Categories_File**: The YAML file at `senzing-bootcamp/hooks/hook-categories.yaml` that maps hooks to their associated modules.
- **Module_1**: The "Business Problem" module where bootcampers define their entity resolution problem, identify data sources, define matching criteria, and document success metrics.
- **Module_3**: The "Quick Demo" module where bootcampers run the Senzing SDK against sample data to observe entity resolution in action.
- **Problem_Statement**: The documented output of Module 1, containing identified data sources, matching criteria, and success metrics stored in `config/bootcamp_progress.json`.
- **Demo_Output**: The entity resolution results produced by running the Module 3 demo script, including resolved entities and match explanations.
- **Validation_Hook**: A hook that checks completeness or correctness of module outputs before allowing progression.
- **Phase_Gate**: A checkpoint between modules that verifies prerequisites are met before transition.
- **Sync_Script**: The Python script `sync_hook_registry.py` that discovers, parses, and registers all hook files.

## Requirements

### Requirement 1: Module 1 Hook File Creation

**User Story:** As a power maintainer, I want a `validate-business-problem` hook file in the hooks directory, so that Module 1 has automated validation coverage consistent with other modules.

#### Acceptance Criteria

1. THE Hook SHALL be stored at `senzing-bootcamp/hooks/validate-business-problem.kiro.hook` as valid JSON
2. THE Hook SHALL contain a `name` field with value "Validate Business Problem"
3. THE Hook SHALL contain a `version` field with value "1.0.0"
4. THE Hook SHALL contain a `description` field summarizing its purpose
5. THE Hook SHALL contain a `when` object with a `type` field set to "postTaskExecution"
6. THE Hook SHALL contain a `then` object with `type` field set to "askAgent" and a `prompt` field containing validation instructions
7. WHEN triggered, THE Hook prompt SHALL instruct the agent to read `config/bootcamp_progress.json` and verify the current module is 1 before performing validation
8. WHEN the current module is 1, THE Hook prompt SHALL instruct the agent to verify that data sources are identified, matching criteria are defined, and success metrics are documented
9. WHEN the current module is not 1, THE Hook prompt SHALL instruct the agent to produce no output

### Requirement 2: Module 3 Hook File Creation

**User Story:** As a power maintainer, I want a `verify-demo-results` hook file in the hooks directory, so that Module 3 has automated validation coverage consistent with other modules.

#### Acceptance Criteria

1. THE Hook SHALL be stored at `senzing-bootcamp/hooks/verify-demo-results.kiro.hook` as valid JSON
2. THE Hook SHALL contain a `name` field with value "Verify Demo Results"
3. THE Hook SHALL contain a `version` field with value "1.0.0"
4. THE Hook SHALL contain a `description` field summarizing its purpose
5. THE Hook SHALL contain a `when` object with a `type` field set to "postTaskExecution"
6. THE Hook SHALL contain a `then` object with `type` field set to "askAgent" and a `prompt` field containing verification instructions
7. WHEN triggered, THE Hook prompt SHALL instruct the agent to read `config/bootcamp_progress.json` and verify the current module is 3 before performing verification
8. WHEN the current module is 3, THE Hook prompt SHALL instruct the agent to confirm that entities were resolved and matches were found in the demo output
9. WHEN the current module is not 3, THE Hook prompt SHALL instruct the agent to produce no output

### Requirement 3: Hook Categories Registration

**User Story:** As a power maintainer, I want both new hooks registered in `hook-categories.yaml`, so that the sync script correctly categorizes them and the registry stays consistent.

#### Acceptance Criteria

1. THE Hook_Categories_File SHALL contain a `1` key under `modules` with a list including "validate-business-problem"
2. THE Hook_Categories_File SHALL contain a `3` key under `modules` with a list including "verify-demo-results"
3. WHEN `sync_hook_registry.py --verify` is executed, THE Sync_Script SHALL pass without errors after the new hooks and categories are added
4. THE Hook_Categories_File SHALL maintain alphabetical ordering of module numbers (existing entries for modules 2, 4, 5, etc. remain unchanged)

### Requirement 4: Hook Schema Compliance

**User Story:** As a power maintainer, I want both hooks to pass all existing validation checks, so that CI remains green and the hooks integrate seamlessly with the existing infrastructure.

#### Acceptance Criteria

1. WHEN parsed by `sync_hook_registry.py`, THE Sync_Script SHALL successfully parse both new hook files without errors
2. WHEN parsed by `test_hooks.py`, THE Validation_Hook files SHALL pass all structural validation checks (required fields present, valid event type, valid action type)
3. THE Hook files SHALL use a `when.type` value that exists in the `VALID_EVENT_TYPES` set defined in `test_hooks.py`
4. THE Hook files SHALL use a `then.type` value of either "askAgent" or "runCommand"
5. WHEN `then.type` is "askAgent", THE Hook files SHALL include a non-empty `then.prompt` field

### Requirement 5: Module 1 Validation Logic

**User Story:** As a bootcamper, I want the system to verify my problem statement is complete before I move to Module 2, so that I do not proceed with gaps in my problem definition.

#### Acceptance Criteria

1. WHEN Module 1 tasks complete, THE Validation_Hook SHALL check that at least one data source is identified in the problem statement
2. WHEN Module 1 tasks complete, THE Validation_Hook SHALL check that matching criteria are defined (attributes to match on)
3. WHEN Module 1 tasks complete, THE Validation_Hook SHALL check that success metrics are documented (what "good" entity resolution looks like for this use case)
4. IF any required field is missing, THEN THE Validation_Hook SHALL report which fields are incomplete and suggest the bootcamper address them before proceeding
5. IF all required fields are present, THEN THE Validation_Hook SHALL confirm readiness to proceed to Module 2

### Requirement 6: Module 3 Verification Logic

**User Story:** As a bootcamper, I want the system to confirm my demo actually produced entity resolution results before marking the module complete, so that I do not miss the "aha moment" of seeing matches.

#### Acceptance Criteria

1. WHEN Module 3 tasks complete, THE Validation_Hook SHALL check that entities were resolved (more than zero entities created from the loaded records)
2. WHEN Module 3 tasks complete, THE Validation_Hook SHALL check that matches were found (at least two records resolved to the same entity)
3. IF the demo produced only singletons (no matches), THEN THE Validation_Hook SHALL report that entity resolution did not produce matches and suggest diagnosing the issue
4. IF the demo produced valid matches, THEN THE Validation_Hook SHALL confirm the demo completed successfully

### Requirement 7: Hook Count Consistency

**User Story:** As a power maintainer, I want every module to have at least one hook after this change, so that automation coverage is uniform across the bootcamp.

#### Acceptance Criteria

1. WHEN the Hook_Categories_File is parsed, THE Hook_Categories_File SHALL list at least one hook for every module from 1 through 11
2. THE total hook count in the Hook_Categories_File (excluding `critical` and `any` categories) SHALL increase by exactly 2 after this change
3. FOR ALL hook IDs listed in the Hook_Categories_File modules section, a corresponding `.kiro.hook` file SHALL exist in `senzing-bootcamp/hooks/`
