---
inclusion: manual
---

# Hook Registry — Module 6 (Full Prompts)

Full hook prompts for Module 6, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 6 Hooks

**backup-before-load** (fileEdited → askAgent, filePatterns: `src/load/*.*`)

Prompt:

````text
A loading program was modified. Before running this in production, remind the user to backup the database using: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows)
````

- id: `backup-before-load`
- name: `to remind you to back up before loading`
- description: `Remind to backup database before running loading programs`

**run-tests-after-change** (fileEdited → askAgent, filePatterns: `src/load/*.*, src/query/*.*, src/transform/*.*`)

Prompt:

````text
Source code was modified. If tests exist in the tests/ directory, remind the user to run them to verify the change didn't break anything. Suggest the appropriate test command for the chosen language.
````

- id: `run-tests-after-change`
- name: `to remind you to run tests`
- description: `Reminds the agent to run the test suite after source code changes in loading, query, or transformation programs.`

**verify-generated-code** (fileCreated → askAgent, filePatterns: `src/transform/*.*, src/load/*.*, src/query/*.*`)

Prompt:

````text
A new bootcamp source file was created. Before moving to the next step, verify this code actually runs: (1) Execute it on a small sample (10-100 records from data/samples/ or data/raw/). (2) Check for errors or exceptions. (3) If it produces output, inspect the first few records. (4) Report the results to the bootcamper — did it work, and if not, what needs fixing? Do not skip this verification step.
````

- id: `verify-generated-code`
- name: `to verify generated code`
- description: `When bootcamp source code is created, prompts the agent to run it on sample data and report results before moving on.`
