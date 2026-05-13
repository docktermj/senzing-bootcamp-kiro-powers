---
inclusion: manual
---

# Module 3: System Verification

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_3_SYSTEM_VERIFICATION.md`.

**Language:** Use the bootcamper's chosen language for all code generation and verification scripts.

**Prerequisites:** Module 2 complete (SDK installed and configured)

**Before/After:** SDK installed but untested end-to-end. After: your entire system is verified — SDK initialization, code generation, compilation, data loading, entity resolution, database operations, and web service scaffolding all confirmed working.

**IMPORTANT:** This module uses the Senzing TruthSet exclusively — a deterministic dataset with known-good expected outputs. No dataset choice is offered. All verification code is generated at runtime by the MCP server, not shipped as static files.

## Phase 1: Verification Pipeline

### Step 1: MCP Connectivity Check

Verify MCP server connectivity before proceeding with code generation operations.

1. Call `search_docs(query="Senzing SDK initialization")` with a 10-second timeout.
2. **If a response is received** (including empty results): MCP connectivity confirmed. Proceed silently — do not display connectivity status to the bootcamper.
3. **If the call fails** (timeout or error): Retry `search_docs` once with the same 10-second timeout.
4. **If the retry succeeds:** Proceed silently.
5. **If the retry fails:** Display troubleshooting steps:
   - Verify internet connectivity
   - Test `mcp.senzing.com:443` endpoint
   - Allowlist the endpoint if behind a corporate proxy
   - Restart MCP connection in Kiro Powers panel
   - Verify DNS resolution

   Block all further module progress until the bootcamper says "retry" and the connectivity check passes.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "mcp_connectivity": {"status": "passed", "duration_ms": <elapsed>}
    }
  }
}
```

### Step 2: TruthSet Acquisition

Retrieve the Senzing TruthSet data for deterministic verification.

1. Call `get_sample_data` to retrieve the TruthSet. Do NOT offer the bootcamper a choice of datasets — TruthSet is always used.
2. Save the TruthSet data to `src/system_verification/truthset_data.jsonl`, overwriting any previously existing file.
3. **Validate the saved file:**
   - Confirm the file contains one valid JSON object per line
   - Confirm the total line count matches the record count reported by the MCP server response
4. **If retrieval fails** (network error, timeout exceeding 30 seconds, or MCP server error): Display an error message identifying the failure reason and suggest troubleshooting steps (check MCP connectivity, verify MCP server is reachable at `mcp.senzing.com`, retry).
5. **If validation fails** (line count mismatch or invalid JSON on any line): Display an error message identifying which validation failed. Do NOT proceed to data loading.

Store the expected record count from the MCP response — it will be used in later validation steps.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "truthset_acquisition": {"status": "passed", "records": <line_count>}
    }
  }
}
```

### Step 3: SDK Initialization

Verify the Senzing SDK initializes correctly and connects to the database.

1. Generate an SDK initialization script using `generate_scaffold(workflow='initialize')` in the bootcamper's chosen language.
2. Save the generated code to `src/system_verification/verify_init.[ext]` where `[ext]` matches the chosen language file extension (`.py`, `.java`, `.cs`, `.rs`, `.ts`).
3. Execute the initialization script with a 30-second timeout.
4. **If the script exits with code 0 and produces no SENZ error codes:** Report pass — SDK connected to the database at `database/G2C.db`.
5. **If the script exits with a non-zero exit code or produces a SENZ error code:** Report fail. Call `explain_error_code` for any SENZ codes. Generate a Fix_Instruction referencing Module 2 remediation steps.
6. **If the script does not complete within 30 seconds:** Terminate the process. Report fail with a Fix_Instruction indicating timeout — advise checking database accessibility and system resources.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "sdk_initialization": {"status": "passed|failed", "duration_ms": <elapsed>}
    }
  }
}
```

### Step 4: Code Generation

Verify the MCP server can generate a full pipeline script in the chosen language.

1. Call `generate_scaffold(workflow='full_pipeline')` in the bootcamper's chosen language.
2. Save the generated code to `src/system_verification/verify_pipeline.[ext]` where `[ext]` is the standard file extension for the chosen language.
3. **Validate the generated file:**
   - Confirm the file contains at least 1 line of non-whitespace content
   - Confirm the file includes at least one language-appropriate structural element: an import statement, a function definition, or a class declaration
