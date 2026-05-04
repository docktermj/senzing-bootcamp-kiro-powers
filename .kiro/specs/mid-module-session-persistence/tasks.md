# Implementation Plan: Mid-Module Session Persistence

## Overview

Extend the senzing-bootcamp progress tracking system to support sub-step granularity. The implementation proceeds in layers: first the data layer (`progress_utils.py` — `write_checkpoint`, `validate_progress_schema`, `parse_parent_step`), then property-based tests to lock in correctness, then steering file updates (`agent-instructions.md`, `session-resume.md`, `module-transitions.md`, `phase-loading-guide.md`), and finally integration wiring. All code is Python 3.11+ stdlib-only; tests use pytest + Hypothesis.

## Tasks

- [x] 1. Extend `write_checkpoint` to accept sub-step identifiers
  - [x] 1.1 Rename the `step_number: int` parameter to `step: int | str` in `senzing-bootcamp/scripts/progress_utils.py`
    - Update the function signature and docstring
    - When `step` is an `int`, write it as an integer in JSON (preserve current behavior)
    - When `step` is a `str`, write it as a string in JSON
    - Update `step_history[str(module_number)]` with `last_completed_step` set to the `step` value (preserving type) and `updated_at` set to current ISO 8601 UTC timestamp
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Update existing unit tests in `senzing-bootcamp/tests/test_progress_utils.py` for the renamed parameter
    - Update all `write_checkpoint` calls from `step_number=` to `step=` (or positional)
    - Add new test cases for dotted sub-step strings (e.g., `"5.3"`) and lettered sub-step strings (e.g., `"7a"`)
    - Verify integer steps still write as JSON integers, string steps write as JSON strings
    - Verify `step_history` entries match the written step type and value
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Extend `validate_progress_schema` to accept sub-step identifiers
  - [x] 2.1 Update the `current_step` validation in `senzing-bootcamp/scripts/progress_utils.py`
    - Accept `None`, `int`, or `str` matching dotted notation (`^\d+\.\d+$`) or lettered notation (`^\d+[a-zA-Z]$`)
    - Reject strings not matching any recognized format with a descriptive error including the value and expected formats
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Update the `step_history[key].last_completed_step` validation in `senzing-bootcamp/scripts/progress_utils.py`
    - Accept `int` or `str` matching the same dotted/lettered patterns
    - Reject strings not matching any recognized format with a descriptive error
    - _Requirements: 2.4_

  - [x] 2.3 Add unit tests for the extended validator in `senzing-bootcamp/tests/test_progress_utils.py`
    - Test valid dotted sub-step strings pass (e.g., `"5.3"`, `"12.1"`)
    - Test valid lettered sub-step strings pass (e.g., `"7a"`, `"3B"`)
    - Test invalid strings fail with descriptive errors (e.g., `""`, `"abc"`, `"5.3.1"`, `"7ab"`)
    - Test integer and null `current_step` still pass (backward compatibility)
    - Test `last_completed_step` string validation in `step_history`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Implement `parse_parent_step` helper function
  - [x] 3.1 Add `parse_parent_step(step: int | str | None) -> int | None` to `senzing-bootcamp/scripts/progress_utils.py`
    - `None` → `None`
    - `int` (e.g., `5`) → `5`
    - Dotted string (e.g., `"5.3"`) → `5`
    - Lettered string (e.g., `"7a"`) → `7`
    - Pure function with no side effects
    - _Requirements: 5.3_

  - [x] 3.2 Add unit tests for `parse_parent_step` in `senzing-bootcamp/tests/test_progress_utils.py`
    - Test each input type: `None`, integer, dotted string, lettered string
    - Test edge cases: single-digit parent, multi-digit parent (e.g., `"12.1"` → `12`, `"11c"` → `11`)
    - _Requirements: 5.3_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Property-based tests for sub-step validation
  - [x] 5.1 Write property test: valid sub-step identifiers pass schema validation
    - **Property 2: Valid Sub-Step Identifiers Pass Schema Validation**
    - **Validates: Requirements 2.1, 2.2, 2.4, 9.1, 9.2**
    - Create `senzing-bootcamp/tests/test_sub_step_validation_properties.py`
    - Implement `st_valid_sub_step()` strategy generating integers (1–30), dotted strings (`"<1-12>.<1-20>"`), and lettered strings (`"<1-12><a-z>"`)
    - Verify `validate_progress_schema` returns zero errors for a progress file containing each generated value as `current_step`
    - Verify the same for `step_history[module].last_completed_step`
    - Use `@settings(max_examples=100)`

  - [x] 5.2 Write property test: invalid current-step values fail validation
    - **Property 3: Invalid Current-Step Values Fail Validation**
    - **Validates: Requirements 2.3, 9.3**
    - Add to `senzing-bootcamp/tests/test_sub_step_validation_properties.py`
    - Implement `st_invalid_current_step()` strategy generating empty strings, strings with no digits, strings with special characters, negative numbers, nested objects, multi-letter suffixes
    - Verify `validate_progress_schema` returns at least one error for each
    - Use `@settings(max_examples=100)`

