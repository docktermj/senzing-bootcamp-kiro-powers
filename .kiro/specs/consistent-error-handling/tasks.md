# Implementation Plan: Consistent Error Handling

## Overview

Add a standard `## Error Handling` section to all 11 root module steering files and a `## Troubleshooting by Symptom` table to `common-pitfalls.md`. A Hypothesis property-based test suite validates completeness using `steering-index.yaml` as the source of truth.

## Tasks

- [x] 1. Add the Error Handling section to all root module steering files
  - [x] 1.1 Add `## Error Handling` section to modules without phase sub-files (2, 3, 4, 7, 8, 9, 10)
    - Use the exact template from the design document (≤15 lines)
    - Insert before the final section in each file (before "Agent Rules", "Success Criteria", "Troubleshooting", or the last heading)
    - Must contain references to `explain_error_code` and `common-pitfalls.md`
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3_

  - [x] 1.2 Add `## Error Handling` section to root files of split modules (1, 5, 6, 11)
    - Add the same template to `module-01-business-problem.md`, `module-05-data-quality-mapping.md`, `module-06-load-data.md`, `module-11-deployment.md`
    - Do NOT add the section to any phase sub-files
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3, 3.1, 4.1, 4.2, 4.3_

- [x] 2. Checkpoint — Verify Error Handling sections
  - Ensure all 11 root module files contain the `## Error Handling` section, ask the user if questions arise.

- [x] 3. Add the Troubleshooting by Symptom table to common-pitfalls.md
  - [x] 3.1 Insert `## Troubleshooting by Symptom` section with the 5-row symptom table
    - Place between the Quick Navigation section and the `## Module 2: SDK Setup` section
    - Table columns: Symptom | Likely Cause | Diagnostic Steps
    - Required rows: "zero entities created", "loading hangs", "query returns no results", "SDK initialization fails", "database connection fails"
    - Diagnostic Steps must reference specific MCP tools (`explain_error_code`, `search_docs`, `get_sdk_reference`)
    - Content for each row must match the detail specified in Requirements 6.1–6.5
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 3.2 Update Quick Navigation to include a Symptoms link
    - Add `[Symptoms](#troubleshooting-by-symptom)` to the Quick Navigation anchor list in `common-pitfalls.md`
    - _Requirements: 5.2_

- [x] 4. Checkpoint — Verify steering file changes
  - Ensure all steering file edits are correct and consistent, ask the user if questions arise.

- [x] 5. Create the property-based test suite
  - [x] 5.1 Create `senzing-bootcamp/tests/test_error_handling_section_properties.py` with test helpers
    - Implement `load_steering_index()` to parse `steering-index.yaml`
    - Implement `resolve_root_path()` to handle both string and dict module entries
    - Implement `read_section()` to extract content under a `##` heading from a Markdown file
    - Implement `parse_symptom_table()` to parse a Markdown table into a list of row dicts
    - Define Hypothesis strategies: `st_module_number()` drawing from steering index module set, `st_symptom_name()` drawing from the 5 required symptoms
    - Use `@settings(max_examples=100)` on every property test
    - _Requirements: 7.1, 7.2, 7.6, 7.7, 8.1, 8.5, 9.1, 9.2, 9.3, 9.4_

  - [x] 5.2 Write property test for Error Handling Section Completeness
    - **Property 1: Error Handling Section Completeness**
    - For any module number drawn from the steering index, verify the root file contains `## Error Handling` with references to `explain_error_code` and `common-pitfalls.md`
    - **Validates: Requirements 1.1, 1.2, 2.1, 2.3, 3.1, 4.3, 7.3, 7.4, 7.5**

  - [x] 5.3 Write property test for Phase Sub-File Exclusion
    - **Property 2: Phase Sub-File Exclusion**
    - For any module with phase sub-files, verify none of the phase sub-files contain `## Error Handling`
    - **Validates: Requirements 1.3**

  - [x] 5.4 Write property test for Section Conciseness
    - **Property 3: Section Conciseness**
    - For any module number drawn from the steering index, verify the `## Error Handling` section is ≤15 lines
    - **Validates: Requirements 4.2**

  - [x] 5.5 Write property test for Symptom Table Completeness
    - **Property 4: Symptom Table Completeness**
    - For any symptom drawn from the 5 required symptoms, verify the table in `common-pitfalls.md` contains a matching row with non-empty Likely Cause and Diagnostic Steps columns
    - **Validates: Requirements 5.3, 5.4, 8.3, 8.4**

  - [x] 5.6 Write property test for Module Path Resolution
    - **Property 5: Module Path Resolution**
    - For any module entry in the steering index, verify the resolution function returns the entry itself for strings and the `root` key value for dicts
    - **Validates: Requirements 9.2, 9.3**

  - [x] 5.7 Write unit tests for section ordering and error reporting
    - Verify `## Troubleshooting by Symptom` appears after Quick Navigation and before `## Module 2: SDK Setup`
    - Verify missing root files produce clear errors, not silent skips
    - _Requirements: 5.2, 9.4_

- [x] 6. Final checkpoint — Ensure all tests pass
  - Run `pytest senzing-bootcamp/tests/test_error_handling_section_properties.py -v` and ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The error handling section template is identical across all 11 modules (design decision: module-agnostic triage procedure)
- The test suite uses `steering-index.yaml` as the oracle — new modules are automatically covered
- Property tests use Hypothesis with `@settings(max_examples=100)`
- All steering file content is Markdown; the test suite is Python 3.11+ with pytest + Hypothesis + PyYAML
