# Requirements Document

## Introduction

The senzing-bootcamp power ships eight Python scripts in `senzing-bootcamp/scripts/` that handle project status reporting, module validation, progress repair, backup/restore, prerequisite checking, pre-flight checks, and hook installation. These scripts have no automated test coverage. This feature adds a `senzing-bootcamp/tests/` directory with pytest-based unit tests for every script, integrated into the existing GitHub Actions CI workflow, so regressions are caught before they reach users.

## Glossary

- **Test_Suite**: The collection of pytest test modules located in `senzing-bootcamp/tests/` that exercise the bootcamp scripts.
- **Script_Under_Test**: Any Python script in `senzing-bootcamp/scripts/` targeted by the Test_Suite: `status.py`, `repair_progress.py`, `validate_module.py`, `backup_project.py`, `restore_project.py`, `check_prerequisites.py`, `preflight_check.py`, `install_hooks.py`.
- **CI_Workflow**: The GitHub Actions workflow defined in `.github/workflows/validate-power.yml` that runs validation and tests on pull requests and pushes.
- **Progress_Data**: The JSON structure stored in `config/bootcamp_progress.json` that tracks module completion state.
- **Preferences_Data**: The YAML-like key-value file at `config/bootcamp_preferences.yaml` that stores bootcamp configuration such as chosen language.

## Requirements

### Requirement 1: Test Directory Structure

**User Story:** As a developer, I want a well-organized test directory inside the power, so that tests are discoverable and runnable with a single pytest command.

#### Acceptance Criteria

1. THE Test_Suite SHALL reside in `senzing-bootcamp/tests/` with one test module per Script_Under_Test.
2. THE Test_Suite SHALL include a `conftest.py` file containing shared fixtures for temporary directories, mock file systems, and sample Progress_Data.
3. WHEN a developer runs `pytest senzing-bootcamp/tests/`, THE Test_Suite SHALL discover and execute all test modules.
4. THE Test_Suite SHALL depend only on `pytest` and Python standard library modules (including `unittest.mock`).

### Requirement 2: Status Script Tests

**User Story:** As a developer, I want tests for `status.py`, so that progress display and tracker sync logic is verified.

#### Acceptance Criteria

1. WHEN Progress_Data contains completed modules, THE Test_Suite SHALL verify that `status.py` reports the correct current module, completion percentage, and status label.
2. WHEN no Progress_Data file exists, THE Test_Suite SHALL verify that `status.py` reports "Not Started" status without raising an exception.
3. WHEN Progress_Data contains corrupted JSON, THE Test_Suite SHALL verify that `status.py` handles the parse error gracefully.
4. WHEN the `--sync` flag is provided, THE Test_Suite SHALL verify that `status.py` writes a `PROGRESS_TRACKER.md` file whose content reflects the Progress_Data.
5. WHEN all 12 modules are completed, THE Test_Suite SHALL verify that `status.py` reports "Bootcamp Complete" status.

### Requirement 3: Repair Progress Script Tests

**User Story:** As a developer, I want tests for `repair_progress.py`, so that artifact detection and progress reconstruction logic is verified.

#### Acceptance Criteria

1. WHEN project artifacts exist for specific modules, THE Test_Suite SHALL verify that `repair_progress.py` detects exactly those modules as completed.
2. WHEN no project artifacts exist, THE Test_Suite SHALL verify that `repair_progress.py` detects zero completed modules.
3. WHEN the `--fix` flag is provided, THE Test_Suite SHALL verify that `repair_progress.py` writes a valid Progress_Data file with the correct `modules_completed` list and `current_module` value.
4. WHEN an existing Progress_Data file has unrecorded modules, THE Test_Suite SHALL verify that `repair_progress.py` reports the discrepancy.
5. FOR ALL sets of module artifacts, writing Progress_Data with `--fix` then re-detecting SHALL produce the same set of completed modules (round-trip property).

### Requirement 4: Validate Module Script Tests

**User Story:** As a developer, I want tests for `validate_module.py`, so that module prerequisite checking logic is verified for all 12 modules.

#### Acceptance Criteria

1. WHEN all required artifacts for a module exist, THE Test_Suite SHALL verify that the module's validator returns all-passing results.
2. WHEN required artifacts for a module are missing, THE Test_Suite SHALL verify that the module's validator returns failing results identifying the missing items.
3. WHEN the `--next N` flag is provided, THE Test_Suite SHALL verify that `validate_module.py` validates module N-1 instead of module N.
4. WHEN `--next 1` is provided, THE Test_Suite SHALL verify that `validate_module.py` reports no prerequisites needed.
5. THE Test_Suite SHALL verify that validators exist for all 12 modules in the `VALIDATORS` dictionary.
6. WHEN a file exists but is empty, THE Test_Suite SHALL verify that `check_file_not_empty` returns a failing result.

### Requirement 5: Backup Project Script Tests

**User Story:** As a developer, I want tests for `backup_project.py`, so that archive creation and file exclusion logic is verified.

#### Acceptance Criteria

