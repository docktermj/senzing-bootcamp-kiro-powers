---
inclusion: manual
---

# Module 8: Performance Testing

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_8_PERFORMANCE_TESTING.md` for background.

**Prerequisites:** Module 7 (Query and Visualize) complete, representative data loaded, cloud provider set at 7→8 gate.

**Before/After:** Entity resolution works but you don't know how it performs at scale. After this module, you'll have benchmarks, bottleneck analysis, and optimizations — confidence that it'll handle production volumes.

Use the bootcamper's chosen language. Read `cloud_provider` and `deployment_target` from `config/bootcamp_preferences.yaml`. When `deployment_target` is set but `cloud_provider` is not, use the deployment target to inform performance guidance.

## Phases

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
