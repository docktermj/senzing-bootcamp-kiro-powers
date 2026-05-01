# Requirements Document

## Introduction

Module 4 collects data source files into `data/raw/` but performs no validation on those files before the bootcamper moves to Module 5 (data quality and mapping). A bootcamper who collects a corrupt file, a file with encoding issues, or a file in an unrecognized format will not discover the problem until Module 5 — wasting time and creating confusion. This feature adds an automated sanity check that runs immediately after each data source is collected in Module 4. The check verifies that the file exists and is readable, the format is recognized, the file contains at least one record, and the encoding is valid. Results are reported to the bootcamper with clear pass/fail indicators, failing checks include remediation guidance, and the data source registry (`config/data_sources.yaml`) is updated with validation outcomes.

## Glossary

- **Validator**: The Python module at `senzing-bootcamp/scripts/validate_data_files.py` that performs sanity checks on collected data source files.
- **Sanity_Check**: A single validation operation performed by the Validator against a data source file. Each Sanity_Check produces a pass or fail result.
- **Validation_Report**: The structured output of all Sanity_Checks for a single data source file, containing the file path, individual check results, an overall pass/fail status, and remediation guidance for any failures.
- **Registry**: The YAML file at `config/data_sources.yaml` in the bootcamper's project directory that stores metadata for every data source tracked by the bootcamp.
- **Registry_Entry**: A single data source record within the Registry, keyed by the DATA_SOURCE name.
- **Agent**: The AI agent running the bootcamp, guided by steering files and hooks.
- **Recognized_Format**: A file format the Validator can parse and inspect for records. The set of Recognized_Formats is: `csv`, `json`, `jsonl`, `xml`, `xlsx`, `parquet`, and `tsv`.
- **Module_4_Steering_File**: The steering file at `senzing-bootcamp/steering/module-04-data-collection.md` that guides the agent through data collection.
- **Bootcamper**: The developer working through the Senzing bootcamp.

## Requirements

### Requirement 1: File Existence and Readability Check

**User Story:** As a bootcamper, I want the system to verify that a collected data file exists and is readable, so that I catch missing or permission-locked files immediately after collection.

#### Acceptance Criteria

1. WHEN the Validator receives a file path, THE Validator SHALL check that the file exists at the specified path
2. WHEN the Validator receives a file path for an existing file, THE Validator SHALL check that the file is readable by attempting to open it for reading
3. WHEN the Validator receives a file path for an existing file, THE Validator SHALL check that the file size is greater than zero bytes
4. IF the file does not exist, THEN THE Validator SHALL return a Sanity_Check result of fail with the message "File not found at path: {file_path}"
5. IF the file exists but is not readable, THEN THE Validator SHALL return a Sanity_Check result of fail with the message "File exists but cannot be opened for reading: {file_path}"
6. IF the file exists but has zero bytes, THEN THE Validator SHALL return a Sanity_Check result of fail with the message "File is empty (0 bytes): {file_path}"

### Requirement 2: Format Recognition Check

**User Story:** As a bootcamper, I want the system to verify that a collected data file is in a recognized format, so that I know the file can be processed by downstream modules.

#### Acceptance Criteria

1. WHEN the Validator checks a file, THE Validator SHALL determine the file format by inspecting the file extension (case-insensitive)
2. THE Validator SHALL recognize the following extensions as Recognized_Formats: `.csv`, `.json`, `.jsonl`, `.xml`, `.xlsx`, `.parquet`, `.tsv`
3. IF the file extension does not match any Recognized_Format, THEN THE Validator SHALL return a Sanity_Check result of fail with the message "Unrecognized file format: {extension}. Supported formats: csv, json, jsonl, xml, xlsx, parquet, tsv"
4. WHEN the file extension matches a Recognized_Format, THE Validator SHALL attempt to parse the first portion of the file to confirm the content matches the declared format
5. IF the file extension matches a Recognized_Format but the content cannot be parsed as that format, THEN THE Validator SHALL return a Sanity_Check result of fail with the message "File extension is {extension} but content does not match expected format"

### Requirement 3: Record Presence Check

**User Story:** As a bootcamper, I want the system to verify that a collected data file contains at least one data record, so that I do not proceed with an empty dataset.

#### Acceptance Criteria

