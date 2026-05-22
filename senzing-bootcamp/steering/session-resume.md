---
inclusion: manual
---

# Session Resume Workflow

Load this steering file when `config/bootcamp_progress.json` exists at session start. This means the bootcamper has a previous session to resume.

## Fast Path Check

Before running the full state reconstruction, check if a fast resume is possible. A fast resume skips the verbose state loading and goes directly to the welcome-back banner when ALL of these conditions are true:

1. `config/bootcamp_progress.json` parses as valid JSON with `current_module` and `modules_completed` present
2. `config/bootcamp_preferences.yaml` exists and contains `language` and `track` fields
3. No mapping checkpoints exist (`config/mapping_state_*.json` — zero files matching this pattern)
4. `current_step` is present in the progress file (we know exactly where to resume)
5. `hooks_installed` is present in preferences (no hook setup needed)

**If ALL conditions are met:** Skip Steps 1–2 entirely. Jump directly to Step 2b, then Step 2c, then Step 3 using the data already read from the progress and preferences files.

**If ANY condition fails:** Fall through to the Routing Logic evaluation, then the full Step 1–2 sequence below.

## Routing Logic

After the fast-path check fails, evaluate ALL of the following conditions independently. Multiple phase-2 files can be loaded simultaneously for compound recovery scenarios.

**Evaluate in this order:**

1. **State repair** — Load `session-resume-phase2-state-repair.md` if ANY of:
   - `config/bootcamp_progress.json` fails to parse as valid JSON
   - `config/bootcamp_progress.json` is missing entirely
   - `current_module` in the progress file is inconsistent with project artifacts

2. **Setup recovery** — Load `session-resume-phase2-setup-recovery.md` if ANY of:
   - `hooks_installed` is missing or empty in `config/bootcamp_preferences.yaml`
   - `config/bootcamp_preferences.yaml` is missing or corrupted
   - MCP health check probe fails or times out
   - `show_whats_new` is not `false` in preferences AND `config/session_log.jsonl` exists

3. **Mapping** — Load `session-resume-phase2-mapping.md` if:
   - One or more `config/mapping_state_*.json` files exist

All conditions are evaluated independently — if state repair AND setup recovery both trigger, load both files.

## Step 1: Read All State Files

Read these files to reconstruct full context:

1. **`config/bootcamp_progress.json`** — completed modules, current module, data sources, database type, `current_step` (last completed step in current module, if present), `step_history` (per-module step records, if present)
2. **`config/bootcamp_preferences.yaml`** — chosen language, track, cloud provider, license info, **detail_level** (if set), **conversation_style** (if set)
3. **`docs/bootcamp_journal.md`** (if exists) — narrative history
4. **`config/mapping_state_*.json`** (if any exist) — in-progress mapping checkpoints
5. **`config/session_log.jsonl`** (if exists) — session analytics for adaptive pacing

If progress or preferences files are missing or corrupted, see `session-resume-phase2-state-repair.md` for reconstruction procedure.

## Step 2: Load Language Steering

Based on the `language` field from preferences, load the corresponding language steering file:

- Python → `lang-python.md`
- Java → `lang-java.md`
- C# → `lang-csharp.md`
- Rust → `lang-rust.md`
- TypeScript → `lang-typescript.md`

## Step 2b: Behavioral Rules Reload

**`conversation-protocol.md` is the authoritative source for all turn-taking and question-handling rules. These rules apply without exception after session resume.**

Before interacting with the bootcamper, re-assert the five core conversation rules. These are summarized below — see `conversation-protocol.md` for complete definitions.

### Core Rules

1. **One-question-per-turn** — Each turn contains at most one 👉 question. End the turn with 🛑 STOP immediately after the question.
2. **👉-prefix-required** — Every question expecting bootcamper input must use the 👉 prefix.
3. **STOP markers as absolute end-of-turn boundaries** — 🛑 STOP means produce zero additional tokens. Wait for the bootcamper's response.
4. **No self-answering** — Never generate text that answers, assumes, or implies a response to your own 👉 question.
5. **No dead-end responses** — Every turn must advance the conversation with a next action.

### Equal Priority Statement

Session resume does not reduce the authority of any behavioral rule. Conversation-protocol rules have equal priority to agent-instructions rules.

### Protocol Confirmation

Before proceeding to Step 3, confirm that `conversation-protocol.md` is loaded (via its `inclusion: auto` setting) and its rules are active. If unavailable, the five rules above serve as the authoritative fallback.

### Self-Answering Prohibition

After asking any 👉 question, produce zero additional tokens. Do not answer the question. Do not assume the bootcamper's response.

After asking the "Ready to continue?" question in Step 3, write `config/.question_pending` with the question text to enforce the wait mechanism.

## Step 2c: Restore Conversation Style

Read the `conversation_style` key from `config/bootcamp_preferences.yaml`. If the key exists, apply these parameters to all subsequent output:

- **verbosity_preset** — `concise`, `standard`, `detailed`, or `custom`
- **question_framing** — `minimal`, `moderate`, or `full`
- **tone** — `concise`, `conversational`, or `detailed`
- **pacing** — `one_concept_per_turn` or `grouped_concepts`

### Fallback Defaults

If `conversation_style` is missing, apply: `verbosity_preset: standard`, `tone: conversational`, `question_framing: moderate`, `pacing: one_concept_per_turn`.

Do not create the `conversation_style` key during resume — it will be written on the next style interaction.

### Style Drift Detection

After generating the first post-resume response, compare output style against the stored profile. If divergent, self-correct in subsequent turns.

## Step 3: Summarize and Confirm

**Display the welcome back banner:**

```text
🎓 Welcome back to the Senzing Bootcamp!
```

Present a concise summary. If `current_step` is present, include step number and total steps. `current_step` can be an integer or a string sub-step identifier (e.g., `"5.3"` or `"7a"`). Display accordingly:

```text
Welcome back! Here's where you left off:

  Track: [track display name]
  Language: [language]
  Completed: Modules [list]
  Current: Module [N] — [module name], Step [S] of [T]
  Database: [sqlite/postgresql]
  Data sources: [list]
```

If `current_step` is absent, omit the step detail.

If mapping checkpoints exist, see `session-resume-phase2-mapping.md` for checkpoint summary integration and resume options.

```text
👉 Ready to continue with Module [N], or would you like to do something else?
```

Write `config/.question_pending` with the question text above.

🛑 STOP — Wait for bootcamper response.

## Step 4: Load the Right Module Steering

Based on the user's response:

- If they want to continue → load the steering file for `current_module` from the Module Steering table in `agent-instructions.md`. **If `current_step` is present**, determine the resume point:
  - **Integer**: skip to step `current_step + 1` (all steps up to and including `current_step` are complete).
  - **Sub-step string** (e.g., `"5.3"` or `"7a"`): skip to the next sub-step after the recorded position. If not found, fall back to the parent step number.
  - **Invalid step** (exceeds total, zero, or negative): log a warning and fall back to artifact scanning.
  - **If mapping checkpoints exist**: see `session-resume-phase2-mapping.md` for checkpoint validation and fast-track logic.
  - **If `current_step` is absent**: fall back to artifact-scanning to infer position.
- If they want to switch modules → verify prerequisites via `module-prerequisites.md`, then load the requested module steering
- If they want to switch tracks → follow "Switching Tracks" in `onboarding-phase2-track-setup.md`
- If they want to start over → confirm, then load `onboarding-flow.md`

## Step 5: Re-establish MCP Context

Call `get_capabilities` to re-establish the MCP session. This is required at the start of every new session regardless of previous progress.
