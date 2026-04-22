# Requirements Document

## Introduction

This spec retroactively documents the session resume workflow — the guided sequence that restores a returning Bootcamper's context and resumes their bootcamp session. The flow lives in `senzing-bootcamp/steering/session-resume.md` and is triggered when `config/bootcamp_progress.json` exists at session start.

## Glossary

- **Session_Resume_Flow**: The process that reads saved state, loads language steering, displays a welcome-back summary, and resumes the Bootcamper's current module.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **State_Files**: The set of files (`bootcamp_progress.json`, `bootcamp_preferences.yaml`, `bootcamp_journal.md`, `mapping_state_*.json`) that persist session context across restarts.
- **Mapping_Checkpoint**: A `config/mapping_state_*.json` file capturing in-progress data mapping work from Module 5.
- **Validation_Script**: `scripts/validate_module.py`, which checks actual project artifacts against claimed progress.

## Requirements

### Requirement 1: State Reconstruction from Saved Files

**User Story:** As a returning Bootcamper, I want my previous session context fully restored from saved files, so that I can continue without re-entering preferences or losing progress.

#### Acceptance Criteria

1. WHEN `config/bootcamp_progress.json` exists at session start, THE Session_Resume_Flow SHALL read all State_Files: `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `docs/bootcamp_journal.md`, and any `config/mapping_state_*.json` files.
2. WHEN the `language` field is read from `bootcamp_preferences.yaml`, THE Agent SHALL load the corresponding language steering file (e.g., Python → `lang-python.md`).
3. IF `bootcamp_progress.json` or `bootcamp_preferences.yaml` is missing or corrupted, THEN THE Agent SHALL inform the Bootcamper and offer to reconstruct state from project artifacts in `src/`, `data/`, and `docs/`.

### Requirement 2: Welcome-Back Summary and Confirmation

**User Story:** As a returning Bootcamper, I want a concise summary of where I left off and a prompt to continue, so that I can quickly orient myself.

#### Acceptance Criteria

1. WHEN state reconstruction completes, THE Agent SHALL display a "🎓 Welcome back to the Senzing Bootcamp!" banner followed by a summary showing: path, language, completed modules, current module, database type, and data sources.
2. WHEN Mapping_Checkpoints exist, THE Agent SHALL mention the in-progress data source and completed mapping steps in the summary.
3. WHEN the summary is displayed, THE Agent SHALL ask "Ready to continue with Module [N]?" with a 👉 marker and WAIT for the Bootcamper's response.

### Requirement 3: Module Loading Based on User Response

**User Story:** As a returning Bootcamper, I want to continue my current module, switch modules, or start over, so that I have flexibility in how I proceed.

#### Acceptance Criteria

1. WHEN the Bootcamper confirms continuation, THE Agent SHALL load the steering file for the current module from the Module Steering table in `agent-instructions.md`.
2. WHEN the Bootcamper requests a different module, THE Agent SHALL verify prerequisites via `module-prerequisites.md` before loading the requested module steering.
3. WHEN the Bootcamper requests to start over, THE Agent SHALL confirm the decision and load `onboarding-flow.md`.
4. WHEN module steering is loaded, THE Agent SHALL call `get_capabilities` to re-establish the MCP session context.

### Requirement 4: Stale or Corrupted State Handling

**User Story:** As a returning Bootcamper, I want discrepancies between my progress file and actual project artifacts detected and corrected, so that I do not resume from an invalid state.

#### Acceptance Criteria

1. IF `bootcamp_progress.json` claims a module is complete but the expected artifacts are missing, THEN THE Agent SHALL run the Validation_Script to check actual artifact state.
2. WHEN the Validation_Script reports discrepancies, THE Agent SHALL show the Bootcamper the differences and offer to correct `bootcamp_progress.json`.
3. WHEN corrections are accepted, THE Session_Resume_Flow SHALL update `bootcamp_progress.json` and resume from the last verifiably complete module.
