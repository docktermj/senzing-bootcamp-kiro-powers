# Requirements Document

## Introduction

The `module-recap-append` and `module-completion-celebration` hooks currently use the `postTaskExecution` event type, which never fires during normal conversational bootcamp flow. This bug fix switches both hooks to the `agentStop` event type with conditional logic that detects module completion by inspecting `config/bootcamp_progress.json`. Integration tests validate the corrected trigger condition.

## Glossary

- **Hook_System**: The Kiro hook execution framework that fires hooks based on IDE event types defined in `.kiro.hook` JSON files.
- **Module_Recap_Hook**: The `module-recap-append.kiro.hook` file responsible for appending structured recap sections to `docs/bootcamp_recap.md` upon module completion.
- **Celebration_Hook**: The `module-completion-celebration.kiro.hook` file responsible for displaying a congratulatory message and next-step guidance upon module completion.
- **Progress_File**: The `config/bootcamp_progress.json` file containing the `modules_completed` array and `current_module` field that tracks bootcamp state.
- **Agent_Stop_Event**: The `agentStop` IDE event type that fires each time the agent finishes responding in a conversation turn.
- **Boundary_Detection**: The conditional logic within a hook prompt that determines whether a module completion boundary has been crossed by examining the Progress_File.

## Requirements

### Requirement 1: Event Type Migration

**User Story:** As a bootcamp maintainer, I want both module-completion hooks to fire on `agentStop` instead of `postTaskExecution`, so that they trigger during normal conversational bootcamp flow.

#### Acceptance Criteria

1. WHEN the Module_Recap_Hook file is loaded, THE Hook_System SHALL find `when.type` set to `agentStop`.
2. WHEN the Celebration_Hook file is loaded, THE Hook_System SHALL find `when.type` set to `agentStop`.
3. THE Module_Recap_Hook SHALL retain all existing fields (`name`, `version`, `description`, `when`, `then`) after the event type change.
4. THE Celebration_Hook SHALL retain all existing fields (`name`, `version`, `description`, `when`, `then`) after the event type change.
5. THE Module_Recap_Hook SHALL preserve the `then.type` value of `askAgent` unchanged.
6. THE Celebration_Hook SHALL preserve the `then.type` value of `askAgent` unchanged.

### Requirement 2: Boundary Detection Preservation

**User Story:** As a bootcamp maintainer, I want the conditional boundary detection logic to remain intact after the event type change, so that hooks only produce output when a module is actually completed.

#### Acceptance Criteria

1. THE Module_Recap_Hook prompt SHALL reference `config/bootcamp_progress.json` for boundary detection.
2. THE Celebration_Hook prompt SHALL reference `config/bootcamp_progress.json` for boundary detection.
3. THE Module_Recap_Hook prompt SHALL contain a silent-exit instruction directing the agent to produce no output when `modules_completed` has not changed.
4. THE Celebration_Hook prompt SHALL contain a silent-exit instruction directing the agent to produce no output when `modules_completed` has not changed.
5. THE Module_Recap_Hook prompt SHALL instruct the agent to identify the newly completed module number from the `modules_completed` array.
6. THE Celebration_Hook prompt SHALL instruct the agent to identify the newly completed module number from the `modules_completed` array.

### Requirement 3: Hook Schema Integrity

**User Story:** As a bootcamp maintainer, I want both modified hooks to remain valid against the hook JSON schema, so that CI validation continues to pass.

#### Acceptance Criteria

1. THE Module_Recap_Hook SHALL parse as valid JSON after modification.
2. THE Celebration_Hook SHALL parse as valid JSON after modification.
3. THE Module_Recap_Hook SHALL contain a `version` field matching semantic versioning format.
4. THE Celebration_Hook SHALL contain a `version` field matching semantic versioning format.
5. WHEN the Hook_System validates the Module_Recap_Hook, THE Hook_System SHALL find all required fields present: `name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`.
6. WHEN the Hook_System validates the Celebration_Hook, THE Hook_System SHALL find all required fields present: `name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`.

### Requirement 4: No Regression in Prompt Functionality

**User Story:** As a bootcamper, I want the recap and celebration behavior to remain identical after the fix, so that my module completion experience is unchanged.

#### Acceptance Criteria

1. THE Module_Recap_Hook prompt SHALL reference `config/module-dependencies.yaml` for module name lookup.
2. THE Celebration_Hook prompt SHALL reference `config/module-dependencies.yaml` for module name lookup.
3. THE Celebration_Hook prompt SHALL reference `config/bootcamp_preferences.yaml` for track determination.
4. THE Module_Recap_Hook prompt SHALL contain instructions to gather session content including information shared, questions asked, answers given, and actions taken.
5. THE Celebration_Hook prompt SHALL contain instructions to display a congratulatory banner with module number and name.
6. THE Celebration_Hook prompt SHALL contain instructions to offer the next module or display graduation acknowledgment.
7. THE Module_Recap_Hook prompt SHALL contain constraints preventing file-system scans and script execution.
8. THE Celebration_Hook prompt SHALL contain constraints preventing file writes, script execution, and file-system scans.

### Requirement 5: Integration Test Coverage

**User Story:** As a bootcamp maintainer, I want integration tests that validate the hook trigger condition, so that regressions in event type or boundary detection are caught by CI.

#### Acceptance Criteria

1. WHEN the test suite runs, THE test file SHALL validate that both hooks use `agentStop` as the event type.
2. WHEN the test suite runs, THE test file SHALL validate that both hook prompts contain boundary detection logic referencing `modules_completed`.
3. WHEN the test suite runs, THE test file SHALL validate that both hook prompts contain silent-exit instructions for the no-change case.
4. WHEN the test suite runs, THE test file SHALL use Hypothesis property-based testing to verify that arbitrary valid progress states trigger correct boundary detection behavior.
5. WHEN the test suite runs, THE test file SHALL validate that the `agentStop` event type is a recognized valid event type in the Hook_System.
6. IF a hook file is modified to use `postTaskExecution`, THEN THE test suite SHALL fail with a clear assertion message indicating the wrong event type.
