# Implementation Plan: Database Corruption Recovery

## Overview

Implement a database health-check script (`scripts/check_database.py`) with a `DatabaseHealthChecker` class that validates SQLite database integrity, integrate it into the existing `preflight.py` runner, and update steering documentation with database recovery guidance. All code is Python 3.11+ stdlib-only, following existing project conventions.

## Tasks

- [x] 1. Create `scripts/check_database.py` with data models and health checker
  - [x] 1.1 Create `scripts/check_database.py` with `DatabaseCheckResult`, `DatabaseHealthReport` dataclasses, and `DatabaseHealthChecker` class
    - Define `DatabaseCheckResult` dataclass with fields: `name`, `status` ("pass"|"warn"|"fail"), `message`, `fix` (str | None), `fixed` (bool)
    - Define `DatabaseHealthReport` dataclass with `checks` list, `db_path`, and `verdict`/`pass_count`/`warn_count`/`fail_count` properties
    - Implement `DatabaseHealthChecker.__init__(self, db_path: str, repair: bool = False)`
    - Implement `check_file_exists()` — returns fail if `os.path.isfile(db_path)` is False
    - Implement `check_connection()` — attempts `sqlite3.connect(db_path)` and catches errors (permission denied, not a database, locked)
    - Implement `check_integrity()` — runs `PRAGMA integrity_check` and reports pass if result is "ok", fail otherwise
    - Implement `check_entity_count()` — queries `SELECT COUNT(*) FROM RES_ENT_OKEY`, reports warn if 0 or table missing
    - Implement `attempt_repair()` — runs `PRAGMA wal_checkpoint(TRUNCATE)` and `VACUUM`, re-checks failing checks
    - Implement `run_all()` — executes checks in sequence, calls `attempt_repair()` if `self.repair` is True and failures exist
    - Follow shebang, docstring, `from __future__ import annotations`, stdlib-only conventions
    - _Requirements: 5, 6_

  - [x] 1.2 Add argparse CLI to `scripts/check_database.py` with `main(argv=None)` entry point
    - Add `--db-path` argument (default: `database/G2C.db`)
    - Add `--repair` flag to trigger automatic recovery attempts
    - Add `--json` flag for JSON output (serialize `DatabaseHealthReport` to JSON)
    - Human-readable output with pass/warn/fail icons matching `preflight.py` style
    - Return exit code 0 on healthy, 1 on failure
    - _Requirements: 5, 6_

- [x] 2. Integrate database check into `preflight.py`
  - [x] 2.1 Add `check_database()` function to `preflight.py` and wire into `CheckRunner.CHECK_SEQUENCE`
    - Import `sqlite3` and `os` (already available)
    - Implement `check_database() -> list[CheckResult]` that checks if `database/G2C.db` exists
    - If file does not exist, return empty list (skip silently)
    - If file exists, run connection test and `PRAGMA integrity_check`
    - Return `CheckResult` instances compatible with existing report format (category: "Database")
    - Add `("Database", check_database)` as the last entry in `CheckRunner.CHECK_SEQUENCE`
    - _Requirements: 7_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Write tests for `check_database.py`
  - [x] 4.1 Write property test for corruption detection
    - **Property 1: Corruption detection**
    - Generate random byte sequences (1–1000 bytes), write to temp file, run `DatabaseHealthChecker`
    - Assert that checker reports failure status (at connection or integrity check stage)
    - Use `@given(st.binary(min_size=1, max_size=1000))` with `@settings(max_examples=20)`
    - **Validates: Requirements 5, 10**

  - [x] 4.2 Write property test for integrity check interpretation
    - **Property 2: Integrity check interpretation**
    - Generate arbitrary text strings, mock `PRAGMA integrity_check` response
    - Assert: if string equals "ok" → status is "pass"; any other string → status is "fail"
    - Use `@given(st.text(min_size=1, max_size=200))` with `@settings(max_examples=20)`
    - **Validates: Requirements 5, 3**

  - [x] 4.3 Write property test for entity count threshold
    - **Property 3: Entity count threshold**
    - Generate non-negative integers (0–10000)
    - Assert: count > 0 → status is "pass"; count == 0 → status is "warn" or "fail"
    - Use `@given(st.integers(min_value=0, max_value=10000))` with `@settings(max_examples=20)`
    - **Validates: Requirements 5**

  - [x] 4.4 Write property test for repair-then-recheck behavior
    - **Property 4: Repair then re-check**
    - Generate combinations of initial check pass/fail states with repair enabled
    - Assert: final report reflects post-repair status (pass if repair succeeded, fail if not)
    - Use `@given()` with composite strategy and `@settings(max_examples=20)`
    - **Validates: Requirements 6**

  - [x] 4.5 Write unit tests for CLI behavior and preflight integration
    - Test: missing database file → fail result
    - Test: healthy database → all checks pass
    - Test: `--repair` triggers WAL checkpoint + vacuum
    - Test: `--json` produces valid JSON output
    - Test: `--db-path` overrides default path
    - Test: preflight integration — file exists → check runs
    - Test: preflight integration — file absent → check skipped
    - _Requirements: 7, 10_

- [x] 5. Update steering documentation
  - [x] 5.1 Add "Database Recovery" section to `steering/recovery-from-mistakes.md`
    - Add item 6+ covering SQLite corruption scenarios: disk full during load, process killed mid-transaction, WAL file corruption, lock file stale
    - Document detection signals: "database is locked", "database disk image is malformed", unexpected zero entity counts
    - Provide SQLite recovery steps: `PRAGMA integrity_check`, `PRAGMA wal_checkpoint(TRUNCATE)`, rebuild from scratch
    - Provide PostgreSQL recovery steps: check orphaned transactions, vacuum, re-run with idempotent RECORD_ID
    - Reference `scripts/check_database.py` as the automated detection tool
    - _Requirements: 1, 2, 3, 4_

  - [x] 5.2 Add "Database Issues" section to `steering/common-pitfalls.md`
    - Add a new section between Module 6 and Module 7 (or after General Pitfalls)
    - Include pitfall table: corruption after disk full, locked database, zero entities after load, WAL file left behind
    - Include fix actions referencing `scripts/check_database.py --repair` and manual recovery steps
    - _Requirements: 8_

  - [x] 5.3 Add "Section G: Database Corruption" branch to `steering/troubleshooting-decision-tree.md`
    - Add "Database Corruption" to the "Start Here" top-level tree
    - Create Section G with decision branches: file missing, connection fails, integrity check fails, entity count zero
    - Reference `scripts/check_database.py` and `--repair` flag in fix actions
    - _Requirements: 9_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All scripts follow the project's stdlib-only Python 3.11+ conventions (shebang, docstring, argparse, `main(argv=None)`)
- Test file location: `senzing-bootcamp/tests/test_check_database.py`
- Mocking strategy: `sqlite3.connect` mocked for connection failures, `os.path.isfile` for file existence, temp files for corruption detection

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "5.1", "5.2", "5.3"] },
    { "id": 2, "tasks": ["2.1"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4", "4.5"] }
  ]
}
```
