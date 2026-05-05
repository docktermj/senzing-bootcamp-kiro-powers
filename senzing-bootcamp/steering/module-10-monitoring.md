---
inclusion: manual
---

# Module 10: Monitoring and Observability

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_10_MONITORING_OBSERVABILITY.md` for background.

**Prerequisites:** Module 9 complete, security hardened.

**Before/After:** Your system is secure but you can't see what's happening inside it. After this module, you'll have dashboards, alerts, health checks, and runbooks — you'll know when something goes wrong and how to fix it.

## Phases

This module is split into two phases. Load the phase file matching the bootcamper's current step:

| Phase | Steps | File | Focus |
|-------|-------|------|-------|
| A | 1–5 | `module-10-phaseA-setup.md` | Monitoring tools, metrics, logging, dashboards, alerts |
| B | 6–10 | `module-10-phaseB-operations.md` | Health checks, Senzing monitoring, runbooks, testing, docs |

Load Phase A to begin.

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

**Success:** Dashboards configured, alerts defined, health checks passing, runbooks created, monitoring tested.
