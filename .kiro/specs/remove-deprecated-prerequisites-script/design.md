# Design Document

## Overview

This feature is a pure cleanup operation: delete the deprecated `check_prerequisites.py` shim, its dedicated test file, and scrub all stale references from documentation and completed spec artifacts. No new code is introduced. The only logic change is removing the `test_check_prerequisites_deprecation` method from `test_preflight.py`.

## Architecture

No architectural changes. The cleanup removes dead code and stale references without altering any active component.

```
Files Deleted:
  senzing-bootcamp/scripts/check_prerequisites.py
  senzing-bootcamp/tests/test_check_prerequisites.py

Files Edited (reference removal):
  senzing-bootcamp/tests/test_preflight.py
  senzing-bootcamp/docs/guides/SCRIPT_REFERENCE.md
  senzing-bootcamp/docs/policies/FILE_STORAGE_POLICY.md
  .kiro/specs/script-test-suite/requirements.md
  .kiro/specs/script-test-suite/design.md
  .kiro/specs/script-test-suite/tasks.md
  .kiro/specs/environment-verification/requirements.md
  .kiro/specs/environment-verification/design.md
  .kiro/specs/environment-verification/tasks.md
  .kiro/specs/senzing-bootcamp-power/tasks.md

Files NOT Modified (preserve check_prerequisites_listed):
  senzing-bootcamp/tests/test_steering_structure_properties.py
  .kiro/specs/steering-structural-validation/*
```

## Components and Interfaces

### 1. File Deletions

| File | Reason |
|------|--------|
| `senzing-bootcamp/scripts/check_prerequisites.py` | Deprecated shim — delegates to `preflight.py`, ships dead code to users |
| `senzing-bootcamp/tests/test_check_prerequisites.py` | Tests the deprecated shim under the old name; all real coverage lives in `test_preflight.py` |

### 2. Test Method Removal

Remove the `test_check_prerequisites_deprecation` method from `TestLegacyScriptsDeprecation` in `senzing-bootcamp/tests/test_preflight.py`. The class itself remains because it still contains `test_preflight_check_deprecation`.

### 3. Documentation Reference Removal

**SCRIPT_REFERENCE.md**: Remove the row referencing `check_prerequisites.py` from the scripts table.

**FILE_STORAGE_POLICY.md**: Remove the `├── check_prerequisites.py # Prerequisites check` line from the directory tree listing.

### 4. Spec Document Reference Cleanup

For completed spec artifacts, references to `check_prerequisites.py` are historical context. The cleanup strategy per spec:

| Spec Directory | Strategy |
|---|---|
| `script-test-suite/` | Remove or annotate references to `check_prerequisites.py` as removed. Update the glossary, design diagrams, task lists, and property descriptions to reflect that the script no longer exists. |
| `environment-verification/` | Add "[removed]" annotations to historical references. These specs document the transition that created the shim, so context is preserved but marked as no longer current. |
| `senzing-bootcamp-power/tasks.md` | Remove `check_prerequisites.py` from the utilities list in task 7.7. |

### 5. Preservation Guard

The function `check_prerequisites_listed` in `senzing-bootcamp/tests/test_steering_structure_properties.py` and all references in `.kiro/specs/steering-structural-validation/` are unrelated to the deprecated script. They validate that steering module files contain a "Prerequisites" section. These MUST NOT be modified.

**Disambiguation rule**: Only match the exact filename string `check_prerequisites.py` or the import/module name `check_prerequisites` (without `_listed` suffix) when identifying references to remove.

## Error Handling

The only risk is accidentally removing the `check_prerequisites_listed` function or its references. The disambiguation rule above prevents this. Additionally, the test suite serves as a regression gate — if `check_prerequisites_listed` is accidentally removed, the steering-structural-validation property tests will fail.

## Testing Strategy

**Smoke tests** (file existence assertions):
- Assert `senzing-bootcamp/scripts/check_prerequisites.py` does not exist
- Assert `senzing-bootcamp/tests/test_check_prerequisites.py` does not exist
- Assert `test_check_prerequisites_deprecation` method is absent from `test_preflight.py`
- Assert `check_prerequisites.py` string is absent from `SCRIPT_REFERENCE.md` and `FILE_STORAGE_POLICY.md`

**Preservation checks** (example assertions):
- Assert `check_prerequisites_listed` function still exists in `test_steering_structure_properties.py`
- Assert references to `check_prerequisites_listed` remain in `steering-structural-validation/` specs

**Integration test**:
- Run `pytest senzing-bootcamp/tests/` — full suite passes with no import errors

## Data Models

No data model changes. This feature only deletes files and removes text references.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

*This is a cleanup/deletion feature. Nearly all acceptance criteria are verifiable through smoke tests (file existence checks) and integration tests (test suite passes). The one universal invariant is the preservation guard — ensuring the cleanup never touches unrelated similarly-named symbols.*

### Property 1: Cleanup preserves unrelated check_prerequisites_listed references

*For any* file in the repository that contains the string `check_prerequisites_listed`, the cleanup process SHALL leave that file completely unmodified.

**Validates: Requirements 4.1, 4.2**
