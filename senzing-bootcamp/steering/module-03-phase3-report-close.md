---
inclusion: manual
---
> **⛔ PRE-ADVANCEMENT VERIFICATION (Agent self-check):**
>
> Before offering to advance to Module 4 or marking Module 3 complete, the agent
> MUST read `config/bootcamp_progress.json` and verify:
>
> - `module_3_verification.checks.web_service.status` = `"passed"`
> - `module_3_verification.checks.web_page.status` = `"passed"`
>
> If these checkpoints are NOT present, the agent MUST execute Step 9 immediately.
> Do NOT offer advancement. Do NOT ask "Ready for Module 4?" Do NOT save progress.
> Execute Step 9 first.

## Phase 2: Report & Close

### Step 10: Verification Report Generation

**Pre-report validation:** Before compiling the Verification Report, confirm that `config/bootcamp_progress.json` contains BOTH `web_service` and `web_page` checkpoint entries under `module_3_verification.checks`. If either entry is missing or has `"status": "failed"`:

- If missing: STOP. Do not generate the report. Return to Step 9 and execute it fully by loading `module-03-phase2-visualization.md`.
- If failed: Include the failure in the report and proceed (failed is different from skipped/missing — it means the step was attempted).

Generate a structured summary of all verification checks.

1. Compile the results from all 10 verification checkpoint entries (mcp_connectivity, truthset_acquisition, sdk_initialization, code_generation, build_compilation, data_loading, results_validation, database_operations, web_service, web_page) into a single Verification Report.

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

**Pre-cleanup confirmation gate:**

Before proceeding with termination, confirm the bootcamper has finished exploring the visualization. Ask the bootcamper for confirmation before terminating the web service or performing any cleanup:

> 👉 Have you finished exploring the visualization? Let me know when you're ready and I'll clean up the server.

🛑 STOP — Wait for the bootcamper to confirm they are done exploring. Do NOT proceed with termination until the bootcamper responds.

**Skip condition:** If the bootcamper skipped Step 9 via the skip-step protocol (no web server was started), skip this confirmation prompt entirely and proceed directly to cleanup.

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

3. **Transition to Module 4:** Display the module transition message indicating Module 4 is now available. Follow the standard transition pattern from `module-transitions.md`.

**Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

**Success indicator:** ✅ System verification passed or explicitly skipped by bootcamper. All 10 verification checks passed + database purged of TruthSet data + web service terminated + module 3 completion recorded in progress file.
