---
inclusion: manual
---

# Hook Registry — any module (Full Prompts)

Full hook prompts for any module, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## any module Hooks

**capture-qa-events** (Stop → command)

- id: `capture-qa-events`
- name: `to record the pending question on the Q&A cadence`
- trigger: `Stop`
- action: `command`

**enforce-critical-artifacts** (Stop → command)

- id: `enforce-critical-artifacts`
- name: `to guarantee critical graduation artifacts on agent stop`
- trigger: `Stop`
- action: `command`

**error-recovery-context** (PostToolUse → agent, matcher: `execute_bash`)

Prompt:

````text
If the shell command exited with code zero, produce no output at all — do not acknowledge, do not explain, do not print anything. STOP immediately and return nothing.

If the exit code is non-zero, check whether `config/bootcamp_progress.json` exists. If it does not exist, produce no output at all — STOP immediately and return nothing.

For non-zero exit codes with a valid bootcamp session:

1. Extract the error message, exit code, and command context from the tool execution result.

2. If the error message contains a SENZ error code prefix (e.g., SENZ0001, SENZ2034), call `explain_error_code` directly to get the official explanation and include it in your response.

3. For non-SENZ errors: Read `senzing-bootcamp/steering/common-pitfalls.md` and `senzing-bootcamp/steering/recovery-from-mistakes.md`. Read `config/bootcamp_progress.json` to determine the current module number. Scope your pitfall lookup to the current module section first. If no match is found in the module-specific section, fall back to the General Pitfalls section and the Troubleshooting by Symptom section.

4. When a known solution is found: present only the matching fix. Cite the source section (e.g., "From common-pitfalls.md § Module 3 — Docker Issues"). Include the specific command or action needed to resolve the issue. Do not dump the entire pitfalls file.

5. When multiple pitfalls could apply, present the most specific match based on the current module context. Prefer module-scoped matches over general matches.

6. When no known solution matches the error, fall back to normal troubleshooting. Do not claim a known solution exists when none was found in the pitfalls or recovery files.
````

- id: `error-recovery-context`
- name: `to help recover from errors`
- trigger: `PostToolUse`
- matcher: `execute_bash`
- action: `agent`

**module-completion-celebration** (Stop → agent)

Prompt:

````text
If `config/.question_pending` exists, produce no output at all — defer to `ask-bootcamper`.

You are checking whether the bootcamper just completed a module. Follow these steps exactly:

1. BOUNDARY DETECTION: Read `config/bootcamp_progress.json` and examine the `modules_completed` array. If `modules_completed` has not changed (no new module number was added since the previous state), produce no output at all — do nothing, do not acknowledge, do not explain, do not print any message. Let the conversation continue normally.

2. IDENTIFY COMPLETED MODULE: If a new module number appears in `modules_completed`, identify that module number. Read `config/module-dependencies.yaml` and find the module name corresponding to that number.

3. CELEBRATION MESSAGE: Display a congratulatory banner that includes the completed module number and name. Provide a one-sentence summary of what the bootcamper built or accomplished in that module.

4. NEXT MODULE: Read `config/bootcamp_preferences.yaml` to determine the bootcamper's selected track. Then consult `config/module-dependencies.yaml` for the track definition to find the next module in sequence. If more modules remain in the track, display the next module's number and name and offer to begin it immediately. If all modules in the track are complete, display a graduation acknowledgment congratulating the bootcamper on finishing the entire track. This track-completion (graduation) acknowledgment is display-only: it runs in addition to — never instead of — the per-module artifact path (recap section, journal entry, and completion certificate) for the final module, which is produced separately by the shared boundary-detection trigger that governs the module-completion workflow. Do NOT treat track completion as a reason to suppress, skip, or replace the final module's per-module artifacts.

5. FULL WORKFLOW MENTION: Let the bootcamper know they can say "completion" or "journal" to access the full completion workflow including reflection. Note that the journal entry, recap section, and certificate are already produced automatically by the shared boundary-detection trigger on module completion — this mention is for the optional reflection step, not because those artifacts require manual invocation.

CONSTRAINTS:
- Do NOT write any files.
- Do NOT run any scripts or commands.
- Do NOT perform file-system scans or directory listings.
- ONLY read these three config files: `config/bootcamp_progress.json`, `config/module-dependencies.yaml`, and `config/bootcamp_preferences.yaml`.
- Keep the celebration concise: one banner line, one summary sentence, and the next-step information.
- Do NOT perform journal entries, generate certificates, or ask reflection questions — those belong to the full completion workflow.
````

- id: `module-completion-celebration`
- name: `to celebrate module completion`
- trigger: `Stop`
- action: `agent`

**session-log-events** (PostToolUse → command, matcher: `fs_write|str_replace|fs_append`)

- id: `session-log-events`
- name: `to log session events after write operations`
- trigger: `PostToolUse`
- matcher: `fs_write|str_replace|fs_append`
- action: `command`