4. **If validation passes:** Report pass for code generation.
5. **If the Code_Generator returns an empty response, an error, or does not respond within 30 seconds:** Report fail with a Fix_Instruction advising the bootcamper to check MCP connectivity to `mcp.senzing.com:443` and retry.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "code_generation": {"status": "passed|failed", "file": "verify_pipeline.[ext]"}
    }
  }
}
```

### Step 5: Build/Compile

Verify the generated code compiles or passes syntax checking.

Execute the appropriate build command based on the bootcamper's chosen language. Enforce a 120-second timeout for all build commands.

| Language | Build Command |
|----------|--------------|
| Python | `python -m py_compile src/system_verification/verify_pipeline.py` |
| Java | `javac src/system_verification/verify_pipeline.java` |
| C# | `dotnet build src/system_verification/` |
| Rust | `cargo build --manifest-path src/system_verification/Cargo.toml` |
| TypeScript | `tsc src/system_verification/verify_pipeline.ts --noEmit` |

1. Execute the build command for the chosen language.
2. **If the build exits with code 0:** Report pass.
3. **If the build fails** (non-zero exit code): Report fail including the first 50 lines of compiler error output. Generate a Fix_Instruction identifying common causes (missing SDK libraries, incorrect PATH, missing build tools).
4. **If the build does not complete within 120 seconds:** Terminate the process. Report fail with a Fix_Instruction indicating the build timed out — suggest checking for dependency resolution issues or network-dependent build steps.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "build_compilation": {"status": "passed|failed", "duration_ms": <elapsed>}
    }
  }
}
```

### Step 6: Data Loading

Execute the verification script to load TruthSet data into Senzing.

1. Execute the generated `verify_pipeline.[ext]` script with a 120-second timeout.
2. **While executing:** Display a progress indicator updated at least every 5 seconds showing records processed out of total expected.
3. **If the script completes with exit code 0:** Confirm the number of records loaded exactly matches the expected TruthSet record count from Step 2.
4. **If the record count matches:** Report pass with the number of records loaded.
5. **If the script encounters an error:** Capture error output, call `explain_error_code` for any SENZ codes, and report fail with remediation guidance.
6. **If fewer records load than expected without error:** Report fail identifying records loaded versus expected. Instruct the bootcamper to check TruthSet data file integrity.
7. **If the script does not complete within 120 seconds:** Terminate the process. Report fail indicating execution timed out.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "data_loading": {"status": "passed|failed", "records_loaded": <count>}
    }
  }
}
```

### Step 7: Deterministic Results Validation

Validate that entity resolution produced the expected outcomes from the TruthSet. Each validation check has a 30-second timeout.

1. Retrieve the Expected_Results for the TruthSet from the MCP server.
2. Query the resolved entities and perform the following validation checks. Execute ALL checks regardless of whether earlier checks pass or fail:

   **a) Entity count tolerance:**
   - Verify the total number of resolved entities falls within ±5% of the expected entity count from the Expected_Results.

   **b) Known matches (at least 3):**
   - Verify that at least 3 known entity matches defined in the Expected_Results are correctly resolved — the specific records designated as matching resolve to the same entity ID.

   **c) Cross-record resolution:**
   - Verify the resolved entity count is strictly less than the total record count loaded, confirming that at least some records merged rather than all loading as singletons.

3. **If all checks pass:** Report pass with entity count and number of matches verified.
4. **If any check fails:** Report fail listing each failed check with expected versus actual values. Suggest re-running data loading or checking that the TruthSet file was loaded completely.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "results_validation": {"status": "passed|failed", "entities": <count>, "matches_verified": <count>}
    }
  }
}
```

### Step 8: Database Operations

Verify read, write, and search operations against the Senzing database. Each operation has a 30-second timeout.

1. **Verify write count:**
   - Confirm the record count returned by the Senzing engine matches the TruthSet record count established during data loading (Step 6).

2. **Verify read by entity ID:**
   - Retrieve a known entity from the Expected_Results by entity ID.
   - Confirm the response contains at least: the entity ID, one constituent record key (data source and record ID pair), and one name attribute from the original TruthSet input.

3. **Verify search by attributes:**
   - Perform a search-by-attributes query using name and address attributes from a known TruthSet record.
   - Confirm the expected entity appears in the search results.

