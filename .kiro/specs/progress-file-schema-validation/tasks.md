# Tasks: Progress File Schema Validation

## Task 1: Define ProgressSchema Dataclass

- [x] 1.1 Add `ProgressSchema` dataclass to `senzing-bootcamp/scripts/progress_utils.py` with all fields, types, defaults, and docstring
- [x] 1.2 Add constants for valid tracks (`VALID_TRACKS`), module range (`MODULE_RANGE`), and step_history key range
- [x] 1.3 Verify the dataclass imports and instantiates without errors by running `python -c "from progress_utils import ProgressSchema"`

## Task 2: Extend `validate_progress_schema` Function

- [x] 2.1 Add validation for `current_module` (type int, range 1–11)
- [x] 2.2 Add validation for `modules_completed` (type list, each element int in 1–11)
- [x] 2.3 Add validation for `track` (must be one of VALID_TRACKS if present)
- [x] 2.4 Add validation for `preferences` (dict with str keys, str|bool values if present)
- [x] 2.5 Add validation for `session_id` (non-empty string if present)
- [x] 2.6 Add validation for `started_at` and `last_activity` (valid ISO 8601 if present)
- [x] 2.7 Add validation for `data_sources` (list of strings if present)
- [x] 2.8 Add validation for `database_type` (string if present)
- [x] 2.9 Ensure all existing validations (current_step, step_history) are preserved
- [x] 2.10 Run existing `test_progress_utils.py` tests and confirm all pass without modification

## Task 3: Create CI Validation Script

- [x] 3.1 Create `senzing-bootcamp/scripts/validate_progress_ci.py` with argparse CLI, schema import, and exit code logic
- [x] 3.2 Implement sample progress file validation (built-in minimal valid dict when no file exists)
- [x] 3.3 Implement schema self-consistency check (verify ProgressSchema fields don't contradict validator logic)
- [x] 3.4 Add the script to `.github/workflows/validate-power.yml` as a new step before the test run

## Task 4: Integrate Validation into Repair Tool

- [x] 4.1 Import `validate_progress_schema` in `repair_progress.py`
- [x] 4.2 Add validation call after constructing the progress dict in `main()`, before writing to disk
- [x] 4.3 Print errors to stderr and exit with code 1 if validation fails, without writing the file

## Task 5: Write Property-Based Tests

- [x] 5.1 Create `senzing-bootcamp/tests/test_progress_schema_validation_properties.py` with Hypothesis strategies (`st_progress_file`, `st_corrupted_progress_file`, `st_optional_field_subset`)
- [x] 5.2 [PBT] Implement Property 1: JSON round-trip serialization — *For any* valid progress file dict, serializing to JSON and deserializing back produces an equal dict. **Feature: progress-file-schema-validation, Property 1: JSON Round-Trip Serialization**
- [x] 5.3 [PBT] Implement Property 2: Valid dicts validate cleanly — *For any* valid progress file dict, `validate_progress_schema` returns an empty error list. **Feature: progress-file-schema-validation, Property 2: Valid Dicts Validate Cleanly**
- [x] 5.4 [PBT] Implement Property 3: Corrupted dicts are detected — *For any* corrupted progress file dict, `validate_progress_schema` returns a non-empty error list identifying the corrupted field. **Feature: progress-file-schema-validation, Property 3: Corrupted Dicts Are Detected**
- [x] 5.5 [PBT] Implement Property 4: Backward compatibility under field removal — *For any* valid progress file dict with optional fields removed, `validate_progress_schema` returns an empty error list. **Feature: progress-file-schema-validation, Property 4: Backward Compatibility Under Field Removal**

## Task 6: Write Unit Tests

- [x] 6.1 Create `senzing-bootcamp/tests/test_progress_schema_validation_unit.py` with example-based tests for each error message format
- [x] 6.2 Add tests for legacy file formats (minimal dict with only required fields)
- [x] 6.3 Add tests for CI script exit codes (success and failure paths)
- [x] 6.4 Add tests for repair tool validation gate (mock repair producing invalid dict)

## Task 7: Final Verification

- [x] 7.1 Run full test suite (`python -m pytest senzing-bootcamp/tests/ -v --tb=short`) and confirm all tests pass
- [x] 7.2 Run CI validation script manually and confirm exit code 0
- [x] 7.3 Verify existing `test_progress_utils.py` passes without any test assertion modifications
