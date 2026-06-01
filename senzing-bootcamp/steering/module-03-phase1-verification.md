---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

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

**Agent behavior:** After Step 8 completes, proceed DIRECTLY to Step 9. Do not ask whether the bootcamper wants to continue — Step 9 is mandatory and unconditional.

> **Step 9 is mandatory — load `module-03-phase2-visualization.md`.**
