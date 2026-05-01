# Requirements Document

## Introduction

Currently, error handling guidance in the senzing-bootcamp steering files is inconsistent. Module 2 and Module 6 Phase D reference `explain_error_code` for SENZ errors, but the remaining nine module steering files (modules 1, 3, 4, 5, 7, 8, 9, 10, 11) have no standardized error handling section. The `agent-instructions.md` file mentions loading `common-pitfalls.md` "on errors" but individual module files do not instruct the agent on how to triage errors — whether to call `explain_error_code`, load `common-pitfalls.md`, or both.

This feature adds a standard "Error Handling" section to every module steering file and a cross-module "Troubleshooting by Symptom" table to `common-pitfalls.md`, so the agent always knows what to do when errors occur regardless of which module the bootcamper is working in.

## Glossary

- **Module_Steering_File**: A Markdown file in `senzing-bootcamp/steering/` whose filename matches the pattern `module-NN-*.md` (root module files) or `module-NN-phase*.md` (phase sub-files). These files contain the step-by-step workflows that guide bootcampers through each module.
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps module numbers to their steering file paths and phase sub-files.
- **Error_Handling_Section**: A section in a Module_Steering_File with the heading `## Error Handling` that provides the agent with a decision procedure for triaging errors during that module.
- **SENZ_Error**: An error produced by the Senzing SDK whose error code matches the pattern `SENZ` followed by digits (e.g., `SENZ2027`, `SENZ0033`). These errors are diagnosable via the `explain_error_code` MCP tool.
- **Non_SENZ_Error**: Any error that does not carry a SENZ error code — including Python/Java/C# exceptions, OS-level errors, database connection failures, and general runtime errors.
- **Symptom_Table**: A Markdown table in `common-pitfalls.md` under the heading `## Troubleshooting by Symptom` that maps observable cross-module symptoms to diagnostic steps and resolutions.
- **Validator**: The pytest test suite component that reads Module_Steering_Files and checks for the presence and structure of the Error_Handling_Section.
- **Test_Suite**: The pytest and Hypothesis test file at `senzing-bootcamp/tests/test_error_handling_section_properties.py` that validates the Error_Handling_Section is present and correctly structured in every Module_Steering_File.

## Requirements

### Requirement 1: Standard Error Handling Section in Every Module Steering File

**User Story:** As a power maintainer, I want every module steering file to contain a standard Error Handling section, so that the agent always has consistent instructions for triaging errors regardless of which module the bootcamper is working in.

#### Acceptance Criteria

1. THE Error_Handling_Section SHALL appear in every root Module_Steering_File listed in the Steering_Index (modules 1 through 11)
2. THE Error_Handling_Section SHALL use the heading `## Error Handling` to maintain a consistent, searchable structure across all Module_Steering_Files
3. WHEN a Module_Steering_File has phase sub-files, THE Error_Handling_Section SHALL appear in the root Module_Steering_File only (not duplicated in each phase sub-file)

### Requirement 2: SENZ Error Triage via explain_error_code

**User Story:** As a bootcamper, I want the agent to automatically use `explain_error_code` when I encounter a SENZ error, so that I get an accurate diagnosis without needing to know which MCP tool to use.

#### Acceptance Criteria

1. THE Error_Handling_Section SHALL instruct the agent to call `explain_error_code(error_code="<code>", version="current")` when the bootcamper encounters an error whose code matches the SENZ_Error pattern
2. THE Error_Handling_Section SHALL instruct the agent to present the explanation from `explain_error_code` to the bootcamper along with the recommended fix
3. IF `explain_error_code` returns no result or an unrecognized code, THEN THE Error_Handling_Section SHALL instruct the agent to fall back to loading `common-pitfalls.md` and searching for the error code or message in the module-specific pitfall table

### Requirement 3: Non-SENZ Error Triage via common-pitfalls.md

**User Story:** As a bootcamper, I want the agent to load the common pitfalls reference when I encounter a non-SENZ error, so that I get relevant troubleshooting guidance for general runtime problems.

#### Acceptance Criteria

1. THE Error_Handling_Section SHALL instruct the agent to load `common-pitfalls.md` when the bootcamper encounters a Non_SENZ_Error
2. THE Error_Handling_Section SHALL instruct the agent to navigate to the current module's section within `common-pitfalls.md` and present only the matching pitfall and fix — not the entire document
3. IF the error does not match any entry in the module-specific pitfall table, THEN THE Error_Handling_Section SHALL instruct the agent to check the General Pitfalls section and the Troubleshooting by Symptom table

### Requirement 4: Error Handling Decision Procedure

**User Story:** As a power maintainer, I want the Error Handling section to define a clear decision procedure, so that the agent follows a deterministic triage path rather than guessing which tool to use.

#### Acceptance Criteria

1. THE Error_Handling_Section SHALL present the triage steps in this order: (a) check if the error code matches the SENZ_Error pattern, (b) if yes call `explain_error_code`, (c) if no or if `explain_error_code` returns no result then load `common-pitfalls.md`, (d) navigate to the current module section, (e) if no match found check the Troubleshooting by Symptom table and General Pitfalls section
2. THE Error_Handling_Section SHALL be concise (no more than 15 lines of Markdown) to minimize token cost when the steering file is loaded into context
3. THE Error_Handling_Section SHALL reference `common-pitfalls.md` by filename (not by inline content) to avoid duplicating pitfall data across steering files

