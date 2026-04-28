# Requirements Document

## Introduction

The senzing-bootcamp power currently tracks progress at the module level via `config/bootcamp_progress.json` (fields: `modules_completed`, `current_module`). When a session drops mid-module, the agent must scan project artifacts to infer where the user left off — a slow, imprecise heuristic that often misjudges position within long modules (5, 7, 12). This feature adds step-level progress checkpointing to `bootcamp_progress.json` so that session resume can jump directly to the correct step within a module, eliminating guesswork and reducing resume latency.

## Glossary

- **Progress_File**: The JSON file at `config/bootcamp_progress.json` that stores bootcamp completion state — completed modules, current module, data sources, and (after this feature) step-level progress.
- **Step**: A numbered, discrete unit of work within a module steering file (e.g., "Step 1: Deployment Target", "Step 6: Database Migration"). Each module defines its own step sequence.
- **Checkpoint**: A write to the Progress_File that records the current step number and timestamp within the active module.
- **Step_History**: A per-module record inside the Progress_File that stores the highest completed step and a timestamp for each module the user has worked on.
- **Session_Resume**: The workflow defined in `senzing-bootcamp/steering/session-resume.md` that restores context when a returning user opens a new Kiro session.
- **Status_Script**: The Python script at `senzing-bootcamp/scripts/status.py` that displays bootcamp progress in the terminal.
- **Repair_Script**: The Python script at `senzing-bootcamp/scripts/repair_progress.py` that reconstructs the Progress_File from project artifacts.
- **Module_Steering_File**: A markdown steering file (e.g., `module-05-data-quality-mapping.md`) that defines the step-by-step workflow for a single bootcamp module.
- **Agent**: The AI agent running the bootcamp, guided by steering files and hooks.

## Requirements

### Requirement 1: Extend Progress File Schema

**User Story:** As a bootcamp user, I want my step-level progress saved in the progress file, so that resuming a session picks up exactly where I left off within a module.

#### Acceptance Criteria

1. THE Progress_File SHALL include a `current_step` integer field representing the last completed step number within the active module.
2. THE Progress_File SHALL include a `step_history` object field where each key is a module number (as a string) and each value is an object containing `last_completed_step` (integer) and `updated_at` (ISO 8601 timestamp).
3. WHEN the Agent completes a step within a module, THE Agent SHALL write a Checkpoint to the Progress_File updating `current_step` to the completed step number and updating the corresponding `step_history` entry.
4. WHEN a module is completed and added to `modules_completed`, THE Agent SHALL remove the `current_step` field (or set it to `null`) and retain the final `step_history` entry for that module.
5. THE Progress_File SHALL conform to the following extended schema (new fields shown alongside existing fields):
   ```json
   {
     "modules_completed": [1, 2, 3],
     "current_module": 4,
     "current_step": 3,
     "step_history": {
       "1": { "last_completed_step": 5, "updated_at": "2026-05-10T14:30:00Z" },
       "4": { "last_completed_step": 3, "updated_at": "2026-05-12T09:15:00Z" }
     },
     "data_sources": [],
     "database_type": "sqlite"
   }
   ```

### Requirement 2: Backward Compatibility

**User Story:** As an existing bootcamp user, I want my current progress file to keep working after this update, so that I do not lose any progress.

#### Acceptance Criteria

1. WHEN the Progress_File lacks the `current_step` field, THE Agent SHALL treat the current step as unknown and fall back to artifact scanning for resume positioning.
2. WHEN the Progress_File lacks the `step_history` field, THE Agent SHALL treat step history as empty and proceed without error.
3. WHEN the Status_Script reads a Progress_File without `current_step` or `step_history`, THE Status_Script SHALL display module-level progress without step detail and SHALL NOT raise an error.
4. WHEN the Repair_Script reads a Progress_File without `current_step` or `step_history`, THE Repair_Script SHALL operate on module-level data only and SHALL NOT raise an error.

### Requirement 3: Session Resume with Step-Level Precision

