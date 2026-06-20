---
inclusion: manual
---

# Hook Registry — Module 1 (Full Prompts)

Full hook prompts for Module 1, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 1 Hooks

**validate-business-problem** (postTaskExecution → askAgent)

Prompt:

````text
Read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT 1, produce no output at all — do not acknowledge, do not explain, do not print anything. If the current module IS 1, validate the business problem definition by checking these three fields in the progress file:

1. **Data sources identified** — At least one data source must be listed (the records the bootcamper wants to resolve).
2. **Matching criteria defined** — The attributes to match on must be specified (e.g., name, address, date of birth).
3. **Success metrics documented** — The bootcamper must have described what successful entity resolution looks like for their use case.

If any of these fields are missing or empty, report which fields are incomplete and suggest the bootcamper address them before moving on. For example: "Your problem statement is missing matching criteria — please specify which attributes (name, address, etc.) you want Senzing to match on."

If all three fields are present and non-empty, confirm readiness: "Your business problem is fully defined. You have data sources identified, matching criteria set, and success metrics documented. Ready to proceed to Module 2."
````

- id: `validate-business-problem`
- name: `to validate your business problem`
- description: `After Module 1 tasks complete, validates that the bootcamper has identified data sources, defined matching criteria, and documented success metrics before proceeding to Module 2.`
