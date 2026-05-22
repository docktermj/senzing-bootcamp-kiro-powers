# Requirements Document

## Introduction

Split the monolithic `session-resume.md` steering file (~4,661 tokens) into a lean phase-1 file and three concern-specific phase-2 files. The restructuring reduces context window consumption on the happy path by loading only the phase-1 file (~2,000 tokens) and conditionally loading phase-2 files only when their specific recovery scenarios are detected. All files are registered in `steering-index.yaml` following the existing phase-splitting pattern.

## Glossary

- **Phase_1_File**: The lean root steering file (`session-resume.md`) containing fast-path check logic, happy-path inline flow (Steps 2b/2c/3), and routing conditions that determine which phase-2 files to load.
- **Phase_2_Mapping_File**: The steering file (`session-resume-phase2-mapping.md`) containing mapping checkpoint recovery logic, loaded when `config/mapping_state_*.json` files exist.
- **Phase_2_State_Repair_File**: The steering file (`session-resume-phase2-state-repair.md`) containing stale or corrupted state handling logic, loaded when `bootcamp_progress.json` is missing, corrupted, or inconsistent with project artifacts.
- **Phase_2_Setup_Recovery_File**: The steering file (`session-resume-phase2-setup-recovery.md`) containing setup recovery logic for missing hooks, MCP health check failures, and What's New notifications.
- **Steering_Index**: The `steering-index.yaml` file that registers all steering files with their token counts, size categories, and phase relationships.
- **Routing_Logic**: The conditional evaluation in Phase_1_File that determines which phase-2 files to load based on detected session state.
- **Fast_Path**: The optimized resume path that skips full state reconstruction when all fast-path conditions are met.
- **Agent**: The Kiro agent that processes steering files and executes bootcamp workflows.

## Requirements

### Requirement 1: Phase-1 File Content Scope

**User Story:** As a power maintainer, I want the phase-1 file to contain only fast-path logic, happy-path flow, and routing conditions, so that the agent loads minimal tokens on the common resume path.

#### Acceptance Criteria

1. THE Phase_1_File SHALL contain the Fast_Path check conditions (five boolean checks) and the skip-to-Step-3 logic.
2. THE Phase_1_File SHALL contain Step 2b (Behavioral Rules Reload) inline.
3. THE Phase_1_File SHALL contain Step 2c (Restore Conversation Style) inline.
4. THE Phase_1_File SHALL contain Step 3 (Summarize and Confirm) inline.
5. THE Phase_1_File SHALL contain Routing_Logic that specifies the conditions under which each phase-2 file is loaded.
6. THE Phase_1_File SHALL contain Step 1 (Read All State Files) for the non-fast-path flow.
7. THE Phase_1_File SHALL contain Step 2 (Load Language Steering) for the non-fast-path flow.
8. THE Phase_1_File SHALL contain Step 4 (Load the Right Module Steering) excluding mapping checkpoint validation logic.
9. THE Phase_1_File SHALL contain Step 5 (Re-establish MCP Context).
10. THE Phase_1_File SHALL have a token count at or below 2,200 tokens.

### Requirement 2: Phase-2 Mapping File Content Scope

**User Story:** As a power maintainer, I want mapping checkpoint recovery logic isolated in its own file, so that it is only loaded when the agent detects in-progress mapping state files.

#### Acceptance Criteria

1. THE Phase_2_Mapping_File SHALL contain the mapping checkpoint validation procedure (JSON parsing, required field checks, MCP status call).
2. THE Phase_2_Mapping_File SHALL contain the mapping resume options presentation (Resume, Restart, Skip).
3. THE Phase_2_Mapping_File SHALL contain the fast-track-through-completed-steps logic for valid checkpoints.
4. THE Phase_2_Mapping_File SHALL contain the corrupted checkpoint handling and restart offer.
5. WHEN one or more `config/mapping_state_*.json` files exist, THE Routing_Logic SHALL direct the Agent to load Phase_2_Mapping_File.
6. THE Phase_2_Mapping_File SHALL have a token count at or below 1,000 tokens.

### Requirement 3: Phase-2 State Repair File Content Scope

**User Story:** As a power maintainer, I want stale and corrupted state handling isolated in its own file, so that it is only loaded when the progress file is detected as problematic.

#### Acceptance Criteria

1. THE Phase_2_State_Repair_File SHALL contain the "Handling Stale or Corrupted State" procedure (artifact scanning, discrepancy reporting, progress file correction).
2. THE Phase_2_State_Repair_File SHALL contain the logic for reconstructing progress from project artifacts when `bootcamp_progress.json` is missing or corrupted.
3. WHEN `config/bootcamp_progress.json` fails to parse as valid JSON, THE Routing_Logic SHALL direct the Agent to load Phase_2_State_Repair_File.
4. WHEN `config/bootcamp_progress.json` contains a `current_module` value that is inconsistent with project artifacts, THE Routing_Logic SHALL direct the Agent to load Phase_2_State_Repair_File.
5. THE Phase_2_State_Repair_File SHALL have a token count at or below 800 tokens.

