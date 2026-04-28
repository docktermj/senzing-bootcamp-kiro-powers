# Tasks

## Task 1: Create rollback_module.py with CLI parsing and constants

- [x] 1.1 Create `senzing-bootcamp/scripts/rollback_module.py` with shebang, docstring, and stdlib-only imports (os, sys, json, zipfile, shutil, argparse, datetime, dataclasses, pathlib)
- [x] 1.2 Add color utility functions (`color_supported`, `c`, `green`, `red`, `yellow`) matching existing script conventions
- [x] 1.3 Define `ModuleArtifacts` dataclass with `files: list[str]`, `directories: list[str]`, `modifies_database: bool`
- [x] 1.4 Define `ARTIFACT_MANIFEST` dict mapping modules 1–12 to their `ModuleArtifacts` per requirements 2.2–2.13
- [x] 1.5 Define `MODULE_NAMES` dict (1–12) matching `status.py`
- [x] 1.6 Define `PREREQUISITES` dict and `get_downstream_modules(module)` function returning sorted transitive dependents
- [x] 1.7 Define `get_completed_downstream(module, modules_completed)` returning sorted list of completed downstream modules
- [x] 1.8 Add `argparse`-based CLI with `--module N` (required, int), `--dry-run` flag, `--force` flag; validate module range 1–12 and exit with code 1 on invalid input

## Task 2: Implement progress file operations

- [x] 2.1 Implement `read_progress_file(path)` returning parsed dict or None on missing/invalid JSON (print warning for invalid JSON suggesting `repair_progress.py`)
- [x] 2.2 Implement `write_progress_file(path, data)` with 2-space indent and trailing newline
- [x] 2.3 Implement `compute_progress_update(progress_data, module)` as a pure function: remove module from `modules_completed`, set `current_module` to N if it was current, remove `step_history` entry for N, clear `current_step` if current module equals N, preserve all other fields

## Task 3: Implement artifact removal and database handling

- [x] 3.1 Implement `RemovalResult` dataclass with `removed_files`, `removed_dirs`, `skipped_missing`, `failed_items`
- [x] 3.2 Implement `remove_artifacts(artifacts, project_root)` that removes manifest files and directories, skips missing items, catches permission errors, and returns `RemovalResult`
- [x] 3.3 Implement `find_latest_backup(backups_dir)` that scans for ZIP files and returns the path with the most recent timestamp (or None)
- [x] 3.4 Implement `restore_database_from_backup(backup_path, project_root)` that extracts only `database/` entries from the ZIP, returns True/False

## Task 4: Implement rollback logging

- [x] 4.1 Define `RollbackLogEntry` dataclass with timestamp, module, removed_files, removed_dirs, skipped_missing, failed_items, database_restored, backup_used, warnings
- [x] 4.2 Implement `build_log_entry(module, removal_result, database_restored, backup_used, warnings)` pure function
- [x] 4.3 Implement `serialize_log_entry(entry)` returning a single JSON line (no embedded newlines)
- [x] 4.4 Implement `append_log_entry(log_path, entry_line)` that creates `logs/` directory if needed and appends the line

## Task 5: Implement dry-run, confirmation, and main orchestration

- [x] 5.1 Implement `format_dry_run_report(module, artifacts, existing_files, existing_dirs, missing_items, backup_path, downstream_completed, progress_changes)` pure function returning formatted preview string
- [x] 5.2 Implement confirmation prompt logic: display summary, prompt "Proceed with rollback? (y/N)", accept only "y"/"Y", skip when `--force` is set
- [x] 5.3 Implement downstream dependency warning: check for completed downstream modules, print warning with module numbers and names, prompt for confirmation (unless `--force`)
- [x] 5.4 Implement database rollback flow: for modules 6/7, find backup, prompt for DB restoration (or auto-restore with `--force`), print appropriate warnings when no backup or user declines
- [x] 5.5 Implement `main(argv)` orchestrating: parse args → check nothing-to-rollback → dry-run path → downstream warning → confirmation → remove artifacts → handle DB → update progress → log → print summary
- [x] 5.6 Add `if __name__ == "__main__": sys.exit(main())` entry point