4. **If all operations succeed within 30 seconds each:** Report pass with operations tested.
5. **If any operation fails or times out:** Report fail identifying which operation failed (write, read, or search), the error received, and a Fix_Instruction referencing database configuration from Module 2.

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "database_operations": {"status": "passed|failed", "ops_tested": ["write", "read", "search"]}
    }
  }
}
```

### Step 9: Web Service + Page

Generate and verify a web service that serves entity resolution results.

1. **Generate web service** using the Code_Generator (e.g., `generate_scaffold(workflow='web_service')`) in the bootcamper's chosen language. Save to `src/system_verification/web_service/`.

2. **Start the web service** on the configured localhost port.

3. **Verify health endpoint:**
   - Issue an HTTP GET to the health check endpoint.
   - Confirm HTTP 200 response within 10 seconds of the service process launching.
   - If no response within 10 seconds: Report fail with Fix_Instruction identifying common causes (port conflict, missing dependencies, firewall).

4. **Verify entity query endpoint:**
   - Call the entity query endpoint with a known TruthSet entity identifier.
   - Confirm HTTP 200 response containing the entity's resolved record data (entity ID and at least one constituent record) within 10 seconds.

5. **Verify HTML page accessible:**
   - Confirm the HTML page at `src/system_verification/web_service/static/index.html` exists, is non-empty, and contains valid HTML structure (`<html>` root with `<head>` and `<body>`).
   - Issue an HTTP GET to the configured localhost URL (default `http://localhost:8080/`).
   - Confirm HTTP 200 response within 10 seconds.

