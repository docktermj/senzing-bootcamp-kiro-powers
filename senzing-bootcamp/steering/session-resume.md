---
inclusion: manual
---

# Session Resume Workflow

Load this steering file when `config/bootcamp_progress.json` exists at session start. This means the bootcamper has a previous session to resume.

## Step 1: Read All State Files

Read these files to reconstruct full context:

1. **`config/bootcamp_progress.json`** — completed modules, current module, data sources, database type, `current_step` (last completed step in current module, if present), `step_history` (per-module step records, if present)
2. **`config/bootcamp_preferences.yaml`** — chosen language, track, cloud provider, license info, **detail_level** (if set — honor their preference for more/less/default detail)
2b. **Check hooks_installed** in `config/bootcamp_preferences.yaml`:
    - If `hooks_installed` key exists with hook names and timestamp → skip hook creation entirely. Hooks are already installed.
    - If `hooks_installed` is missing or empty → load the Hook Registry from `onboarding-flow.md` and create Critical Hooks using the `createHook` tool before the welcome-back banner. This handles bootcampers who started before hook distribution was implemented, or whose preferences were reset.
    - If `config/bootcamp_preferences.yaml` itself is missing or corrupted → treat as no hooks installed and create Critical Hooks from the Hook Registry.
    - If any Critical Hook creation fails during resume, log the failure and continue with the remaining hooks. Report failures after all attempts (see the failure impact messages in the Hook Registry).
3. **`docs/bootcamp_journal.md`** (if exists) — narrative history of what was done and why
4. **`config/mapping_state_*.json`** (if any exist) — in-progress mapping checkpoints from Module 5. If found, the user was mid-mapping when the session ended.

If progress or preferences files are missing or corrupted, inform the user and offer to reconstruct from project artifacts (check `src/`, `data/`, `docs/` for evidence of completed work).

## Step 2: Load Language Steering

Based on the `language` field from preferences, load the corresponding language steering file:

- Python → `lang-python.md`
- Java → `lang-java.md`
- C# → `lang-csharp.md`
- Rust → `lang-rust.md`
- TypeScript → `lang-typescript.md`

## Step 3: Summarize and Confirm

**Display the welcome back banner:**

```text
🎓 Welcome back to the Senzing Bootcamp!
```

Present a concise summary to the user. If `current_step` is present in the progress file, include the step number and total steps for the module (count numbered steps in the module steering file). `current_step` can be either an integer (whole step) or a string sub-step identifier (dotted notation like `"5.3"` or lettered notation like `"7a"`). When it is a string, display it directly (e.g., "Step 5.3 of 12" or "Step 7a of 10"). When it is an integer, display the existing format (e.g., "Step 5 of 12"):

```text
Welcome back! Here's where you left off:

  Track: [track letter]
  Language: [language]
  Completed: Modules [list]
  Current: Module [N] — [module name], Step [S] of [T]
  Database: [sqlite/postgresql]
  Data sources: [list]
```

If `current_step` is absent, omit the step detail and display only:

```text
  Current: Module [N] — [module name]
```

**If mapping checkpoints exist** (`config/mapping_state_*.json`), include the data source name and completed mapping steps in the summary. For each checkpoint, mention: "You were in the middle of mapping [data source name] — we completed steps [list of completed_steps] last time. I can pick up where we left off." If multiple mapping checkpoints exist, list each one.

```text
👉 Ready to continue with Module [N], or would you like to do something else?
```

WAIT for their response.

## Step 4: Load the Right Module Steering

Based on the user's response:

- If they want to continue → load the steering file for `current_module` from the Module Steering table in `agent-instructions.md`. **If `current_step` is present**, determine the resume point based on its type:
  - **Integer `current_step`**: skip to step `current_step + 1` in the module steering file (all steps up to and including `current_step` are already complete).
  - **Sub-step identifier string** (dotted like `"5.3"` or lettered like `"7a"`): skip to the next sub-step after the recorded position in the module steering file (not the next whole step). For example, if `current_step` is `"5.3"`, resume at sub-step `5.4` (or the next defined sub-step after `5.3`). If the sub-step identifier is not found in the module steering file, log a warning and fall back to resuming at the parent step number (extract the parent step using `parse_parent_step` logic — e.g., `"5.3"` → step 5, `"7a"` → step 7).
  - **If `current_step` references a step number that does not exist in the module steering file** (e.g., exceeds the total number of steps, is zero, or is negative), log a warning and fall back to artifact scanning to determine the correct resume point.
  - **If mapping checkpoints exist** (`config/mapping_state_*.json`), restart `mapping_workflow` for each data source with a checkpoint and fast-track through the completed mapping steps (listed in `completed_steps`) before resuming from the first incomplete mapping step. If a mapping checkpoint file contains invalid JSON or is missing required fields (`data_source`, `current_step`, `completed_steps`), log a warning, skip that checkpoint, and inform the bootcamper that the mapping for that data source will need to restart from the beginning.
  **If `current_step` is absent**, fall back to the existing artifact-scanning behavior to infer position.
- If they want to switch modules → verify prerequisites via `module-prerequisites.md`, then load the requested module steering
- If they want to switch tracks → follow the "Switching Tracks" section in `onboarding-flow.md`
- If they want to start over → confirm, then load `onboarding-flow.md`

## Step 5: Re-establish MCP Context

Call `get_capabilities` to re-establish the MCP session. This is required at the start of every new session regardless of previous progress.

## Handling Stale or Corrupted State

If `bootcamp_progress.json` exists but seems wrong (e.g., claims Module 8 is complete but `src/query/` is empty):

1. Run `python3 scripts/validate_module.py` to check actual artifact state
2. Show the user any discrepancies
3. Offer to correct the progress file based on what actually exists
4. Proceed from the last verifiably complete module