### Requirement 5: Troubleshooting by Symptom Table in common-pitfalls.md

**User Story:** As a bootcamper, I want a symptom-based troubleshooting table in the common pitfalls reference, so that I can find help based on what I observe rather than needing to know the specific error code or module.

#### Acceptance Criteria

1. THE Symptom_Table SHALL appear in `common-pitfalls.md` under the heading `## Troubleshooting by Symptom`
2. THE Symptom_Table SHALL be placed between the Quick Navigation section and the first module-specific section, so the agent finds it before module-specific pitfalls
3. THE Symptom_Table SHALL contain rows for at least these five cross-module symptoms: "zero entities created," "loading hangs," "query returns no results," "SDK initialization fails," and "database connection fails"
4. WHEN a symptom row is present, THE Symptom_Table SHALL include three columns: Symptom, Likely Cause, and Diagnostic Steps
5. THE Diagnostic Steps column SHALL reference specific MCP tools or commands (e.g., `explain_error_code`, `search_docs`, `get_sdk_reference`) rather than vague instructions

### Requirement 6: Symptom Table Covers Cross-Module Scenarios

**User Story:** As a power maintainer, I want the symptom table to cover problems that span multiple modules, so that the agent can diagnose issues that do not fit neatly into a single module's pitfall table.

#### Acceptance Criteria

1. THE Symptom_Table row for "zero entities created" SHALL reference checking data format, DATA_SOURCE and RECORD_ID fields, and loading program output — applicable to modules 3, 5, 6, and 7
2. THE Symptom_Table row for "loading hangs" SHALL reference checking record count, database type (SQLite vs PostgreSQL), threading configuration, and system resources — applicable to modules 6 and 8
3. THE Symptom_Table row for "query returns no results" SHALL reference verifying entity IDs, checking that data was loaded, and using `get_sdk_reference(topic='flags')` for correct query flags — applicable to modules 7 and 8
4. THE Symptom_Table row for "SDK initialization fails" SHALL reference verifying `SENZING_ENGINE_CONFIGURATION_JSON`, checking CONFIGPATH/RESOURCEPATH/SUPPORTPATH, and using `explain_error_code` for the specific SENZ code — applicable to modules 2, 3, and 6
5. THE Symptom_Table row for "database connection fails" SHALL reference checking database file existence, connection string, permissions, and PostgreSQL service status — applicable to modules 2, 6, and 8

### Requirement 7: Property-Based Test for Error Handling Section Presence

**User Story:** As a power maintainer, I want a property-based test that verifies every module steering file contains the Error Handling section, so that regressions are caught automatically when new modules are added or existing files are edited.

#### Acceptance Criteria

1. THE Test_Suite SHALL use a Hypothesis strategy that draws module numbers from the set of modules defined in the Steering_Index
2. WHEN a module number is drawn, THE Test_Suite SHALL resolve the module number to its root Module_Steering_File path using the Steering_Index
3. THE Test_Suite SHALL verify that the root Module_Steering_File contains a line matching the heading `## Error Handling`
4. THE Test_Suite SHALL verify that the Error_Handling_Section contains a reference to `explain_error_code`
5. THE Test_Suite SHALL verify that the Error_Handling_Section contains a reference to `common-pitfalls.md`
6. THE Test_Suite SHALL use `@settings(max_examples=100)` for each property test
7. THE Test_Suite SHALL be located at `senzing-bootcamp/tests/test_error_handling_section_properties.py`

### Requirement 8: Property-Based Test for Symptom Table Completeness

**User Story:** As a power maintainer, I want a property-based test that verifies the Troubleshooting by Symptom table contains all required symptoms, so that missing entries are caught automatically.

#### Acceptance Criteria

1. THE Test_Suite SHALL read `common-pitfalls.md` and extract the Symptom_Table content under the `## Troubleshooting by Symptom` heading
2. THE Test_Suite SHALL use a Hypothesis strategy that draws symptom names from the set {"zero entities created", "loading hangs", "query returns no results", "SDK initialization fails", "database connection fails"}
3. WHEN a symptom name is drawn, THE Test_Suite SHALL verify that the Symptom_Table contains a row whose Symptom column includes that symptom text (case-insensitive match)
4. THE Test_Suite SHALL verify that each matched row has non-empty Likely Cause and Diagnostic Steps columns
5. THE Test_Suite SHALL use `@settings(max_examples=100)` for each property test

### Requirement 9: Steering Index as Source of Truth for Tests

**User Story:** As a power maintainer, I want the test suite to use the steering index as the authoritative source for which module files to validate, so that new modules are automatically covered without updating the test file.

#### Acceptance Criteria

1. THE Test_Suite SHALL parse the Steering_Index at `senzing-bootcamp/steering/steering-index.yaml` to discover all module numbers and their associated root file paths
2. WHEN the Steering_Index maps a module number to a simple filename string, THE Test_Suite SHALL treat that filename as the root Module_Steering_File for that module
3. WHEN the Steering_Index maps a module number to an object with a `root` key, THE Test_Suite SHALL use the `root` value as the root Module_Steering_File for that module
4. IF a root file listed in the Steering_Index does not exist on disk, THEN THE Test_Suite SHALL report a clear error rather than silently skipping the module
