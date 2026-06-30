# Implementation Plan: Module 1 Business Case Offer

## Overview

This plan implements the `Business_Case_Offer` third path in the Module 1 discovery flow. Work
proceeds bottom-up: first the pure-Python validation/recording helper
(`senzing-bootcamp/scripts/business_case_offer.py`) with its property-based test suite, then the
steering edits that surface the offer and define the generation/recording/MCP-fallback behavior,
and finally the steering-content example and integration tests that pin that behavior.

Per the steering rules: scripts are stdlib-only Python 3.11+ with a `main()` argparse CLI; tests
use pytest + Hypothesis and live in `senzing-bootcamp/tests/`; steering files are CommonMark
Markdown in `senzing-bootcamp/steering/` and must keep `validate_commonmark.py` and
`measure_steering.py --check` green. All Senzing/CORD facts come from the MCP server at runtime —
no hardcoded CORD names or counts in any shipped file.

## Tasks

- [x] 1. Scaffold the validation/recording helper module
  - Create `senzing-bootcamp/scripts/business_case_offer.py` (stdlib-only, `from __future__ import annotations`)
  - Define `RECOGNIZED_CATEGORIES: frozenset[str]` with exactly the 10 Module 1 categories (Customer 360, Fraud Detection, Data Migration, Compliance, Marketing, Healthcare, Supply Chain, KYC, Insurance, Vendor MDM)
  - Define `GENERATED_MARKER: str` observable marker text identifying a bootcamp-generated case
  - Define `@dataclass ScenarioDataSource` (`name: str`, `fields: list[str]`, `records: list[dict]`)
  - Define `@dataclass GeneratedScenario` (`problem_description`, `use_case_category`, `success_definition`, `data_sources`, `provenance`, `selected_pattern_category`)
  - Import `scripts/data_sources.py` via the established `sys.path` manipulation pattern so recording shares the downstream code path
  - Do NOT embed any CORD dataset names or record counts
  - _Requirements: 2.2_

- [x] 2. Implement scenario validation and mapping-complexity logic
  - [x] 2.1 Implement `validate_scenario(s) -> list[str]`
    - Return human-readable violation strings (empty list = valid); raise no exceptions for invalid input
    - Check non-empty (trimmed) `problem_description` and `success_definition`
    - Check `use_case_category` is exactly one value in `RECOGNIZED_CATEGORIES`
    - Check `data_sources` has ≥ 2 distinctly named sources, each with ≥ 1 record
    - Check `provenance` ∈ `{"cord", "generated"}`
    - Check that when `selected_pattern_category` is set it equals `use_case_category`
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.3_

  - [x] 2.2 Write property test for scenario shape validity
    - **Property 1: Generated scenario has a valid shape**
    - **Validates: Requirements 2.1, 2.2**
    - In `senzing-bootcamp/tests/test_business_case_offer_properties.py`; use `st_scenario()` plus deliberately-invalid variants (empty/whitespace description/success, off-list category); tag with `# Feature: module1-business-case-offer, Property 1: ...`

  - [x] 2.3 Write property test for selected-pattern category match
    - **Property 2: Scenario category matches a selected pattern**
    - **Validates: Requirements 2.3**
    - Scenarios with `selected_pattern_category` set to matching and mismatching values

  - [x] 2.4 Write property test for multi-source data with known provenance
    - **Property 3: Scenario data is multi-source with known provenance**
    - **Validates: Requirements 3.1, 3.3, 3.5**
    - `st_scenario_data()` over both provenances; min 2 sources, ≥ 1 record each

  - [x] 2.5 Implement `detect_mapping_complexity(sources) -> set[str]`
    - Return the subset present of `{"differing_field_names", "combine_or_split", "inconsistent_formatting"}`
    - Compare `fields`/values across sources to detect differing field names, combine/split, and inconsistent formatting
    - _Requirements: 3.2, 3.5_

  - [x] 2.6 Write property test for mapping complexity presence
    - **Property 4: Scenario data exhibits mapping complexity**
    - **Validates: Requirements 3.2, 3.5**
    - Data with at least one transformation trait injected; assert non-empty subset returned

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement document rendering and registry recording
  - [x] 4.1 Implement `render_business_problem(s) -> str`
    - Render the `docs/business_problem.md` body using the existing Step 12 template sections (Problem Description, Use Case Category, Data Sources, Key Matching Criteria, Success Criteria)
    - Include the problem description, use-case category, every distinct data source, the definition of success, and the `GENERATED_MARKER`
    - _Requirements: 4.1, 4.3, 4.4_

  - [x] 4.2 Write property test for business-problem completeness and marker
    - **Property 5: Business problem document is complete and marked generated**
    - **Validates: Requirements 4.1, 4.3, 4.4**
    - `st_scenario()`; assert all content elements + `GENERATED_MARKER` present in standard structure

  - [x] 4.3 Implement `record_data_sources(s) -> str`
    - Serialize one `RegistryEntry` per distinct `ScenarioDataSource` to `data_sources.yaml` text, reusing `serialize_registry_yaml` / registry types from `scripts/data_sources.py`
    - Number of recorded entries equals the number of distinct sources
    - _Requirements: 4.2, 5.1, 5.2_

  - [x] 4.4 Write property test for data-source recording round-trip
    - **Property 6: Data source recording round-trips**
    - **Validates: Requirements 4.2, 5.1, 5.2**
    - `st_scenario()`; record via `record_data_sources` then parse back with `parse_registry_yaml`; compare distinct source-name sets and counts