## Task 6: Integration updates (module-completion, POWER.md, status.py)

- [x] 6.1 Update `senzing-bootcamp/steering/module-completion.md` to add rollback option ("Undo: Roll back this module's work with `python scripts/rollback_module.py --module N`") after Iterate/Explore and before Share
- [x] 6.2 Update `senzing-bootcamp/POWER.md` Useful Commands section to include `python3 senzing-bootcamp/scripts/rollback_module.py --module N`
- [x] 6.3 Update `senzing-bootcamp/scripts/status.py` to display a rollback hint when showing completed modules (e.g., "Tip: Use `python scripts/rollback_module.py --module N` to undo a module")

## Task 7: Property-based tests

- [x] 7.1 Create `senzing-bootcamp/scripts/test_rollback_module.py` with imports (pytest, hypothesis, json, tempfile, pathlib, zipfile, dataclasses)
- [x] 7.2 Implement Hypothesis strategies: module numbers, progress states, RemovalResult, RollbackLogEntry, backup ZIP files, confirmation input strings
- [x] 7.3 [PBT] Property 1: Module number validation — for any integer, validate_module_range accepts 1–12 and rejects others
- [x] 7.4 [PBT] Property 2: Manifest completeness — for any module 1–12, ARTIFACT_MANIFEST contains valid ModuleArtifacts with correct modifies_database flag
- [x] 7.5 [PBT] Property 3: Rollback removes exactly manifest items — for any module, create manifest artifacts + extras in temp dir, run remove_artifacts, verify only manifest items removed
- [x] 7.6 [PBT] Property 4: Removal resilience — for any module and random subset of existing artifacts, remove_artifacts correctly categorizes removed/skipped/failed
- [x] 7.7 [PBT] Property 5: Dry-run safety — for any module and temp filesystem, dry-run produces output but modifies nothing
- [x] 7.8 [PBT] Property 6: Downstream dependency reporting — for any module and progress state with completed downstream modules, output lists each downstream module
- [x] 7.9 [PBT] Property 7: Progress file update correctness — for any progress state and module N, compute_progress_update produces correct mutations
- [x] 7.10 [PBT] Property 8: Progress file JSON formatting — for any progress dict, write then read produces identical dict with 2-space indent and trailing newline
- [x] 7.11 [PBT] Property 9: Confirmation input validation — for any string, confirmation proceeds iff input is "y" or "Y"
- [x] 7.12 [PBT] Property 10: Latest backup selection — for any set of timestamped ZIP filenames, find_latest_backup returns the most recent
- [x] 7.13 [PBT] Property 11: Database restoration extracts only database/ — for any ZIP with database/ and other dirs, only database/ is extracted
- [x] 7.14 [PBT] Property 12: Rollback log entry round-trip — for any RollbackLogEntry, serialize then json.loads produces matching dict
- [x] 7.15 [PBT] Property 13: Downstream artifacts untouched — for any module with downstream artifacts on disk, rollback only removes target module artifacts

## Task 8: Unit tests for specific examples and edge cases

- [x] 8.1 Add unit tests verifying each module's manifest content matches requirements 2.2–2.13 (12 test cases)
- [x] 8.2 Add unit test verifying dependency map matches module-prerequisites diagram
- [x] 8.3 Add unit tests for error scenarios: missing --module, out-of-range module, nothing to roll back, missing progress file, invalid JSON progress file
- [x] 8.4 Add unit tests for database scenarios: backup found + user confirms, backup found + user declines, no backup found, --force with backup
- [x] 8.5 Add unit tests for confirmation prompt: --force skips prompt, user enters "y"/"Y" proceeds, user enters other text cancels
- [x] 8.6 Run all tests and verify they pass
