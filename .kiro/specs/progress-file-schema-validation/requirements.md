# Requirements Document

## Introduction

The senzing-bootcamp Kiro power tracks bootcamp progress in `config/bootcamp_progress.json`. This file is read and written by multiple components (progress checkpointing via `progress_utils.py`, session resume logic, and the `repair_progress.py` repair tool). Corruption occurs often enough that a dedicated repair script exists. This feature adds a formal schema definition as a Python dataclass/dict, a validation function that checks progress files against the schema, CI integration to catch corruption before merge, and property-based tests to verify schema round-trip correctness.

## Glossary

- **Progress_File**: The JSON file at `config/bootcamp_progress.json` that stores bootcamp state including current module, step, completed modules, track, preferences, and timestamps.
- **Schema_Validator**: A Python module that defines the canonical schema for the Progress_File and validates arbitrary dicts against it, returning a list of human-readable error strings.
- **CI_Validation**: The automated check that runs during continuous integration (via `validate_power.py` or a dedicated script) to reject commits that would introduce schema-violating progress file structures.
- **Progress_Schema**: A Python dataclass or typed dict defining the expected structure, types, and constraints for every field in the Progress_File.
- **Round_Trip_Property**: A property-based test asserting that any valid Progress_File generated from the schema can be serialized to JSON and deserialized back without data loss or type coercion errors.
- **Track**: One of the predefined bootcamp paths: `quick_demo`, `core_bootcamp`, or `advanced_topics`.
- **Module_Number**: An integer in the range 1–11 representing a bootcamp module.
- **Sub_Step_Identifier**: A string matching either dotted notation (`<digits>.<digits>`) or lettered notation (`<digits><letter>`) representing a sub-step within a module.

## Requirements

### Requirement 1: Define Progress File Schema

**User Story:** As a developer maintaining the bootcamp power, I want a single authoritative schema definition for `bootcamp_progress.json`, so that all components agree on the file's structure and valid values.

#### Acceptance Criteria

1. THE Progress_Schema SHALL define `current_module` as an integer in the range 1–11.
2. THE Progress_Schema SHALL define `current_step` as one of: an integer, a valid Sub_Step_Identifier string, or null.
3. THE Progress_Schema SHALL define `modules_completed` as a list of integers where each element is in the range 1–11.
4. THE Progress_Schema SHALL define `track` as one of the string literals `quick_demo`, `core_bootcamp`, or `advanced_topics`.
5. THE Progress_Schema SHALL define `preferences` as a dict with optional string keys and string or boolean values.
6. THE Progress_Schema SHALL define `session_id` as a non-empty string.
7. THE Progress_Schema SHALL define `started_at` as a valid ISO 8601 timestamp string.
8. THE Progress_Schema SHALL define `last_activity` as a valid ISO 8601 timestamp string.
9. THE Progress_Schema SHALL define `step_history` as a dict whose keys are string representations of integers 1–12 and whose values contain `last_completed_step` and `updated_at`.
10. THE Progress_Schema SHALL define `data_sources` as a list of strings.
11. THE Progress_Schema SHALL define `database_type` as a string.

### Requirement 2: Schema Validation Function

**User Story:** As a developer, I want a validation function that checks any progress dict against the schema, so that I can detect corruption programmatically.

#### Acceptance Criteria

1. WHEN a valid Progress_File dict is provided, THE Schema_Validator SHALL return an empty list of errors.
2. WHEN a Progress_File dict contains a field with an incorrect type, THE Schema_Validator SHALL return an error string identifying the field name and the expected type.
3. WHEN a Progress_File dict contains `current_module` outside the range 1–11, THE Schema_Validator SHALL return an error string indicating the value is out of range.
4. WHEN a Progress_File dict contains `modules_completed` with a value outside 1–11, THE Schema_Validator SHALL return an error string identifying the invalid module number.
5. WHEN a Progress_File dict contains `track` with a value not in the allowed set, THE Schema_Validator SHALL return an error string listing the allowed track values.
6. WHEN a Progress_File dict contains an invalid ISO 8601 string for `started_at` or `last_activity`, THE Schema_Validator SHALL return an error string identifying the field and the malformed value.
7. WHEN a Progress_File dict is missing optional fields, THE Schema_Validator SHALL treat them as absent without error (backward compatibility).
8. THE Schema_Validator SHALL validate all fields present in the dict without short-circuiting on the first error.

