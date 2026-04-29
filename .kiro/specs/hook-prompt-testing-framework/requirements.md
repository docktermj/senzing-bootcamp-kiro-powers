# Requirements Document

## Introduction

The Senzing Bootcamp power distributes 18 `.kiro.hook` files that control agent behavior during the bootcamp. Prompt wording bugs have been found in 6 of these hooks — issues like missing silent-processing instructions, inline closing questions that conflict with the `ask-bootcamper` hook, and prompt text drifting out of sync with the hook registry. These bugs reach bootcampers before anyone notices.

This feature adds `test_hook_prompt_standards.py`, a pytest-based test suite that parses every `.kiro.hook` file and validates prompt patterns, JSON structure, required fields, and registry synchronization. The suite runs in CI so prompt regressions are caught before distribution.

## Glossary

- **Hook_File**: A `.kiro.hook` JSON file in `senzing-bootcamp/hooks/` that defines a single hook's name, version, description, trigger event, and agent prompt.
- **Hook_Registry**: The `senzing-bootcamp/steering/hook-registry.md` markdown file that lists all 18 hook definitions with their canonical prompt text, id, name, and description.
- **Test_Suite**: The `tests/test_hook_prompt_standards.py` pytest module that validates Hook_Files against prompt quality standards and registry consistency.
- **Silent_Processing_Instruction**: A prompt phrase directing the agent to produce no output when the hook's trigger condition is not met (e.g., "produce no output at all" or "do nothing").
- **Pass_Through_Hook**: A hook with event type `preToolUse`, `promptSubmit`, or `postToolUse` that fires on every matching event and must silently pass through when its specific condition is not met.
- **Inline_Closing_Question**: A question at the end of a hook prompt that asks the bootcamper what to do next, conflicting with the dedicated `ask-bootcamper` agentStop hook that owns closing questions.
- **Event_Type**: The `when.type` field in a Hook_File, one of: `promptSubmit`, `preToolUse`, `postToolUse`, `fileEdited`, `fileCreated`, `fileDeleted`, `agentStop`, `userTriggered`, `postTaskExecution`.
- **Required_Fields**: The mandatory JSON fields every Hook_File must contain: `name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`.

## Requirements

### Requirement 1: Valid JSON Structure

**User Story:** As a bootcamp maintainer, I want every hook file to be valid JSON with all required fields, so that hooks load without runtime errors.

#### Acceptance Criteria

1. THE Test_Suite SHALL parse every `.kiro.hook` file in `senzing-bootcamp/hooks/` as JSON and report a test failure for any file that is not valid JSON.
2. WHEN a Hook_File is parsed, THE Test_Suite SHALL verify that the Required_Fields (`name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`) are present and report a test failure for any missing field.
3. WHEN a Hook_File contains a `when.type` of `fileEdited`, `fileCreated`, or `fileDeleted`, THE Test_Suite SHALL verify that `when.patterns` is present and is a non-empty list.
4. WHEN a Hook_File contains a `when.type` of `preToolUse` or `postToolUse`, THE Test_Suite SHALL verify that `when.toolTypes` is present and is a non-empty list.
5. THE Test_Suite SHALL verify that the `then.type` field in every Hook_File is `askAgent`.
6. THE Test_Suite SHALL verify that the `then.prompt` field in every Hook_File is a non-empty string with at least 20 characters.

### Requirement 2: Silent Processing for Pass-Through Hooks

**User Story:** As a bootcamp maintainer, I want pass-through hooks to contain explicit silent-processing instructions, so that the agent produces no visible output when the hook's condition is not met.

#### Acceptance Criteria

1. WHEN a Hook_File has a `when.type` of `preToolUse` or `promptSubmit`, THE Test_Suite SHALL verify that the `then.prompt` contains a Silent_Processing_Instruction (a phrase matching "produce no output at all" or "do nothing" or equivalent silent-pass directive).
2. IF a Pass_Through_Hook prompt lacks a Silent_Processing_Instruction, THEN THE Test_Suite SHALL report a test failure identifying the hook file name and the missing instruction.

