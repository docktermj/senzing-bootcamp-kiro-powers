---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

# Module 8: Performance Testing

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_8_PERFORMANCE_TESTING.md` for background.

**Prerequisites:** Module 7 (Query, Visualize, and Discover) complete, queries answer the business problem (7→8 gate), representative data loaded.

**Before/After:** Entity resolution works but you don't know how it performs at scale. After this module, you'll have benchmarks, bottleneck analysis, and optimizations — confidence that it'll handle production volumes.

**Success indicator**: ✅ Baselines captured (transformation, loading, query) + bottlenecks documented + optimizations applied + performance report complete

## Phase Sub-Files

This module is split into three phases. Load the phase file matching the bootcamper's current step:

| Phase | Steps | File | Focus |
|-------|-------|------|-------|
| A | 1–3 | `module-08-phaseA-requirements.md` | Requirements, anti-patterns, environment baseline |
| B | 4–7 | `module-08-phaseB-benchmarking.md` | Transformation, loading, query, and resource benchmarks |
| C | 8–13 | `module-08-phaseC-optimization.md` | Database tuning, scalability, optimization, final report |

Load Phase A to begin.

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

**Success:** Performance baselines captured, bottlenecks identified, optimizations documented, report complete.
