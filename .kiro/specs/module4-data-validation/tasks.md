# Implementation Plan: Module 4 Data Validation

## Overview

Implement an automated data file validator for Module 4 of the Senzing bootcamp. The validator script (`senzing-bootcamp/scripts/validate_data_files.py`) checks file existence/readability, format recognition, record presence, and encoding validity. Results are reported with pass/fail indicators and remediation guidance. The CLI supports `--update-registry` and `--json` flags. Property-based tests validate the core logic using Hypothesis.

## Tasks

- [x] 1. Create data structures and existence check
  - [x] 1.1 Create `senzing-bootcamp/scripts/validate_data_files.py` with `CheckResult` and `ValidationReport` dataclasses, including the `failed_checks` and `failure_count` properties on `ValidationReport`, and the `RECOGNIZED_FORMATS` mapping and `FALLBACK_ENCODINGS` list as module-level constants
    - Define `CheckResult(name, status, message, remediation, details)` and `ValidationReport(file_path, file_name, format, record_count, encoding, checks, overall_status)`
    - _Requirements: 5.1_
  - [x] 1.2 Implement `check_existence(file_path: str) -> CheckResult` that checks file exists, is readable (open for reading), and has size > 0 bytes — returning fail with the exact message and remediation text from requirements for each failure condition
    - Check order: exists → readable → non-zero size
    - Fail messages: "File not found at path: {file_path}", "File exists but cannot be opened for reading: {file_path}", "File is empty (0 bytes): {file_path}"
    - Remediation per Requirement 6.1, 6.2, 6.3
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1, 6.2, 6.3_

- [x] 2. Implement format and record checks
  - [x] 2.1 Implement `check_format(file_path: str) -> CheckResult` that determines format from file extension (case-insensitive), validates against `RECOGNIZED_FORMATS`, and for text formats (csv, json, jsonl, xml, tsv) attempts to parse content to confirm format match — returning fail with exact messages and remediation for unrecognized or mismatched formats
    - Extension matching: `Path(file_path).suffix.lower()`
    - Content validation: `csv.reader` for csv/tsv, `json.loads` for json, first-line `json.loads` for jsonl, `xml.etree.ElementTree.fromstring` for xml
    - Binary formats (xlsx, parquet): extension match only, skip content parsing
    - Fail messages per Requirement 2.3, 2.5; remediation per Requirement 6.4, 6.5
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.4, 6.5_
  - [x] 2.2 Implement `check_records(file_path: str, detected_format: str) -> CheckResult` that counts data records based on format — CSV/TSV rows excluding header, JSON array length or 1 for object, JSONL non-empty lines, XML direct children of root — returning fail if zero records, pass with record count otherwise
    - Binary formats (xlsx, parquet): return pass with message indicating count is skipped (no stdlib parser)
    - Fail message: "File contains no data records"; remediation per Requirement 6.6
    - Pass details: `{"record_count": N}`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 6.6_

- [x] 3. Implement encoding check and orchestrator
  - [x] 3.1 Implement `check_encoding(file_path: str, detected_format: str) -> CheckResult` that for text formats reads the first 8192 bytes and attempts UTF-8 decode, then falls back to latin-1, utf-16, cp1252 — returning pass for UTF-8, warn with conversion command for alternative encodings, fail if no encoding works, and pass (skip) for binary formats
    - UTF-8 pass details: `{"encoding": "utf-8"}`
    - Warn message per Requirement 4.4 with conversion command
    - Fail message per Requirement 4.5; remediation per Requirement 6.7
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 6.7_
  - [x] 3.2 Implement `validate_file(file_path: str) -> ValidationReport` that runs checks in order (existence → format → records → encoding), skipping downstream checks when existence or format fails, and assembles a `ValidationReport` with overall_status set to "pass" only if all checks are pass or warn
    - Populate `format`, `record_count`, `encoding` fields from check details
    - _Requirements: 5.1, 10.6_

