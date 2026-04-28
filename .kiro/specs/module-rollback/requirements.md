# Requirements Document

## Introduction

The senzing-bootcamp power currently supports full-project backup and restore via `backup_project.py` and `restore_project.py`, but these operate on the entire project as a single snapshot. There is no way to undo the work of a single module without reverting everything. This feature adds a `scripts/rollback_module.py` that can revert the artifacts produced by a specific module — removing files, restoring database state where applicable, and updating `config/bootcamp_progress.json` — so that a bootcamper can undo one module's work without losing progress from other modules.

## Glossary

- **Rollback_Script**: The Python script at `senzing-bootcamp/scripts/rollback_module.py` that reverts the artifacts of a specific module.
- **Artifact_Manifest**: A per-module data structure inside the Rollback_Script that declares which files, directories, and database effects belong to each module (1 through 12).
- **Progress_File**: The JSON file at `config/bootcamp_progress.json` that stores bootcamp completion state — completed modules, current module, data sources, and step-level progress.
- **Downstream_Module**: A module whose artifacts depend on the output of an earlier module (e.g., Module 6 depends on Module 5 mappings; Module 7 depends on Module 6 loading).
- **Database_Module**: A module that modifies the Senzing database (`database/G2C.db`) by loading or purging records — specifically Modules 6 and 7.
- **Pre_Load_Backup**: A project backup ZIP file created before a Database_Module runs, typically triggered by the `backup-before-load` hook or manual `backup_project.py` invocation.
- **Dry_Run**: An execution mode of the Rollback_Script (activated by `--dry-run`) that previews what would be removed or reverted without making any changes.
- **Status_Script**: The Python script at `senzing-bootcamp/scripts/status.py` that displays bootcamp progress in the terminal.
- **Repair_Script**: The Python script at `senzing-bootcamp/scripts/repair_progress.py` that reconstructs the Progress_File from project artifacts.
- **Module_Completion_Workflow**: The steering workflow in `module-completion.md` that handles journal entries, reflection, and next-step options after completing a module.

## Requirements

### Requirement 1: Rollback Script Creation

**User Story:** As a bootcamper, I want a dedicated rollback script, so that I can undo a specific module's work from the command line.

#### Acceptance Criteria

1. THE Rollback_Script SHALL reside at `senzing-bootcamp/scripts/rollback_module.py`.
2. THE Rollback_Script SHALL accept a `--module N` argument where N is an integer from 1 to 12 identifying the module to roll back.
3. THE Rollback_Script SHALL accept a `--dry-run` flag that previews the rollback without making changes.
4. THE Rollback_Script SHALL accept a `--force` flag that skips the interactive confirmation prompt.
5. THE Rollback_Script SHALL depend only on the Python standard library (no third-party packages).
6. THE Rollback_Script SHALL be cross-platform, supporting Linux, macOS, and Windows.

### Requirement 2: Per-Module Artifact Manifests

**User Story:** As a bootcamp maintainer, I want each module's artifacts defined in a single manifest, so that the rollback script knows exactly what to remove for each module.

#### Acceptance Criteria

1. THE Rollback_Script SHALL contain an Artifact_Manifest for each of the 12 modules, declaring the files and directories that module produces.
2. THE Artifact_Manifest for Module 1 SHALL include `docs/business_problem.md`.
3. THE Artifact_Manifest for Module 2 SHALL include `database/G2C.db` and `config/bootcamp_preferences.yaml`.
4. THE Artifact_Manifest for Module 3 SHALL include the `src/quickstart_demo/` directory.
5. THE Artifact_Manifest for Module 4 SHALL include `docs/data_source_locations.md` and the `data/raw/` directory contents.
6. THE Artifact_Manifest for Module 5 SHALL include `docs/data_source_evaluation.md`, `docs/data_quality_report.md`, the `src/transform/` directory, and the `data/transformed/` directory.
7. THE Artifact_Manifest for Module 6 SHALL include the `src/load/` directory and mark the database as modified.
8. THE Artifact_Manifest for Module 7 SHALL include `docs/loading_strategy.md` and mark the database as modified.
9. THE Artifact_Manifest for Module 8 SHALL include the `src/query/` directory and `docs/results_validation.md`.
10. THE Artifact_Manifest for Module 9 SHALL include `docs/performance_requirements.md`, `docs/performance_report.md`, and the `tests/performance/` directory.
11. THE Artifact_Manifest for Module 10 SHALL include `docs/security_checklist.md`.
12. THE Artifact_Manifest for Module 11 SHALL include `docs/monitoring_setup.md` and the `monitoring/` directory.
13. THE Artifact_Manifest for Module 12 SHALL include `docs/deployment_plan.md`.
14. WHEN a module's Artifact_Manifest references a directory, THE Rollback_Script SHALL remove the directory and all its contents.
15. WHEN a module's Artifact_Manifest references a file, THE Rollback_Script SHALL remove only that file.

