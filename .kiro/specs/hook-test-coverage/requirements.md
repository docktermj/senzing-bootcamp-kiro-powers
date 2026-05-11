# Requirements Document

## Introduction

The senzing-bootcamp Kiro power has 25 hooks but only 4 have dedicated tests (16% coverage). The existing test files (`test_hook_prompt_standards.py` and `test_hook_prompt_properties.py`) validate structural schema compliance and prompt patterns, but do not cover the semantic correctness of individual critical hook prompts or verify that `hook-categories.yaml` stays synchronized with the actual hook files on disk. This feature adds property-based tests for the 7 critical hooks, structural validation tests for all 25 hooks, prompt logic tests verifying hook prompts contain required instructions, and synchronization tests between `hook-categories.yaml` and the hook files directory.

## Glossary

- **Hook_File**: A JSON file with the `.kiro.hook` extension located in `senzing-bootcamp/hooks/`, containing `name`, `version`, `description`, `when` (with `type` and optionally `patterns` or `toolTypes`), and `then` (with `type` and `prompt` or `command`).
- **Critical_Hook**: One of the 7 hooks listed under the `critical` key in `hook-categories.yaml`: `ask-bootcamper`, `review-bootcamper-input`, `code-style-check`, `commonmark-validation`, `enforce-feedback-path`, `enforce-working-directory`, `verify-senzing-facts`.
- **Hook_Schema**: The expected JSON structure of a Hook_File including required fields (`name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`), conditional fields (`when.patterns` for file events, `when.toolTypes` for tool events), and valid value constraints.
- **Categories_File**: The YAML file at `senzing-bootcamp/hooks/hook-categories.yaml` that maps hook identifiers to categories (`critical`, module numbers, `any`).
- **Structural_Validation_Test**: A test that verifies a Hook_File conforms to the Hook_Schema without examining the semantic content of the prompt.
- **Prompt_Logic_Test**: A test that verifies a hook prompt contains specific required instructions, keywords, or behavioral patterns appropriate to that hook's purpose.
- **Property_Based_Test**: A test using Hypothesis to generate many random inputs and verify that a property (invariant) holds for all of them.
- **Silent_Processing_Instruction**: A phrase in a hook prompt directing the agent to produce no output when conditions are not met (e.g., "produce no output at all").
- **Event_Type**: One of the valid hook trigger types: `promptSubmit`, `preToolUse`, `postToolUse`, `fileEdited`, `fileCreated`, `fileDeleted`, `agentStop`, `userTriggered`, `postTaskExecution`, `preTaskExecution`.

## Requirements

### Requirement 1: Property-Based Tests for Critical Hook Prompts

**User Story:** As a developer maintaining the bootcamp power, I want property-based tests for all 7 critical hooks, so that I have high confidence their prompt logic handles diverse inputs correctly.

#### Acceptance Criteria

1. FOR ALL generated prompt strings containing Senzing-specific terms (attribute names, SDK method calls, configuration values), THE verify-senzing-facts hook prompt SHALL contain an instruction referencing MCP tools or the Senzing MCP server.
2. FOR ALL generated file paths that reference `/tmp/`, `%TEMP%`, `~/Downloads`, or paths outside the working directory, THE enforce-working-directory hook prompt SHALL contain an instruction to reject or redirect those paths.
3. FOR ALL generated user messages containing feedback trigger phrases (case-insensitive variations of "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue"), THE review-bootcamper-input hook prompt SHALL contain those trigger phrases as detection targets.
4. FOR ALL generated file paths targeting feedback content, THE enforce-feedback-path hook prompt SHALL contain the canonical path `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`.
5. FOR ALL generated source code file patterns matching `src/**/*.py`, `src/**/*.java`, `src/**/*.cs`, `src/**/*.rs`, `src/**/*.ts`, or `src/**/*.js`, THE code-style-check hook SHALL list those patterns in its `when.patterns` field.
6. FOR ALL generated markdown file paths matching `**/*.md`, THE commonmark-validation hook SHALL list a pattern in its `when.patterns` field that matches markdown files.
7. FOR ALL generated conversation states where no question is pending, THE ask-bootcamper hook prompt SHALL contain instructions about the `.question_pending` file and the closing question behavior.

### Requirement 2: Structural Validation Tests for All 25 Hooks

**User Story:** As a developer, I want structural validation tests covering all 25 hooks, so that any schema violation is caught immediately.

#### Acceptance Criteria

1. THE Structural_Validation_Test SHALL verify that every Hook_File in `senzing-bootcamp/hooks/` parses as valid JSON.
2. THE Structural_Validation_Test SHALL verify that every Hook_File contains all required fields: `name`, `version`, `description`, `when.type`, `then.type`, and `then.prompt`.
3. THE Structural_Validation_Test SHALL verify that every Hook_File's `when.type` field contains a valid Event_Type.
4. THE Structural_Validation_Test SHALL verify that every Hook_File's `then.prompt` field is a non-empty string with at least 20 characters.
5. THE Structural_Validation_Test SHALL verify that Hook_Files with `when.type` in (`fileEdited`, `fileCreated`, `fileDeleted`) contain a non-empty `when.patterns` list.
6. THE Structural_Validation_Test SHALL verify that Hook_Files with `when.type` in (`preToolUse`, `postToolUse`) contain a non-empty `when.toolTypes` list.
7. THE Structural_Validation_Test SHALL verify that the `version` field in every Hook_File matches semantic versioning format (digits.digits.digits).
8. THE Structural_Validation_Test SHALL verify that exactly 25 Hook_Files exist in the hooks directory.

