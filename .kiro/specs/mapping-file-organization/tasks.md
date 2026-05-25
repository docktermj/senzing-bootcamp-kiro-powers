# Implementation Plan: Mapping File Organization

## Overview

Implement a Python CLI script (`organize_mapping_files.py`) that routes mapping workflow output files into project subdirectories based on file extension, plus steering file edits to invoke it automatically. The script uses stdlib only, follows existing project conventions, and includes property-based tests with Hypothesis.

## Tasks

- [x] 1. Create the organizer script with core logic
  - [x] 1.1 Create `senzing-bootcamp/scripts/organize_mapping_files.py` with routing table and data model
    - Add shebang, module docstring, `from __future__ import annotations`
    - Define `ROUTING_RULES` constant mapping extensions to subdirectories (`.py` → `scripts/`, `.md` → `docs/`, `.jsonl` → `data/`, `.json` → `config/`)
    - Define `MoveResult` dataclass with `source`, `destination`, `status`, `reason` fields
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Implement `scan_source`, `plan_moves`, and `execute_moves` functions
    - `scan_source(source_dir: Path) -> list[Path]`: list regular non-hidden files in source directory
    - `plan_moves(files: list[Path], project_root: Path) -> list[MoveResult]`: apply routing rules, detect conflicts
    - `execute_moves(plan: list[MoveResult]) -> None`: create target dirs and move files with `shutil.move`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 3.1, 3.2_

  - [x] 1.3 Implement `print_summary` and `main` with argparse CLI
    - `print_summary(plan: list[MoveResult], dry_run: bool) -> None`: stdout for moves, stderr for warnings/skips
    - `main(argv: list[str] | None = None) -> int`: parse args (`--source`, `--project-root`, `--dry-run`), orchestrate workflow, return exit code
    - Add `if __name__ == "__main__": main()` entry point
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 8.1, 8.2_

- [x] 2. Checkpoint - Verify script runs correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Add property-based and unit tests
  - [x] 3.1 Write property test for extension-based routing correctness
    - **Property 1: Extension-based routing correctness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    - Generate arbitrary file sets with recognized extensions, run `plan_moves` + `execute_moves`, assert each file lands in the correct target subdirectory

  - [x] 3.2 Write property test for unrecognized extensions remaining in place
    - **Property 2: Unrecognized extensions remain in place**
    - **Validates: Requirements 1.5**
    - Generate files with extensions not in routing table, run organizer, assert files remain at source

  - [x] 3.3 Write property test for conflict detection
    - **Property 3: Conflict detection prevents overwrite**
    - **Validates: Requirements 2.1**
    - Pre-populate target directory with same-named files, run organizer, assert neither source nor target is modified

  - [x] 3.4 Write property test for idempotence
    - **Property 4: Idempotence**
    - **Validates: Requirements 2.3**
    - Run organizer twice on same file set, assert second run produces no additional changes

  - [x] 3.5 Write property test for non-existent source error
    - **Property 5: Non-existent source exits with error**
    - **Validates: Requirements 4.6**
    - Generate non-existent paths, invoke `main`, assert exit code 1 and stderr output

  - [x] 3.6 Write property test for dry-run preserving file system
    - **Property 6: Dry-run preserves file system**
    - **Validates: Requirements 5.1, 5.2**
    - Run with `--dry-run`, assert no files moved, planned moves printed to stdout

  - [x] 3.7 Write property test for summary reporting completeness
    - **Property 7: Summary reporting completeness**
    - **Validates: Requirements 8.1, 8.2**
    - Run organizer on file sets, assert stdout contains a line per moved file or "no files" message when none moved

  - [x] 3.8 Write unit tests for CLI argument defaults and error messages
    - Test `--source` defaults to cwd when omitted
    - Test `--project-root` defaults to cwd when omitted
    - Test error message when `--source` is a file not a directory
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update steering files with agent instructions
  - [x] 5.1 Add organizer instruction to `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
    - Insert agent instruction block after the step where `mapping_workflow` generates output files
    - Instruction directs agent to run `organize_mapping_files.py --source <workspace_dir> --project-root <bootcamper_project_root>`
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 5.2 Add organizer instruction to `senzing-bootcamp/steering/module-05-phase3-test-load.md`
    - Insert agent instruction block after the step where `mapping_workflow` steps 5–8 generate output files
    - Instruction directs agent to run `organize_mapping_files.py --source <workspace_dir> --project-root <bootcamper_project_root>`
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The script follows existing project conventions: shebang, `from __future__ import annotations`, stdlib-only, argparse with `main(argv=None)`, dataclasses
- Tests use `sys.path` manipulation to import the script, class-based organization, and Hypothesis with `@settings(max_examples=20)`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "5.1", "5.2"] }
  ]
}
```
