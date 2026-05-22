# Implementation Plan: Preferences Schema Validation

## Overview

Implement schema validation for `config/bootcamp_preferences.yaml` by creating `preferences_utils.py` (schema, parser, validator) and `validate_preferences_ci.py` (CI script), mirroring the existing `progress_utils.py` + `validate_progress_ci.py` pattern. All code is Python 3.11+ stdlib-only.

## Tasks

- [x] 1. Create preferences_utils.py with schema constants and dataclass
  - [x] 1.1 Create `senzing-bootcamp/scripts/preferences_utils.py` with module boilerplate, schema constants, and PreferencesSchema dataclass
    - Add shebang, module docstring, `from __future__ import annotations`, stdlib imports
    - Define `KNOWN_TOP_LEVEL_KEYS`, `CONVERSATION_STYLE_KEYS`, `PRODUCTION_SPECS_KEYS` sets
    - Define `VALID_MAPPING_VERBOSITY`, `VALID_HARDWARE_TARGET`, `VALID_VERBOSITY_PRESET`, `VALID_QUESTION_FRAMING`, `VALID_TONE`, `VALID_PACING` tuples
    - Define `PreferencesSchema` dataclass with all fields and types per design
    - Add `main(argv=None)` entry point with argparse (no-op placeholder)
    - _Requirements: 2.1, 7.1, 7.4, 7.6_

- [x] 2. Implement minimal YAML parser
  - [x] 2.1 Implement `parse_yaml(text: str) -> dict` in `preferences_utils.py`
    - Parse flat key-value pairs at top level
    - Parse nested dicts (indented key-value pairs under a parent key)
    - Parse lists (`- ` prefix items) and lists of dicts
    - Parse scalar values: strings (quoted/unquoted), integers, booleans, null
    - Ignore comment lines and blank lines
    - Raise `ValueError` with line number on unparseable content
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [x] 2.2 Write property test for YAML round-trip parsing
    - **Property 8: YAML round-trip parsing**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

  - [x] 2.3 Write property test for comments and blank lines transparency
    - **Property 9: Comments and blank lines are transparent to parsing**
    - **Validates: Requirements 4.6, 4.7**

  - [x] 2.4 Write property test for malformed YAML error reporting
    - **Property 10: Malformed YAML raises ValueError with line info**
    - **Validates: Requirements 4.8**

- [x] 3. Implement preferences validator
  - [x] 3.1 Implement `validate_preferences_schema(data: dict) -> list[str]` in `preferences_utils.py`
    - Reject unknown top-level keys with descriptive error messages
    - Require `database_type` (only required field)
    - Validate types for all known keys against schema definitions
    - Validate enum constraints for `mapping_verbosity`, `hardware_target`
    - Validate nested dict structures (`conversation_style` sub-keys and their enum constraints, `production_specs` sub-keys and types)
    - Validate list element structures (`hooks_installed` as list of str, `runtimes_installed_during_onboarding` as list of dicts with `name`/`version`)
    - Collect all errors without short-circuiting
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 6.1, 6.2, 6.3_

  - [x] 3.2 Write property test for valid preferences validate cleanly
    - **Property 1: Valid preferences validate cleanly**
    - **Validates: Requirements 2.1, 6.1, 6.2**

  - [x] 3.3 Write property test for unknown top-level keys rejection
    - **Property 2: Unknown top-level keys are rejected**
    - **Validates: Requirements 1.1**

  - [x] 3.4 Write property test for unknown nested keys rejection
    - **Property 3: Unknown nested keys are rejected**
    - **Validates: Requirements 1.2, 1.3**

  - [x] 3.5 Write property test for type mismatch errors
    - **Property 4: Type mismatches produce descriptive errors**
    - **Validates: Requirements 3.1, 2.2, 2.3, 2.4, 2.5**

  - [x] 3.6 Write property test for enum constraint violations
    - **Property 5: Enum constraint violations are rejected**
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

  - [x] 3.7 Write property test for all errors collected
    - **Property 6: All errors collected without short-circuiting**
    - **Validates: Requirements 1.4**

  - [x] 3.8 Write property test for missing required key
    - **Property 7: Missing required key detected**
    - **Validates: Requirements 6.3, 3.2**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Create CI validation script
  - [x] 5.1 Create `senzing-bootcamp/scripts/validate_preferences_ci.py` with full CI logic
    - Add shebang, module docstring, `from __future__ import annotations`, stdlib imports
    - Use same `sys.path` pattern as `validate_progress_ci.py` for imports
    - Implement argparse CLI accepting optional positional path argument (default: `config/bootcamp_preferences.yaml`)
    - Define built-in minimal sample (`{"database_type": "sqlite"}`)
    - Implement schema self-consistency check (Known_Keys non-empty, sample passes validation)
    - If file exists: parse with `parse_yaml()`, validate with `validate_preferences_schema()`
    - If file does not exist: validate built-in sample only
    - Print "Schema validation passed" and exit 0 on success
    - Print errors to stderr and exit 1 on failure
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 7.2, 7.3, 7.5_

  - [x] 5.2 Write unit tests for CI script
    - Test exit code 0 with valid file
    - Test exit code 1 with invalid file
    - Test fallback to built-in sample when file missing
    - Test self-consistency check
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All property tests go in `senzing-bootcamp/tests/test_preferences_schema_validation_properties.py`
- Unit tests go in `senzing-bootcamp/tests/test_preferences_schema_validation_unit.py`
- Implementation language: Python 3.11+ (stdlib only)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8"] },
    { "id": 4, "tasks": ["5.1"] },
    { "id": 5, "tasks": ["5.2"] }
  ]
}
```
