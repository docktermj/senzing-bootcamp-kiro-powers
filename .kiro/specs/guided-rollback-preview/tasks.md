# Tasks: Guided Rollback with Diff Preview

## Task 1: Add --preview and --yes flags to rollback_module.py

- [x] 1.1 Read the current `senzing-bootcamp/scripts/rollback_module.py` to understand its structure and rollback logic
- [x] 1.2 Add `--preview` (aliased `--dry-run`) flag to argparse
- [x] 1.3 Add `--yes` (aliased `-y`) flag to argparse for non-interactive execution
- [x] 1.4 Refactor existing rollback logic into a `compute_rollback_plan(module)` function that returns a plan without executing

## Task 2: Implement rollback plan computation

- [x] 2.1 Implement file discovery: identify files that would be deleted based on module output directories
- [x] 2.2 Implement backup detection: check if backups exist for files that would be affected
- [x] 2.3 Implement progress change computation: determine what entries in `bootcamp_progress.json` would be modified
- [x] 2.4 Implement registry change computation: determine what entries in `config/data_sources.yaml` would be reset
- [x] 2.5 Implement irreversible action detection: identify files with no backup
- [x] 2.6 Implement downstream impact analysis: check module-dependencies.yaml for dependent modules with existing artifacts

## Task 3: Implement preview output formatting

- [x] 3.1 Format "Files to be deleted" section with file sizes
- [x] 3.2 Format "Files to be reverted" section with backup timestamps
- [x] 3.3 Format "Progress entries to be cleared" section
- [x] 3.4 Format "Irreversible actions" section with ⚠️ warning indicators
- [x] 3.5 Format "Safety Assessment" section (backed up count, reversibility)
- [x] 3.6 Format "Downstream impact" section with dependent module warnings
- [x] 3.7 Add "No changes made" footer for --preview mode
- [x] 3.8 Ensure --preview always exits with code 0

## Task 4: Implement interactive confirmation flow

- [x] 4.1 When run without --preview and without --yes: display the plan, then prompt for confirmation
- [x] 4.2 When --yes is provided: execute immediately without prompting
- [x] 4.3 When user declines confirmation: exit with code 0 and "Rollback cancelled" message

## Task 5: Update module-completion.md steering

- [x] 5.1 Read the current `senzing-bootcamp/steering/module-completion.md` to find the rollback offer section
- [x] 5.2 Update rollback instructions: agent should run `rollback_module.py --preview` first
- [x] 5.3 Add instruction to present preview results conversationally before asking for confirmation
- [x] 5.4 Add instruction to run `rollback_module.py --yes` only after bootcamper confirms

## Task 6: Write tests

- [x] 6.1 Create `senzing-bootcamp/tests/test_guided_rollback_preview.py`
- [x] 6.2 Unit test: --preview flag accepted by argparse
- [x] 6.3 Unit test: --yes flag accepted by argparse
- [x] 6.4 Unit test: --preview always exits with code 0
- [x] 6.5 Unit test: preview output contains "No changes made" text
- [x] 6.6 Unit test: downstream impact detection identifies dependent modules
- [x] 6.7 Unit test: irreversible action detection works for files without backups
- [x] 6.8 Property test: compute_rollback_plan for any valid module (1-11) returns a valid plan structure
- [x] 6.9 Unit test: module-completion.md contains instruction to run --preview before rollback

## Task 7: Validate

- [x] 7.1 Run `pytest senzing-bootcamp/tests/test_guided_rollback_preview.py -v`
- [x] 7.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified files
- [x] 7.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
- [x] 7.4 Verify existing rollback tests still pass
