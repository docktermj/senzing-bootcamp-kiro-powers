---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

# Module 7: Query, Visualize, and Discover

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_7_QUERY_VISUALIZE_DISCOVER.md`.

**Purpose:** Create query programs and visualizations.

**Before/After:** Your data is loaded and entities are resolved, but you haven't examined the results yet. After this module, you'll have query programs that answer your business questions and visualizations of your resolved entities.

**Prerequisites:**

- ✅ Module 6 complete (all sources loaded, single or multi-source)
- ✅ No critical loading errors

**Success indicator:** ✅ Query programs created and tested + queries answer business problem + visualizations offered (entity graph and results dashboard)

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

## Phase Sub-Files

- **Phase 1 — Query and Visualize** (steps 1–3d): `module-07-phase1-query-visualize.md`
- **Phase 2a — Discover (Part A)** (steps 4a–4c): `module-07-phase2-discover.md`
- **Phase 2b — Discover (Part B)** (steps 4d–4e): `module-07-phase2b-discover.md`
