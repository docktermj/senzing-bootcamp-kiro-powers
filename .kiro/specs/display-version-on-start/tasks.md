# Implementation Plan: Display Version on Start

## Overview

Implement version display for the Senzing Bootcamp Power's onboarding flow. A plain-text `VERSION` file stores the authoritative version string, a `version.py` script reads/validates/formats it, the onboarding steering file integrates version display as Step 0c, and CI validation ensures the version stays valid.

## Tasks

- [x] 1. Create VERSION file and version script
  - [x] 1.1 Create the VERSION source file
    - Create `senzing-bootcamp/VERSION` containing `0.1.0` (single line, no trailing content)
    - This is the single authoritative version source for the entire power
    - _Requirements: 1.1, 1.2, 1.3, 4.3, 4.4_

  - [x] 1.2 Implement `senzing-bootcamp/scripts/version.py`
    - Create the script following the project's script pattern (shebang, docstring, `from __future__ import annotations`, argparse, `main(argv=None)`)
    - Define `VERSION_FILE_PATH` as the absolute path to `senzing-bootcamp/VERSION` (resolved relative to the script's location)
    - Implement `VersionError` exception class with `message`, `file_path`, and `invalid_value` attributes
    - Implement `validate_version(value: str) -> str` using regex `^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`; raises `VersionError` with the invalid value verbatim on failure
    - Implement `parse_version(version: str) -> tuple[int, int, int]` to split a validated version into integer components
    - Implement `format_version(major: int, minor: int, patch: int) -> str` to produce `"MAJOR.MINOR.PATCH"` from integers
    - Implement `format_version_display(version: str) -> str` returning `"Senzing Bootcamp Power v{version}"`
    - Implement `read_version(version_file: Path | None = None) -> str` that reads the file, strips whitespace, validates, and returns the version string; raises `VersionError` if file is missing, unreadable, or contains invalid content
    - Implement CLI with `--file PATH` and `--format {raw,display}` options; exit 0 on success (print to stdout), exit 1 on failure (print error with file path to stderr)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.2, 3.1, 3.2, 3.3, 4.1, 4.2, 4.5_

  - [x] 1.3 Write property tests for version round-trip (Property 1)
    - **Property 1: Version String Round-Trip**
    - For any three integers (major, minor, patch) each in range 0–99, `format_version(*parse_version(format_version(major, minor, patch)))` produces the original string
    - Create `senzing-bootcamp/tests/test_version_properties.py`
    - Use `@given(st.integers(0, 99), st.integers(0, 99), st.integers(0, 99))` with `@settings(max_examples=100)`
    - **Validates: Requirements 3.4**

  - [x] 1.4 Write property tests for display format (Property 2)
    - **Property 2: Display Format Correctness**
    - For any valid version string (components 0–99, no leading zeros), `format_version_display(v)` equals `"Senzing Bootcamp Power v" + v`
    - Add to `senzing-bootcamp/tests/test_version_properties.py`
    - **Validates: Requirements 2.2**

  - [x] 1.5 Write property tests for invalid version rejection (Property 3)
    - **Property 3: Invalid Version Rejection**
    - For any string not matching strict `MAJOR.MINOR.PATCH` format (leading zeros, pre-release, build metadata, extra chars), `validate_version()` raises `VersionError`
    - Add to `senzing-bootcamp/tests/test_version_properties.py`
    - **Validates: Requirements 3.1, 3.3**

  - [x] 1.6 Write property tests for error message content (Property 4)
    - **Property 4: Error Message Contains Invalid Value**
    - For any invalid version string rejected by the validator, the `VersionError` message contains the invalid input verbatim
    - Add to `senzing-bootcamp/tests/test_version_properties.py`
    - **Validates: Requirements 3.2**

  - [x] 1.7 Write property tests for malformed content (Property 5)
    - **Property 5: Malformed Content Produces Error Not Default**
    - For any string that is not a valid version (empty, whitespace-only, random text), `validate_version()` raises `VersionError` rather than returning a default or empty value
    - Add to `senzing-bootcamp/tests/test_version_properties.py`
    - **Validates: Requirements 1.4**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Integrate version display into onboarding and CI
  - [x] 3.1 Add Step 0c to `senzing-bootcamp/steering/onboarding-flow.md`
    - Insert a new "## 0c. Version Display" section between Step 0b (MCP Health Check) and Step 1 (Directory Structure)
    - Instruct the agent to read `senzing-bootcamp/VERSION` using `version.py` logic and display `"Senzing Bootcamp Power v{version}"` as the first onboarding output
    - Include graceful degradation: if version cannot be read, display `"⚠️ Could not determine power version."` and continue without blocking
    - The version display must be automatic (no user interaction required)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.2 Add version validation to `senzing-bootcamp/scripts/validate_power.py`
    - Add a `check_version_file()` function that reads `senzing-bootcamp/VERSION` and validates the format using `version.py`'s `validate_version()` function
    - Import `validate_version` and `VersionError` from `version` module (using sys.path manipulation per project conventions)
    - Call `check_version_file()` from `main()` alongside existing checks
    - On failure: report error via the existing `check()` helper (which adds to `errors` list and causes non-zero exit)
    - _Requirements: 4.1, 4.2, 4.5_

  - [x] 3.3 Write property tests for script/display path identity (Property 6)
    - **Property 6: Script and Display Paths Produce Identical Version**
    - For any valid version string written to a temp VERSION file, `read_version()` and `format_version_display()` produce a display string whose version substring is byte-for-byte identical to the raw `read_version()` result
    - Add to `senzing-bootcamp/tests/test_version_properties.py`
    - **Validates: Requirements 4.2**

  - [x] 3.4 Write property tests for script exit behavior (Property 7)
    - **Property 7: Script Exits Non-Zero on Invalid Input**
    - For any malformed version file content, invoking `main()` results in `SystemExit(1)` and error output includes the file path
    - Add to `senzing-bootcamp/tests/test_version_properties.py`
    - **Validates: Requirements 4.5**

  - [x] 3.5 Write unit tests for version functionality
    - Create `senzing-bootcamp/tests/test_version_unit.py`
    - Test `read_version` from default path, missing file raises error, empty file raises error
    - Test known-good versions accepted, leading zeros rejected, pre-release rejected, build metadata rejected
    - Test CLI raw format output, CLI display format output, CLI missing file exit code
    - Test onboarding-flow.md contains version step before welcome banner
    - Test VERSION file exists at fixed path and contains valid content
    - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.2, 2.4, 3.1, 3.3, 4.1, 4.4, 4.5_

- [x] 4. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The VERSION file uses plain text (no JSON/YAML) for maximum simplicity and stdlib parseability
- All scripts use Python 3.11+ stdlib only, following the project's script pattern

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "1.4", "1.5", "1.6", "1.7"] },
    { "id": 3, "tasks": ["3.1", "3.2"] },
    { "id": 4, "tasks": ["3.3", "3.4", "3.5"] }
  ]
}
```
