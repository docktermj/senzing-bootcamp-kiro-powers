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

**Success indicator:** All 10 verification checks report "passed", the Verification Report is persisted, the web service and database are cleaned up, and gate 3→4 is marked completed (full criteria in `module-03-phase1-verification.md`).

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
