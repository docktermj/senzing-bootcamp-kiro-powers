---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

# Module 6: Data Processing

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_6_DATA_PROCESSING.md`.

**Purpose:** Guide the Data Processing workflow — build production-quality loading programs, load all data sources into Senzing, process redo records, and validate entity resolution results — from first load through cross-source validation.

**Before/After:** You have Senzing-formatted JSON files (and possibly test load results from Module 5 Phase 3). After this module, all your data is loaded, redo records are processed, and entity resolution results are validated — duplicates matched, cross-source connections found.

**Prerequisites:** Module 5 complete (at least one transformed data source in `data/transformed/`), SDK installed and configured (Module 2), database configured (SQLite or PostgreSQL), transformation validated with linter.

**Success indicator:** ✅ All data sources loaded into Senzing + redo records processed + no critical errors + entity resolution results validated

---

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

## Phase Sub-Files

- **Phase A: Build Loading Program** (steps 1–4): `module-06-phaseA-build-loading.md`
- **Phase B: Load First Source** (steps 5–11): `module-06-phaseB-load-first-source.md`
- **Phase C: Multi-Source Orchestration (Conditional — 2+ Data Sources)** (steps 12–20): `module-06-phaseC-multi-source.md`
- **Phase D: Validation** (steps 21–28): `module-06-phaseD-validation.md`
