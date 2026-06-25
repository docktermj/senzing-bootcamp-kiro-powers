# Implementation Plan: Module Recap Document Fix

## Overview

Fix the `module-recap-append` and `module-completion-celebration` hooks by changing their `when.type` from `postTaskExecution` to `agentStop`. Both hooks already contain boundary detection logic that silently exits when no module completion occurred, making `agentStop` a safe replacement. Integration tests validate the corrected trigger condition using pytest + Hypothesis.

## Tasks

- [x] 1. Fix hook event types
  - [x] 1.1 Change `module-recap-append.kiro.hook` event type to `agentStop`
    - Open `senzing-bootcamp/hooks/module-recap-append.kiro.hook`
    - Replace `"type": "postTaskExecution"` with `"type": "agentStop"` inside the `when` object
    - Verify no other fields are modified — the `then.prompt` content must remain byte-for-byte identical
    - _Requirements: 1.1, 1.3, 1.5_

  - [x] 1.2 Change `module-completion-celebration.kiro.hook` event type to `agentStop`
    - Open `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook`
    - Replace `"type": "postTaskExecution"` with `"type": "agentStop"` inside the `when` object
    - Verify no other fields are modified — the `then.prompt` content must remain byte-for-byte identical
    - _Requirements: 1.2, 1.4, 1.6_

- [x] 2. Checkpoint - Validate hook files
  - Ensure both hook files parse as valid JSON and pass schema validation, ask the user if questions arise.

- [x] 3. Write integration tests
  - [x] 3.1 Create test file with event type validation tests
    - Create `tests/test_module_recap_document_fix.py`
    - Import `json`, `Path`, `re` from stdlib and `hypothesis` / `pytest`
    - Import helpers from `tests/hook_test_helpers.py` (`load_hook`, `validate_required_fields`, `validate_version`, `VALID_EVENT_TYPES`, `HOOKS_DIR`, `SEMVER_PATTERN`)
    - Define constants for the two affected hook paths
    - Write `class TestEventTypeMigration` with tests asserting both hooks use `agentStop`
    - Include a test that asserts `"agentStop"` is in `VALID_EVENT_TYPES`
    - Include a test that fails with a clear assertion message if either hook uses `postTaskExecution`
    - _Requirements: 5.1, 5.5, 5.6_

  - [x] 3.2 Add boundary detection and schema integrity tests
    - In the same test file, write `class TestBoundaryDetection` with tests asserting both hook prompts contain:
      - Reference to `config/bootcamp_progress.json`
      - Reference to `modules_completed`
      - Silent-exit instruction for the no-change case
    - Write `class TestSchemaIntegrity` with tests asserting:
      - All required fields present (`name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`)
      - `then.type` equals `"askAgent"` for both hooks
      - `version` matches semver format
    - _Requirements: 5.2, 5.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 3.3 Add prompt content regression tests
    - In the same test file, write `class TestPromptRegression` with tests asserting:
      - Both hooks reference `config/module-dependencies.yaml`
      - Celebration hook references `config/bootcamp_preferences.yaml`
      - Recap hook contains session content gathering instructions (information shared, questions asked, answers given, actions taken)
      - Celebration hook contains congratulatory banner instructions
      - Celebration hook contains next module or graduation instructions
      - Both hooks contain constraint language preventing script execution and file-system scans
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [x] 3.4 Write property test for event type correctness (Property 1)
    - **Property 1: Event type is agentStop for all affected hooks**
    - In the same test file, write `class TestPropertyEventType` using `@given` with a strategy that samples from the two affected hook filenames
    - Assert `when.type == "agentStop"` for each
    - Use `@settings(max_examples=20)`
    - **Validates: Requirements 1.1, 1.2**

  - [x] 3.5 Write property test for schema integrity (Property 2)
    - **Property 2: Schema integrity preserved after modification**
    - Write a property test that for any hook in the affected set, all required fields are present and `then.type == "askAgent"`
    - Use `@settings(max_examples=20)`
    - **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 3.1, 3.2, 3.5, 3.6**

  - [x] 3.6 Write property test for semver validation (Property 3)
    - **Property 3: Version field is valid semver**
    - Write a property test that for any hook in the affected set, the `version` field matches `SEMVER_PATTERN`
    - Use `@settings(max_examples=20)`
    - **Validates: Requirements 3.3, 3.4**

  - [x] 3.7 Write property test for boundary detection prompt integrity (Property 4)
    - **Property 4: Boundary detection prompt integrity**
    - Write a property test that for any hook in the affected set, the prompt contains `config/bootcamp_progress.json`, `modules_completed`, and a silent-exit instruction
    - Use `@settings(max_examples=20)`
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

  - [x] 3.8 Write property test for boundary detection correctness (Property 7)
    - **Property 7: Boundary detection correctness for arbitrary progress states**
    - Write a `has_new_completion(before, after)` function
    - Write a property test using `@given` with `st.lists(st.integers(1, 11))` for before/after states
    - Assert detection returns `True` iff `set(after) - set(before)` is non-empty
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 5.4**

  - [x] 3.9 Write property test for wrong event type rejection (Property 8)
    - **Property 8: Wrong event type causes test failure**
    - Write a property test using `@given` with a strategy generating event type strings that are NOT `"agentStop"`
    - Assert that validating such a type against the expected value produces a failure
    - Use `@settings(max_examples=20)`
    - **Validates: Requirements 5.6**

- [x] 4. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Test file lives in repo-root `tests/` per project structure rules (hook tests validating real hook files)
- All tests use `@settings(max_examples=20)` minimum per project conventions (Property 7 uses 100 due to combinatorial state space)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 2, "tasks": ["3.4", "3.5", "3.6", "3.7"] },
    { "id": 3, "tasks": ["3.8", "3.9"] }
  ]
}
```
