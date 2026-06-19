# Implementation Plan: language-example-coverage

## Overview

This plan implements the cross-language example-coverage tracking feature in Python 3.11+
(stdlib only, plus a lazily-imported PyYAML in the loader), following the existing power
conventions in `tech.md`, `structure.md`, and `security.md`. Work proceeds from the
canonical Coverage_Record data file, to the script's pure logic (loading, validation,
ranking, reporting, disclosure rendering), to the `argparse` CLI that wires the three
modes together, then to CI integration and the supporting test suite. Property-based
tests (Hypothesis) for the 14 correctness properties are placed next to the logic they
validate so defects surface early; smoke/example/edge tests cover the placement and
configuration criteria. All script paths are relative to the repository root; the script
resolves config/POWER.md paths relative to its own location.

## Tasks

- [x] 1. Create the Coverage_Record data file
  - [x] 1.1 Author `senzing-bootcamp/config/example-coverage.yaml`
    - Create the YAML record with `metadata`, `languages`, `topics`, and `coverage` sections per the Data Models design
    - Populate `metadata.signal_definition`, `metadata.status_meanings.available`, `metadata.status_meanings.unknown`, `metadata.maintenance`, and `metadata.snapshot.{last_observed, senzing_version}`
    - List the five Supported_Language keys (`python`, `java`, `csharp`, `rust`, `typescript`) and a non-empty set of Coverage_Topic ids, each with a human-readable `label`
    - Provide exactly one Coverage_Status (`available`/`none`/`unknown`) for every (language, topic) pair; include no MCP URLs
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 5.1, 5.3, 5.4, 8.3_

- [x] 2. Script foundation: data models and record loading
  - [x] 2.1 Create `senzing-bootcamp/scripts/example_coverage_report.py` skeleton
    - Define `VALID_STATUSES = ("available", "none", "unknown")` and the frozen dataclasses (`Snapshot`, `CoverageRecord`, `LanguageSummary`, `Report`, `Violation`)
    - Implement `load_coverage_record(path)` resolving paths relative to the script location, importing PyYAML lazily inside the function, and raising `CoverageError` on missing/unparseable/non-mapping input
    - Keep the module stdlib-only at top level (PyYAML imported only inside the loader)
    - _Requirements: 3.1, 3.2, 5.2_

  - [x] 2.2 Write unit tests for the loader
    - Add `senzing-bootcamp/tests/test_example_coverage_report_unit.py` importing the script via `sys.path` manipulation
    - Test successful load of a valid record, and error behavior for missing file, invalid YAML, and non-mapping top level
    - _Requirements: 3.7_

- [x] 3. Schema validation and language ranking
  - [x] 3.1 Implement `validate_record` and `derive_ranking`
    - `validate_record(record_data)` returns a list of `Violation`: missing (language, topic) entries, statuses outside `VALID_STATUSES`, missing snapshot fields, and topics lacking a label
    - `derive_ranking(record)` orders languages by `available` proportion descending, breaking ties by declared language order for determinism
    - _Requirements: 1.4, 1.5, 1.6, 2.4, 7.1, 7.2, 7.3_

  - [x] 3.2 Write property test for schema completeness
    - **Property 1: Schema completeness** — no completeness violation iff a coverage entry exists for every (language, topic) pair; a violation whenever any single entry is missing
    - **Validates: Requirements 1.4, 7.2**

  - [x] 3.3 Write property test for status value constraint
    - **Property 2: Status value constraint** — a violation reported iff at least one coverage entry has a status outside `{available, none, unknown}`
    - **Validates: Requirements 1.5, 7.1**

  - [x] 3.4 Write property test for required fields present
    - **Property 3: Required fields present** — a violation reported iff a required Snapshot_Metadata field is missing or any tracked topic lacks a label
    - **Validates: Requirements 1.6, 2.4, 7.3**