### Requirement 3: No Inline Closing Questions

**User Story:** As a bootcamp maintainer, I want hook prompts to avoid inline closing questions, so that the dedicated `ask-bootcamper` hook remains the single owner of closing questions and bootcampers are not asked the same question twice.

#### Acceptance Criteria

1. THE Test_Suite SHALL check every Hook_File prompt for Inline_Closing_Questions — phrases that ask the bootcamper what to do next (e.g., "what would you like to do", "what do you want to do next", "would you like to continue").
2. WHEN a Hook_File has a `when.type` other than `agentStop` and `userTriggered`, THE Test_Suite SHALL report a test failure if the prompt contains an Inline_Closing_Question.
3. WHEN a Hook_File has a `when.type` of `agentStop` or `userTriggered`, THE Test_Suite SHALL exempt that hook from the Inline_Closing_Question check because those hooks are expected to interact directly with the bootcamper.

### Requirement 4: Hook File and Registry Prompt Synchronization

**User Story:** As a bootcamp maintainer, I want the hook registry to stay in sync with the actual hook files, so that the agent creates hooks with the correct prompt text.

#### Acceptance Criteria

1. THE Test_Suite SHALL parse the Hook_Registry file and extract each hook's id, name, description, and prompt text.
2. FOR EACH hook id found in the Hook_Registry, THE Test_Suite SHALL verify that a corresponding Hook_File named `{id}.kiro.hook` exists in `senzing-bootcamp/hooks/`.
3. FOR EACH Hook_File in `senzing-bootcamp/hooks/`, THE Test_Suite SHALL verify that a corresponding entry exists in the Hook_Registry.
4. WHEN a hook exists in both the Hook_Registry and as a Hook_File, THE Test_Suite SHALL verify that the `name` field in the Hook_File matches the name in the Hook_Registry entry.
5. WHEN a hook exists in both the Hook_Registry and as a Hook_File, THE Test_Suite SHALL verify that the `description` field in the Hook_File matches the description in the Hook_Registry entry.

### Requirement 5: Hook Count Integrity

**User Story:** As a bootcamp maintainer, I want the test suite to verify the expected number of hooks, so that accidentally added or removed hooks are caught.

#### Acceptance Criteria

1. THE Test_Suite SHALL verify that exactly 18 `.kiro.hook` files exist in `senzing-bootcamp/hooks/`.
2. THE Test_Suite SHALL verify that the Hook_Registry defines exactly 18 hook entries.
3. IF the count of Hook_Files or Hook_Registry entries changes, THEN THE Test_Suite SHALL report a test failure with the actual count versus the expected count of 18.

### Requirement 6: CI Integration

**User Story:** As a bootcamp maintainer, I want the test suite to run in CI, so that prompt regressions are caught before they reach bootcampers.

#### Acceptance Criteria

1. THE Test_Suite SHALL be a pytest module located at `tests/test_hook_prompt_standards.py` that can be executed with `pytest tests/test_hook_prompt_standards.py`.
2. THE Test_Suite SHALL exit with a non-zero status code when any test fails.
3. THE Test_Suite SHALL produce clear failure messages that identify the specific hook file and the specific validation rule that was violated.
4. THE Test_Suite SHALL complete execution within 10 seconds for all 18 hooks.

### Requirement 7: Event Type Validation

**User Story:** As a bootcamp maintainer, I want the test suite to verify that every hook uses a recognized event type, so that typos in event types are caught before distribution.

#### Acceptance Criteria

1. THE Test_Suite SHALL maintain a list of valid Event_Types: `promptSubmit`, `preToolUse`, `postToolUse`, `fileEdited`, `fileCreated`, `fileDeleted`, `agentStop`, `userTriggered`, `postTaskExecution`, `preTaskExecution`.
2. WHEN a Hook_File contains a `when.type` value not in the valid Event_Types list, THE Test_Suite SHALL report a test failure identifying the hook file and the invalid event type.
