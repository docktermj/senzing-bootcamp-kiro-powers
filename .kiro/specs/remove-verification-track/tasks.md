# Implementation Plan: Remove Verification Track

## Overview

Remove the `quick_demo` track from the Senzing Bootcamp following the design's propagation order: Config → Scripts → Validation → Steering → Documentation → Tests. Each task modifies specific files to eliminate `quick_demo` references while preserving Module 3 content and the two remaining tracks (`core_bootcamp`, `advanced_topics`).

## Tasks

- [x] 1. Remove quick_demo from configuration and update script constants
  - [x] 1.1 Remove `quick_demo` track block from `senzing-bootcamp/config/module-dependencies.yaml`
    - Delete the entire `quick_demo:` block (name, description, modules, recommendation) from the `tracks:` section
    - Verify the file remains valid YAML with exactly two track entries: `core_bootcamp` and `advanced_topics`
    - Ensure all non-track sections (metadata, modules, gates) are unchanged
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Update `VALID_TRACKS` constant in `senzing-bootcamp/scripts/progress_utils.py`
    - Change `VALID_TRACKS = ("quick_demo", "core_bootcamp", "advanced_topics")` to `VALID_TRACKS = ("core_bootcamp", "advanced_topics")`
    - _Requirements: 3.1_

  - [x] 1.3 Update `senzing-bootcamp/scripts/track_switcher.py` module docstring
    - Remove `quick_demo` from usage examples and CLI help text in the module docstring
    - No logic changes needed — `compute_switch()` validates against YAML-loaded track definitions
    - _Requirements: 4.4_

- [x] 2. Update validation script and add legacy detection
  - [x] 2.1 Add `quick_demo` to legacy identifiers in `senzing-bootcamp/scripts/validate_dependencies.py`
    - Add `"quick_demo"` to `LEGACY_TRACK_IDENTIFIERS` set
    - Add `"Quick Demo"` and `"System Verification"` to `LEGACY_TRACK_PHRASES` list
    - Ensure the validator detects any lingering references to the removed track
    - _Requirements: 5.3, 5.4_

  - [x] 2.2 Write property test for invalid track rejection (Property 1)
    - **Property 1: Invalid track rejection produces descriptive error**
    - For any string not in `("core_bootcamp", "advanced_topics")` — including `"quick_demo"` — when used as the `track` field in a progress record, `validate_progress_schema()` SHALL return a non-empty error list containing both the invalid value and the tuple of accepted tracks
    - Add/update test in `senzing-bootcamp/tests/test_progress_schema_validation_properties.py`
    - **Validates: Requirements 3.2, 3.3**

- [x] 3. Checkpoint - Ensure config and scripts are consistent
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update steering files
  - [x] 4.1 Update Step 5 in `senzing-bootcamp/steering/onboarding-flow.md`
    - Remove the "System Verification" bullet and its description from Step 5
    - Remove the `"verify"/"system_verification"→start at Module 2` mapping from interpreting-responses guidance
    - Retain the `"core"/"core_bootcamp"` and `"advanced"/"advanced_topics"` response mappings
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 4.2 Update `senzing-bootcamp/steering/inline-status.md`
    - Remove Quick Demo from the "Track module lists" section
    - Retain Core Bootcamp (Modules 1–7) and Advanced Topics (Modules 1–11)
    - _Requirements: 8.1_

- [x] 5. Update documentation files
  - [x] 5.1 Update `senzing-bootcamp/POWER.md`
    - Remove the "Quick Demo" track bullet from the Quick Start section
    - Retain Module 3 ("Quick Demo") in the Core Bootcamp module sequence and in the Bootcamp Modules table
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 5.2 Update `senzing-bootcamp/docs/guides/QUICK_START.md`
    - Remove "Quick Demo" as a path name or selectable option
    - Present exactly two tracks: Core Bootcamp and Advanced Topics
    - Map "quick demo" user requests to Module 3 within Core Bootcamp
    - Remove any "After A" section referencing Quick Demo path
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 5.3 Update `senzing-bootcamp/docs/diagrams/module-prerequisites.md`
    - Remove Quick Demo row from Learning Paths table
    - Retain M2→M3 dependency edge in mermaid graph
    - _Requirements: 8.2, 8.4_

  - [x] 5.4 Update `senzing-bootcamp/docs/diagrams/module-flow.md`
    - Remove Quick Demo subsection under Learning Paths
    - Retain Core Bootcamp and Advanced Topics subsections
    - _Requirements: 8.3_

