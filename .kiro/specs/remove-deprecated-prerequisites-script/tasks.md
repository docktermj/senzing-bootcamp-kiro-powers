# Implementation Plan: Remove Deprecated Prerequisites Script

## Overview

Pure cleanup operation: delete the deprecated `check_prerequisites.py` shim and its test file, remove the deprecation test method from `test_preflight.py`, and scrub all stale references from documentation and completed spec artifacts. No new code is introduced. The `check_prerequisites_listed` function and its references must be preserved.

## Tasks

- [x] 1. Delete deprecated script and test files
  - [x] 1.1 Delete `senzing-bootcamp/scripts/check_prerequisites.py`
    - Remove the deprecated shim script that delegates to `preflight.py`
    - _Requirements: 1.1_

  - [x] 1.2 Delete `senzing-bootcamp/tests/test_check_prerequisites.py`
    - Remove the dedicated test file for the deprecated shim
    - _Requirements: 1.2_

  - [x] 1.3 Remove `test_check_prerequisites_deprecation` method from `senzing-bootcamp/tests/test_preflight.py`
    - Remove only the `test_check_prerequisites_deprecation` method from the `TestLegacyScriptsDeprecation` class
    - Preserve the class itself and the `test_preflight_check_deprecation` method
    - _Requirements: 1.3_

- [x] 2. Clean up documentation references
  - [x] 2.1 Remove `check_prerequisites.py` reference from `senzing-bootcamp/docs/guides/SCRIPT_REFERENCE.md`
    - Remove the row referencing `check_prerequisites.py` from the scripts table
    - _Requirements: 2.1_

  - [x] 2.2 Remove `check_prerequisites.py` reference from `senzing-bootcamp/docs/policies/FILE_STORAGE_POLICY.md`
    - Remove the `├── check_prerequisites.py # Prerequisites check` line from the directory tree listing
    - _Requirements: 2.2_

- [x] 3. Clean up spec document references
  - [x] 3.1 Update `.kiro/specs/script-test-suite/` spec documents
    - Remove or annotate references to `check_prerequisites.py` as removed in requirements.md, design.md, and tasks.md
    - Update glossary, design diagrams, task lists, and property descriptions to reflect the script no longer exists
    - _Requirements: 3.1_

  - [x] 3.2 Update `.kiro/specs/environment-verification/` spec documents
    - Add "[removed]" annotations to historical references to `check_prerequisites.py` in requirements.md, design.md, and tasks.md
    - Preserve historical context but mark references as no longer current
    - _Requirements: 3.2_

  - [x] 3.3 Update `.kiro/specs/senzing-bootcamp-power/tasks.md`
    - Remove `check_prerequisites.py` from the utilities list in task 7.7
    - _Requirements: 3.3_

- [x] 4. Checkpoint - Verify cleanup and preservation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Validate test suite integrity
  - [x] 5.1 Run the full test suite to confirm no regressions
    - Run `pytest senzing-bootcamp/tests/` and verify all tests pass with no import errors related to `check_prerequisites`
    - Verify `check_prerequisites_listed` function in `senzing-bootcamp/tests/test_steering_structure_properties.py` is preserved and its tests pass
    - _Requirements: 4.1, 4.2, 5.1, 5.2_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- The disambiguation rule is critical: only match the exact filename `check_prerequisites.py` or module name `check_prerequisites` (without `_listed` suffix) when removing references
- The `check_prerequisites_listed` function in `test_steering_structure_properties.py` and all references in `.kiro/specs/steering-structural-validation/` MUST NOT be modified
- No new code is introduced — this is purely a deletion and reference cleanup task
- The `TestLegacyScriptsDeprecation` class in `test_preflight.py` must be preserved (it still contains `test_preflight_check_deprecation`)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "2.1", "2.2"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 2, "tasks": ["5.1"] }
  ]
}
```
