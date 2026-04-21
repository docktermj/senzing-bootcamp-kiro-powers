---
inclusion: manual
---

# Session Resume Workflow

Load this steering file when `config/bootcamp_progress.json` exists at session start. This means the bootcamper has a previous session to resume.

## Step 1: Read All State Files

Read these files to reconstruct full context:

1. **`config/bootcamp_progress.json`** — completed modules, current module, data sources, database type
2. **`config/bootcamp_preferences.yaml`** — chosen language, path, cloud provider, license info, **detail_level** (if set — honor their preference for more/less/default detail)
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

Present a concise summary to the user:

```text
Welcome back! Here's where you left off:

  Path: [path letter]
  Language: [language]
  Completed: Modules [list]
  Current: Module [N] — [module name]
  Database: [sqlite/postgresql]
  Data sources: [list]
```

**If mapping checkpoints exist** (`config/mapping_state_*.json`), also mention: "You were in the middle of mapping [data source name] — we completed steps [list] last time. I can pick up where we left off."

```text
👉 Ready to continue with Module [N], or would you like to do something else?
```

WAIT for their response.

## Step 4: Load the Right Module Steering

Based on the user's response:

- If they want to continue → load the steering file for `current_module` from the Module Steering table in `agent-instructions.md`
- If they want to switch modules → verify prerequisites via `module-prerequisites.md`, then load the requested module steering
- If they want to switch paths → follow the "Switching Paths Mid-Bootcamp" section in `onboarding-flow.md`
- If they want to start over → confirm, then load `onboarding-flow.md`

## Step 5: Re-establish MCP Context

Call `get_capabilities` to re-establish the MCP session. This is required at the start of every new session regardless of previous progress.

## Handling Stale or Corrupted State

If `bootcamp_progress.json` exists but seems wrong (e.g., claims Module 8 is complete but `src/query/` is empty):

1. Run `python scripts/validate_module.py` to check actual artifact state
2. Show the user any discrepancies
3. Offer to correct the progress file based on what actually exists
4. Proceed from the last verifiably complete module
