# Implementation Plan: Module Artifacts Completeness

## Overview

Complete the `config/module-artifacts.yaml` manifest by adding Modules 1–3, introduce the "sentinel" artifact type for non-file outcomes, align the `requires_from` dependency graph with module-dependencies.yaml, and update the validation script and test suites to accept the new type. All changes are in Python and YAML within the `senzing-bootcamp/` subtree.

## Tasks

- [x] 1. Add Modules 1–3 to module-artifacts.yaml and update dependency graph
  - [x] 1.1 Add Module 1, Module 2, and Module 3 entries to `senzing-bootcamp/config/module-artifacts.yaml`
    - Insert Module 1 with produces: `docs/business_problem.md` (file), `config/data_sources.yaml` (file); empty `requires_from`
    - Insert Module 2 with produces: `database/G2C.db` (file), `config/engine_config.json` (file), `config/bootcamp_preferences.yaml` (file), `sdk_installed` (sentinel); empty `requires_from`
    - Insert Module 3 with produces: `src/system_verification/` (directory), `docs/progress/MODULE_3_COMPLETE.md` (file); `requires_from` referencing Module 2 for `database/G2C.db`
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 4.1_

  - [x] 1.2 Update Module 4 and Module 6 `requires_from` entries
    - Add `1: ["config/data_sources.yaml"]` to Module 4's `requires_from`
    - Add `2: ["database/G2C.db"]` to Module 6's `requires_from` (alongside existing `5: ["data/transformed/"]`)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 2. Update validation script to support sentinel artifact type
  - [x] 2.1 Add `VALID_ARTIFACT_TYPES` constant and update `check_artifact_on_disk` in `senzing-bootcamp/scripts/validate_module.py`
    - Add module-level constant `VALID_ARTIFACT_TYPES = {"file", "directory", "sentinel"}`
    - Change `check_artifact_on_disk` signature to accept `artifact_type: str` parameter
    - When `artifact_type == "sentinel"`, return `(True, False)` immediately without filesystem I/O
    - _Requirements: 4.2, 4.3_

  - [x] 2.2 Update `run_artifact_check` to resolve artifact type before disk check
    - Look up the artifact type from the source module's `produces` list before calling `check_artifact_on_disk`
    - Pass the resolved `artifact_type` to `check_artifact_on_disk`
    - _Requirements: 4.2, 4.3_

  - [x] 2.3 Write property test for artifact type validation exhaustiveness
    - **Property 1: Artifact type validation is exhaustive**
    - Generate random strings and verify the validator accepts exactly "file", "directory", and "sentinel"
    - **Validates: Requirements 4.1, 4.3, 6.1, 6.2**

  - [x] 2.4 Write property test for sentinel disk-check bypass
    - **Property 2: Sentinel artifacts bypass filesystem validation**
    - Generate random sentinel artifact entries and verify `check_artifact_on_disk` returns `(True, False)` without filesystem I/O
    - **Validates: Requirements 4.2**

- [x] 3. Checkpoint - Ensure manifest and validation script are consistent
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update chain integration tests to accept sentinel type
  - [x] 4.1 Update `test_produces_items_have_valid_structure` in `senzing-bootcamp/tests/test_artifact_chain_integration.py`
    - Change type validation from `("file", "directory")` to `("file", "directory", "sentinel")`
    - Update error message to list all three valid types
    - _Requirements: 6.1_

  - [x] 4.2 Update `TestSteeringReferencesArtifacts` parametrization
    - Change `@pytest.mark.parametrize("module_num", [5, 6, 7, 8, 9, 10, 11])` to `list(range(1, 12))` to cover modules 1–11
    - _Requirements: 7.1_

  - [x] 4.3 Update `TestArtifactChainContinuity.test_chain_is_connected` for root modules
    - Define `root_modules = {1, 2}` and skip connectivity assertion for those modules
    - Ensure all modules > 2 have at least one `requires_from` entry
    - _Requirements: 7.1, 7.2_

- [x] 5. Update dependency tracking tests to accept sentinel type
  - [x] 5.1 Update `test_manifest_produces_have_required_fields` in `senzing-bootcamp/tests/test_artifact_dependency_tracking.py`
    - Change type assertion from `("file", "directory")` to `("file", "directory", "sentinel")`
    - _Requirements: 6.2_

  - [x] 5.2 Write property test for non-root module dependency invariant
    - **Property 3: Non-root modules have upstream dependencies**
    - Sample modules from the manifest and verify modules with number > 2 always have `requires_from`
    - **Validates: Requirements 7.2**

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation language is Python 3.11+ (stdlib only) per project conventions
- All paths are relative to `senzing-bootcamp/`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "4.1", "4.2", "4.3", "5.1"] },
    { "id": 3, "tasks": ["2.3", "2.4", "5.2"] }
  ]
}
```
