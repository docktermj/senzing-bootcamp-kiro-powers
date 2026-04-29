# Requirements Document

## Introduction

After `rollback_module.py` removes a module's artifacts and updates the progress file, it currently has no way to confirm the rollback actually worked. This enhancement adds a post-rollback verification step that re-runs the module's validator (from `validate_module.py`) to confirm all artifact checks now fail — meaning the module is back to a "not started" state. If any validator check still passes after rollback, the script warns the user about leftover artifacts.

## Glossary

- **Rollback_Script**: The `rollback_module.py` script that reverts artifacts produced by a specific bootcamp module
- **Module_Validator**: The `VALIDATORS` dict in `validate_module.py`, where each entry is a callable returning a list of `(ok, description, detail)` tuples for a given module number
- **Verification_Step**: The new post-rollback phase that invokes the Module_Validator to confirm the module is no longer in a completed state
- **Validator_Check**: A single `(ok, description, detail)` tuple returned by a Module_Validator callable; `ok=True` means the artifact still exists
- **Rollback_Log_Entry**: The JSON Lines record appended to `logs/rollback_log.jsonl` after each rollback

## Requirements

### Requirement 1: Post-Rollback Verification

**User Story:** As a bootcamp user, I want the rollback script to verify that the module is back to "not started" after removing artifacts, so that I can trust the rollback was complete.

#### Acceptance Criteria

1. WHEN artifact removal and progress update are complete, THE Rollback_Script SHALL invoke the Module_Validator for the rolled-back module number
2. WHEN all Validator_Checks return `ok=False`, THE Rollback_Script SHALL print a verification-passed message to stdout
3. WHEN one or more Validator_Checks return `ok=True` after rollback, THE Rollback_Script SHALL print a warning listing each still-passing check description
4. IF the Module_Validator raises an exception, THEN THE Rollback_Script SHALL print a warning that verification could not be completed and continue without failing the rollback

### Requirement 2: Verification in Dry-Run Mode

**User Story:** As a bootcamp user, I want dry-run mode to skip the verification step, so that dry-run remains a read-only preview with no side effects.

#### Acceptance Criteria

1. WHILE the `--dry-run` flag is active, THE Rollback_Script SHALL skip the Verification_Step entirely
2. WHILE the `--dry-run` flag is active, THE Rollback_Script SHALL not invoke the Module_Validator

### Requirement 3: Verification Result in Rollback Log

**User Story:** As a bootcamp user, I want the rollback log to record whether verification passed, so that I have an audit trail of rollback outcomes.

#### Acceptance Criteria

1. WHEN verification passes (all checks return `ok=False`), THE Rollback_Script SHALL include `"verification": "passed"` in the Rollback_Log_Entry
2. WHEN verification finds leftover artifacts, THE Rollback_Script SHALL include `"verification": "failed"` and a `"leftover_checks"` list of the still-passing check descriptions in the Rollback_Log_Entry
3. WHEN verification is skipped (dry-run) or the Module_Validator raises an exception, THE Rollback_Script SHALL include `"verification": null` in the Rollback_Log_Entry
