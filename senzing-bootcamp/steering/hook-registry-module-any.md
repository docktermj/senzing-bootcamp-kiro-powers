---
inclusion: manual
---

# Hook Registry — any module (Full Prompts)

Full hook prompts for any module, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## any module Hooks

**backup-project-on-request** (userTriggered → askAgent)

Prompt:

````text
The user wants to back up their project. Run the backup script: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows). Create the backups/ directory first if it doesn't exist.
````

- id: `backup-project-on-request`
- name: `to back up your project`
- description: `Run project backup when user clicks the hook button. Avoids firing on every prompt — use the manual trigger button in the Agent Hooks panel instead.`

**error-recovery-context** (postToolUse → askAgent, toolTypes: shell)

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
- description: `Detects shell command failures and consults common-pitfalls.md and recovery-from-mistakes.md to provide targeted error recovery guidance during bootcamp modules.`

**git-commit-reminder** (userTriggered → askAgent)

Prompt:

````text
The user wants to commit their bootcamp progress. Check config/bootcamp_progress.json for the current module number and list of completed modules. Then suggest a git commit with a descriptive message like: git add . && git commit -m "Complete Module [N]: [Module Name]". Show the user the command and ask if they'd like you to run it.
````

- id: `git-commit-reminder`
- name: `to remind you to commit`
- description: `Reminds the user to commit their work after completing a module. Triggered manually via button click.`

**module-completion-celebration** (agentStop → askAgent)

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
- description: `Detects module completion boundaries and displays a brief celebration with next-step guidance.`

**module-recap-append** (agentStop → askAgent)

Prompt:

````text
If `config/.question_pending` exists, produce no output at all — defer to `ask-bootcamper`.

You are checking whether the bootcamper just completed a module and, if so, appending a structured recap section to docs/bootcamp_recap.md. Follow these steps exactly:

1. BOUNDARY DETECTION: Read `config/bootcamp_progress.json` and examine the `modules_completed` array. If `modules_completed` has not changed (no new module number was added since the previous state), produce no output at all — do nothing, do not acknowledge, do not explain. Let the conversation continue normally. This boundary detection fires for EVERY new entry added to `modules_completed`, INCLUDING the final module of a track. Track completion (graduation or celebration) MUST NOT suppress the per-module recap section: if the newly completed module is the last module of the bootcamper's track, still append its recap section exactly as for any other module.

2. IDENTIFY COMPLETED MODULE: If a new module number appears in `modules_completed`, identify that module number. Read `config/module-dependencies.yaml` to find the module name corresponding to that number.

3. GATHER SESSION CONTENT: Review the current session context to collect:
   - Information Shared: key concepts, explanations, and reference material presented to the bootcamper during this module
   - Questions Asked: all substantive questions the agent posed to the bootcamper (exclude rhetorical or transitional prompts)
   - Answers Given: the bootcamper's responses to each question, maintaining 1:1 correspondence with questions
   - Actions Taken: all file creations, modifications, code generation, configuration changes, and commands executed during the module

4. COMPUTE DURATION (no placeholders): Obtain the per-module Duration and the cumulative Total Duration from the deterministic planner instead of from session context. Run:

   ```
   python senzing-bootcamp/scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --journal docs/bootcamp_journal.md --progress-dir docs/progress --plan
   ```

   Parse the emitted JSON. Use `module_durations["N"]` (where N is the completed module number) as that module's Duration, and `total_duration` as the cumulative Total Duration. These values are computed from the ISO 8601 timestamps stored in `step_history` and the top-level `started_at` in `config/bootcamp_progress.json`. If the planner does not return a value for this module (the key is absent or null), OMIT the `### Duration` field for this module entirely — do NOT write a placeholder such as "Module N session". If `total_duration` is null, OMIT the **Total Duration** value in the header rather than writing a placeholder. If the planner cannot be run (file-system error or timeout), log a warning and continue, omitting the Duration fields rather than fabricating a value.

5. GET BOOTCAMPER NAME: Read `config/bootcamp_preferences.yaml` and extract the bootcamper's name. If the file does not exist or the name field is missing, use "Bootcamper" as the default.

6. CREATE OR VERIFY FILE: Check if `docs/bootcamp_recap.md` exists.
   - If it does NOT exist, create it with this header (include the **Total Duration** line only when the planner returned a non-null `total_duration`; otherwise omit that line entirely):
     ```
     # Senzing Bootcamp Recap

     **Bootcamper:** [Name]
     **Started:** [ISO 8601 timestamp with timezone of current time]
     **Total Duration:** [total_duration from planner]

     ---
     ```
   - If it already exists, do NOT overwrite or modify any existing content.

7. APPEND RECAP SECTION: Append the following structured section to the end of `docs/bootcamp_recap.md`. Include the `### Duration` heading and value ONLY when the planner returned a value for this module; when no reliable duration was computed, omit the `### Duration` heading and its value entirely:
   ```

   ## Module N: [Module Name] — [ISO 8601 timestamp with timezone]

   ### Information Shared
   - [Concept or explanation presented]
   - [Reference material shared]

   ### Questions Asked
   1. [Agent question to bootcamper]
   2. [Agent question to bootcamper]

   ### Answers Given
   1. [Bootcamper response to question 1]
   2. [Bootcamper response to question 2]

   ### Actions Taken
   - Created `[file path]`
   - Modified `[file path]`
   - Ran `[command]`

   ### Duration
   [module_durations["N"] from planner]

   ---
   ```

8. UPDATE TOTAL DURATION: If the file header contains a **Total Duration** line and the planner returned a non-null `total_duration`, update it to that value. The total duration is rolled up from the real per-module elapsed times and must be monotonically non-decreasing. If the planner returned null for `total_duration`, leave the header without a Total Duration value rather than writing a placeholder.

9. CONFIRMATION: Display a single brief line confirming the recap was updated, for example: "Recap updated for Module N: [Module Name]."

CONSTRAINTS:
- All timestamps MUST use ISO 8601 format with timezone offset (e.g., 2026-05-23T10:30:00-05:00).
- Preserve all existing file content byte-for-byte when appending.
- Duration and Total Duration values come ONLY from `completion_artifacts.py`; never derive them from session context and never write a placeholder such as "Module N session". When the planner omits a value, omit the corresponding field.
- If any section has no content (e.g., no questions were asked), include the subsection heading with a single item "None" or "N/A". This does NOT apply to the `### Duration` field, which is omitted entirely when the planner returns no value.
- If the file cannot be written due to a file system error, log a warning message and continue without blocking the module completion flow. Do NOT raise an error or halt execution.
- Do NOT alter the behavior of any other hooks (celebration, journal entry, etc.).
- Keep the recap factual and concise — summarize rather than reproduce entire conversations.
- Do NOT include secrets, credentials, environment variable values, or connection strings in the recap content.
- Module sections must appear in chronological order of completion timestamps.
````

- id: `module-recap-append`
- name: `to append module recap on completion`
- description: `Appends a structured recap section to docs/bootcamp_recap.md when a module is completed.`

**session-log-events** (postToolUse → runCommand, toolTypes: write)

- id: `session-log-events`
- name: `to log session events after write operations`
- description: `Logs a session event after write operations complete. The IDE appends the log line directly via a runCommand (no agent round-trip), invoking senzing-bootcamp/scripts/log_write_event.py, which records a generic write action (timestamp + current module) to config/session_log.jsonl for the completion summary.`
