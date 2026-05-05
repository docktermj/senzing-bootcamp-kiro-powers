---
inclusion: manual
---

# Module 9: Security Hardening

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_9_SECURITY_HARDENING.md` for background.

**Prerequisites:** Module 8 complete, working Senzing deployment to harden.

**Before/After:** Your system works and performs well, but it's not secure. After this module, secrets are managed, access is controlled, data is encrypted, and you have a security checklist signed off by stakeholders.

## Phases

This module is split into two phases. Load the phase file matching the bootcamper's current step:

| Phase | Steps | File | Focus |
|-------|-------|------|-------|
| A | 1–4 | `module-09-phaseA-assessment.md` | Security assessment, secrets, authentication, RBAC |
| B | 5–12 | `module-09-phaseB-hardening.md` | Encryption, audit logging, scanning, checklist, review |

Load Phase A to begin.

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

**Success:** No critical vulnerabilities, secrets managed, audit logging active, checklist complete, stakeholder sign-off documented.