### Requirement 3: Dry Run Mode

**User Story:** As a bootcamper, I want to preview what a rollback would do before committing, so that I can verify the scope of changes and avoid surprises.

#### Acceptance Criteria

1. WHEN the `--dry-run` flag is provided, THE Rollback_Script SHALL list all files and directories that would be removed, without deleting anything.
2. WHEN the `--dry-run` flag is provided and the target module is a Database_Module, THE Rollback_Script SHALL report whether a Pre_Load_Backup is available and which backup file would be used for database restoration.
3. WHEN the `--dry-run` flag is provided, THE Rollback_Script SHALL list any Downstream_Modules that would be invalidated by the rollback.
4. WHEN the `--dry-run` flag is provided, THE Rollback_Script SHALL show the Progress_File changes that would be made (modules removed from `modules_completed`, updated `current_module`).
5. WHEN the `--dry-run` flag is provided, THE Rollback_Script SHALL exit with code 0 without modifying any files.

### Requirement 4: File and Directory Removal

**User Story:** As a bootcamper, I want the rollback to cleanly remove the target module's artifacts, so that I can redo the module from a clean state.

#### Acceptance Criteria

1. WHEN the Rollback_Script executes a rollback for a module, THE Rollback_Script SHALL remove all files and directories listed in that module's Artifact_Manifest.
2. WHEN an artifact listed in the Artifact_Manifest does not exist, THE Rollback_Script SHALL skip the missing artifact and continue without error.
3. WHEN all artifacts for a module have been removed, THE Rollback_Script SHALL print a summary listing each removed item and each skipped item.
4. THE Rollback_Script SHALL NOT remove files or directories that are not listed in the target module's Artifact_Manifest.

### Requirement 5: Database State Handling

**User Story:** As a bootcamper, I want the rollback of a loading module to offer database restoration from a backup, so that loaded records are properly removed.

#### Acceptance Criteria

1. WHEN the target module is a Database_Module (Module 6 or Module 7), THE Rollback_Script SHALL scan the `backups/` directory for the most recent Pre_Load_Backup ZIP file.
2. WHEN a Pre_Load_Backup is found, THE Rollback_Script SHALL prompt the user to confirm database restoration from that backup.
3. WHEN the user confirms database restoration, THE Rollback_Script SHALL extract only the `database/` directory from the Pre_Load_Backup, overwriting the current database files.
4. WHEN the user declines database restoration, THE Rollback_Script SHALL print a warning that loaded records remain in the database and suggest running `backup_project.py` followed by a manual database reset.
5. WHEN no Pre_Load_Backup is found, THE Rollback_Script SHALL print a warning that no backup is available and advise the user to re-run Module 2 SDK Setup to recreate a clean database.
6. WHEN the `--force` flag is provided alongside a Database_Module rollback with an available Pre_Load_Backup, THE Rollback_Script SHALL restore the database without prompting.

### Requirement 6: Progress File Update

**User Story:** As a bootcamper, I want the progress file updated after a rollback, so that the bootcamp state accurately reflects which modules are complete.

#### Acceptance Criteria

1. WHEN the Rollback_Script completes a rollback for module N, THE Rollback_Script SHALL remove N from the `modules_completed` list in the Progress_File.
2. WHEN the Rollback_Script completes a rollback for module N and N equals the `current_module`, THE Rollback_Script SHALL set `current_module` to N.
3. WHEN the Rollback_Script completes a rollback for module N and the Progress_File contains a `step_history` entry for module N, THE Rollback_Script SHALL remove that entry.
4. WHEN the Rollback_Script completes a rollback for module N and the Progress_File contains a `current_step` value associated with module N, THE Rollback_Script SHALL remove the `current_step` field.
5. IF the Progress_File does not exist, THEN THE Rollback_Script SHALL print a warning and skip the progress update.
6. THE Rollback_Script SHALL write the updated Progress_File with proper JSON formatting (2-space indent, trailing newline).