1. WHEN the Validator checks a file with a Recognized_Format, THE Validator SHALL count the number of data records in the file
2. FOR CSV and TSV files, THE Validator SHALL count rows excluding the header row as data records
3. FOR JSON files, THE Validator SHALL count top-level array elements as data records, or count the file as one record if the top-level value is an object
4. FOR JSONL files, THE Validator SHALL count non-empty lines as data records
5. FOR XML files, THE Validator SHALL count direct child elements of the root element as data records
6. IF the file contains zero data records, THEN THE Validator SHALL return a Sanity_Check result of fail with the message "File contains no data records"
7. WHEN the file contains one or more data records, THE Validator SHALL include the record count in the Sanity_Check result

### Requirement 4: Encoding Validation Check

**User Story:** As a bootcamper, I want the system to verify that a collected data file uses valid encoding, so that I avoid garbled text and parsing errors in later modules.

#### Acceptance Criteria

1. WHEN the Validator checks a text-based file (csv, json, jsonl, xml, tsv), THE Validator SHALL attempt to decode the file content as UTF-8
2. WHEN the file decodes successfully as UTF-8, THE Validator SHALL return a Sanity_Check result of pass with encoding reported as "utf-8"
3. IF the file fails to decode as UTF-8, THEN THE Validator SHALL attempt to detect the actual encoding by reading the first 8192 bytes and testing common encodings (latin-1, utf-16, cp1252)
4. IF an alternative encoding is detected, THEN THE Validator SHALL return a Sanity_Check result of pass with a warning: "File uses {detected_encoding} encoding. UTF-8 is recommended. Consider converting with: python -c \"open('output.csv','w',encoding='utf-8').write(open('{file_path}',encoding='{detected_encoding}').read())\""
5. IF no valid encoding can be determined, THEN THE Validator SHALL return a Sanity_Check result of fail with the message "Unable to determine file encoding. The file may be corrupted or use an unsupported encoding"
6. THE Validator SHALL skip encoding checks for binary formats (xlsx, parquet)

### Requirement 5: Validation Report Output

**User Story:** As a bootcamper, I want clear pass/fail results after each data file is validated, so that I immediately know whether my collected data is usable.

#### Acceptance Criteria

1. WHEN the Validator completes all Sanity_Checks for a file, THE Validator SHALL produce a Validation_Report containing: the file path, the file format, the record count (if determined), the encoding (if determined), a list of individual Sanity_Check results each with a status (pass, fail, or warn) and a message, and an overall status (pass if all checks pass, fail if any check fails)
2. WHEN the Agent presents a Validation_Report to the Bootcamper, THE Agent SHALL use clear visual indicators: ✅ for pass, ❌ for fail, and ⚠️ for warn
3. WHEN a Validation_Report contains one or more failed Sanity_Checks, THE Agent SHALL present remediation guidance for each failure explaining how to fix the issue
4. WHEN a Validation_Report has an overall status of pass, THE Agent SHALL display a summary line: "✅ {file_name}: All checks passed ({record_count} records, {format}, {encoding})"
5. WHEN a Validation_Report has an overall status of fail, THE Agent SHALL display a summary line: "❌ {file_name}: {failure_count} check(s) failed — see details below" followed by the individual failure messages and remediation guidance

### Requirement 6: Remediation Guidance for Failures

**User Story:** As a bootcamper, I want actionable guidance when a validation check fails, so that I can fix the problem without searching for solutions.

#### Acceptance Criteria

1. WHEN a file-not-found Sanity_Check fails, THE Validator SHALL include remediation guidance: "Re-upload or re-download the file. Verify the file path is correct and the file was saved to data/raw/"
2. WHEN a file-not-readable Sanity_Check fails, THE Validator SHALL include remediation guidance: "Check file permissions. On Linux/macOS run: chmod 644 {file_path}"
3. WHEN an empty-file Sanity_Check fails, THE Validator SHALL include remediation guidance: "The file has no content. Re-download or re-export the data from the original source"
4. WHEN a format-unrecognized Sanity_Check fails, THE Validator SHALL include remediation guidance: "Convert the file to one of the supported formats (CSV, JSON, JSONL, XML) before proceeding. See Module 4 steering for format conversion guidance"
5. WHEN a format-mismatch Sanity_Check fails, THE Validator SHALL include remediation guidance: "The file content does not match the {extension} extension. Verify the file was exported correctly, or rename it with the correct extension"
6. WHEN a no-records Sanity_Check fails, THE Validator SHALL include remediation guidance: "The file structure is valid but contains no data rows. Re-export with data included, or check that the export query/filter returned results"
7. WHEN an encoding Sanity_Check fails, THE Validator SHALL include remediation guidance: "The file may be corrupted. Re-download from the original source, or try opening it in a text editor to check for garbled characters"