- [x] 5. Implement the CLI entry point
  - [x] 5.1 Implement `main(argv=None) -> int` with argparse
    - Add a `validate` subcommand that loads an existing `business_problem.md` + `data_sources.yaml` pair and checks the generated-scenario invariants, reporting violations and a non-zero exit on failure
    - Degrade gracefully (no exception) when an artifact is missing/unreadable, reporting the condition
    - _Requirements: 4.5, 5.4_

  - [x] 5.2 Write unit tests for the CLI and category set
    - Assert `RECOGNIZED_CATEGORIES` equals exactly the 10 Module 1 categories
    - Assert `validate` reports violations and exits non-zero for an invalid pair, and exits zero for a valid pair
    - Assert no CORD dataset names or record counts appear in `business_case_offer.py` (only-source-is-MCP guard) — _Requirements: 6.2_
    - _Requirements: 4.5, 5.4_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Edit discovery steering to surface the offer (Phase 1)
  - [x] 7.1 Add the third path to Step 5 of `steering/module-01-phase1-discovery.md`
    - Restructure the Discovery_Prompt into three separately selectable paths: describe a real case, adopt a Design_Pattern_Gallery entry, and accept the Business_Case_Offer
    - State the offer applies both when the bootcamper has no case and when they have one but won't share it
    - State the Bootcamp will generate a realistic, multi-source scenario enabling completion of the full bootcamp without supplying or inventing a case
    - Add a 🛑 STOP marker so no scenario is produced before explicit acceptance
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_

  - [x] 7.2 Reference the offer from Step 4 and design-patterns
    - In Step 4 (Design Pattern Gallery) add a sentence referencing the Business_Case_Offer as an available selectable path
    - Add a small reference in `steering/design-patterns.md`
    - _Requirements: 1.4_

  - [x] 7.3 Define the acceptance/decline/failure branch in steering
    - On acceptance: generate the scenario, determine CORD-vs-generated via MCP, validate, and on success record artifacts
    - On decline: continue with the bootcamper's own description and write no generated document
    - On generation failure (including `validate_scenario` violations): inform the bootcamper and fall back to their own description without writing a generated `business_problem.md`
    - _Requirements: 2.1, 2.4, 2.5_

  - [x] 7.4 Define MCP CORD-sourcing and fallback in steering
    - Instruct the Agent to retrieve CORD dataset names/contents/availability via `get_sample_data` / `search_docs` during the active session and present returned values verbatim (no static figures)
    - Encode the 30-second timeout / single-retry pattern; on timeout or unreachable, omit CORD facts, inform the bootcamper CORD details are unavailable from the MCP server, and produce Generated_Data satisfying multi-source + mapping-complexity criteria
    - _Requirements: 3.4, 6.1, 6.2, 6.3, 6.4_

- [x] 8. Edit recording steering to write artifacts (Phase 2)
  - [x] 8.1 Update Step 12 of `steering/module-01-phase2-document-confirm.md`
    - When a Generated_Scenario is in effect, write the standard `docs/business_problem.md` template plus the observable bootcamp-generated marker
    - Record each distinct Scenario_Data source into `config/data_sources.yaml` (entries = distinct sources)
    - Ensure the document contains problem description, use-case category, data sources, and definition of success regardless of registry recording
    - Specify write-failure handling (4.5) and downstream missing/unreadable-artifact handling (5.4): inform the bootcamper and allow supplying real data
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.3, 5.4_

- [x] 9. Checkpoint - Validate steering edits
  - Ensure `validate_commonmark.py` and `measure_steering.py --check` stay green; ask the user if questions arise.

- [x] 10. Write steering-content and integration tests
  - [x] 10.1 Write steering-content example tests
    - In `senzing-bootcamp/tests/test_business_case_offer_steering.py`; parse `module-01-phase1-discovery.md` and assert Step 5 presents the three selectable paths including the offer, the offer text covers both "no case" and "won't share", describes realistic multi-source generation, Step 4 references the offer, and a 🛑 STOP marker precedes generation
    - Assert the decline branch continues without writing a generated doc; generation-failure and write-failure branches inform and fall back; downstream-missing-artifact branch informs and allows real data; the CORD-unavailable message is present
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.4, 2.5, 4.5, 5.4, 6.4_

  - [x] 10.2 Write MCP-sourcing integration tests
    - Assert `module-01-phase1-discovery.md` Step 5 / acceptance branch instructs the Agent to call `get_sample_data` / `search_docs` for CORD details and present returned values verbatim
    - Assert the steering encodes the 30-second timeout and single-retry fallback to Generated_Data, consistent with the Step 6d pattern
    - _Requirements: 3.4, 6.1, 6.3_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass (pytest, CommonMark, steering budget), ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific requirements clauses for traceability.
- Property tests (2.2, 2.3, 2.4, 2.6, 4.2, 4.4) validate the six universal correctness properties from the design; each is annotated with its property number and the requirements it validates.
- Steering-content (10.1) and MCP-sourcing (10.2) criteria are covered by example/integration tests rather than properties, since they are not pure functions over varied input.
- The Python helper raises no exceptions for invalid input; `validate_scenario` returns violation strings and registry read-back reuses the tolerant parser in `data_sources.py`.
- No CORD dataset names or counts appear in any shipped file — all CORD facts come from the MCP server at runtime.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.5"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.6", "4.1", "4.3"] },
    { "id": 3, "tasks": ["4.2", "4.4", "5.1"] },
    { "id": 4, "tasks": ["5.2", "7.1", "7.2", "8.1"] },
    { "id": 5, "tasks": ["7.3", "7.4"] },
    { "id": 6, "tasks": ["10.1", "10.2"] }
  ]
}
```
