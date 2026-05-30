# Implementation Plan: Session Persistence

## Overview

This implementation extends `preferences_utils.py` with preference writing, loading, context reset formatting, language steering resolution, and session resume summary functions. It also creates/updates steering files for session resume and context reset agent behavior. All script code is Python 3.11+ stdlib-only; tests use pytest + Hypothesis with class-based organization.

## Tasks

- [x] 1. Implement core preference writer and data models
  - [x] 1.1 Add `WriteResult` and `LoadResult` dataclasses and `FORBIDDEN_TEMPORAL_PHRASES` constant to `senzing-bootcamp/scripts/preferences_utils.py`
    - Add `WriteResult` dataclass with `success: bool` and `error: str | None`
    - Add `LoadResult` dataclass with `preferences: dict | None`, `missing_required: list[str]`, and `error: str | None`
    - Add `ContextResetMessage` dataclass with `message: str`, `module_number: int`, `step_identifier: str | int | None`, and `continuation_phrase: str`
    - Add `FORBIDDEN_TEMPORAL_PHRASES` tuple constant
    - Add `LANGUAGE_STEERING_MAP` dict constant mapping language strings to steering file names
    - _Requirements: 4.6, 6.1, 2.4_

  - [x] 1.2 Implement `write_preference()` function in `senzing-bootcamp/scripts/preferences_utils.py`
    - Read existing preferences file (if any) using `parse_yaml()`
    - Merge new key-value pair; remove key if value is None
    - Validate key is in `KNOWN_TOP_LEVEL_KEYS`
    - Validate resulting file would be under 10 KB
    - Write atomically via temp file + `os.replace()`
    - On filesystem error, preserve original file and return `WriteResult(success=False, error=...)`
    - Create `config/` directory and file if they don't exist
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 1.3 Implement `load_preferences()` function in `senzing-bootcamp/scripts/preferences_utils.py`
    - Read and parse preferences file using existing `parse_yaml()`
    - Return `LoadResult` with appropriate error for missing/unreadable/invalid files
    - Identify missing required fields (language, track, verbosity)
    - Return parsed preferences dict with missing field list
    - _Requirements: 2.1, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 2. Implement formatting and mapping functions
  - [x] 2.1 Implement `resolve_language_steering()` function in `senzing-bootcamp/scripts/preferences_utils.py`
    - Map language string (case-insensitive) to steering file name using `LANGUAGE_STEERING_MAP`
    - Return `None` for unrecognized languages
    - _Requirements: 2.4, 2.5_

  - [x] 2.2 Implement `format_resume_summary()` function in `senzing-bootcamp/scripts/preferences_utils.py`
    - Accept language, track, and verbosity strings
    - Return a 1-2 sentence summary containing all three values
    - _Requirements: 2.2_

  - [x] 2.3 Implement `format_context_reset()` function in `senzing-bootcamp/scripts/preferences_utils.py`
    - Read progress file (`config/bootcamp_progress.json`) to get current module and step
    - Use fallback (module=1, step=None) if progress file is missing or corrupt
    - Format message with: technical reason, immediacy clarification, progress reassurance, continuation phrase
    - Ensure message is at most 4 sentences with no forbidden temporal phrases or question marks
    - Return `ContextResetMessage` with message and metadata
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4_

- [x] 3. Checkpoint - Ensure script functions work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create session resume steering file
  - [x] 4.1 Create or update `senzing-bootcamp/steering/session-resume.md` with preference loading and recovery behavior
    - Add YAML frontmatter with inclusion rules
    - Document that on new session start, agent reads preferences file via `load_preferences()`
    - Document confirmation message format (max 2 sentences with language, track, verbosity)
    - Document that loaded language triggers corresponding language steering file via `resolve_language_steering()`
    - Document recovery flow: if file missing/corrupt, prompt for language, track, verbosity one at a time
    - Document that partial preferences preserve loaded values and prompt only for missing fields
    - Document that recovered preferences are persisted via `write_preference()` before next response
    - Document that unrecognized language triggers re-prompt while preserving other preferences
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Create context reset steering file
  - [x] 5.1 Create or update `senzing-bootcamp/steering/agent-context-management.md` with context reset communication rules
    - Add YAML frontmatter with inclusion rules
    - Document trigger condition (80% context capacity or degraded quality)
    - Document required message elements: technical reason, immediacy, progress reassurance, continuation phrase with module number
    - Document forbidden temporal phrases list
    - Document single-message constraint (no splitting across responses, no questions)
    - Document 4-sentence maximum format
    - Document that continuation phrase must be in quotation marks
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4_