### Requirement 3: Backward Compatibility

**User Story:** As a developer, I want the schema validation to accept legacy progress files that lack newer fields, so that existing bootcamp sessions are not broken.

#### Acceptance Criteria

1. WHEN a Progress_File dict lacks `track`, `preferences`, `session_id`, `started_at`, or `last_activity`, THE Schema_Validator SHALL produce no errors for those missing fields.
2. WHEN a Progress_File dict lacks `step_history` and `current_step`, THE Schema_Validator SHALL produce no errors (legacy format).
3. WHEN a Progress_File dict contains only `modules_completed`, `current_module`, `data_sources`, and `database_type`, THE Schema_Validator SHALL produce no errors.

### Requirement 4: CI Integration

**User Story:** As a maintainer, I want schema validation to run in CI, so that pull requests introducing schema-violating code are caught before merge.

#### Acceptance Criteria

1. WHEN CI runs the validation script, THE CI_Validation SHALL import the Schema_Validator and validate a sample progress file against the Progress_Schema.
2. IF the Schema_Validator returns one or more errors, THEN THE CI_Validation SHALL exit with a non-zero exit code and print each error to stderr.
3. THE CI_Validation SHALL validate that the schema definition itself is internally consistent (no contradictory constraints).
4. WHEN CI runs the validation script and the schema is valid, THE CI_Validation SHALL exit with exit code 0 and print a success message.

### Requirement 5: Property-Based Tests for Round-Trip Correctness

**User Story:** As a developer, I want property-based tests that generate arbitrary valid progress files and verify round-trip serialization, so that I have high confidence the schema and validator are correct.

#### Acceptance Criteria

1. FOR ALL valid Progress_File dicts generated by the Hypothesis strategy, THE Round_Trip_Property SHALL hold: serializing to JSON and deserializing back produces a dict equal to the original.
2. FOR ALL valid Progress_File dicts generated by the Hypothesis strategy, THE Schema_Validator SHALL return an empty error list.
3. FOR ALL invalid Progress_File dicts generated by a corruption strategy, THE Schema_Validator SHALL return a non-empty error list.
4. THE property-based tests SHALL use `@settings(max_examples=100)` to balance coverage and execution time.

### Requirement 6: Integration with Existing Validation

**User Story:** As a developer, I want the new schema validation to integrate with the existing `validate_progress_schema` function in `progress_utils.py`, so that there is a single source of truth for progress file validity.

#### Acceptance Criteria

1. WHEN the Schema_Validator is invoked, THE Schema_Validator SHALL extend or replace the existing `validate_progress_schema` function in `progress_utils.py`.
2. THE Schema_Validator SHALL preserve all existing validation checks (step_history keys, ISO 8601 timestamps, sub-step identifier format).
3. WHEN the existing test suite (`test_progress_utils.py`) is run after the change, THE Schema_Validator SHALL pass all existing tests without modification to test assertions.

### Requirement 7: Integration with Repair Tool

**User Story:** As a developer, I want the repair tool to validate its output against the schema before writing, so that repairs never introduce new corruption.

#### Acceptance Criteria

1. WHEN `repair_progress.py` runs with `--fix`, THE repair tool SHALL validate the reconstructed progress dict against the Progress_Schema before writing to disk.
2. IF the reconstructed dict fails schema validation, THEN THE repair tool SHALL print the validation errors and exit with a non-zero exit code without writing the file.