6. **If all checks pass:** Report pass with the port number.
7. **If any check fails:** Report fail with Fix_Instruction identifying the specific failure (service didn't start, port conflict, missing static file, endpoint error).

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "web_service": {"status": "passed|failed", "port": <port>},
      "web_page": {"status": "passed|failed", "url": "http://localhost:<port>/"}
    }
  }
}
```

## Phase 2: Report & Close

### Step 10: Verification Report Generation

Generate a structured summary of all verification checks.

1. Compile the results from all 8 verification checks (MCP connectivity, TruthSet acquisition, SDK initialization, code generation, build/compilation, data loading, results validation, database operations, web service, web page) into a single Verification Report.

2. For each check, record:
   - Pass or fail status
   - Duration in milliseconds (where applicable)
   - Any relevant metadata (record counts, entity counts, file paths, ports)

3. **If ALL checks passed:** Display a success banner:

   ```text
   ╔══════════════════════════════════════════════════════════╗
   ║  ✅ SYSTEM VERIFICATION COMPLETE                        ║
   ║                                                         ║
   ║  All checks passed. Your environment is verified and    ║
   ║  ready for subsequent modules.                          ║
   ╚══════════════════════════════════════════════════════════╝
   ```

4. **If ANY checks failed:** Display a failure summary listing each failed check with its Fix_Instructions:

   ```text
   ⚠️  SYSTEM VERIFICATION — FAILURES DETECTED

   Failed checks:
   • <check_name>: <error_summary>
     Fix: <Fix_Instruction>

   Please resolve the issues above and re-run Module 3.
   ```

5. **Persist the report** to `config/bootcamp_progress.json` with the following structure:

   ```json
   {
     "module_3_verification": {
       "timestamp": "<ISO 8601 timestamp>",
       "status": "passed|failed",
       "checks": {
         "mcp_connectivity": {"status": "passed|failed", "duration_ms": 0},
         "truthset_acquisition": {"status": "passed|failed", "records": 0},
         "sdk_initialization": {"status": "passed|failed", "duration_ms": 0},
         "code_generation": {"status": "passed|failed", "file": "verify_pipeline.[ext]"},
         "build_compilation": {"status": "passed|failed", "duration_ms": 0},
         "data_loading": {"status": "passed|failed", "records_loaded": 0},
         "results_validation": {"status": "passed|failed", "entities": 0, "matches_verified": 0},
         "database_operations": {"status": "passed|failed", "ops_tested": ["write", "read", "search"]},
         "web_service": {"status": "passed|failed", "port": 8080},
         "web_page": {"status": "passed|failed", "url": "http://localhost:8080/"}
       },
       "fix_instructions": []
     }
   }
   ```

   - The `timestamp` field SHALL use ISO 8601 format (e.g., `2026-05-13T10:30:00Z`).
   - The `fix_instructions` array SHALL contain one entry per failed check, each with the check name and remediation text.
   - If verification was interrupted, mark unexecuted checks as `"status": "skipped"`.

6. **If all checks passed:** Proceed to Step 11 (Cleanup).
7. **If any checks failed:** Do NOT proceed to cleanup. Advise the bootcamper to fix issues and re-run Module 3 from the beginning.

**Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

### Step 11: Cleanup

Terminate test services and clean up verification data from the database.

1. **Terminate the web service:**
   - Send a termination signal to the Verification_Web_Service process.
   - Wait up to 5 seconds for the process to exit and release the bound port.
   - If the process does not terminate within 5 seconds: Force-stop the process and display a warning to the bootcamper indicating the port may need manual release.

2. **Display test-only artifact message:**

   ```text
   ℹ️  All files in src/system_verification/ are test-only artifacts.
      Real project work begins in subsequent modules.
      These files are retained for reference.
   ```

3. **Purge TruthSet data from the database:**
   - Remove all records loaded from the TruthSet data source from the Senzing database.
   - After purge, verify zero TruthSet entities remain while preserving any non-TruthSet database state.
   - If the purge fails: Report a fail status identifying which records could not be removed. Provide a Fix_Instruction advising the bootcamper to re-run cleanup or manually reset the database.

4. **Retain verification artifacts:** All generated files in `src/system_verification/` remain in place for reference.

**Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

### Step 12: Module Close

Complete the module using the standard module completion workflow.

1. Follow the `module-completion.md` workflow:
   - Update module status in `config/bootcamp_progress.json`
   - Update gate 3→4 status to "completed"

2. **Journal entry:** Append a journal entry to `docs/bootcamp_journal.md` summarizing:
   - Module 3 completed (System Verification)
   - Number of checks passed
   - Timestamp of completion

3. **Reflection question:** Present one reflection question to the bootcamper, such as:
   - "Now that your system is verified end-to-end, which verification step gave you the most confidence that your environment is ready for real entity resolution work?"

4. **Transition to Module 4:** Display the module transition message indicating Module 4 is now available. Follow the standard transition pattern from `module-transitions.md`.

**Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

**Success indicator:** ✅ All 10 verification checks passed + database purged of TruthSet data + web service terminated + module 3 completion recorded in progress file.

## Error Handling

When the bootcamper encounters an error during this module:

1. **SENZ error codes:** Call `explain_error_code(error_code="<code>", version="current")` and include the explanation in the Fix_Instruction.
2. **Load `common-pitfalls.md`** for known issues (port conflicts on 8080, database lock contention, missing language toolchains, MCP proxy connectivity).
3. **Cross-module resources:** SDK install/config issues → Module 2 remediation; MCP issues → connectivity troubleshooting; language toolchains → platform-specific SDK guide.
4. **Timeouts:** Each step has an explicit timeout (MCP 10s, TruthSet 30s, SDK init 30s, build 120s, data loading 120s, web service 10s per endpoint). On timeout, terminate the process, record a fail with a timeout Fix_Instruction, and continue to the next check (no short-circuit).

## Success Criteria

Module 3 is considered successfully complete when ALL of the following are true:

- All 8 verification checks report "passed" status
- The Verification Report is persisted to `config/bootcamp_progress.json` with a valid ISO 8601 timestamp
- The web service process is terminated and the port is released
- TruthSet records are purged from the database (zero TruthSet entities remain)
- The gate 3→4 status is updated to "completed"
- A journal entry is appended to `docs/bootcamp_journal.md`
- The bootcamper has answered the reflection question

## Agent Rules

The following rules are mandatory for the agent executing this module:

1. **TruthSet only:** The agent MUST use the Senzing TruthSet exclusively. No dataset choice SHALL be offered to the bootcamper. Do not use CORD, Las Vegas, London, Moscow, or any other dataset.

2. **Database path:** The Senzing database is located at `database/G2C.db`. All SDK initialization and database operations MUST reference this path.

3. **No dataset choice:** The agent SHALL NOT present any dataset selection prompt, menu, or question to the bootcamper. TruthSet is the only dataset used in this module.

4. **All checks execute regardless of failures:** If any verification step fails, the agent MUST continue executing all subsequent steps. No short-circuiting. The Verification Report MUST include the status of every check.

5. **Artifact isolation:** All verification artifacts (scripts, data files, web service code) MUST be created within `src/system_verification/`. No verification files SHALL be written outside this directory.

6. **Timeouts enforced:** Every verification step MUST enforce its defined timeout. If a process exceeds its timeout, terminate it immediately and record a fail status.

7. **MCP as source of truth:** All Senzing facts, expected results, and code generation MUST come from the MCP server tools. Do NOT use training data or hardcoded values for TruthSet expected outcomes.

8. **Overwrite on re-run:** If the module is re-run after a previous attempt, all existing artifacts in `src/system_verification/` SHALL be overwritten. The database cleanup ensures a clean slate for re-verification.

9. **Web service lifecycle:** The web service started in Step 9 MUST be terminated in Step 11. Do not leave orphaned processes.

10. **Progress persistence:** Every step MUST write its checkpoint to `config/bootcamp_progress.json` immediately upon completion, before proceeding to the next step.
