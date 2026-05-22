# Implementation Plan: Individual Progress Dashboard

## Overview

Implement `progress_dashboard.py` as a standalone Python CLI script that reads bootcamp progress, preferences, and module dependency data, then generates a self-contained HTML dashboard. The implementation follows a pipeline architecture: CLI → Parsers → Computation → Renderer → File Output. All code uses Python 3.11+ stdlib only.

## Tasks

- [x] 1. Create script skeleton with CLI and data models
  - [x] 1.1 Create `senzing-bootcamp/scripts/progress_dashboard.py` with shebang, `from __future__ import annotations`, argparse CLI, and all dataclass models
    - Add shebang line and future annotations import
    - Implement `main(argv=None)` with argparse: `--progress`, `--preferences`, `--dependencies`, `--output` arguments with defaults relative to script's parent directory
    - Add `if __name__ == "__main__": main()` entry point
    - Define all dataclasses: `ProgressData`, `PreferencesData`, `ModuleInfo`, `GateInfo`, `DependencyData`, `Artifact`, `NextStep`
    - Implement file-existence validation (print error to stderr, exit 1 if missing)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 10.1, 10.2, 10.3_

- [x] 2. Implement parsers
  - [x] 2.1 Implement the minimal YAML parser function
    - Write `parse_yaml(text: str) -> dict` supporting scalar key-value pairs, lists with `- item` syntax, nested mappings via indentation, comments, quoted strings, bare values, and `null` → None
    - Handle edge cases: empty files, comment-only files, mixed indentation
    - _Requirements: 3.1, 4.1_

  - [x] 2.2 Implement `parse_progress` function for JSON progress file
    - Read and parse JSON with `json.loads`
    - Extract `current_module`, `modules_completed`, `current_step`, `language`, `step_history`
    - Print error and exit 1 on invalid JSON
    - Return `ProgressData` dataclass instance
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 2.3 Implement `parse_preferences` function for YAML preferences file
    - Use `parse_yaml` to parse the file content
    - Extract `language`, `track`, `database_type`, `deployment_target`
    - Map `null` or absent fields to `None`
    - Return `PreferencesData` dataclass instance
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 2.4 Implement `parse_dependencies` function for YAML dependencies file
    - Use `parse_yaml` to parse the file content
    - Extract `modules` section into `list[ModuleInfo]` with number, name, requires
    - Extract `gates` section into `list[GateInfo]` with from_module, to_module, requirements
    - Return `DependencyData` dataclass instance
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 2.5 Write property tests for parsers (Properties 2, 3, 4)
    - **Property 2: Progress Data Parsing Preservation** — for any valid progress JSON, all `modules_completed` entries and artifact references are preserved after parsing
    - **Property 3: YAML Preferences Parsing Round-Trip** — for any valid preferences YAML, parsed values match originals (None for null/absent)
    - **Property 4: Dependency Graph Parsing Completeness** — for any valid dependencies YAML, all module numbers, names, requires lists, and gates are captured
    - **Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3**

- [x] 3. Implement computation layer
  - [x] 3.1 Implement `compute_module_statuses` function
    - Classify each module as "completed", "in-progress", or "not-started"
    - Module is "completed" if its number is in `modules_completed`
    - Module is "in-progress" if it equals `current_module` and is not completed
    - All others are "not-started"
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 3.2 Implement `compute_next_steps` function
    - Identify modules where all `requires` entries are in `modules_completed`
    - Exclude completed modules and the current in-progress module
    - Attach gate requirements from `DependencyData.gates` to each next step
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 3.3 Implement `extract_artifacts` function
    - Scan `step_history` entries for artifact references
    - Group artifacts by module number (derived from step key prefix)
    - Return sorted list of `Artifact` objects
    - _Requirements: 6.1, 6.2_

  - [x] 3.4 Write property tests for computation (Properties 5, 6)
    - **Property 5: Module Status Classification Correctness** — every module is classified as exactly one status matching its state
    - **Property 6: Next Steps Computation Correctness** — computed next steps are exactly the set satisfying all three conditions (requires met, not completed, not current)
    - **Validates: Requirements 5.1, 5.2, 5.3, 7.1, 7.2**

- [x] 4. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement HTML renderer
  - [x] 5.1 Implement `render_dashboard` function — progress summary and module list
    - Generate HTML5 document with `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`
    - Add inline `<style>` element with all CSS (no external stylesheets)
    - Render progress summary: completed count / total count
    - Render module list with visual status indicators (completed ✓, in-progress ●, not-started ○)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 9.1, 9.2, 9.3_

  - [x] 5.2 Implement renderer sections — preferences card, artifacts, next steps, and completion states
    - Render Preferences_Card with language, track, database_type, deployment_target (show "Not set" for None)
    - Render artifacts section grouped by module (or "No artifacts produced yet" message)
    - Render next steps with gate requirements (or blocking message, or congratulatory message if all complete)
    - _Requirements: 3.3, 6.1, 6.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 5.3 Write property tests for renderer (Properties 7, 8, 9)
    - **Property 7: Preferences Card Rendering Completeness** — rendered HTML contains all four preference fields with actual value or "Not set"
    - **Property 8: Self-Contained HTML Output** — output has DOCTYPE, `<style>` element, no external resource references
    - **Property 9: Artifact Display Correctness** — every artifact reference in source data appears in rendered HTML
    - **Validates: Requirements 3.3, 6.1, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3**

- [x] 6. Wire pipeline and output
  - [x] 6.1 Wire all components together in `main()` and implement file output
    - Call parsers in sequence, then computation functions, then renderer
    - Create output directory with `os.makedirs(exist_ok=True)`
    - Write rendered HTML to output path
    - Exit with code 0 on success
    - _Requirements: 1.6, 9.4, 10.1, 10.2, 10.3_

  - [x] 6.2 Write property test for exit code correctness (Property 1)
    - **Property 1: Exit Code Correctness** — script exits 0 iff all input files exist and are parseable; exits 1 otherwise
    - **Validates: Requirements 1.6, 1.7, 2.4**

  - [x] 6.3 Write unit tests for CLI defaults and edge cases
    - Test `--help` exits with code 0
    - Test missing file produces error message and exit code 1
    - Test empty `modules_completed` renders 0% progress
    - Test all modules completed renders congratulatory message
    - Verify no imports from `status.py` or other project scripts (static check)
    - _Requirements: 1.5, 1.7, 5.4, 7.5, 10.1_

- [x] 7. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The script uses Python 3.11+ stdlib only — no PyYAML, no third-party dependencies
- Test file location: `senzing-bootcamp/tests/test_progress_dashboard_properties.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "2.4"] },
    { "id": 3, "tasks": ["2.5", "3.1", "3.2", "3.3"] },
    { "id": 4, "tasks": ["3.4", "5.1"] },
    { "id": 5, "tasks": ["5.2"] },
    { "id": 6, "tasks": ["5.3", "6.1"] },
    { "id": 7, "tasks": ["6.2", "6.3"] }
  ]
}
```