### Requirement 4: Phase-2 Setup Recovery File Content Scope

**User Story:** As a power maintainer, I want setup recovery logic (hooks, MCP health, What's New) isolated in its own file, so that it is only loaded when setup issues are detected.

#### Acceptance Criteria

1. THE Phase_2_Setup_Recovery_File SHALL contain the hook installation logic (reading Hook Registry, creating Critical Hooks via `createHook`, handling failures).
2. THE Phase_2_Setup_Recovery_File SHALL contain Step 2d (MCP Health Check) including the probe call, success path, and failure path with troubleshooting steps.
3. THE Phase_2_Setup_Recovery_File SHALL contain Step 2e (What's New Notification) including CHANGELOG parsing and display logic.
4. WHEN `hooks_installed` is missing or empty in `config/bootcamp_preferences.yaml`, THE Routing_Logic SHALL direct the Agent to load Phase_2_Setup_Recovery_File.
5. WHEN `config/bootcamp_preferences.yaml` is missing or corrupted, THE Routing_Logic SHALL direct the Agent to load Phase_2_Setup_Recovery_File.
6. WHEN the MCP health check probe fails or times out, THE Routing_Logic SHALL direct the Agent to load Phase_2_Setup_Recovery_File.
7. WHEN `show_whats_new` is not set to `false` in preferences and `config/session_log.jsonl` exists, THE Routing_Logic SHALL direct the Agent to load Phase_2_Setup_Recovery_File.
8. THE Phase_2_Setup_Recovery_File SHALL have a token count at or below 700 tokens.

### Requirement 5: Simultaneous Phase-2 Loading

**User Story:** As a power maintainer, I want multiple phase-2 files to be loadable simultaneously, so that compound recovery scenarios (e.g., corrupted state AND missing hooks) are handled in a single resume flow.

#### Acceptance Criteria

1. THE Routing_Logic SHALL evaluate all phase-2 loading conditions independently.
2. WHEN multiple phase-2 loading conditions are true simultaneously, THE Agent SHALL load all triggered phase-2 files.
3. THE Phase_1_File SHALL specify the evaluation order for Routing_Logic conditions as: state repair first, setup recovery second, mapping third.

### Requirement 6: Steering Index Registration

**User Story:** As a power maintainer, I want all new steering files registered in `steering-index.yaml`, so that the agent file selection system can discover and track them.

#### Acceptance Criteria

1. THE Steering_Index SHALL contain a `session-resume` entry with a `phases` map listing all four files (phase-1 root and three phase-2 files).
2. THE Steering_Index SHALL record the `token_count` for each session-resume phase file.
3. THE Steering_Index SHALL record the `size_category` for each session-resume phase file based on the existing category thresholds.
4. THE Steering_Index `file_metadata` section SHALL contain entries for `session-resume-phase2-mapping.md`, `session-resume-phase2-state-repair.md`, and `session-resume-phase2-setup-recovery.md` with their respective token counts and size categories.
5. THE Steering_Index `file_metadata` entry for `session-resume.md` SHALL reflect the updated (reduced) token count of the Phase_1_File.

### Requirement 7: Behavioral Equivalence

**User Story:** As a power maintainer, I want the split files to produce identical agent behavior to the original monolithic file, so that no bootcamper-facing functionality is lost or altered.

#### Acceptance Criteria

1. THE combined content of Phase_1_File, Phase_2_Mapping_File, Phase_2_State_Repair_File, and Phase_2_Setup_Recovery_File SHALL cover all instructions present in the original `session-resume.md`.
2. THE Phase_1_File SHALL preserve the `inclusion: manual` frontmatter setting.
3. WHEN all phase-2 files are loaded simultaneously, THE Agent SHALL produce the same resume behavior as the original monolithic `session-resume.md`.
4. THE `keywords` section in Steering_Index SHALL continue to map `resume` to `session-resume.md` (the Phase_1_File).

### Requirement 8: Token Budget Reduction on Happy Path

**User Story:** As a power maintainer, I want the happy-path resume to consume approximately 2,000 tokens instead of 4,661, so that more context budget is available for module steering content.

#### Acceptance Criteria

1. WHEN all Fast_Path conditions are met and no phase-2 loading conditions are triggered, THE Agent SHALL load only the Phase_1_File.
2. WHEN only the Phase_1_File is loaded, THE Agent SHALL consume no more than 2,200 tokens of context budget for session resume logic.
3. IF a phase-2 file is loaded unnecessarily (no matching condition is true), THEN THE Agent SHALL skip the phase-2 file content without executing any of its instructions.