### Requirement 3: Prompt Logic Tests for Critical Hooks

**User Story:** As a developer, I want tests verifying that each critical hook's prompt contains the required behavioral instructions, so that prompt regressions are caught.

#### Acceptance Criteria

1. WHEN the verify-senzing-facts hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it references at least one Senzing MCP tool name (`mapping_workflow`, `generate_scaffold`, `get_sdk_reference`, `search_docs`, `explain_error_code`, or `sdk_guide`).
2. WHEN the enforce-working-directory hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it references at least one forbidden path pattern (`/tmp/`, `%TEMP%`, `~/Downloads`).
3. WHEN the review-bootcamper-input hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it contains at least 3 of the feedback trigger phrases: "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue".
4. WHEN the enforce-feedback-path hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it contains the canonical feedback file path `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`.
5. WHEN the code-style-check hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it references at least one coding standard (PEP-8, rustfmt, clippy, or ESLint).
6. WHEN the commonmark-validation hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it references at least one CommonMark rule identifier (MD022, MD031, MD032, or MD040).
7. WHEN the ask-bootcamper hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it contains instructions about the `.question_pending` file and the closing question emoji character.
8. WHEN any Critical_Hook prompt is examined, THE Prompt_Logic_Test SHALL confirm it contains a Silent_Processing_Instruction if the hook's event type is `preToolUse` or `promptSubmit`.

### Requirement 4: Hook Categories Synchronization Tests

**User Story:** As a developer, I want tests verifying that `hook-categories.yaml` stays synchronized with the actual hook files on disk, so that category drift is detected immediately.

#### Acceptance Criteria

1. FOR ALL hook identifiers listed in the Categories_File, THE synchronization test SHALL verify that a corresponding `.kiro.hook` file exists in `senzing-bootcamp/hooks/`.
2. FOR ALL `.kiro.hook` files in `senzing-bootcamp/hooks/`, THE synchronization test SHALL verify that the hook identifier (filename without `.kiro.hook`) appears in exactly one category in the Categories_File.
3. THE synchronization test SHALL verify that the `critical` category in the Categories_File contains exactly 7 entries.
4. THE synchronization test SHALL verify that the total count of hook identifiers across all categories in the Categories_File equals the number of `.kiro.hook` files on disk.
5. THE synchronization test SHALL verify that no hook identifier appears in more than one category in the Categories_File.

### Requirement 5: Property-Based Tests for Schema Compliance

**User Story:** As a developer, I want property-based tests that generate random hook-like JSON structures and verify the structural validator correctly accepts valid hooks and rejects invalid ones, so that the validator itself is trustworthy.

#### Acceptance Criteria

1. FOR ALL valid Hook_File dicts generated by a Hypothesis strategy (containing all required fields with correct types and valid Event_Types), THE structural validator SHALL report zero errors.
2. FOR ALL Hook_File dicts generated with one required field removed, THE structural validator SHALL report exactly that field as missing.
3. FOR ALL Hook_File dicts generated with an invalid Event_Type string, THE structural validator SHALL report an event type error.
4. FOR ALL Hook_File dicts generated with a file event type but missing `when.patterns`, THE structural validator SHALL report a conditional field error.
5. FOR ALL Hook_File dicts generated with a tool event type but missing `when.toolTypes`, THE structural validator SHALL report a conditional field error.
6. THE property-based tests SHALL use `@settings(max_examples=100)` to balance coverage and execution time.

### Requirement 6: Test Organization and Integration

**User Story:** As a developer, I want the new tests organized consistently with the existing test suite and runnable in CI, so that they integrate seamlessly into the development workflow.

#### Acceptance Criteria

1. THE test files SHALL be located in the `tests/` directory at the repository root.
2. THE test files SHALL use pytest as the test runner and Hypothesis for property-based tests.
3. THE test files SHALL use only Python standard library plus pytest and Hypothesis (no other third-party dependencies).
4. THE test files SHALL use class-based test organization with descriptive class names.
5. THE test files SHALL include property test docstrings documenting which requirements they validate.
6. WHEN the full test suite is run via `pytest tests/`, THE new tests SHALL pass without errors alongside existing tests.

### Requirement 7: Version Format Validation

**User Story:** As a developer, I want tests that verify all hook files use valid semantic versioning, so that version parsing logic can rely on a consistent format.

#### Acceptance Criteria

1. FOR ALL Hook_Files, THE version validation test SHALL verify the `version` field matches the pattern `<major>.<minor>.<patch>` where each component is a non-negative integer.
2. FOR ALL randomly generated version strings, THE version validator SHALL accept strings matching `<digits>.<digits>.<digits>` and reject all other formats.
3. THE version validation test SHALL verify that no Hook_File uses a version with leading zeros in any component (e.g., "01.0.0" is invalid).