**User Story:** As a returning bootcamp user, I want the session resume to tell me exactly which step I was on, so that I can continue without repeating work.

#### Acceptance Criteria

1. WHEN the Session_Resume workflow reads a Progress_File containing a `current_step` value, THE Session_Resume workflow SHALL include the step number and step name in the welcome-back summary (e.g., "Current: Module 5 — Data Quality & Mapping, Step 3 of 12").
2. WHEN the Session_Resume workflow reads a Progress_File containing a `current_step` value, THE Session_Resume workflow SHALL instruct the Agent to load the Module_Steering_File and skip to the step after `current_step` instead of restarting the module from the beginning.
3. WHEN the Session_Resume workflow reads a Progress_File without a `current_step` value, THE Session_Resume workflow SHALL fall back to the existing artifact-scanning behavior described in the current `session-resume.md`.
4. IF the `current_step` value in the Progress_File references a step number that does not exist in the Module_Steering_File, THEN THE Session_Resume workflow SHALL log a warning, ignore the invalid step, and fall back to artifact scanning.

### Requirement 4: Module Steering Files Emit Checkpoints

**User Story:** As a bootcamp user working through a module, I want my progress saved at each major step, so that a session drop loses at most one step of work.

#### Acceptance Criteria

1. WHEN the Agent completes a numbered step in a Module_Steering_File, THE Agent SHALL write a Checkpoint to the Progress_File before proceeding to the next step.
2. THE Checkpoint write SHALL update both the `current_step` field and the corresponding entry in `step_history` with the step number and current ISO 8601 timestamp.
3. WHEN the Agent begins a module that has a `step_history` entry with a `last_completed_step` value, THE Agent SHALL skip all steps up to and including `last_completed_step` and resume from the next step.
4. THE Agent SHALL emit Checkpoints for all 12 module steering files (modules 1 through 12).

### Requirement 5: Status Script Displays Step Progress

**User Story:** As a bootcamp user, I want `status.py` to show which step I am on within the current module, so that I can see my detailed progress at a glance.

#### Acceptance Criteria

1. WHEN the Progress_File contains a `current_step` value and the current module is not yet complete, THE Status_Script SHALL display the current step number alongside the current module (e.g., "Current Module: Module 5, Step 3").
2. WHEN the Progress_File does not contain a `current_step` value, THE Status_Script SHALL display module-level progress only, matching the existing behavior.
3. WHEN the `--sync` flag is passed, THE Status_Script SHALL include step-level progress in the generated `PROGRESS_TRACKER.md` file for the current module.

### Requirement 6: Repair Script Reconstructs Step Progress

**User Story:** As a bootcamp user with a corrupted progress file, I want the repair tool to reconstruct step-level progress from artifacts, so that I do not lose intra-module progress.

#### Acceptance Criteria

1. WHEN the Repair_Script runs with the `--fix` flag, THE Repair_Script SHALL attempt to infer `current_step` for the current module by scanning module-specific artifacts (e.g., presence of `docs/data_source_evaluation.md` implies Module 5 Phase 1 is complete).
2. WHEN the Repair_Script cannot determine the step within a module, THE Repair_Script SHALL omit the `current_step` field for that module rather than guessing incorrectly.
3. WHEN the Repair_Script runs without the `--fix` flag, THE Repair_Script SHALL report detected step-level progress alongside module-level progress in its scan output.
4. THE Repair_Script SHALL populate `step_history` entries for all modules where step-level artifacts can be identified.

### Requirement 7: Module Transitions Steering Update

**User Story:** As a bootcamp user, I want the module start banner to reflect my step-level position when resuming mid-module, so that I have clear context about where I am.

#### Acceptance Criteria

1. WHEN the module-transitions steering file displays the journey map for a module that has a `current_step` value, THE module-transitions steering file SHALL include the step number in the status column (e.g., "🔄 Current — Step 3/12").
2. WHEN the module-transitions steering file displays the journey map for a module without a `current_step` value, THE module-transitions steering file SHALL display the existing "🔄 Current" status without step detail.
