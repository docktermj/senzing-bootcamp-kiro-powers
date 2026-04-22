# Requirements Document

## Introduction

This spec retroactively documents the module transition enforcement feature. User feedback reported that the agent was not displaying the module start banner (defined in `module-transitions.md`) when transitioning between modules. The root cause was that `module-transitions.md` uses `inclusion: fileMatch` on `config/bootcamp_progress.json`, meaning it only loads when that file is read. However, nothing explicitly instructed the agent to read the progress file at module boundaries, so the banner, journey map, and before/after framing instructions were never loaded.

This feature ensures that module transition guidance is reliably triggered at every module start by making the progress file read an explicit, reinforced instruction rather than relying on implicit behavior.

## Glossary

- **Agent**: The AI assistant executing the Senzing Bootcamp power, guided by steering files
- **Module_Steering_File**: A per-module steering file (`module-00-sdk-setup.md` through `module-12-deployment.md`) that defines the workflow for a specific bootcamp module
- **Module_Transitions_Steering**: The `module-transitions.md` steering file containing the module start banner template, journey map format, and before/after framing instructions
- **Progress_File**: The `config/bootcamp_progress.json` file that tracks the bootcamper's progress through modules
- **Module_Start_Banner**: The formatted ASCII banner displayed at the beginning of each module to orient the user
- **Journey_Map**: A table showing completed, current, and upcoming modules displayed at module start
- **Before_After_Framing**: A summary presented at module start showing what the user has now and what they will have when the module is complete
- **Core_Instructions**: The `agent-instructions.md` steering file loaded on every session via `inclusion: always`
- **FileMatch_Loading**: The steering file inclusion mechanism that loads a file only when a matching file pattern is accessed

## Requirements

### Requirement 1: Explicit Progress File Read at Module Start

**User Story:** As a bootcamper, I want the agent to always read my progress file at the start of every module, so that the module transition guidance is reliably loaded and displayed.

#### Acceptance Criteria

1. WHEN the Agent begins a new module, THE Core_Instructions SHALL direct the Agent to read the Progress_File before performing any module-specific work.
2. WHEN the Agent reads the Progress_File at module start, THE FileMatch_Loading mechanism SHALL load the Module_Transitions_Steering file.
3. IF the Agent starts a module without first reading the Progress_File, THEN THE Core_Instructions SHALL contain an explicit instruction that prevents this omission.

### Requirement 2: Per-Module Reinforcement of Transition Protocol

**User Story:** As a bootcamper, I want each module steering file to remind the agent about the transition protocol, so that the banner and orientation are never skipped regardless of which module I start.

#### Acceptance Criteria

1. THE Module_Steering_File for each of the 13 modules (module-00 through module-12) SHALL contain a visible reminder to read the Progress_File and follow the Module_Transitions_Steering before proceeding.
2. WHEN the Agent loads a Module_Steering_File, THE reminder SHALL appear before any module-specific workflow instructions.
3. THE reminder in each Module_Steering_File SHALL specify that the Module_Start_Banner, Journey_Map, and Before_After_Framing are required before proceeding.

### Requirement 3: Module Start Banner Display

**User Story:** As a bootcamper, I want to see a clear visual banner at the start of every module, so that I know which module I am entering.

#### Acceptance Criteria

1. WHEN the Agent transitions to a new module, THE Agent SHALL display the Module_Start_Banner as defined in the Module_Transitions_Steering.
2. THE Module_Start_Banner SHALL include the module number and the module name in uppercase.
3. WHEN the Module_Start_Banner is displayed, THE Agent SHALL display it before any other module content.

### Requirement 4: Journey Map Display at Module Start

**User Story:** As a bootcamper, I want to see a journey map showing my progress across all modules, so that I understand where I am in the bootcamp.

#### Acceptance Criteria

1. WHEN the Agent transitions to a new module, THE Agent SHALL display the Journey_Map after the Module_Start_Banner.
2. THE Journey_Map SHALL indicate completed modules, the current module, and upcoming modules using distinct visual markers.
3. THE Journey_Map SHALL reflect the bootcamper's selected path as recorded in their preferences.

### Requirement 5: Before/After Framing at Module Start

**User Story:** As a bootcamper, I want to see what I have now and what I will have after completing the module, so that I understand the module's purpose and value.

#### Acceptance Criteria

1. WHEN the Agent transitions to a new module, THE Agent SHALL display the Before_After_Framing after the Journey_Map.
2. THE Before_After_Framing SHALL describe the bootcamper's current state and the expected state after module completion.
3. WHEN the Module_Start_Banner, Journey_Map, and Before_After_Framing have all been displayed, THE Agent SHALL proceed with module-specific work.
