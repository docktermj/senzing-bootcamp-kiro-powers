# Implementation Plan: Test Data Terminology

## Overview

Replace all instances of "mock data" with "test data" or "sample data" across the senzing-bootcamp power's steering files, documentation, and test suite. Each task targets a specific file or group of files, with property-based tests validating the universal invariant that no "mock data" references remain.

## Tasks

- [x] 1. Update steering file terminology
  - [x] 1.1 Replace "mock data" with "test data" / "sample data" in `senzing-bootcamp/steering/onboarding-flow.md`
    - In Step 4, replace "Mock data available anytime" with "Test data available anytime"
    - Use "sample datasets" when referring to the named city datasets (Las Vegas, London, Moscow)
    - Ensure no occurrence of "mock data" (case-insensitive) remains in the file
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Update documentation terminology
  - [x] 2.1 Replace "mock data" with "test data" in `senzing-bootcamp/POWER.md`
    - Change "mock data can be generated at any point" to "test data can be generated at any point"
    - Ensure no occurrence of "mock data" (case-insensitive) remains in the file
    - _Requirements: 2.1_

  - [x] 2.2 Replace "mock data" with "test data" in `senzing-bootcamp/docs/guides/QUICK_START.md`
    - Change "Mock data can be generated at any point" to "Test data can be generated at any point"
    - Ensure no occurrence of "mock data" (case-insensitive) remains in the file
    - _Requirements: 2.2_

  - [x] 2.3 Replace "mock data" with "test data" in `senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md`
    - Change "can generate mock data at any point" to "can generate test data at any point"
    - Ensure no occurrence of "mock data" (case-insensitive) remains in the file
    - _Requirements: 2.3_

- [x] 3. Update existing test assertions
  - [x] 3.1 Update `senzing-bootcamp/tests/test_track_selection_gate_preservation.py`
    - Rename method `test_step4_contains_mock_data` to `test_step4_contains_test_data`
    - Update the regex assertion from `r"[Mm]ock data"` to `r"[Tt]est data|[Ss]ample data"`
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 3.2 Update `senzing-bootcamp/tests/test_comprehension_check.py`
    - Rename method `test_step_4_mock_data_and_license` to `test_step_4_test_data_and_license`
    - Update the assertion to check for "test data" or "sample data" instead of "Mock data"
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 4. Checkpoint - Verify existing tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Add property-based tests for terminology invariants
  - [x] 5.1 Write property test: No "mock data" in file content
    - **Property 1: No "mock data" in file content**
    - **Validates: Requirements 1.1, 1.3, 2.1, 2.2, 2.3, 3.2, 4.2, 5.1**
    - Use Hypothesis to sample files with extensions `.md`, `.py`, `.yaml` from `senzing-bootcamp/`
    - Assert that no sampled file contains "mock data" (case-insensitive)

  - [x] 5.2 Write property test: No "mock_data" or "mock-data" in filenames
    - **Property 2: No "mock_data" or "mock-data" in filenames**
    - **Validates: Requirements 3.1, 5.2**
    - Use Hypothesis to sample file paths from `senzing-bootcamp/`
    - Assert that no filename contains the substring `mock_data` or `mock-data` (case-insensitive)

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation language is Python (pytest + Hypothesis for tests, Markdown for content files)
- No script filename changes are needed — no `generate_mock_data.py` exists in the codebase
- Property tests serve as the primary regression guard against future reintroduction of "mock data"