- [x] 6. Property-based tests for checkpoint round-trip
  - [x] 6.1 Write property test: checkpoint round-trip preserves type and value
    - **Property 1: Checkpoint Round-Trip Preserves Type and Value**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 10.1, 10.2, 10.3, 10.4**
    - Create `senzing-bootcamp/tests/test_sub_step_checkpoint_properties.py`
    - Implement `st_module_step_pair()` strategy generating `(module_number, step)` tuples where step is int, dotted string, or lettered string
    - Call `write_checkpoint`, read back the progress file, verify `current_step` matches in type and value
    - Verify `step_history[module].last_completed_step` matches
    - Verify `step_history[module].updated_at` is a valid ISO 8601 datetime string
    - Use `@settings(max_examples=100)`

- [x] 7. Property-based tests for backward compatibility
  - [x] 7.1 Write property test: legacy integer-only progress files pass validation
    - **Property 4: Backward Compatibility — Legacy Integer-Only Progress Files**
    - **Validates: Requirements 2.5, 8.1, 8.3, 11.1, 11.2, 11.3**
    - Create `senzing-bootcamp/tests/test_sub_step_backward_compat_properties.py`
    - Implement `st_legacy_progress()` strategy generating progress dicts with integer-only `current_step` (or null), integer `last_completed_step` in `step_history`, and no sub-step identifier strings
    - Verify `validate_progress_schema` returns zero errors for each generated dict
    - Verify `write_checkpoint` with an integer step produces a file that passes validation
    - Use `@settings(max_examples=100)`

- [x] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Update `agent-instructions.md` for sub-step checkpointing
  - [x] 9.1 Update the "State & Progress" section in `senzing-bootcamp/steering/agent-instructions.md`
    - Document that `current_step` accepts both integer values and string sub-step identifiers (dotted `"5.3"` or lettered `"7a"` notation)
    - Instruct the agent to write a sub-step checkpoint after completing each sub-step within a multi-part step, using the sub-step identifier format defined in the module steering file
    - Instruct the agent to write a mapping checkpoint to `config/mapping_state_[datasource].json` after each `mapping_workflow` step, not only at workflow completion
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 10. Update `session-resume.md` for sub-step resumption and mapping checkpoints
  - [x] 10.1 Update Step 3 summary display in `senzing-bootcamp/steering/session-resume.md`
    - When `current_step` is a sub-step identifier string, display it directly (e.g., "Step 5.3 of 26" or "Step 7a of 10")
    - When `current_step` is an integer, preserve the existing format
    - When mapping checkpoints exist, include data source name and completed mapping steps in the summary
    - _Requirements: 5.1, 4.2_

  - [x] 10.2 Update Step 4 resume logic in `senzing-bootcamp/steering/session-resume.md`
    - When `current_step` is a sub-step identifier, instruct the agent to skip to the next sub-step after the recorded position (not the next whole step)
    - If the sub-step is not found in the module steering file, log a warning and fall back to resuming at the parent step number
    - When mapping checkpoints exist and the bootcamper chooses to continue, instruct the agent to restart `mapping_workflow` and fast-track through completed mapping steps before resuming from the first incomplete step
    - If a mapping checkpoint file contains invalid JSON or missing required fields, log a warning, skip it, and inform the bootcamper
    - _Requirements: 5.2, 5.4, 4.1, 4.3, 4.4_

- [x] 11. Update `module-transitions.md` for sub-step journey map display
  - [x] 11.1 Update the step-level detail rule in `senzing-bootcamp/steering/module-transitions.md`
    - When `current_step` is a sub-step identifier, display it in the status column (e.g., `🔄 Current — Step 5.3/26`)
    - When `current_step` is an integer, preserve the existing format (e.g., `🔄 Current — Step 5/26`)
    - Update the checkpoint emission rule to reference that sub-step checkpoints follow the same emission pattern as whole-step checkpoints
    - _Requirements: 7.1, 7.2, 6.4_

- [x] 12. Update `phase-loading-guide.md` for sub-step phase determination
  - [x] 12.1 Update the phase determination logic in `senzing-bootcamp/steering/phase-loading-guide.md`
    - When `current_step` is a sub-step identifier, use the parent step number (extracted via `parse_parent_step`) to determine which phase sub-file to load
    - The sub-step suffix does not affect phase selection — only the parent step number matters for `step_range` matching
    - If the parent step number does not fall within any phase's `step_range`, load the root file (matching existing fallback behavior)
    - _Requirements: 5.3_

- [x] 13. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Integration wiring and backward compatibility verification
  - [x] 14.1 Verify backward compatibility end-to-end
    - Ensure `write_checkpoint` with integer steps produces files that pass `validate_progress_schema` with zero errors
    - Ensure `clear_step` still works correctly after a sub-step checkpoint
    - Ensure existing progress files with integer-only `current_step` values continue to work with all updated steering file logic
    - Verify `repair_progress.py` continues to produce integer `current_step` values (no changes needed to that script)
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 14.2 Write integration tests for end-to-end sub-step checkpoint flow
    - Write sub-step checkpoint → validate → read back → verify round-trip in `senzing-bootcamp/tests/test_progress_utils.py`
    - Verify steering file content: `agent-instructions.md`, `session-resume.md`, `module-transitions.md`, `phase-loading-guide.md` contain expected sub-step documentation
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 5.1, 5.2, 6.1, 7.1_

- [x] 15. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after each layer (data, tests, steering, integration)
- Property tests validate universal correctness properties from the design document using Hypothesis
- Unit tests validate specific examples and edge cases
- All Python code targets 3.11+ with stdlib only; tests use pytest + Hypothesis
- Steering file changes are markdown content updates (no code changes needed for the checkpoint layer)