1. WHEN project directories contain files, THE Test_Suite SHALL verify that `backup_project.py` creates a valid ZIP archive in the `backups/` directory.
2. THE Test_Suite SHALL verify that files matching exclusion patterns (e.g., `__pycache__`, `.git`, `*.pyc`, `.env`) are omitted from the archive.
3. THE Test_Suite SHALL verify that the `_is_excluded` function correctly identifies excluded paths and allows non-excluded paths.
4. WHEN a backup item directory does not exist, THE Test_Suite SHALL verify that `backup_project.py` skips the missing item without error.

### Requirement 6: Restore Project Script Tests

**User Story:** As a developer, I want tests for `restore_project.py`, so that archive extraction and validation logic is verified.

#### Acceptance Criteria

1. WHEN a valid ZIP backup file is provided, THE Test_Suite SHALL verify that `restore_project.py` extracts all files to the target directory.
2. WHEN the backup file does not exist, THE Test_Suite SHALL verify that `restore_project.py` exits with an error.
3. WHEN the backup file is not a valid ZIP, THE Test_Suite SHALL verify that `restore_project.py` exits with an error.
4. WHEN no arguments are provided, THE Test_Suite SHALL verify that `restore_project.py` prints usage information and exits.

### Requirement 7: Check Prerequisites Script Tests

**User Story:** As a developer, I want tests for `check_prerequisites.py`, so that environment detection logic is verified.

#### Acceptance Criteria

1. WHEN required commands (git, curl) are available, THE Test_Suite SHALL verify that `check_prerequisites.py` reports them as passed.
2. WHEN required commands are missing, THE Test_Suite SHALL verify that `check_prerequisites.py` increments the failure count.
3. WHEN no language runtime is found, THE Test_Suite SHALL verify that `check_prerequisites.py` reports a failure.
4. WHEN at least one language runtime is found, THE Test_Suite SHALL verify that `check_prerequisites.py` does not report a language failure.
5. THE Test_Suite SHALL verify the `check_command` function by mocking `shutil.which` to simulate present and absent commands.

### Requirement 8: Preflight Check Script Tests

**User Story:** As a developer, I want tests for `preflight_check.py`, so that system requirement detection logic is verified.

#### Acceptance Criteria

1. WHEN all language runtimes are missing, THE Test_Suite SHALL verify that `preflight_check.py` reports an error.
2. WHEN disk space is below 10GB, THE Test_Suite SHALL verify that `preflight_check.py` reports a warning.
3. WHEN disk space is 10GB or above, THE Test_Suite SHALL verify that `preflight_check.py` reports a pass.
4. THE Test_Suite SHALL verify that `_get_total_memory_gb` returns a numeric value or None by mocking platform-specific calls.
5. THE Test_Suite SHALL verify that the write-permission check creates and removes a temporary directory.

### Requirement 9: Install Hooks Script Tests

**User Story:** As a developer, I want tests for `install_hooks.py`, so that hook discovery and installation logic is verified.

#### Acceptance Criteria

1. WHEN hook files exist in the power hooks directory, THE Test_Suite SHALL verify that `discover_hooks` returns entries for each hook file.
2. WHEN a hook file is not in the known HOOKS list, THE Test_Suite SHALL verify that `discover_hooks` derives a display name from the filename.
3. WHEN `install_hooks` is called with a list of hooks, THE Test_Suite SHALL verify that each hook file is copied from source to destination.
4. WHEN a hook is already installed at the destination, THE Test_Suite SHALL verify that `install_hooks` skips the file and increments the skipped count.
5. THE Test_Suite SHALL verify that `install_hooks` returns correct installed and skipped counts.

### Requirement 10: CI Workflow Integration

**User Story:** As a developer, I want the test suite to run automatically in CI, so that regressions are caught on every pull request and push.

#### Acceptance Criteria

1. THE CI_Workflow SHALL include a step that installs `pytest` and runs `python -m pytest senzing-bootcamp/tests/ -v --tb=short`.
2. WHEN any test in the Test_Suite fails, THE CI_Workflow SHALL fail the build.
3. THE CI_Workflow SHALL run the Test_Suite on the `ubuntu-latest` runner with Python 3.11.

### Requirement 11: Edge Case Coverage

**User Story:** As a developer, I want tests for boundary conditions and error scenarios, so that scripts handle unexpected input gracefully.

#### Acceptance Criteria

1. WHEN Progress_Data contains an empty `modules_completed` list, THE Test_Suite SHALL verify that scripts treat the bootcamp as not started.
2. WHEN Progress_Data contains module numbers outside the 1-12 range, THE Test_Suite SHALL verify that scripts handle the out-of-range values without crashing.
3. WHEN a directory expected to contain files is empty, THE Test_Suite SHALL verify that `check_dir_has_files` returns a failing result.
4. WHEN the `color_supported` function is called with `NO_COLOR` environment variable set, THE Test_Suite SHALL verify that color output is disabled.
5. IF a JSON file contains invalid syntax, THEN THE Test_Suite SHALL verify that the script reading the file handles the `JSONDecodeError` without crashing.