- [x] 4. Report computation and rendering
  - [x] 4.1 Implement `build_report`, `render_report_text`, and `render_report_json`
    - `build_report(record)` computes per-language status counts, the `none`/`unknown` gap list, and `available_proportion` (0.0 when no topics, never `ZeroDivisionError`)
    - `render_report_text` produces the human-readable summary including Snapshot_Metadata and the honest-scope statement (availability only; not `generate_scaffold`/`sdk_guide` quality)
    - `render_report_json` emits structured, stable-keyed output carrying per-language proportions
    - _Requirements: 3.4, 3.5, 3.8, 6.3, 8.1, 8.2_

  - [x] 4.2 Write property test for per-language status counts
    - **Property 5: Per-language status counts are exhaustive and accurate** — per-language counts sum to the topic count and each per-status count is exact
    - **Validates: Requirements 3.4**

  - [x] 4.3 Write property test for the gap list
    - **Property 6: Gap list equals the none/unknown topics** — listed gaps equal exactly the topics whose status is `none` or `unknown`
    - **Validates: Requirements 3.5**

  - [x] 4.4 Write property test for available proportion
    - **Property 7: Available proportion is the available fraction** — equals (available topics) ÷ (tracked topics) and lies within [0, 1]
    - **Validates: Requirements 8.1**

  - [x] 4.5 Write property test for JSON proportion round-trip
    - **Property 8: JSON report proportions round-trip** — parsing `--format json` output yields per-language proportions equal to those from `build_report`
    - **Validates: Requirements 8.2**

  - [x] 4.6 Write property test for report content
    - **Property 9: Report content includes snapshot metadata and honest-scope statement** — rendered report contains both snapshot values and the supplementary-availability-only scope statement
    - **Validates: Requirements 3.8, 6.3**

- [x] 5. Disclosure region rendering and verification
  - [x] 5.1 Add the `example-coverage` generated region to `POWER.md`
    - Insert the `<!-- BEGIN GENERATED: example-coverage -->` / `<!-- END GENERATED: example-coverage -->` marker pair (initially empty body) using the same scheme as `generate_power_docs.py`
    - Leave all other `POWER.md` content unchanged
    - _Requirements: 4.3_

  - [x] 5.2 Implement `render_disclosure`, `write_disclosure_region`, and `check_disclosure`
    - `render_disclosure(record)` builds the deterministic Markdown body: names the top-ranked language(s) by `available` proportion, states the signal reflects supplementary example availability only, and states `generate_scaffold`/`sdk_guide` are equivalent across languages
    - `write_disclosure_region(power_md, body)` replaces only the text between the markers via atomic temp-file + `os.replace`; raise a marker error if markers are missing/unpaired
    - `check_disclosure(power_md, record)` compares the committed region body to `render_disclosure(record)` and returns a drift `Violation` on mismatch
    - _Requirements: 4.1, 4.2, 4.4, 6.1, 6.2_

  - [x] 5.3 Write property test for disclosure content
    - **Property 10: Disclosure content states scope, equivalence, and names the top-ranked language** — body contains the availability-only scope statement, the equivalence statement, and the highest-ranked language(s)
    - **Validates: Requirements 4.1, 6.1, 6.2**

  - [x] 5.4 Write property test for render/check round-trip
    - **Property 11: Disclosure render/check round-trip is drift-free** — writing the region from a record then checking against the same record reports no drift
    - **Validates: Requirements 4.1**

  - [x] 5.5 Write property test for drift detection
    - **Property 12: Disclosure drift is detected** — mutating the region to an inconsistent ranking causes `check_disclosure` to report drift and `main(["--check"])` to exit non-zero
    - **Validates: Requirements 4.2**

  - [x] 5.6 Write property test for scoped write
    - **Property 13: Disclosure write is scoped to the generated region** — writing changes only the bytes strictly between the markers and leaves all other document bytes unchanged
    - **Validates: Requirements 4.4**

