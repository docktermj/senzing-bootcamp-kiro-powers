---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

# Module 1: Discover the Business Problem

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_1_BUSINESS_PROBLEM.md`.

**Before/After:** You may have seen the demo, but you don't yet have a defined problem or plan. After this module, you'll have a documented business problem, identified data sources, and clear success criteria — the roadmap for everything that follows.

**Prerequisites:** None (or Module 3 complete if they did the demo)

**Success indicator:** ✅ Business problem documented in `docs/business_problem.md` + data sources identified + success criteria defined + user confirmation

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

- **Phase 1 — Discovery** (steps 1–9): `module-01-phase1-discovery.md`
- **Phase 2 — Document and Confirm** (steps 10–18): `module-01-phase2-document-confirm.md`