- [x] 6. Checkpoint - Validate steering and documentation consistency
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update test suite constants and strategies
  - [x] 7.1 Update `senzing-bootcamp/tests/test_track_switcher_properties.py`
    - Update `VALID_TRACKS` to `{"core_bootcamp", "advanced_topics"}`
    - Remove `"quick_demo": [2, 3]` from `TRACK_DEFINITIONS`
    - Update Hypothesis strategies to `st.sampled_from(("core_bootcamp", "advanced_topics"))`
    - Remove any test class/method that exclusively tests `quick_demo` switching scenarios
    - _Requirements: 7.1, 7.3, 7.4, 7.7_

  - [x] 7.2 Update `senzing-bootcamp/tests/test_track_switcher_unit.py`
    - Remove `quick_demo`-specific test cases
    - Add a test asserting CLI rejects `quick_demo` with exit code 1 and stderr message
    - Retain all tests for `core_bootcamp` and `advanced_topics` switching
    - _Requirements: 7.4, 7.5_

  - [x] 7.3 Update `senzing-bootcamp/tests/test_dependency_graph_unit.py`
    - Assert YAML has exactly 2 tracks
    - Assert `"quick_demo"` is absent from YAML tracks
    - Assert Core Bootcamp properties (name, modules, recommendation) are preserved
    - _Requirements: 7.1_

  - [x] 7.4 Update `senzing-bootcamp/tests/test_module_flow_integration.py`
    - Update assertions to expect exactly 2 track bullets in onboarding Step 5
    - Remove assertions checking for "System Verification" track bullet presence
    - _Requirements: 7.2_

  - [x] 7.5 Update `senzing-bootcamp/tests/test_track_reorganization.py`
    - Assert POWER.md lists exactly 2 tracks
    - Assert Module 3 is retained in modules table
    - Remove any `quick_demo` track assertions
    - _Requirements: 7.1, 7.6_

  - [x] 7.6 Update `senzing-bootcamp/tests/test_progress_schema_validation_properties.py`
    - Update `VALID_TRACKS` or equivalent constants to `("core_bootcamp", "advanced_topics")`
    - Update Hypothesis strategies to exclude only the two valid tracks
    - _Requirements: 7.3, 7.7_

  - [x] 7.7 Update `senzing-bootcamp/tests/test_validate_module.py`
    - Ensure `validate_dependencies.py` integration test expects exit code 0 with updated files
    - _Requirements: 7.1_

  - [x] 7.8 Update any remaining test files with `quick_demo` references
    - Search all files in `senzing-bootcamp/tests/` for `quick_demo`, `"Quick Demo"`, or `_VALID_TRACK_IDS` references
    - Update constants and remove obsolete assertions in any additional test files found
    - _Requirements: 7.1, 7.6, 7.7_

- [x] 8. Write property-based tests for track switching
  - [x] 8.1 Write property test for valid track switching (Property 2)
    - **Property 2: Valid track switching succeeds for all module states**
    - For any pair of tracks from `{"core_bootcamp", "advanced_topics"}` and any subset of modules 1–11 as `modules_completed`, `compute_switch()` SHALL return a `SwitchResult` without raising, and `remaining_modules` ∪ (`modules_completed` ∩ target modules) SHALL equal the target track's module set
    - Add/update test in `senzing-bootcamp/tests/test_track_switcher_properties.py`
    - **Validates: Requirements 4.1**

  - [x] 8.2 Write property test for side-effect-free rejection (Property 3)
    - **Property 3: Invalid track switch is side-effect-free**
    - For any string not in `{"core_bootcamp", "advanced_topics"}`, when provided as source or target to the track switcher CLI with `--apply`, the progress file SHALL remain byte-for-byte identical
    - Add/update test in `senzing-bootcamp/tests/test_track_switcher_properties.py`
    - **Validates: Requirements 4.2, 4.3**

- [x] 9. Final checkpoint - Full test suite validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after each propagation layer
- Property tests validate universal correctness properties from the design document
- The propagation order (Config → Scripts → Validation → Steering → Documentation → Tests) ensures downstream files always reference valid upstream state
- Module 3 content and functionality is preserved throughout — only the `quick_demo` track routing is removed

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "2.2"] },
    { "id": 3, "tasks": ["4.1", "4.2"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3", "5.4"] },
    { "id": 5, "tasks": ["7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8"] },
    { "id": 6, "tasks": ["8.1", "8.2"] }
  ]
}
```