- [x] 6. CLI wiring (report / json / write / check modes)
  - [x] 6.1 Implement `main(argv=None)` and `if __name__ == "__main__"` entry point
    - Add `argparse` options `--format {text,json}`, `--write`, `--check`, `--record PATH`, `--power-md PATH`
    - Dispatch: default/`--format json` prints the report; `--write` regenerates the `POWER.md` disclosure region from the record; `--check` runs schema validation plus disclosure consistency (Coverage_Validator)
    - Return 0 on success and 1 on any error/violation; write descriptive errors to stderr; on drift print the `--write` regeneration command
    - Run `--write` once to populate the region created in 5.1 from the committed record
    - _Requirements: 3.3, 3.6, 3.7, 4.2, 4.3, 7.4, 8.2_

  - [x] 6.2 Write property test for the check exit code
    - **Property 4: Validation result drives the check exit code** — `main(["--check"])` exits non-zero with a non-empty message when a schema violation exists, and 0 when valid and consistent
    - **Validates: Requirements 7.4**

  - [x] 6.3 Write property test for report-mode exit codes
    - **Property 14: Report-mode exit codes** — `main([])` exits 0 for a schema-valid record; missing path or unparseable content yields exit 1 after a non-empty error message
    - **Validates: Requirements 3.6, 3.7**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. CI integration
  - [x] 8.1 Wire the Coverage_Validator into `.github/workflows/validate-power.yml`
    - Add a step (alongside the other validators, e.g. after the `generate_power_docs.py --verify` step) that runs `python senzing-bootcamp/scripts/example_coverage_report.py --check`
    - _Requirements: 7.5_

- [x] 9. Smoke, example, and edge tests
  - [x] 9.1 Write smoke/placement tests
    - In `test_example_coverage_report_unit.py`: assert the record exists at `config/example-coverage.yaml` with `.yaml` snake_case naming; the script exists at `scripts/example_coverage_report.py`; only stdlib + lazily-imported PyYAML at module top level; the script makes no MCP/network calls; the record contains no MCP URL substring; the workflow runs `example_coverage_report.py --check`; `POWER.md` contains the `example-coverage` markers
    - _Requirements: 1.1, 1.7, 3.1, 3.2, 4.3, 5.2, 5.3, 7.5, 7.6_

  - [x] 9.2 Write example/edge tests
    - In `test_example_coverage_report_unit.py`: assert the committed record lists the expected Supported_Languages and a non-empty topic set; `signal_definition` references `find_examples`; `status_meanings.available`/`.unknown` and `metadata.maintenance` are present and non-empty; `main(argv=...)` accepts explicit argv and `--help` works; snapshot is a single current object
    - _Requirements: 1.2, 1.3, 2.1, 2.2, 2.3, 3.3, 5.4, 8.3_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation tasks are never optional.
- Each task references specific requirements (granular sub-requirements) for traceability.
- Property tests use Hypothesis at >= 100 examples each, one test per correctness property, carrying a `# Feature: language-example-coverage, Property {n}: ...` tag comment, and live in `senzing-bootcamp/tests/test_example_coverage_report_properties.py`.
- Smoke/example/edge tests live in `senzing-bootcamp/tests/test_example_coverage_report_unit.py`.
- Checkpoints ensure incremental validation; run the suite with `python -m pytest senzing-bootcamp/tests/ -v`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "5.1"] },
    { "id": 1, "tasks": ["3.1"] },
    { "id": 2, "tasks": ["4.1", "3.2"] },
    { "id": 3, "tasks": ["5.2", "3.3"] },
    { "id": 4, "tasks": ["6.1", "3.4"] },
    { "id": 5, "tasks": ["4.2", "8.1"] },
    { "id": 6, "tasks": ["4.3", "2.2"] },
    { "id": 7, "tasks": ["4.4", "9.1"] },
    { "id": 8, "tasks": ["4.5", "9.2"] },
    { "id": 9, "tasks": ["4.6"] },
    { "id": 10, "tasks": ["5.3"] },
    { "id": 11, "tasks": ["5.4"] },
    { "id": 12, "tasks": ["5.5"] },
    { "id": 13, "tasks": ["5.6"] },
    { "id": 14, "tasks": ["6.2"] },
    { "id": 15, "tasks": ["6.3"] }
  ]
}
```
