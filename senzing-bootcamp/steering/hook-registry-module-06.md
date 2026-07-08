---
inclusion: manual
---

# Hook Registry — Module 6 (Full Prompts)

Full hook prompts for Module 6, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 6 Hooks

**backup-before-load** (PostFileSave → agent, matcher: `^(?:src/load/[^/]*\.[^/]*)$`)

Prompt:

````text
A loading program was modified. Before running this in production, remind the user to backup the database using: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows)
````

- id: `backup-before-load`
- name: `to remind you to back up before loading`
- trigger: `PostFileSave`
- matcher: `^(?:src/load/[^/]*\.[^/]*)$`
- action: `agent`

**run-tests-after-change** (PostFileSave → agent, matcher: `^(?:src/load/[^/]*\.[^/]*|src/query/[^/]*\.[^/]*|src/transform/[^/]*\.[^/]*)$`)

Prompt:

````text
Source code was modified. If tests exist in the tests/ directory, remind the user to run them to verify the change didn't break anything. Suggest the appropriate test command for the chosen language.
````

- id: `run-tests-after-change`
- name: `to remind you to run tests`
- trigger: `PostFileSave`
- matcher: `^(?:src/load/[^/]*\.[^/]*|src/query/[^/]*\.[^/]*|src/transform/[^/]*\.[^/]*)$`
- action: `agent`

**verify-generated-code** (PostFileCreate → agent, matcher: `^(?:src/transform/[^/]*\.[^/]*|src/load/[^/]*\.[^/]*|src/query/[^/]*\.[^/]*)$`)

Prompt:

````text
A new bootcamp source file was created. Before moving to the next step, verify this code actually runs: (1) Execute it on a small sample (10-100 records from data/samples/ or data/raw/). (2) Check for errors or exceptions. (3) If it produces output, inspect the first few records. (4) Report the results to the bootcamper — did it work, and if not, what needs fixing? Do not skip this verification step.
````

- id: `verify-generated-code`
- name: `to verify generated code`
- trigger: `PostFileCreate`
- matcher: `^(?:src/transform/[^/]*\.[^/]*|src/load/[^/]*\.[^/]*|src/query/[^/]*\.[^/]*)$`
- action: `agent`
