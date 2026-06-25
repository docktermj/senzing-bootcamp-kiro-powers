---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

# Module 11: Packaging and Deployment

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_11_PACKAGING_DEPLOYMENT.md` for background.

**Prerequisites:** Module 10 complete, all tests passing.

**Before/After:** Everything works locally. After this module, your entity resolution system is packaged and ready for deployment — and optionally deployed to your target environment.

**Success indicator**: ✅ Code packaged (containerized, multi-environment config, CI/CD) + deployment complete (or deferred by bootcamper) + rollback plan documented + all tests passing

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

- **Phase 1 — Packaging** (steps 1–12): `module-11-phase1-packaging.md`
- **Phase 2 — Deployment (Optional)** (steps 13–15): `module-11-phase2-deploy.md`
