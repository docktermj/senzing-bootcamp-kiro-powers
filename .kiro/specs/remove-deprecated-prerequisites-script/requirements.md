# Requirements Document

## Introduction

The deprecated `check_prerequisites.py` script was replaced by `preflight.py` during the environment-verification feature. A thin deprecation shim was left in place temporarily. Now that `preflight.py` is fully established and all test coverage exists in `test_preflight.py`, the shim script, its dedicated test file, and all stale references across documentation and completed spec artifacts should be removed to reduce maintenance burden and avoid shipping dead code in the distributed power.

## Glossary

- **Cleanup_Process**: The set of file deletions and reference removals performed to eliminate the deprecated `check_prerequisites.py` script and its associated artifacts from the repository.
- **Deprecated_Script**: The file `senzing-bootcamp/scripts/check_prerequisites.py`, a thin shim that delegates to `preflight.py`.
- **Deprecated_Test_File**: The file `senzing-bootcamp/tests/test_check_prerequisites.py`, which tests preflight functionality under the old script name.
- **Deprecation_Test**: The `test_check_prerequisites_deprecation` method in `senzing-bootcamp/tests/test_preflight.py` that verifies the shim behavior.
- **Spec_Documents**: The completed spec artifacts in `.kiro/specs/` that reference the deprecated script.
- **Documentation_Files**: The user-facing documentation files that list or reference the deprecated script.

## Requirements

### Requirement 1: Remove Deprecated Script File

**User Story:** As a power maintainer, I want the deprecated `check_prerequisites.py` shim removed from the repository, so that dead code is not shipped to users.

#### Acceptance Criteria

1. WHEN the Cleanup_Process completes, THE Deprecated_Script SHALL no longer exist at `senzing-bootcamp/scripts/check_prerequisites.py`.
2. WHEN the Cleanup_Process completes, THE Deprecated_Test_File SHALL no longer exist at `senzing-bootcamp/tests/test_check_prerequisites.py`.
3. WHEN the Cleanup_Process completes, THE Deprecation_Test SHALL no longer exist in `senzing-bootcamp/tests/test_preflight.py`.

### Requirement 2: Clean Up Documentation References

**User Story:** As a power maintainer, I want all documentation references to `check_prerequisites.py` removed or updated, so that users are not confused by references to a non-existent script.

#### Acceptance Criteria

1. WHEN the Cleanup_Process completes, THE Documentation_Files SHALL not contain any reference to `check_prerequisites.py` in `senzing-bootcamp/docs/guides/SCRIPT_REFERENCE.md`.
2. WHEN the Cleanup_Process completes, THE Documentation_Files SHALL not contain any reference to `check_prerequisites.py` in `senzing-bootcamp/docs/policies/FILE_STORAGE_POLICY.md`.

### Requirement 3: Clean Up Spec Document References

**User Story:** As a power maintainer, I want completed spec documents updated to remove stale references to the deprecated script, so that spec history remains accurate.

#### Acceptance Criteria

1. WHEN the Cleanup_Process completes, THE Spec_Documents in `.kiro/specs/script-test-suite/` SHALL not reference `check_prerequisites.py` as a current script or test target.
2. WHEN the Cleanup_Process completes, THE Spec_Documents in `.kiro/specs/environment-verification/` SHALL not reference `check_prerequisites.py` as a currently existing file.
3. WHEN the Cleanup_Process completes, THE Spec_Documents in `.kiro/specs/senzing-bootcamp-power/tasks.md` SHALL not list `check_prerequisites.py` as a current utility.

### Requirement 4: Preserve Unrelated References

**User Story:** As a power maintainer, I want unrelated functions with similar names preserved, so that the cleanup does not break other features.

#### Acceptance Criteria

1. THE Cleanup_Process SHALL preserve the `check_prerequisites_listed` function in `senzing-bootcamp/tests/test_steering_structure_properties.py` without modification.
2. THE Cleanup_Process SHALL preserve all references to `check_prerequisites_listed` in `.kiro/specs/steering-structural-validation/` without modification.

### Requirement 5: Test Suite Integrity

**User Story:** As a power maintainer, I want the test suite to pass after the cleanup, so that no regressions are introduced.

#### Acceptance Criteria

1. WHEN the Cleanup_Process completes, THE test suite SHALL pass without errors related to missing `check_prerequisites` imports or references.
2. WHEN the Cleanup_Process completes, THE existing `test_preflight.py` tests (excluding the removed Deprecation_Test) SHALL continue to pass.
