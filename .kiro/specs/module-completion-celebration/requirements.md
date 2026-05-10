# Requirements Document

## Introduction

The senzing-bootcamp Kiro power currently has no automated acknowledgment when a bootcamper finishes a module. The existing `module-completion.md` steering file defines a rich completion workflow (journal entries, certificates, next-step options), but it requires manual inclusion and is never triggered automatically. This creates a flat UX where progress goes unrecognized at module boundaries. This feature adds a lightweight `postTaskExecution` hook that detects module completion from progress state, triggers a brief celebration message summarizing what was built, shows what comes next, and offers to begin the next module immediately. The hook fires only at module boundaries — not after every step.

## Glossary

- **Celebration_Hook**: The `.kiro.hook` JSON file that triggers after task execution to detect and celebrate module completion.
- **Progress_File**: The JSON file at `config/bootcamp_progress.json` that stores bootcamp state including `modules_completed`, `current_module`, `current_step`, and `step_history`.
- **Module_Boundary**: The point at which a module's final step is completed, indicated by the module number appearing in `modules_completed` and `current_step` being `null`.
- **Step_Range**: The `[first_step, last_step]` pair defined in `steering-index.yaml` for each module or phase, identifying the total numbered steps in that module.
- **Next_Module**: The next module in the bootcamper's selected track as defined in `config/bootcamp_preferences.yaml` and `config/module-dependencies.yaml`.
- **Track_Completion**: The state where all modules in the bootcamper's selected track appear in `modules_completed`.
- **Celebration_Message**: A brief agent response acknowledging module completion, summarizing artifacts built, and presenting next-step options.
- **Hook_Categories_File**: The YAML file at `senzing-bootcamp/hooks/hook-categories.yaml` that maps hook identifiers to categories.

## Requirements

### Requirement 1: Hook File Structure

**User Story:** As a power developer, I want a properly structured hook file that triggers on `postTaskExecution`, so that the celebration logic runs automatically after each task completes.

#### Acceptance Criteria

1. THE Celebration_Hook SHALL be a valid JSON file located at `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook`.
2. THE Celebration_Hook SHALL contain the required fields: `name`, `version`, `description`, `when`, and `then`.
3. THE Celebration_Hook SHALL use `postTaskExecution` as the `when.type` value.
4. THE Celebration_Hook SHALL use `askAgent` as the `then.type` value.
5. THE Celebration_Hook SHALL use semantic versioning format for the `version` field.

### Requirement 2: Module Boundary Detection

**User Story:** As a bootcamper, I want the celebration to fire only when I finish a module, so that I am not interrupted after every step.

#### Acceptance Criteria

1. WHEN the hook prompt executes, THE Celebration_Hook prompt SHALL instruct the agent to read `config/bootcamp_progress.json` and compare the `modules_completed` array against the previous known state.
2. IF `modules_completed` has not changed since the last check, THEN THE Celebration_Hook prompt SHALL instruct the agent to produce no output and let the conversation continue normally.
3. WHEN a new module number appears in `modules_completed`, THE Celebration_Hook prompt SHALL instruct the agent to proceed with the celebration message.
4. THE Celebration_Hook prompt SHALL instruct the agent to identify the newly completed module by finding the module number that was added to `modules_completed`.

### Requirement 3: Celebration Message Content

**User Story:** As a bootcamper, I want a brief summary of what I accomplished when I finish a module, so that my progress feels acknowledged.

#### Acceptance Criteria

1. WHEN a Module_Boundary is detected, THE Celebration_Hook prompt SHALL instruct the agent to display a congratulatory banner including the completed module number and name.
2. WHEN a Module_Boundary is detected, THE Celebration_Hook prompt SHALL instruct the agent to provide a one-to-two sentence summary of what was built or accomplished in the completed module.
3. THE Celebration_Hook prompt SHALL instruct the agent to derive the module name from `config/module-dependencies.yaml`.
4. THE Celebration_Message SHALL be concise — no more than a banner line, a summary sentence, and the next-step information.

### Requirement 4: Next Module Presentation

**User Story:** As a bootcamper, I want to see what comes next after completing a module, so that I understand my path forward.

#### Acceptance Criteria

1. WHEN a Module_Boundary is detected and the bootcamper's track has remaining modules, THE Celebration_Hook prompt SHALL instruct the agent to display the next module's number and name.
2. WHEN a Module_Boundary is detected and the bootcamper's track has remaining modules, THE Celebration_Hook prompt SHALL instruct the agent to offer to begin the next module immediately.
3. WHEN a Module_Boundary is detected and all modules in the bootcamper's track are complete (Track_Completion), THE Celebration_Hook prompt SHALL instruct the agent to display a graduation acknowledgment instead of a next-module offer.
4. THE Celebration_Hook prompt SHALL instruct the agent to determine the bootcamper's track from `config/bootcamp_preferences.yaml` and the track definitions in `config/module-dependencies.yaml`.

### Requirement 5: Lightweight Execution

**User Story:** As a power developer, I want the hook to be lightweight and non-blocking, so that it does not degrade the bootcamp experience with heavy processing.

#### Acceptance Criteria

1. THE Celebration_Hook prompt SHALL contain a silent-exit instruction directing the agent to produce no output when no Module_Boundary is detected.
2. THE Celebration_Hook prompt SHALL NOT instruct the agent to write files, run scripts, or perform file-system scans.
3. THE Celebration_Hook prompt SHALL limit the agent's work to reading at most three configuration files: `config/bootcamp_progress.json`, `config/module-dependencies.yaml`, and `config/bootcamp_preferences.yaml`.
4. THE Celebration_Hook prompt SHALL NOT duplicate the full `module-completion.md` workflow (journal entries, certificates, reflection questions) — it provides only the brief celebration and next-step offer.

### Requirement 6: Hook Registry Integration

**User Story:** As a power developer, I want the hook registered in `hook-categories.yaml`, so that the hook registry stays synchronized with hook files on disk.

#### Acceptance Criteria

1. THE Hook_Categories_File SHALL include `module-completion-celebration` in a category.
2. THE `module-completion-celebration` identifier SHALL appear in the `any` category of the Hook_Categories_File, since it applies to all modules.
3. THE `module-completion-celebration` identifier SHALL appear in exactly one category in the Hook_Categories_File.

### Requirement 7: Coexistence with Manual Completion Workflow

**User Story:** As a power developer, I want the hook to complement rather than replace the existing `module-completion.md` steering file, so that bootcampers can still access the full completion workflow when desired.

#### Acceptance Criteria

1. THE Celebration_Hook prompt SHALL NOT instruct the agent to load `module-completion.md`.
2. THE Celebration_Hook prompt SHALL instruct the agent to mention that the bootcamper can say "completion" or "journal" to access the full completion workflow (journal entry, certificate, reflection).
3. THE Celebration_Hook prompt SHALL NOT perform any actions that conflict with or duplicate the `module-completion.md` workflow steps.
