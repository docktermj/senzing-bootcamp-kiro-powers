---
inclusion: manual
---

# Session Resume Workflow

Load this steering file when `config/bootcamp_progress.json` exists at session start. This means the bootcamper has a previous session to resume.

## Step 1: Read All State Files

Read these files to reconstruct full context:

1. **`config/bootcamp_progress.json`** — completed modules, current module, data sources, database type, `current_step` (last completed step in current module, if present), `step_history` (per-module step records, if present)
2. **`config/bootcamp_preferences.yaml`** — chosen language, track, cloud provider, license info, **detail_level** (if set — honor their preference for more/less/default detail), **conversation_style** (if set — restore tone, pacing, question framing, and verbosity preset for style continuity)
2b. **Check hooks_installed** in `config/bootcamp_preferences.yaml`:
    - If `hooks_installed` key exists with hook names and timestamp → skip hook creation entirely. Hooks are already installed.
    - If `hooks_installed` is missing or empty → load the Hook Registry from `onboarding-flow.md` and create Critical Hooks using the `createHook` tool before the welcome-back banner. This handles bootcampers who started before hook distribution was implemented, or whose preferences were reset.
    - If `config/bootcamp_preferences.yaml` itself is missing or corrupted → treat as no hooks installed and create Critical Hooks from the Hook Registry.
    - If any Critical Hook creation fails during resume, log the failure and continue with the remaining hooks. Report failures after all attempts (see the failure impact messages in the Hook Registry).
3. **`docs/bootcamp_journal.md`** (if exists) — narrative history of what was done and why
4. **`config/mapping_state_*.json`** (if any exist) — in-progress mapping checkpoints from Module 5. If found, the user was mid-mapping when the session ended.
5. **`config/session_log.jsonl`** (if exists) — session analytics for adaptive pacing. Compute pacing classifications for completed modules and merge with `pacing_overrides` from preferences. Store in working memory for module-start decisions.

If progress or preferences files are missing or corrupted, inform the user and offer to reconstruct from project artifacts (check `src/`, `data/`, `docs/` for evidence of completed work).

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

### Core Rules with Enforcement Mechanisms

1. **One-question-per-turn** — Each turn contains at most one 👉 question. End the turn with 🛑 STOP immediately after the question. Enforcement: if a turn contains more than one 👉 question, the turn is invalid and must be revised before sending.

2. **👉-prefix-required** — Every question expecting bootcamper input must use the 👉 prefix. Enforcement: any question directed at the bootcamper that lacks the 👉 prefix is a protocol violation. Self-check before sending: does every bootcamper-directed question have the prefix?

3. **STOP markers as absolute end-of-turn boundaries (wait-for-response)** — 🛑 STOP means produce zero additional tokens. No content, no acknowledgment, no continuation after a STOP marker. Wait for the bootcamper's response before generating anything. Enforcement: any token generated after a 🛑 STOP is a violation. The turn ends at the marker unconditionally.

4. **No self-answering under any circumstance** — Never generate text that answers, assumes, or implies a response to your own 👉 question. Enforcement: after outputting a 👉 question, the only permitted action is writing `config/.question_pending` and stopping. Any text that could be interpreted as a response to the question is a violation.

5. **No dead-end responses after bootcamper input** — Every turn must advance the conversation with a next action: a 👉 follow-up question, a summary of what comes next, or proceeding to the next step. Enforcement: if a turn ends with only an acknowledgment ("Got it.", "Understood.") and no next action, it is a violation.

### Equal Priority Statement

Session resume does not reduce the authority of any behavioral rule. Conversation-protocol rules have equal priority to agent-instructions rules. No rule is relaxed, deferred, or weakened because the session was resumed rather than started fresh.

### Protocol Confirmation

Before proceeding to Step 3, confirm that `conversation-protocol.md` is loaded (via its `inclusion: auto` setting) and its rules are active. The auto-inclusion mechanism ensures the protocol is present in every active session. If for any reason the protocol is unavailable, the five rules summarized above serve as the authoritative fallback — enforce them without exception.

### Self-Answering Prohibition

After asking any 👉 question, produce zero additional tokens. Do not answer the question. Do not assume the bootcamper's response. Do not generate placeholder answers like "just me" or "I will go with X."

**WRONG — generating a placeholder answer after resume:**

```text
👉 Who will be working on this project?
I'll assume it's just me for now. Let's continue.
```

**CORRECT:**

```text
👉 Who will be working on this project?
🛑 STOP
```

**WRONG — answering your own language question:**

```text
👉 What programming language would you like to use?
I'll go with Python since that's most common.
```

**CORRECT:**

```text
👉 What programming language would you like to use?
🛑 STOP
```

**WRONG — answering the Ready to continue? question:**

```text
👉 Ready to continue with Module 3, or would you like to do something else?
Great, let's continue with Module 3!
```

**CORRECT:**

```text
👉 Ready to continue with Module 3, or would you like to do something else?
🛑 STOP
```

**Question pending enforcement:** While `config/.question_pending` exists, the agent must not generate any response content until the bootcamper provides input. The file's existence is the definitive signal that a question is awaiting a response — no output is permitted until the bootcamper replies and the file is deleted.

After asking the "Ready to continue?" question in Step 3, write `config/.question_pending` with the question text to enforce the wait mechanism.

