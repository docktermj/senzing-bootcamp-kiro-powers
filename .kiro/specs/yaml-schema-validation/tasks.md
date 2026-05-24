# Implementation Plan: YAML Schema Validation

## Overview

Implement a Python stdlib-only script (`senzing-bootcamp/scripts/validate_yaml_schemas.py`) that validates the top-level key structure of four authoritative YAML configuration files. The script integrates into the existing CI workflow and includes property-based tests using Hypothesis.

## Tasks

- [x] 1. Implement the validation script
  - [x] 1.1 Create `senzing-bootcamp/scripts/validate_yaml_schemas.py` with schema registry and data model
    - Define `SCHEMA_REGISTRY` dict mapping file paths to expected key sets
    - Define `ValidationResult` dataclass with `file_path`, `passed`, `missing_keys`, `unexpected_keys`, `error` fields
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.1_

  - [x] 1.2 Implement `parse_top_level_keys` function
    - Extract top-level mapping keys from YAML content using stdlib string parsing
    - Handle lines starting with non-space, non-comment characters containing a colon
    - Raise `ValueError` if no keys found
    - _Requirements: 6.1_

  - [x] 1.3 Implement `validate_file` function
    - Read file content with UTF-8 encoding, handle `OSError`
    - Parse top-level keys, handle `ValueError`
    - Compute missing and unexpected keys via set difference
    - Return `ValidationResult`
    - _Requirements: 1.5, 1.6, 4.3_

  - [x] 1.4 Implement `format_result` reporter function
    - Format passing results as `PASS: <filename>`
    - Format failing results as `FAIL: <filename> — <reason>` including missing/unexpected keys and errors
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 1.5 Implement `main` CLI entry point with argparse
    - Add `--file` optional argument for single-file validation
    - Default to validating all four files in `SCHEMA_REGISTRY`
    - Resolve file paths relative to power root (`Path(__file__).resolve().parent.parent`)
    - Implement `_resolve_to_registry_key` helper for `--file` path resolution
    - Print error to stderr and exit 1 for unrecognized `--file` paths
    - Return exit code 0 if all pass, 1 otherwise
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 6.2_

- [x] 2. Checkpoint - Verify script works manually
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Write tests
  - [x] 3.1 Write property test for key set validation (Property 1)
    - **Property 1: Key Set Validation Detects Symmetric Difference**
    - Use Hypothesis to generate arbitrary expected key sets and YAML content
    - Assert `missing_keys | unexpected_keys == expected_keys ^ actual_keys`
    - **Validates: Requirements 1.5, 1.6**

  - [x] 3.2 Write property test for output format correctness (Property 2)
    - **Property 2: Output Format Correctness**
    - Use Hypothesis to generate arbitrary `ValidationResult` instances
    - Assert output starts with `PASS:` or `FAIL:` and line count equals file count
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [x] 3.3 Write property test for exit code correctness (Property 3)
    - **Property 3: Exit Code Correctness**
    - Use Hypothesis to generate lists of `ValidationResult` with varying `passed` values
    - Assert exit code is 0 iff all results passed
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [x] 3.4 Write property test for single-file flag isolation (Property 4)
    - **Property 4: Single-File Flag Isolation**
    - Use Hypothesis to select from registry keys
    - Assert exactly one output line when `--file` is used
    - **Validates: Requirements 3.2**

  - [x] 3.5 Write property test for unrecognized file rejection (Property 5)
    - **Property 5: Unrecognized File Rejection**
    - Use Hypothesis to generate paths not in the registry
    - Assert non-zero exit and error message contains the path
    - **Validates: Requirements 3.3**

  - [x] 3.6 Write unit tests for the four specific file schemas
    - Test each of the four YAML files against their expected key sets
    - Verify correct PASS output for valid files
    - Verify correct FAIL output for modified files
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 4. Integrate into CI workflow
  - [x] 4.1 Add validation step to `.github/workflows/validate-power.yml`
    - Add a step `Validate YAML schemas` that runs `python senzing-bootcamp/scripts/validate_yaml_schemas.py`
    - Place it after existing validation steps and before the pytest step
    - _Requirements: 5.1, 5.2_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The script uses only Python stdlib (no PyYAML) per project conventions
- Tests go in `senzing-bootcamp/tests/test_validate_yaml_schemas.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "1.4"] },
    { "id": 3, "tasks": ["1.5"] },
    { "id": 4, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "4.1"] }
  ]
}
```
