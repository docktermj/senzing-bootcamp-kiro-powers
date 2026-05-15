```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 3: SYSTEM VERIFICATION  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 3: System Verification

> **Agent workflow:** The agent follows `steering/module-03-system-verification.md` for this module's step-by-step workflow.

## Overview

Module 3 is a verification gate that confirms your entire development environment works end-to-end before you proceed to real work in subsequent modules. It checks SDK initialization, MCP-driven code generation, compilation, execution, data loading, entity resolution with expected results, database operations, and web service scaffolding.

Unlike a demo, this module produces a structured pass/fail report. If everything passes, you know your system is ready. If something fails, you get specific instructions on what to fix.

**Prerequisites:** Module 2 (SDK Setup) complete
**Output:** Verification report confirming all system components work correctly

## Why TruthSet?

Module 3 uses the Senzing TruthSet exclusively — a curated dataset with known entities, known matches, and predictable resolution outcomes. This is deliberate:

- **Deterministic results** — The TruthSet always produces the same entity resolution outcomes, so the module can check for specific expected values rather than just confirming "something happened."
- **Known-good matches** — Specific record pairs are guaranteed to resolve to the same entity, enabling precise validation.
- **Predictable entity counts** — The expected number of resolved entities is known in advance, allowing tolerance-based checks.
- **No dataset choice** — Using a single fixed dataset eliminates variables and makes verification reliable across all environments.

You do not choose a dataset for this module. The TruthSet is retrieved automatically from the MCP server.

## Learning Objectives

By the end of this module, you will:

- Confirm your SDK installation connects to the database
- Confirm the MCP server generates code in your chosen language
- Confirm generated code compiles and runs
- Confirm data loading and entity resolution produce correct results
- Confirm database read/write/search operations work
- Confirm web service scaffolding works in your environment

## What You'll Do

1. MCP connectivity check
2. TruthSet data acquisition
3. SDK initialization verification
4. Code generation verification
5. Build/compile verification
6. Data loading and execution
7. Deterministic results validation
8. Database operations check
9. Web service and page verification
10. Review verification report

## Verification Steps Explained

### Step 1: MCP Connectivity

Confirms the Senzing MCP server at `mcp.senzing.com` is reachable and responding. This is the foundation — if MCP is unreachable, code generation and data retrieval cannot work.

**What it checks:** A lightweight `search_docs` call returns a response within 10 seconds.

### Step 2: TruthSet Acquisition

Downloads the TruthSet data from the MCP server and saves it to `src/system_verification/truthset_data.jsonl`. Validates the file contains valid JSON and the correct number of records.

**What it checks:** File exists, each line is valid JSON, line count matches expected record count.

### Step 3: SDK Initialization

Generates and runs an initialization script that connects to the Senzing database at `database/G2C.db`. This confirms the SDK installed in Module 2 is functional.

**What it checks:** Script exits with code 0, no SENZ error codes in output, completes within 30 seconds.

### Step 4: Code Generation

Requests a full pipeline script from the MCP server's `generate_scaffold` tool in your chosen language. Validates the generated file is non-empty and contains language-appropriate structural elements.

**What it checks:** Generated file has content, includes imports/functions/classes appropriate to the language.

### Step 5: Build/Compile

Runs the language-appropriate build command against the generated code. For Python, this is a syntax check (`py_compile`). For compiled languages, this is the standard build tool (javac, dotnet build, cargo build, tsc).

**What it checks:** Build command exits with code 0 within 120 seconds.

### Step 6: Data Loading

Executes the verification script to load all TruthSet records into the Senzing database. Confirms the loaded record count matches the expected TruthSet count.

**What it checks:** Script completes within 120 seconds, loaded record count matches expected count exactly.

### Step 7: Deterministic Results Validation

Queries the resolved entities and validates against known-good expected results from the TruthSet:

- Entity count falls within ±5% of the expected value
- At least 3 known match pairs resolve to the same entity
- Total entities is strictly less than total records (confirming merges occurred)

**What it checks:** Specific, predictable outcomes — not just "resolution ran without errors."

### Step 8: Database Operations

Verifies the three core database operations work correctly:

- **Write:** Record count matches expected TruthSet count
- **Read:** Retrieving a known entity by ID returns expected attributes
- **Search:** Searching by name/address attributes finds the expected entity

**What it checks:** Each operation returns correct results within 30 seconds.

### Step 9: Web Service and Page

Generates a web service with health check and entity query endpoints. Starts the service and verifies:

- Health endpoint returns HTTP 200
- Entity query endpoint returns resolved data
- HTML page is accessible and displays results

**What it checks:** HTTP endpoints respond correctly within 10 seconds of service startup.

## Verification Report

After all steps complete, you receive a structured report showing pass/fail status for each check. The report is persisted to `config/bootcamp_progress.json`.

### All Checks Pass

If every check passes, you see a success message confirming your system is verified and ready for subsequent modules. The module closes normally.

### One or More Checks Fail

If any check fails, the report lists each failure with specific Fix_Instructions. All checks run regardless of earlier failures — you get the complete picture in one pass.

## What to Do If Checks Fail

1. **Read the Fix_Instructions** — Each failed check includes specific remediation steps.
2. **Fix the identified issue** — Common fixes:
   - MCP connectivity: Check internet, verify `mcp.senzing.com:443` is reachable, check proxy settings
   - SDK initialization: Re-run Module 2, verify database path exists (`mkdir -p database`)
   - Build failures: Check language toolchain is installed, verify PATH includes build tools
   - Data loading: Check disk space, verify database is writable
   - Web service: Check for port conflicts, verify dependencies
3. **Re-run verification** — After fixing issues, run Module 3 again from the beginning.

## Re-Running Verification

Module 3 is designed to be re-run after fixes:

- Existing files in `src/system_verification/` are overwritten on re-run
- The database is cleaned of TruthSet data during cleanup, so re-runs start fresh
- The verification report in `config/bootcamp_progress.json` is updated with the latest results

To re-run, simply start Module 3 again. The agent will execute the full verification pipeline from Step 1.

## File Locations

All verification artifacts are generated into a dedicated directory:

```text
src/system_verification/
├── verify_init.[ext]           # SDK initialization script
├── verify_pipeline.[ext]       # Full pipeline (load + resolve + query)
├── truthset_data.jsonl         # TruthSet data file
└── web_service/
    ├── server.[ext]            # Web service entry point
    ├── routes.[ext]            # HTTP endpoint handlers
    └── static/
        └── index.html          # Entity resolution results page
