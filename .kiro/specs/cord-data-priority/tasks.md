# Implementation Plan: CORD Data Priority

## Overview

Update all user-facing messaging across the Senzing Bootcamp power to establish and enforce the data recommendation hierarchy: (1) bootcamper's own data, (2) CORD data from Senzing, (3) synthesized test data as a last resort. Changes span 5 Markdown files plus a new Python test file using pytest + Hypothesis.

## Tasks

- [x] 1. Update onboarding flow and POWER.md data messaging
  - [x] 1.1 Update `senzing-bootcamp/steering/onboarding-flow.md` Step 4 data messaging
    - In Step 4 (Bootcamp Introduction), replace the line "Test data available anytime. Three sample datasets: Las Vegas, London, Moscow" with messaging that:
      - Explicitly names CORD as Senzing's curated data collections for entity resolution evaluation
      - Includes the CORD reference URL: <https://senzing.com/senzing-ready-data-collections-cord/>
      - Identifies Las Vegas, London, Moscow as CORD datasets
      - Positions synthesized test data as available only if CORD doesn't meet needs
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 1.2 Update `senzing-bootcamp/POWER.md` "Don't have data?" section
    - Replace the "Don't have data handy?" paragraph with messaging that:
      - Leads with CORD as the primary recommendation for bootcampers without their own data
      - Explains CORD briefly (curated, real-world-like datasets for ER evaluation)
      - Includes the CORD reference URL: <https://senzing.com/senzing-ready-data-collections-cord/>
      - Mentions synthesized test data as a fallback if CORD doesn't suffice
      - Retains the `get_sample_data` tool reference for downloading CORD datasets
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 2. Update documentation guides
  - [x] 2.1 Update `senzing-bootcamp/docs/guides/QUICK_START.md` data messaging
    - Replace the line "**Don't have data?** Test data can be generated at any point." with messaging that:
      - Recommends CORD data as the primary option for bootcampers without their own data
      - Positions synthesized test data as a last-resort fallback after CORD
      - References `get_sample_data` tool for obtaining CORD datasets
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 2.2 Update `senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md` data section
    - Replace the paragraph "If you don't have data ready, the bootcamp provides three sample datasets (Las Vegas, London, Moscow) and can generate test data at any point." with messaging that:
      - Names CORD as the primary sample data option (Las Vegas, London, Moscow are CORD datasets)
      - Positions synthesized test data as available if CORD doesn't suffice
    - _Requirements: 6.1, 6.2_

- [x] 3. Update Module 4 steering file
  - [x] 3.1 Update `senzing-bootcamp/steering/module-04-data-collection.md` Step 2 data options
    - In Step 2, update the "If the user doesn't have their own data" section to:
      - Lead with CORD data as the primary alternative, explaining it provides curated, real-world-like datasets for entity resolution evaluation
      - Include the CORD reference URL: <https://senzing.com/senzing-ready-data-collections-cord/>
      - Position synthesized test data generation as available only after CORD is declined
      - Retain the `get_sample_data` tool reference and the free-data GitHub link as secondary options
    - Also update the "Agent behavior" section at the bottom to reflect the hierarchy (CORD first, then free-data repo)
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 4. Checkpoint - Verify hierarchy consistency
  - Ensure all modified files present CORD before synthesized test data. Ensure the CORD URL appears in all files that recommend CORD. Ask the user if questions arise.

- [x] 5. Write property-based and unit tests
  - [x] 5.1 Create test file `senzing-bootcamp/tests/test_cord_data_priority.py` with test infrastructure
    - Create the test file with imports (pytest, hypothesis, pathlib, re)
    - Define helper functions to scan Markdown files under `senzing-bootcamp/`
    - Define regex patterns for detecting CORD mentions and synthesized test data mentions
    - Set up the `TestCordDataPriorityProperties` and `TestCordDataPriorityExamples` test classes
    - _Requirements: 7.1, 7.2_

  - [x] 5.2 Write property test for Property 1: CORD precedes synthesized test data
    - **Property 1: CORD precedes synthesized test data in all touchpoints**
    - **Validates: Requirements 1.1, 1.2, 7.1, 7.2**
    - For any Markdown file under `senzing-bootcamp/` that mentions both CORD and synthesized test data, verify the first CORD mention appears at a lower line number than the first synthesized test data mention

  - [x] 5.3 Write property test for Property 2: CORD reference URL present wherever CORD is recommended
    - **Property 2: CORD reference URL present wherever CORD is recommended**
    - **Validates: Requirements 2.3, 3.2, 4.3, 5.3**
    - For any Markdown file under `senzing-bootcamp/` that recommends CORD data, verify the file contains the URL `https://senzing.com/senzing-ready-data-collections-cord/` or a reference to the `get_sample_data` MCP tool

  - [x] 5.4 Write example-based unit tests for individual file requirements
    - `test_onboarding_flow_cord_in_step4` — Step 4 mentions CORD with description, before synthesized data (Requirements 2.1, 2.2, 2.4)
    - `test_power_md_cord_primary` — POWER.md leads with CORD, retains get_sample_data (Requirements 3.1, 3.3, 3.4)
    - `test_quick_start_cord_first` — QUICK_START.md recommends CORD before synthesized (Requirements 4.1, 4.2)
    - `test_module04_cord_hierarchy` — Module 4 steering recommends CORD first, synthesized as fallback (Requirements 5.1, 5.2)
    - `test_onboarding_checklist_cord` — Checklist mentions CORD as primary, synthesized as fallback (Requirements 6.1, 6.2)
    - _Requirements: 2.1, 2.2, 2.4, 3.1, 3.3, 3.4, 4.1, 4.2, 5.1, 5.2, 6.1, 6.2_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Run `pytest senzing-bootcamp/tests/test_cord_data_priority.py -v` and ensure all tests pass. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (CORD ordering and URL presence)
- Unit tests validate specific examples and edge cases per file
- The implementation language is Python for tests and Markdown for content changes
- All content changes follow the same pattern: reorder to show CORD before synthesized test data, add the CORD reference URL, and frame synthesized data as a fallback

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "2.2", "3.1"] },
    { "id": 1, "tasks": ["5.1"] },
    { "id": 2, "tasks": ["5.2", "5.3", "5.4"] }
  ]
}
```
