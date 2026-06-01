---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

# Module 3: System Verification

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_3_SYSTEM_VERIFICATION.md`.

**Language:** Use the bootcamper's chosen language for all code generation and verification scripts.

**Prerequisites:** Module 2 complete (SDK installed and configured)

**Before/After:** SDK installed but untested end-to-end. After: your entire system is verified — SDK initialization, code generation, compilation, data loading, entity resolution, database operations, and web service scaffolding all confirmed working.

**IMPORTANT:** This module uses the Senzing TruthSet exclusively — a deterministic dataset with known-good expected outputs. No dataset choice is offered. All verification code is generated at runtime by the MCP server, not shipped as static files.

## Opt-Out Gate

Before starting Module 3 steps, check if the bootcamper has explicitly requested to skip:

**Trigger phrases:** "skip verification", "I've already verified", "skip module 3"

**If triggered:**

1. Record skip in `config/bootcamp_progress.json`:

   ```json
   {"module_3_verification": {"status": "skipped", "reason": "bootcamper_opted_out"}}
   ```

2. Display warning:

   ```text
   ⚠️ Skipping system verification. If you encounter issues in later modules
   (data loading failures, SDK errors), Module 3 can help diagnose them.
   Say "run verification" at any time to come back.
   ```

3. Update gate 3→4 to "skipped" and proceed to Module 4.

**If NOT triggered:** Proceed with Module 3 normally (default path).

## Phase Sub-Files

- **Phase 1 — Verification Pipeline** (steps 1–8): `module-03-phase1-verification.md`
- **Phase 2 — Visualization** (step 9): `module-03-phase2-visualization.md`
- **Phase 3 — Report & Close** (steps 10–12): `module-03-phase3-report-close.md`

## Error Handling

When the bootcamper encounters an error during this module:

1. **SENZ error codes:** Call `explain_error_code(error_code="<code>", version="current")` and include the explanation in the Fix_Instruction.
2. **Load `common-pitfalls.md`** for known issues (port conflicts on 8080, database lock contention, missing language toolchains, MCP proxy connectivity).
3. **Cross-module resources:** SDK install/config issues → Module 2 remediation; MCP issues → connectivity troubleshooting; language toolchains → platform-specific SDK guide.
4. **Timeouts:** Each step has an explicit timeout (MCP 10s, TruthSet 30s, SDK init 30s, build 120s, data loading 120s, web service 10s per endpoint). On timeout, terminate the process, record a fail with a timeout Fix_Instruction, and continue to the next check (no short-circuit).

## Success Criteria

Module 3 is considered successfully complete when ALL of the following are true:

- All 10 verification checkpoint entries report "passed" status (mcp_connectivity, truthset_acquisition, sdk_initialization, code_generation, build_compilation, data_loading, results_validation, database_operations, web_service, web_page)
- The Verification Report is persisted to `config/bootcamp_progress.json` with a valid ISO 8601 timestamp
- The web service process is terminated and the port is released
- TruthSet records are purged from the database (zero TruthSet entities remain)
- The gate 3→4 status is updated to "completed"
- A journal entry is appended to `docs/bootcamp_journal.md`

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