## Step 2c: Restore Conversation Style

Before generating any bootcamper-facing output, restore the conversation style from the persisted profile so that tone, pacing, and question framing are consistent with the previous session.

### Apply Stored Style Parameters

Read the `conversation_style` key from `config/bootcamp_preferences.yaml`. If the key exists, apply these parameters to all subsequent output in this session:

- **verbosity_preset** — The active preset (`concise`, `standard`, `detailed`, or `custom`). Governs overall output depth.
- **question_framing** — Length of contextual lead-in before 👉 questions (`minimal`, `moderate`, or `full`).
- **tone** — Overall tone descriptor (`concise`, `conversational`, or `detailed`). Determines sentence structure and preamble length.
- **pacing** — Content density per turn (`one_concept_per_turn` or `grouped_concepts`).

### Fallback Logic

If the `conversation_style` key does not exist in the preferences file (or the file itself is missing/corrupted), apply these defaults derived from `conversation-protocol.md` and `verbosity-control.md` settings:

| Parameter | Default Value |
|-----------|--------------|
| `verbosity_preset` | `standard` |
| `tone` | `conversational` |
| `question_framing` | `moderate` |
| `pacing` | `one_concept_per_turn` |

Do not create the `conversation_style` key during resume — it will be written on the next style interaction or verbosity adjustment.

### Tone Descriptor Mapping

Use this table to translate the stored `tone` value into observable output characteristics:

| Tone | Observable Characteristics |
|------|---------------------------|
| `concise` | Short contextual lead-ins (1-2 sentences), minimal preamble before questions, direct language |
| `conversational` | Moderate lead-ins (2-4 sentences), friendly framing, balanced explanation depth |
| `detailed` | Full contextual framing (4+ sentences), thorough explanations, explicit rationale for each step |

### Style Drift Detection

After generating the first post-resume response, compare the output style against the stored `conversation_style` profile. If the response diverges from the profile (e.g., using detailed framing when the profile specifies concise tone), self-correct in subsequent turns by re-reading the profile and adjusting output to match.

When loading a new module steering file during the session, re-read the `conversation_style` profile from `config/bootcamp_preferences.yaml` to ensure module-specific instructions do not override the bootcamper's established style preferences.

## Step 2d: MCP Health Check

Before proceeding, verify that the Senzing MCP server is reachable. This ensures MCP-dependent features (code generation, fact lookup, example search) are available for the session.

### Probe

Attempt a lightweight MCP tool call with a 10-second timeout:

```text
search_docs(query="health check", version="current")
```

### Success Path

If the call returns any response (even empty results) within 10 seconds:

1. Proceed silently — do not display anything to the bootcamper.
2. Write `config/.mcp_status` with:

```json
{"last_check": "<ISO 8601 timestamp>", "status": "healthy", "error_message": null}
```

### Failure Path

If the call times out or errors after 10 seconds:

1. Write `config/.mcp_status` with:

```json
{"last_check": "<ISO 8601 timestamp>", "status": "unreachable", "error_message": "<error details>"}
```

2. Display the following warning to the bootcamper:

```text
⚠️ The Senzing MCP server is currently unreachable.

**What's unavailable:** Code generation, fact lookup, example search
**What you can still do:** Review existing artifacts, work on documentation, plan next steps

For detailed offline capabilities, see docs/guides/OFFLINE_MODE.md
```

3. Ask:

```text
👉 Would you like to continue in offline mode, or try again later?
```

### Mid-Session Recovery

Before any step that requires MCP tools, check `config/.mcp_status`. If `status` is `"unreachable"`:

1. Re-attempt the `search_docs(query="health check", version="current")` probe with a 10-second timeout.
2. If successful, update `config/.mcp_status` to `"healthy"` and display: "✅ MCP server is back online — full functionality restored."
3. If still unreachable, inform the bootcamper that MCP remains unavailable and offer alternatives.

## Step 2e: What's New Notification

Before the welcome-back banner, check whether there are CHANGELOG entries newer than the bootcamper's last session. Follow the instructions in `whats-new.md`:

1. Read the last session date from `config/session_log.jsonl` (last line's `timestamp` field)
2. Check `config/bootcamp_preferences.yaml` for `show_whats_new: false` — if set, skip
3. Parse `CHANGELOG.md` for version entries newer than the last session date
4. If new entries exist, show a brief notification (max 3 bullets) before the welcome-back banner
5. If no new entries or conditions not met, skip silently

## Step 3: Summarize and Confirm

**Display the welcome back banner:**

```text
🎓 Welcome back to the Senzing Bootcamp!
```

Present a concise summary to the user. If `current_step` is present in the progress file, include the step number and total steps for the module (count numbered steps in the module steering file). `current_step` can be either an integer (whole step) or a string sub-step identifier (dotted notation like `"5.3"` or lettered notation like `"7a"`). When it is a string, display it directly (e.g., "Step 5.3 of 12" or "Step 7a of 10"). When it is an integer, display the existing format (e.g., "Step 5 of 12"):

```text
Welcome back! Here's where you left off:

  Track: [track display name]
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

Write `config/.question_pending` with the question text above.

🛑 STOP — Wait for bootcamper response. Do not generate any additional content.

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