### Requirement 7: Downstream Dependency Warnings

**User Story:** As a bootcamper, I want to be warned about downstream modules that depend on the module I am rolling back, so that I understand the full impact before proceeding.

#### Acceptance Criteria

1. THE Rollback_Script SHALL define a dependency map declaring which modules depend on which earlier modules, consistent with the module-prerequisites steering file.
2. WHEN the target module has Downstream_Modules that are listed in `modules_completed`, THE Rollback_Script SHALL print a warning listing each affected Downstream_Module by number and name.
3. WHEN the target module has completed Downstream_Modules and the `--force` flag is not provided, THE Rollback_Script SHALL prompt the user to confirm the rollback despite downstream dependencies.
4. WHEN the user declines the confirmation, THE Rollback_Script SHALL exit without making changes.
5. THE Rollback_Script SHALL NOT automatically roll back Downstream_Modules — the warning is informational only.

### Requirement 8: Interactive Confirmation

**User Story:** As a bootcamper, I want a confirmation prompt before a rollback executes, so that I do not accidentally lose work.

#### Acceptance Criteria

1. WHEN the `--force` flag is not provided, THE Rollback_Script SHALL display a summary of the planned rollback and prompt the user with "Proceed with rollback? (y/N)".
2. WHEN the user responds with "y" or "Y", THE Rollback_Script SHALL proceed with the rollback.
3. WHEN the user responds with anything other than "y" or "Y", THE Rollback_Script SHALL exit with code 0 and print "Rollback cancelled."
4. WHEN the `--force` flag is provided, THE Rollback_Script SHALL skip the confirmation prompt and proceed immediately.

### Requirement 9: Module Completion Workflow Integration

**User Story:** As a bootcamper, I want the module completion workflow to mention rollback as an option, so that I know I can undo a module if needed.

#### Acceptance Criteria

1. THE Module_Completion_Workflow SHALL include a rollback option in the next-step options presented after completing a module (e.g., "Undo: Roll back this module's work with `python scripts/rollback_module.py --module N`").
2. THE Module_Completion_Workflow SHALL present the rollback option after the existing Iterate and Explore options and before the Share option.

### Requirement 10: POWER.md and Status Integration

**User Story:** As a bootcamper, I want the rollback script listed in the power documentation and referenced by the status script, so that I can discover and use it easily.

#### Acceptance Criteria

1. THE `POWER.md` Useful Commands section SHALL include the rollback command: `python3 senzing-bootcamp/scripts/rollback_module.py --module N`.
2. THE Status_Script SHALL display a hint about the rollback command when showing completed modules (e.g., "Tip: Use `python scripts/rollback_module.py --module N` to undo a module").

### Requirement 11: Error Handling

**User Story:** As a bootcamper, I want clear error messages when the rollback script encounters problems, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN the `--module` argument is missing, THE Rollback_Script SHALL print usage information and exit with a non-zero exit code.
2. WHEN the `--module` argument is outside the range 1-12, THE Rollback_Script SHALL print an error message stating the valid range and exit with a non-zero exit code.
3. WHEN the target module is not in `modules_completed` and has no artifacts on disk, THE Rollback_Script SHALL print a message that there is nothing to roll back and exit with code 0.
4. IF a file removal fails due to a permission error, THEN THE Rollback_Script SHALL print a warning identifying the file, continue removing remaining artifacts, and report the failure in the summary.
5. IF the Progress_File contains invalid JSON, THEN THE Rollback_Script SHALL print a warning, skip the progress update, and suggest running `repair_progress.py` after resolving the issue.

### Requirement 12: Rollback Logging

**User Story:** As a bootcamper, I want a record of what was rolled back, so that I can review past rollbacks if something goes wrong.

#### Acceptance Criteria

1. WHEN the Rollback_Script completes a rollback (not a dry run), THE Rollback_Script SHALL append a timestamped entry to `logs/rollback_log.jsonl` recording the module number, list of removed artifacts, database restoration status, and any warnings.
2. WHEN the `logs/` directory does not exist, THE Rollback_Script SHALL create it before writing the log entry.
3. THE log entry SHALL be a single JSON object on one line, conforming to JSON Lines format.
4. FOR ALL log entries written by the Rollback_Script, parsing each line with `json.loads` SHALL produce a valid Python dictionary without raising an exception (round-trip property).