```

These files are retained after verification for reference. They are test-only artifacts — real project work begins in subsequent modules.

## Cleanup

After successful verification, the module automatically:

- Terminates the web service process (releases the port)
- Purges all TruthSet records from the Senzing database
- Retains generated files in `src/system_verification/` for reference

The database is left clean for subsequent modules.

## Skipping Module 3

If you are already familiar with Senzing and your system has been verified previously, you can skip this module. The agent will confirm your skip reason and update the gate condition so you can proceed to Module 4.

## Success Criteria

- ✅ MCP server is reachable
- ✅ TruthSet data downloads and validates
- ✅ SDK initializes and connects to database
- ✅ Code generation produces valid source files
- ✅ Generated code compiles/builds without errors
- ✅ Data loads completely with correct record count
- ✅ Entity resolution produces expected deterministic results
- ✅ Database read/write/search operations work
- ✅ Web service starts and responds to HTTP requests
- ✅ Verification report shows all checks passed

## Common Issues

> **Agent instruction:** For any SENZ error codes encountered during verification, use
> `explain_error_code(error_code="<code>", version="current")` for diagnosis.
> Use `search_docs(query="<issue>", category="troubleshooting", version="current")`
> for general troubleshooting guidance.

- **MCP connectivity fails:** Check internet connection, verify `mcp.senzing.com:443` is reachable, check corporate proxy/firewall settings
- **SDK initialization fails:** Re-run Module 2, verify `database/G2C.db` path is accessible
- **Build fails:** Verify language toolchain is installed and on PATH
- **Data loading times out:** Check disk space, verify database is not locked by another process
- **Web service port conflict:** Another process is using the port — stop it or the agent will report the conflict
- **Entity count outside tolerance:** TruthSet file may be corrupted — re-run from Step 2

## Next Steps

After successful verification:

- **Module 1** (Business Problem) — Start working with your own data
- **Module 4** (Data Collection) — Begin collecting and preparing your datasets

## Related Documentation

- `POWER.md` — Bootcamp overview
- `steering/module-03-system-verification.md` — Module 3 workflow
- `docs/modules/MODULE_2_SDK_SETUP.md` — Module 2 (prerequisite)
- Use `explain_error_code` MCP tool for SENZ error diagnosis
- Use `search_docs` MCP tool for troubleshooting guidance
