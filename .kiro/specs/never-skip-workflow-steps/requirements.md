# Requirements Document

## Introduction

This feature enforces strict sequential execution of all numbered workflow steps across the Senzing Bootcamp Power. Currently, only steps marked with ⛔ (mandatory gates) have enforcement mechanisms. Steps with 👉 questions can be skipped by the agent without detection. This feature elevates all numbered steps with 👉 questions to the same "never skip" enforcement level as ⛔ mandatory gates, using steering-file language reinforcement and a generic agentStop hook that detects when the agent advances past a 👉 step without writing its checkpoint.

## Glossary

- **Agent**: The AI assistant executing bootcamp workflows within the Kiro IDE
- **Bootcamper**: The human user participating in the Senzing Bootcamp
- **Numbered_Step**: A workflow step identified by a sequential number within a module steering file
- **Pointing_Hand_Question**: A question prefixed with 👉 that requires bootcamper input before the agent may proceed
- **Mandatory_Gate**: A step marked with ⛔ that the agent must execute unconditionally
- **Checkpoint**: An entry in `config/bootcamp_progress.json` recording that a step has been completed
- **Step_Progression**: The sequential advancement of `current_step` in `config/bootcamp_progress.json`
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that provides behavioral instructions to the Agent
- **Module_Steering_File**: A steering file specific to one of the 11 bootcamp modules (e.g., `module-01-business-problem.md`)
- **Sequential_Execution_Reminder**: A per-module instruction block reinforcing the never-skip rule within a Module_Steering_File
- **Enforce_Sequential_Steps_Hook**: An agentStop hook that detects when the Agent has advanced past a Pointing_Hand_Question step without writing its Checkpoint

## Requirements

### Requirement 1: Sequential Step Execution

**User Story:** As a bootcamper, I want the agent to execute every numbered step in order, so that I am never denied a choice or interaction that the workflow guarantees.

#### Acceptance Criteria

1. THE Agent SHALL execute every Numbered_Step containing a Pointing_Hand_Question in sequential order without skipping any step.
2. WHEN the Agent completes a Numbered_Step, THE Agent SHALL advance to the immediately next Numbered_Step and not skip ahead to a later step.
3. WHILE a Pointing_Hand_Question is pending, THE Agent SHALL not advance `current_step` in `config/bootcamp_progress.json` beyond the step containing that question.

### Requirement 2: No Unauthorized Step Merging

**User Story:** As a bootcamper, I want the agent to never combine or merge steps without asking me first, so that I retain full control over my learning pace.

#### Acceptance Criteria

1. THE Agent SHALL present each Numbered_Step as a distinct interaction turn, separate from all other steps.
2. IF the Agent identifies an opportunity to combine multiple Numbered_Steps into a single turn, THEN THE Agent SHALL ask the bootcamper for explicit consent before combining.
3. WHEN the bootcamper declines a request to combine steps, THE Agent SHALL continue executing steps one at a time in sequential order.

### Requirement 3: Turn Boundary Enforcement at Stop Markers

**User Story:** As a bootcamper, I want the agent to stop and wait for my response after every 🛑 STOP marker, so that I always have the opportunity to provide input.

#### Acceptance Criteria

1. WHEN the Agent encounters a 🛑 STOP marker after a Pointing_Hand_Question, THE Agent SHALL end the current turn immediately and produce no further output.
2. WHILE a 🛑 STOP marker has been reached, THE Agent SHALL not generate any additional content until the bootcamper provides a response.
3. THE Agent SHALL write `config/.question_pending` with the question text before ending the turn at a 🛑 STOP marker.

### Requirement 4: Explicit Consent Before Time-Saving Actions

**User Story:** As a bootcamper, I want the agent to always ask before taking shortcuts, so that my agency over the learning experience is preserved.

#### Acceptance Criteria

1. IF the Agent determines that skipping or abbreviating a Numbered_Step would save time, THEN THE Agent SHALL ask the bootcamper for permission before taking that action.
2. WHEN the bootcamper denies permission to skip or abbreviate, THE Agent SHALL execute the Numbered_Step in full as specified by the Module_Steering_File.
3. THE Agent SHALL not use internal reasoning (context budget, session length, perceived redundancy) as justification to skip a Numbered_Step without bootcamper consent.

### Requirement 5: agentStop Hook for Step Progression Detection

**User Story:** As a bootcamp power developer, I want an agentStop hook that detects when the agent has advanced past a 👉 step without writing its checkpoint, so that step-skipping violations are caught automatically.

#### Acceptance Criteria

1. THE Enforce_Sequential_Steps_Hook SHALL fire on every agentStop event across all modules.
2. WHEN the Enforce_Sequential_Steps_Hook fires, THE Enforce_Sequential_Steps_Hook SHALL read `config/bootcamp_progress.json` and compare `current_step` against the `step_history` for the current module.
3. IF `current_step` has advanced by more than one step since the last recorded checkpoint in `step_history`, THEN THE Enforce_Sequential_Steps_Hook SHALL output a violation message identifying the skipped step numbers.
4. IF `current_step` has advanced by exactly one step and the previous step's checkpoint exists in `step_history`, THEN THE Enforce_Sequential_Steps_Hook SHALL produce no output.
5. THE Enforce_Sequential_Steps_Hook SHALL be registered in `senzing-bootcamp/hooks/hook-categories.yaml` under the `critical` category.

### Requirement 6: Per-Module Sequential Execution Reminders

**User Story:** As a bootcamp power developer, I want every module steering file to contain a sequential execution reminder, so that the never-skip rule is reinforced at the point of use.

#### Acceptance Criteria

1. THE Sequential_Execution_Reminder SHALL be present in each of the 11 Module_Steering_Files.
2. THE Sequential_Execution_Reminder SHALL state that all Numbered_Steps with Pointing_Hand_Questions must be executed sequentially without skipping.
3. THE Sequential_Execution_Reminder SHALL reference the same absolute precedence level as Mandatory_Gate rules defined in `agent-instructions.md`.
4. WHEN the Agent loads a Module_Steering_File, THE Agent SHALL apply the Sequential_Execution_Reminder for the duration of that module.

### Requirement 7: Rule Precedence Parity with Mandatory Gates

**User Story:** As a bootcamp power developer, I want the never-skip rule to have the same absolute precedence as ⛔ mandatory gate rules, so that no agent-internal reasoning can override it.

#### Acceptance Criteria

1. THE Agent SHALL treat the never-skip-numbered-steps rule with the same absolute precedence as the Mandatory_Gate Precedence rule defined in `agent-instructions.md`.
2. IF context budget pressure, session length, or token limits conflict with executing a Numbered_Step, THEN THE Agent SHALL apply context management strategies (unload non-essential files, adaptive pacing) rather than skipping the step.
3. THE `agent-instructions.md` steering file SHALL contain the never-skip-numbered-steps rule in the Mandatory Gate Precedence section.
4. THE `conversation-protocol.md` steering file SHALL contain strengthened language in the Question Stop Protocol reinforcing that every Pointing_Hand_Question step is a mandatory execution boundary.
