# Tasks

## Task 1: Create test directory and conftest.py

- [x] 1.1 Create `senzing-bootcamp/tests/__init__.py` (empty)
- [x] 1.2 Create `senzing-bootcamp/tests/conftest.py` with shared fixtures: `project_root` (tmp_path + monkeypatch.chdir), `sample_progress_data` factory, `write_progress_file` helper, and `mock_no_color` fixture
- [x] 1.3 Verify `pytest --collect-only senzing-bootcamp/tests/` discovers the conftest without errors

## Task 2: Test status.py

- [x] 2.1 Create `senzing-bootcamp/tests/test_status.py` with example tests: no progress file → "Not Started", corrupted JSON → graceful handling, all 12 complete → "Bootcamp Complete", `--sync` writes PROGRESS_TRACKER.md, empty modules_completed → not started, NO_COLOR disables color
- [x] 2.2 [PBT] Property 1: Status computation correctness — for any subset of {1..12} as completed modules, verify percentage = len(completed)*100//12 and correct status label
- [x] 2.3 [PBT] Property 2: Sync tracker reflects progress data — for any completed set and current module, sync_progress_tracker produces correct ✅/🔄/⬜ markers

## Task 3: Test repair_progress.py

- [x] 3.1 Create `senzing-bootcamp/tests/test_repair_progress.py` with example tests: no artifacts → empty detect, --fix writes valid JSON, discrepancy reporting for unrecorded modules
- [x] 3.2 [PBT] Property 3: Artifact detection correctness — for any subset of module artifacts created on disk, detect() returns exactly those module numbers
- [x] 3.3 [PBT] Property 4: Repair progress round-trip — for any artifact set, detect → fix → re-detect produces the same completed set

## Task 4: Test validate_module.py

- [x] 4.1 Create `senzing-bootcamp/tests/test_validate_module.py` with example tests: --next N validates N-1, --next 1 reports no prerequisites, VALIDATORS has keys 1-12, check_file_not_empty fails on empty file, check_dir_has_files fails on empty dir
- [x] 4.2 [PBT] Property 5: Module validator passes on complete artifacts — for any module 1-12 with all artifacts present, all results have ok=True
- [x] 4.3 [PBT] Property 6: Module validator fails on missing artifacts — for any module 1-12 with artifacts absent, at least one result has ok=False

## Task 5: Test backup_project.py

- [x] 5.1 Create `senzing-bootcamp/tests/test_backup_project.py` with example tests: backup creates valid ZIP, missing item directories are skipped, backup contains expected files
- [x] 5.2 [PBT] Property 7: Exclusion filter correctness — for any path with an excluded component _is_excluded returns True, for any clean path it returns False

## Task 6: Test restore_project.py

- [x] 6.1 Create `senzing-bootcamp/tests/test_restore_project.py` with example tests: valid ZIP extracts all files, missing file → exit 1, non-ZIP file → exit 1, no arguments → usage + exit 1

## Task 7: Test check_prerequisites.py

- [x] 7.1 Create `senzing-bootcamp/tests/test_check_prerequisites.py` with example tests: no language runtimes → failure, NO_COLOR disables color
- [x] 7.2 [PBT] Property 8: check_command reflects availability — for any command name, present → PASSED incremented, absent+required → FAILED incremented
- [x] 7.3 [PBT] Property 9: Language runtime detection — for any single runtime present while others absent, no language failure reported

## Task 8: Test preflight_check.py

- [x] 8.1 Create `senzing-bootcamp/tests/test_preflight_check.py` with example tests: all runtimes missing → error, disk < 10GB → warning, disk >= 10GB → pass, _get_total_memory_gb returns numeric or None, write-permission check creates/removes temp dir

## Task 9: Test install_hooks.py

- [x] 9.1 Create `senzing-bootcamp/tests/test_install_hooks.py` with example tests for discover_hooks and install_hooks basic behavior
- [x] 9.2 [PBT] Property 10: Hook discovery completeness — for any set of .kiro.hook files, discover_hooks returns one entry per file
- [x] 9.3 [PBT] Property 11: Unknown hook name derivation — for any filename not in HOOKS, display name is derived by removing suffix, replacing hyphens, title-casing
- [x] 9.4 [PBT] Property 12: Hook install copy/skip correctness — for any mix of new and existing hooks, installed + skipped = total with valid sources

## Task 10: Update CI workflow

- [x] 10.1 Update `.github/workflows/validate-power.yml` to run `python -m pytest senzing-bootcamp/tests/ tests/ -v --tb=short` in the "Run tests" step

## Task 11: Final validation

- [x] 11.1 Run `python -m pytest senzing-bootcamp/tests/ -v --tb=short` and verify all tests pass
- [x] 11.2 Verify `pytest --collect-only senzing-bootcamp/tests/` discovers all 8 test modules