- [x] 4. Implement report formatting and CLI
  - [x] 4.1 Implement `format_report_text(report: ValidationReport) -> str` that formats a report with ✅/❌/⚠️ indicators — pass summary as "✅ {file_name}: All checks passed ({record_count} records, {format}, {encoding})", fail summary as "❌ {file_name}: {failure_count} check(s) failed — see details below" followed by individual failures with remediation prefixed by "→"
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  - [x] 4.2 Implement `format_report_json(reports: list[ValidationReport]) -> str` that serializes reports as a JSON array with file_path, file_name, format, record_count, encoding, overall_status, and checks array (each with name, status, message)
    - _Requirements: 8.6_
  - [x] 4.3 Implement `main(argv)` with argparse: no args scans `data/raw/`, positional args validate specific files, `--update-registry` updates the registry, `--json` outputs JSON — exit 0 if all pass, exit 1 if any fail
    - Handle missing `data/raw/` directory and empty directory cases
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 8.6_

- [x] 5. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement registry update
  - [x] 6.1 Implement `update_registry(reports, registry_path)` that imports `parse_registry_yaml` and `serialize_registry_yaml` from `data_sources.py`, reads the existing registry (or creates one with `version: "1"` and empty `sources`), and for each report updates the corresponding entry with `validation_status`, `validation_checks` mapping, `record_count`, `encoding`, and `updated_at` timestamp
    - Derive DATA_SOURCE key from file name (uppercase, replace non-alphanumeric with underscore)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  - [x] 6.2 Write unit tests for registry update: verify new registry creation, existing entry update, validation fields written correctly, updated_at timestamp set
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 7. Update Module 4 steering file
  - [x] 7.1 Update `senzing-bootcamp/steering/module-04-data-collection.md` step 2 to add a validation sub-step instructing the agent to run `python senzing-bootcamp/scripts/validate_data_files.py <file_path> --update-registry` after each file is saved to `data/raw/`, present the report to the bootcamper, and help resolve failures before proceeding
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [x] 7.2 Update `senzing-bootcamp/steering/module-04-data-collection.md` step 7 to reference validation results already captured in the registry rather than performing manual checks
    - _Requirements: 9.5_

- [x] 8. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Property-based tests
  - [x] 9.1 Create `senzing-bootcamp/tests/test_data_validation_properties.py` with Hypothesis strategies for generating valid CSV content (header + N data rows), valid JSON arrays, valid UTF-8 strings, invalid byte sequences, and file extension case variants
    - Import check functions and dataclasses from `validate_data_files`
    - _Requirements: 10.1_
  - [x] 9.2 Write property test: valid CSV content produces correct record count
    - **Property 1: Valid CSV content produces correct record count**
    - **Validates: Requirements 3.1, 3.2, 10.2**
  - [x] 9.3 Write property test: valid JSON arrays produce correct record count
    - **Property 2: Valid JSON arrays produce correct record count**
    - **Validates: Requirements 3.3, 10.3**
  - [x] 9.4 Write property test: valid UTF-8 content passes encoding check
    - **Property 3: Valid UTF-8 content passes encoding check**
    - **Validates: Requirements 4.1, 4.2, 10.4**
  - [x] 9.5 Write property test: invalid encoding fails encoding check
    - **Property 4: Invalid encoding fails encoding check**
    - **Validates: Requirements 4.5, 10.5**
  - [x] 9.6 Write property test: overall status is pass iff all checks pass or warn
    - **Property 5: Overall status consistency**
    - **Validates: Requirements 5.1, 10.6**
  - [x] 9.7 Write property test: every failed check has non-empty remediation
    - **Property 6: Failed checks have remediation guidance**
    - **Validates: Requirements 5.3, 6.1–6.7, 10.7**
  - [x] 9.8 Write property test: format detection is case-insensitive
    - **Property 7: Format detection is case-insensitive**
    - **Validates: Requirements 2.1, 2.2**

- [x] 10. Unit tests for edge cases and CLI
  - [x] 10.1 Write unit tests for each remediation message matching exact text from requirements (file not found, not readable, empty, unrecognized format, format mismatch, no records, encoding failure)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  - [x] 10.2 Write unit tests for CLI: no args with data/raw/ containing files, positional file args, --update-registry flag, --json flag, exit code 0 for all pass, exit code 1 for any fail
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  - [x] 10.3 Write unit tests for edge cases: binary format handling (xlsx/parquet skip content and encoding checks), XML record counting, JSONL counting, JSON single object as 1 record, empty data/raw/ directory
    - _Requirements: 2.4, 3.2, 3.3, 3.4, 3.5, 4.6_

- [x] 11. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The validator uses Python stdlib only (no external dependencies) per project conventions
- Registry update reuses the existing YAML parser from `data_sources.py`