- [x] 6. Checkpoint - Verify steering files
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Write property-based tests
  - [x] 7.1 Create `senzing-bootcamp/tests/test_session_persistence_properties.py` with Hypothesis strategies and imports
    - Set up test file with `sys.path` manipulation to import `preferences_utils`
    - Define `st_preference_key_value()` strategy for valid key-value pairs from schema
    - Define `st_valid_preferences()` strategy for complete valid preferences dicts
    - Define `st_progress_state()` strategy for valid progress states (module 1-11, step)
    - Use `@settings(max_examples=20)` per project convention
    - _Requirements: 6.1_

  - [x] 7.2 Write property test for Property 1: Preference Write Round-Trip
    - **Property 1: Preference Write Round-Trip**
    - For any valid preference key-value pair, writing then reading back produces identical value
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.5, 6.5**

  - [x] 7.3 Write property test for Property 2: Field Preservation on Update
    - **Property 2: Field Preservation on Update**
    - For any valid preferences file with N fields, writing one field preserves all others unchanged
    - **Validates: Requirements 1.6, 6.3**

  - [x] 7.4 Write property test for Property 3: No Null Fields Written
    - **Property 3: No Null Fields Written**
    - Writing None removes the key; writing non-None produces only non-None keys in file
    - **Validates: Requirements 6.2**

  - [x] 7.5 Write property test for Property 4: Schema Validation Correctness
    - **Property 4: Schema Validation Correctness**
    - Valid dicts produce zero errors; dicts with schema violations produce at least one error
    - **Validates: Requirements 6.1, 3.2, 6.4**

  - [x] 7.6 Write property test for Property 5: Missing Required Field Detection
    - **Property 5: Missing Required Field Detection**
    - Removing a subset of required fields from valid prefs reports exactly those fields as missing
    - **Validates: Requirements 3.3**

  - [x] 7.7 Write property test for Property 6: Language Steering Mapping
    - **Property 6: Language Steering Mapping**
    - Supported languages return non-None steering file; unsupported return None
    - **Validates: Requirements 2.4, 2.5**

  - [x] 7.8 Write property test for Property 7: Session Resume Summary Format
    - **Property 7: Session Resume Summary Format**
    - For any language/track/verbosity, summary contains all three and is at most 2 sentences
    - **Validates: Requirements 2.2**

  - [x] 7.9 Write property test for Property 8: Context Reset Message Completeness
    - **Property 8: Context Reset Message Completeness**
    - For any valid progress state, message contains technical reason, immediacy, reassurance, continuation phrase, and module number
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 5.1, 5.2, 5.3**

  - [x] 7.10 Write property test for Property 9: Context Reset Message Constraints
    - **Property 9: Context Reset Message Constraints**
    - No forbidden temporal phrases, no question marks, at most 4 sentences
    - **Validates: Requirements 4.6, 5.2, 5.4**

- [x] 8. Write unit tests
  - [x] 8.1 Create `senzing-bootcamp/tests/test_session_persistence_unit.py` with unit tests for preference writing
    - Test file creation when preferences file does not exist
    - Test filesystem error handling with mocked I/O (returns WriteResult with error)
    - Test write preserves existing fields when adding new field
    - Test write rejects unknown keys
    - Test write rejects file exceeding 10 KB
    - _Requirements: 1.7, 1.8, 6.3, 6.6_

  - [x] 8.2 Write unit tests for preference loading and recovery
    - Test loading from valid complete file returns all preferences
    - Test loading from missing file returns appropriate error
    - Test loading from invalid YAML returns parse error
    - Test loading from file with missing required fields lists them correctly
    - Test empty preferences file handling
    - _Requirements: 2.1, 3.1, 3.2, 3.3_

  - [x] 8.3 Write unit tests for language steering mapping and resume summary
    - Test specific language mappings (python to lang-python.md, csharp to lang-csharp.md)
    - Test case-insensitive matching (Python, PYTHON, python all map correctly)
    - Test unrecognized language returns None
    - Test resume summary contains all three values and is at most 2 sentences
    - _Requirements: 2.2, 2.4, 2.5_

  - [x] 8.4 Write unit tests for context reset message formatting
    - Test message with valid progress file contains all required elements
    - Test message with missing progress file uses fallback values
    - Test message contains no forbidden temporal phrases
    - Test message is at most 4 sentences
    - Test message contains no question marks
    - Test continuation phrase is in quotation marks
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4_

- [x] 9. Checkpoint - Run all tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Integration wiring and final validation
  - [x] 10.1 Write integration tests in `senzing-bootcamp/tests/test_session_persistence_integration.py`
    - Test full session resume flow: write preferences, load, verify round-trip
    - Test recovery flow: corrupt file, load, re-write, load succeeds
    - Test context reset message generation with real progress file
    - Test steering file content validation (no forbidden phrases in templates)
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1_

  - [x] 10.2 Update `senzing-bootcamp/steering/steering-index.yaml` with token counts for new/modified steering files
    - Add or update entry for `session-resume.md`
    - Add or update entry for `agent-context-management.md`
    - _Requirements: 2.1, 4.1_

  - [x] 10.3 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify all steering files are valid CommonMark
    - _Requirements: 2.1, 4.1_

  - [x] 10.4 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets are not exceeded
    - _Requirements: 2.1, 4.1_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All script code is Python 3.11+ stdlib only (no third-party deps)
- Tests use pytest + Hypothesis with `@settings(max_examples=20)` per project convention
- Import `preferences_utils` in tests via `sys.path` manipulation (scripts aren't packages)
- The existing `parse_yaml()` and `validate_preferences_schema()` functions are reused; new functions extend the same module

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "2.2", "2.3"] },
    { "id": 3, "tasks": ["4.1", "5.1"] },
    { "id": 4, "tasks": ["7.1", "8.1", "8.2"] },
    { "id": 5, "tasks": ["7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "7.10", "8.3", "8.4"] },
    { "id": 6, "tasks": ["10.1", "10.2"] },
    { "id": 7, "tasks": ["10.3", "10.4"] }
  ]
}
```