### Requirement 7: Registry Update with Validation Results

**User Story:** As a bootcamper, I want validation results stored in the data source registry, so that the agent and CLI tools can reference validation status in later modules.

#### Acceptance Criteria

1. WHEN the Validator completes validation for a data source file, THE Agent SHALL update the corresponding Registry_Entry with a `validation_status` field set to `passed` or `failed`
2. WHEN the Validator completes validation, THE Agent SHALL update the Registry_Entry with a `validation_checks` field containing a mapping of check names to their results (pass, fail, or warn)
3. WHEN the Validator determines the record count, THE Agent SHALL update the Registry_Entry `record_count` field with the validated count
4. WHEN the Validator determines the encoding, THE Agent SHALL update the Registry_Entry with an `encoding` field set to the detected encoding string
5. WHEN the Agent updates a Registry_Entry with validation results, THE Agent SHALL update the `updated_at` timestamp to the current ISO 8601 value
6. IF the Registry file does not exist when validation completes, THEN THE Agent SHALL create the Registry file with `version: "1"` and an empty `sources` mapping before adding the validation results

### Requirement 8: Validate-Data-Files Script

**User Story:** As a bootcamper, I want a standalone script to validate data files on demand, so that I can re-run validation without starting an agent session.

#### Acceptance Criteria

1. THE Validator SHALL be located at `senzing-bootcamp/scripts/validate_data_files.py` and SHALL be executable as `python senzing-bootcamp/scripts/validate_data_files.py` from the repository root with no external dependencies beyond the Python standard library
2. WHEN the Validator is run with no arguments, THE Validator SHALL scan all files in `data/raw/` and validate each one, printing a Validation_Report for each file
3. WHEN the Validator is run with one or more file path arguments, THE Validator SHALL validate only the specified files
4. WHEN the Validator is run with a `--update-registry` flag, THE Validator SHALL update the Registry with validation results for each validated file
5. THE Validator SHALL exit with status code 0 if all validated files pass, and exit with a non-zero status code if any file fails validation
6. WHEN the Validator is run with a `--json` flag, THE Validator SHALL output Validation_Reports as a JSON array instead of formatted text

### Requirement 9: Module 4 Steering File Integration

**User Story:** As a power developer, I want the Module 4 steering file to instruct the agent to run validation after each data source is collected, so that validation happens automatically as part of the collection workflow.

#### Acceptance Criteria

1. THE Module_4_Steering_File SHALL include a validation sub-step within step 2 (data collection) that instructs the Agent to run the Validator on each newly collected file immediately after it is saved to `data/raw/`
2. THE Module_4_Steering_File SHALL instruct the Agent to present the Validation_Report to the Bootcamper after each file is validated
3. THE Module_4_Steering_File SHALL instruct the Agent to update the Registry with validation results using the `--update-registry` flag
4. IF a validation fails, THE Module_4_Steering_File SHALL instruct the Agent to help the Bootcamper resolve the issue before proceeding to the next data source
5. THE Module_4_Steering_File SHALL update step 7 (verify data quality at a glance) to reference the validation results already captured, rather than performing manual checks

### Requirement 10: Property-Based Tests for Validator

**User Story:** As a power developer, I want property-based tests for the validation logic, so that the Validator handles a wide range of file contents and edge cases correctly.

#### Acceptance Criteria

1. THE test file SHALL be located at `senzing-bootcamp/tests/test_data_validation_properties.py` and SHALL use pytest and Hypothesis
2. FOR ALL valid CSV content generated by Hypothesis (header row plus one or more data rows), THE Validator SHALL return a Sanity_Check result of pass for the record-presence check and the record count SHALL equal the number of generated data rows
3. FOR ALL valid JSON arrays generated by Hypothesis (containing one or more objects), THE Validator SHALL return a Sanity_Check result of pass for the record-presence check and the record count SHALL equal the array length
4. FOR ALL valid UTF-8 strings generated by Hypothesis, WHEN written to a file, THE Validator SHALL return a Sanity_Check result of pass for the encoding check with encoding reported as "utf-8"
5. FOR ALL byte sequences generated by Hypothesis that are not valid UTF-8 and not valid in any fallback encoding, THE Validator SHALL return a Sanity_Check result of fail for the encoding check
6. FOR ALL Validation_Reports produced by the Validator, THE overall status SHALL be "pass" if and only if every individual Sanity_Check status is "pass" or "warn"
7. FOR ALL Validation_Reports with at least one failed Sanity_Check, THE Validation_Report SHALL contain a non-empty remediation guidance string for each failed check
