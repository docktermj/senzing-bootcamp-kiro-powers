# Requirements Document

## Introduction

Module 3 of the Senzing Bootcamp is redesigned from "Quick Demo" to "System Verification." Its purpose is to serve as a gate that confirms the bootcamper's entire development environment works end-to-end before proceeding to real work in subsequent modules. The module always uses the Senzing TruthSet — a deterministic dataset with known-good expected outputs — so that verification checks can validate specific, predictable results rather than merely confirming "something happened." The verification covers SDK initialization, MCP-driven code generation, compilation/build, execution, data loading, entity resolution with expected results, and web service scaffolding with a rendered web page.

## Glossary

- **System_Verification_Module**: Module 3 of the Senzing Bootcamp, responsible for confirming the bootcamper's environment is fully functional before proceeding to subsequent modules.
- **TruthSet**: The Senzing TruthSet — a curated, deterministic dataset with known entities, known matches, and predictable resolution outcomes used exclusively by Module 3 for verification.
- **Verification_Script**: The generated SDK program that loads TruthSet data, performs entity resolution, and produces results for validation.
- **Code_Generator**: The Senzing MCP server's `generate_scaffold` tool that produces SDK code in the bootcamper's chosen language.
- **Verification_Web_Service**: A sample web service generated during system verification that serves entity resolution results via HTTP endpoints and a web page.
- **Expected_Results**: The predetermined entity resolution outcomes from the TruthSet — specific entity counts, known matched record pairs, and known relationship patterns that verification checks validate against.
- **Verification_Report**: A structured summary produced at the end of Module 3 listing each verification step, its pass/fail status, and any remediation instructions for failures.
- **Chosen_Language**: The programming language selected by the bootcamper during onboarding (Python, Java, C#, Rust, or TypeScript).
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that generates SDK code, provides documentation, and supports interactive workflows.
- **Build_Step**: The language-appropriate compilation or build command (e.g., `javac`, `dotnet build`, `cargo build`, `tsc`) that transforms generated source code into an executable artifact.

## Requirements

### Requirement 1: TruthSet Data Acquisition

**User Story:** As a bootcamper, I want Module 3 to always use the Senzing TruthSet data, so that verification results are deterministic and I can confirm my system produces the correct expected outputs.

#### Acceptance Criteria

1. WHEN Module 3 begins data acquisition, THE System_Verification_Module SHALL call the MCP_Server `get_sample_data` tool to retrieve the TruthSet without offering the bootcamper a choice of datasets.
2. WHEN the TruthSet retrieval succeeds, THE System_Verification_Module SHALL save the TruthSet data to `src/system_verification/truthset_data.jsonl`, overwriting any previously existing file at that path.
3. WHEN the TruthSet file is saved, THE System_Verification_Module SHALL validate that the file contains one valid JSON object per line and that the total line count matches the record count reported by the MCP_Server response before proceeding to data loading.
4. IF the TruthSet retrieval fails due to network error, timeout exceeding 30 seconds, or an MCP_Server error response, THEN THE System_Verification_Module SHALL display an error message identifying the failure reason (network unreachable, timeout, or server error) and suggest troubleshooting steps (check MCP connectivity, verify MCP_Server is reachable at `mcp.senzing.com`, retry).
5. IF the saved TruthSet file fails validation because the line count does not match the expected record count or any line is not valid JSON, THEN THE System_Verification_Module SHALL display an error message identifying which validation failed and SHALL NOT proceed to data loading.

### Requirement 2: SDK Initialization Verification

**User Story:** As a bootcamper, I want to confirm that the Senzing SDK initializes correctly and connects to the database, so that I know the SDK installation from Module 2 is functional.

#### Acceptance Criteria

1. THE System_Verification_Module SHALL generate an SDK initialization script in the Chosen_Language using the Code_Generator with the `initialize` workflow and save it to `src/system_verification/verify_init.[ext]` where `[ext]` matches the Chosen_Language file extension.
2. WHEN the initialization script executes with exit code 0 and produces no SENZ error codes in its output within 30 seconds, THE System_Verification_Module SHALL report a pass status for the SDK initialization check in the Verification_Report confirming the SDK connected to the database at `database/G2C.db`.
3. IF the initialization script exits with a non-zero exit code or produces a SENZ error code in its output, THEN THE System_Verification_Module SHALL report a fail status with the error code (calling `explain_error_code` for any SENZ codes) and a Fix_Instruction referencing Module 2 remediation steps.
4. IF the initialization script does not complete within 30 seconds, THEN THE System_Verification_Module SHALL terminate the script process and report a fail status with a Fix_Instruction indicating a timeout and advising the bootcamper to check database accessibility and system resources.

### Requirement 3: Code Generation Verification

**User Story:** As a bootcamper, I want to confirm that the MCP server can generate SDK code in my chosen language, so that I know code generation will work for subsequent modules.

#### Acceptance Criteria

1. THE System_Verification_Module SHALL request code generation from the Code_Generator using `generate_scaffold` with the `full_pipeline` workflow in the Chosen_Language.
2. WHEN the Code_Generator returns source code, THE System_Verification_Module SHALL save the generated code to `src/system_verification/verify_pipeline.[ext]` where `[ext]` is the standard file extension for the Chosen_Language (`.py` for Python, `.java` for Java, `.cs` for C#, `.rs` for Rust, `.ts` for TypeScript).
3. THE System_Verification_Module SHALL validate that the generated source file contains at least 1 line of non-whitespace content and includes at least one language-appropriate structural element: an import statement, a function definition, or a class declaration.
4. WHEN the generated source file passes validation, THE System_Verification_Module SHALL report a pass status for the code generation check in the Verification_Report.
5. IF the Code_Generator returns an empty response, returns an error response, or does not respond within 30 seconds, THEN THE System_Verification_Module SHALL report a fail status with a Fix_Instruction advising the bootcamper to check MCP connectivity to `mcp.senzing.com:443` and retry.

### Requirement 4: Build and Compilation Verification

**User Story:** As a bootcamper, I want to confirm that generated code compiles or builds without errors, so that I know my language toolchain is correctly configured.

#### Acceptance Criteria

1. WHEN the Chosen_Language requires a Build_Step (Java, C#, Rust, TypeScript), THE System_Verification_Module SHALL execute the appropriate build command against the generated Verification_Script and enforce a timeout of 120 seconds.
2. WHEN the Build_Step completes with exit code 0, THE System_Verification_Module SHALL report a pass status for the build check in the Verification_Report.
3. IF the Build_Step fails with a non-zero exit code, THEN THE System_Verification_Module SHALL report a fail status including the first 50 lines of compiler error output and a Fix_Instruction identifying common causes (missing SDK libraries, incorrect PATH, missing build tools).
4. IF the Chosen_Language is Python, THEN THE System_Verification_Module SHALL perform a syntax check (`python -m py_compile`) instead of a full compilation step and report pass or fail status in the Verification_Report using the same exit-code criteria as the Build_Step.
5. IF the Build_Step or syntax check does not complete within 120 seconds, THEN THE System_Verification_Module SHALL terminate the process and report a fail status with a Fix_Instruction indicating the build timed out and suggesting the bootcamper check for dependency resolution issues or network-dependent build steps.

### Requirement 5: Data Loading and Execution Verification

**User Story:** As a bootcamper, I want to confirm that the generated code runs successfully and loads TruthSet data into Senzing, so that I know end-to-end execution works.

#### Acceptance Criteria

1. THE System_Verification_Module SHALL execute the Verification_Script to load all TruthSet records into the Senzing database with a maximum execution timeout of 120 seconds.
2. WHEN the Verification_Script completes with exit code 0, THE System_Verification_Module SHALL report the number of records loaded and confirm it exactly matches the expected TruthSet record count retrieved during data acquisition.
3. WHILE the Verification_Script is executing, THE System_Verification_Module SHALL display a progress indicator updated at least every 5 seconds showing the number of records processed out of the total expected.
4. IF the Verification_Script encounters an error during execution, THEN THE System_Verification_Module SHALL capture the error output, call `explain_error_code` for any SENZ error codes, and report a fail status with the remediation guidance returned by `explain_error_code`.
5. IF the Verification_Script loads fewer records than the expected TruthSet record count without raising an error, THEN THE System_Verification_Module SHALL report a fail status identifying the number of records successfully loaded versus expected and instruct the bootcamper to check the TruthSet data file integrity.
6. IF the Verification_Script does not complete within 120 seconds, THEN THE System_Verification_Module SHALL terminate the script process and report a fail status indicating the execution timed out.

### Requirement 6: Deterministic Results Validation

**User Story:** As a bootcamper, I want the system verification to check for specific expected entity resolution outcomes from the TruthSet, so that I have confidence the SDK is resolving entities correctly — not just running without errors.

#### Acceptance Criteria

1. WHEN data loading completes, THE System_Verification_Module SHALL retrieve the Expected_Results for the TruthSet from the MCP_Server and compare the resolved entity outcomes against those expected values.
2. WHEN validating entity count, THE System_Verification_Module SHALL verify that the total number of resolved entities falls within a tolerance of plus or minus 5% of the expected entity count defined in the Expected_Results.
3. WHEN validating known matches, THE System_Verification_Module SHALL verify that at least three known entity matches defined in the Expected_Results are correctly resolved, confirming that the specific records designated as matching resolve to the same entity ID.
4. WHEN validating cross-record resolution, THE System_Verification_Module SHALL verify that the resolved entity count is strictly less than the total record count loaded, confirming that at least some records merged rather than all loading as singletons.
5. THE System_Verification_Module SHALL execute all validation checks (entity count, known matches, cross-record resolution) regardless of whether earlier checks pass or fail, so that the full set of results is reported together.
6. IF any validation check fails (entity count outside tolerance, fewer than three known matches resolved correctly, or entity count equals record count), THEN THE System_Verification_Module SHALL report a fail status listing each failed check with its expected versus actual value and suggest re-running data loading or checking that the TruthSet file was loaded completely.

### Requirement 7: Web Service Scaffolding Verification

**User Story:** As a bootcamper, I want Module 3 to generate and start a sample web service, so that I know my environment can serve HTTP endpoints — a capability needed in later modules.

#### Acceptance Criteria

1. THE System_Verification_Module SHALL generate a web service in the Chosen_Language using the Code_Generator that exposes at least two HTTP endpoints: a health check endpoint and an entity query endpoint.
2. THE System_Verification_Module SHALL save the web service code to `src/system_verification/web_service/`.
3. WHEN the web service is started, THE System_Verification_Module SHALL verify the health check endpoint responds on the configured localhost port with an HTTP 200 status within 10 seconds of the service process launching.
4. WHEN the entity query endpoint is called with a known TruthSet entity identifier, THE System_Verification_Module SHALL verify the endpoint returns an HTTP 200 response containing the entity's resolved record data (entity ID and at least one constituent record) within 10 seconds.
5. IF the web service fails to start or respond within 10 seconds, THEN THE System_Verification_Module SHALL report a fail status with a Fix_Instruction identifying common causes (port conflict, missing dependencies, firewall).

### Requirement 8: Web Page Rendering Verification

**User Story:** As a bootcamper, I want Module 3 to generate a web page that displays entity resolution results, so that I know my environment supports the visualization workflows used in later modules.

#### Acceptance Criteria

1. THE System_Verification_Module SHALL generate an HTML page that displays TruthSet entity resolution results served by the Verification_Web_Service.
2. THE System_Verification_Module SHALL save the HTML page to `src/system_verification/web_service/static/index.html` and verify the saved file is non-empty and contains valid HTML structure (a `<html>` root element with `<head>` and `<body>` sections).
3. THE web page SHALL display a summary section containing: total records loaded (numeric value), total entities created (numeric value), and match rate expressed as a percentage calculated by (1 - total entities / total records) × 100.
4. THE web page SHALL display at least one resolved entity with a minimum of 2 constituent records, demonstrating that multiple TruthSet records resolved to a single entity by showing each record's data source and record identifier.
5. WHEN the web page is served by the Verification_Web_Service, THE System_Verification_Module SHALL verify the page is accessible by issuing an HTTP GET request to the configured localhost URL (default `http://localhost:8080/`) and confirming an HTTP 200 response is received within 10 seconds.
6. IF the web page accessibility check fails (non-200 response, connection refused, or timeout exceeded), THEN THE System_Verification_Module SHALL report a fail status with a Fix_Instruction identifying common causes (web service not started, port conflict, missing static file) and suggest the bootcamper verify the Verification_Web_Service is running.

### Requirement 9: Database Operations Verification

**User Story:** As a bootcamper, I want to confirm that read and write operations to the Senzing database work correctly, so that I know the database layer is functional for subsequent modules.

#### Acceptance Criteria

1. THE System_Verification_Module SHALL verify write operations by confirming that the record count returned by the Senzing engine matches the TruthSet record count established during data loading (Requirement 5), completing within 30 seconds.
2. THE System_Verification_Module SHALL verify read operations by retrieving a known entity from the Expected_Results by entity ID and confirming the response contains at least the entity ID, one constituent record key (data source and record ID pair), and one name attribute from the original TruthSet input.
3. THE System_Verification_Module SHALL verify search operations by performing a search-by-attributes query using name and address attributes from a known TruthSet record and confirming the expected entity appears in the search results.
4. IF any database operation fails or does not return a response within 30 seconds, THEN THE System_Verification_Module SHALL report a fail status identifying which operation failed (write, read, or search), the error received, and a Fix_Instruction referencing database configuration from Module 2.

### Requirement 10: Verification Report Generation

**User Story:** As a bootcamper, I want a clear summary report at the end of Module 3 showing which verification steps passed and which failed, so that I know exactly what needs fixing before proceeding.

#### Acceptance Criteria

1. WHEN all verification steps complete, THE System_Verification_Module SHALL generate a Verification_Report listing each check with its pass or fail status in the order the checks were executed.
2. THE Verification_Report SHALL include the following checks: SDK initialization, code generation, build/compilation, data loading, deterministic results validation, web service health, web page accessibility, and database operations.
3. WHEN all checks pass, THE System_Verification_Module SHALL display a success message confirming the system is verified and ready for subsequent modules.
4. WHEN one or more checks fail, THE System_Verification_Module SHALL display each failed check with its Fix_Instructions and advise the bootcamper to resolve issues before proceeding.
5. THE System_Verification_Module SHALL persist the Verification_Report results to `config/bootcamp_progress.json` including an ISO 8601 timestamp, the pass or fail status for each check, and the Fix_Instructions for any failed checks.
6. IF verification is interrupted before all steps complete, THEN THE System_Verification_Module SHALL mark any unexecuted checks as "skipped" in the Verification_Report and persist the partial results to `config/bootcamp_progress.json`.

### Requirement 11: Module Gate Compliance

**User Story:** As a bootcamp maintainer, I want Module 3 to enforce proper gate conditions, so that bootcampers only proceed when their system is verified or they explicitly choose to skip.

#### Acceptance Criteria

1. IF Module 2 (SDK Setup) is not marked complete in `config/module-dependencies.yaml` prerequisites, THEN THE System_Verification_Module SHALL block entry to Module 3 and display a message indicating that Module 2 must be completed first.
2. WHEN the verification has been executed and the gate 3→4 condition is satisfied by completion, THE System_Verification_Module SHALL update the gate 3→4 status to "completed" within 5 seconds of the final check passing.
3. WHEN the bootcamper requests to skip Module 3, THE System_Verification_Module SHALL confirm the skip reason matches the configured `skip_if` condition ("Already familiar with Senzing"), allow skipping, and update the gate 3→4 status to "skipped."
4. WHEN Module 3 ends by either completion or skip, THE System_Verification_Module SHALL execute the `module-completion.md` workflow, which includes appending a journal entry to `docs/bootcamp_journal.md` and presenting one reflection question to the bootcamper.
5. IF the gate 3→4 status is neither "completed" nor "skipped," THEN THE System_Verification_Module SHALL prevent the bootcamper from starting Module 4.

### Requirement 12: MCP Connectivity Re-confirmation

**User Story:** As a bootcamper, I want Module 3 to confirm MCP connectivity in the context of code generation, so that I know the MCP server works for the specific operations needed in subsequent modules.

#### Acceptance Criteria

1. WHEN Module 3 begins, THE System_Verification_Module SHALL verify MCP_Server connectivity by calling `search_docs` with a lightweight query and confirming a response (including empty results) is received within 10 seconds.
2. IF the initial MCP connectivity check fails (timeout or error), THEN THE System_Verification_Module SHALL retry the `search_docs` call once before reporting failure.
3. WHEN MCP connectivity is confirmed on the first attempt or the retry, THE System_Verification_Module SHALL proceed to code generation without displaying any connectivity status to the bootcamper.
4. IF MCP connectivity fails after the retry attempt, THEN THE System_Verification_Module SHALL display troubleshooting steps (verify internet connectivity, test `mcp.senzing.com:443` endpoint, allowlist the endpoint if behind a corporate proxy, restart MCP connection in Kiro Powers panel, verify DNS resolution) and block all further module progress until the bootcamper says "retry" and the connectivity check passes.

### Requirement 13: Cleanup After Verification

**User Story:** As a bootcamper, I want the verification artifacts to remain available for reference but clearly identified as test artifacts, so that I do not confuse them with real project work in later modules.

#### Acceptance Criteria

1. WHEN Module 3 completes successfully, THE System_Verification_Module SHALL retain all generated verification files in `src/system_verification/` for reference.
2. WHEN verification is complete, THE System_Verification_Module SHALL terminate the Verification_Web_Service process within 5 seconds by releasing the bound port and ending the process.
3. IF the Verification_Web_Service process fails to terminate within 5 seconds, THEN THE System_Verification_Module SHALL force-stop the process and report a warning to the bootcamper indicating the port may need manual release.
4. WHEN verification is complete, THE System_Verification_Module SHALL display a message to the bootcamper stating that all files in `src/system_verification/` are test-only artifacts and that real project work begins in subsequent modules.
5. WHEN verification is complete, THE System_Verification_Module SHALL purge all records loaded from the TruthSet data source from the Senzing database, resulting in zero TruthSet entities remaining while preserving any non-TruthSet database state.
6. IF the TruthSet data purge fails, THEN THE System_Verification_Module SHALL report a fail status identifying which records could not be removed and provide a Fix_Instruction advising the bootcamper to re-run cleanup or manually reset the database.
