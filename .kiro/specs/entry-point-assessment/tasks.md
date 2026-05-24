# Implementation Plan: Entry Point Assessment

## Overview

Implement `senzing-bootcamp/scripts/assess_entry_point.py` — a single-file Python 3.11+ CLI tool that reads the module-artifacts manifest, scans the bootcamper's filesystem for produced artifacts, checks Senzing SDK importability, and outputs a per-module checklist with a recommended entry point. The implementation follows the project's stdlib-only, argparse-based script conventions.

## Tasks

- [x] 1. Create data models and helper utilities
  - [x] 1.1 Create `senzing-bootcamp/scripts/assess_entry_point.py` with all dataclass definitions and internal helper functions
    - Define `Artifact`, `ModuleManifest`, `ArtifactStatus`, `ModuleStatus`, `SdkStatus`, `Recommendation`, `AssessmentReport` dataclasses
    - Implement `_normalize_path(manifest_path: str) -> Path` using `PurePosixPath` for cross-platform handling
    - Implement `_is_dir_present(path: Path) -> bool` (exists and non-empty)
    - Implement `_is_file_present(path: Path) -> bool` (exists and size > 0)
    - Implement `_find_python() -> str | None` using `shutil.which`
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 1.2 Write property test for path separator normalization
    - **Property 7: Path Separator Normalization**
    - **Validates: Requirements 8.3**

- [x] 2. Implement manifest parser
  - [x] 2.1 Implement `parse_manifest(text: str) -> list[ModuleManifest]`
    - Line-by-line parser using indentation depth for nesting
    - Recognize top-level `modules:` key, numeric module keys, `produces:` sequences, `requires_from:` mappings
    - Raise `ValueError` on malformed structure or missing required fields
    - _Requirements: 1.1, 1.3, 1.4_

  - [x] 2.2 Write property test for manifest parsing round-trip
    - **Property 1: Manifest Parsing Round-Trip**
    - **Validates: Requirements 1.1, 1.3, 1.4**

- [x] 3. Implement artifact scanner
  - [x] 3.1 Implement `scan_artifacts(artifacts: list[Artifact], project_dir: Path) -> list[ArtifactStatus]`
    - Resolve each artifact path against `project_dir` using `_normalize_path`
    - Use `_is_dir_present` for directory-type artifacts, `_is_file_present` for file-type artifacts
    - Handle `PermissionError` by marking artifact as missing
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 Write property test for artifact presence detection
    - **Property 2: Artifact Presence Detection**
    - **Validates: Requirements 2.2, 2.3**

- [x] 4. Implement SDK checker
  - [x] 4.1 Implement `check_sdk() -> SdkStatus`
    - Use `_find_python()` to locate interpreter
    - Run `subprocess.run([python, "-c", "import senzing; print(senzing.__version__)"], timeout=15)`
    - Handle exit code 0 (available + version), non-zero (unavailable), `TimeoutExpired` (unavailable + timeout note), no interpreter (unknown + diagnostic)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement completeness logic and recommendation engine
  - [x] 6.1 Implement `determine_completeness(manifest: ModuleManifest, artifact_statuses: list[ArtifactStatus]) -> ModuleStatus`
    - Module is complete if and only if all required=True artifacts are present
    - Optional artifacts reported but do not affect completeness
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 6.2 Write property test for completeness depends only on required artifacts
    - **Property 3: Completeness Depends Only on Required Artifacts**
    - **Validates: Requirements 2.4, 2.5, 4.1, 4.2**

  - [x] 6.3 Implement `recommend_entry_point(module_statuses: list[ModuleStatus], sdk_status: SdkStatus) -> Recommendation`
    - If SDK unavailable and module 2 incomplete → recommend module 2
    - Otherwise recommend first incomplete module in ascending order
    - If all complete → recommend graduation
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 6.4 Write property test for recommendation is first incomplete module
    - **Property 4: Recommendation Is First Incomplete Module**
    - **Validates: Requirements 5.1, 5.2**

  - [x] 6.5 Write property test for SDK unavailable overrides recommendation
    - **Property 5: SDK Unavailable Overrides Recommendation**
    - **Validates: Requirements 5.3, 5.4**

- [x] 7. Implement output formatter
  - [x] 7.1 Implement `format_report(report: AssessmentReport) -> str`
    - Per-module section with artifact checklist (path, type, required, status)
    - SDK check result (availability + version)
    - Summary recommendation line
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 7.2 Write property test for output report completeness
    - **Property 6: Output Report Completeness**
    - **Validates: Requirements 6.1, 6.2**

- [x] 8. Implement CLI entry point and wire components together
  - [x] 8.1 Implement `main(argv: list[str] | None = None) -> None`
    - argparse with `--project-dir` (default: cwd) and `--manifest` (default: `config/module-artifacts.yaml` relative to script dir)
    - Orchestrate: read manifest → parse → scan artifacts per module → check SDK → determine completeness → recommend → format → print
    - Error handling: missing manifest → stderr + exit 1, unreadable file → stderr + exit 1, malformed YAML → stderr + exit 1
    - Add `if __name__ == "__main__": main()` guard
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 1.2, 6.4, 6.5_

  - [x] 8.2 Write property test for successful assessment exits zero
    - **Property 8: Successful Assessment Exits Zero**
    - **Validates: Requirements 7.4**

  - [x] 8.3 Write unit tests for CLI argument parsing and error conditions
    - Test default project-dir and manifest paths
    - Test --project-dir and --manifest overrides
    - Test exit code 1 on missing manifest
    - Test exit code 1 on unreadable file
    - Test SDK check result interpretation (mocked subprocess)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All code goes in a single file: `senzing-bootcamp/scripts/assess_entry_point.py`
- Tests go in `senzing-bootcamp/tests/test_assess_entry_point.py`
- Python 3.11+ stdlib only — no third-party dependencies in the script

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "4.1"] },
    { "id": 4, "tasks": ["6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3"] },
    { "id": 6, "tasks": ["6.4", "6.5", "7.1"] },
    { "id": 7, "tasks": ["7.2", "8.1"] },
    { "id": 8, "tasks": ["8.2", "8.3"] }
  ]
}
```
