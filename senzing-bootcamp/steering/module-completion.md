---
inclusion: manual
---

# Module Completion Workflow

Load this after completing any module. Handles journal entries, certificates, and path completion.

## Completion Step Ordering

The module completion process executes the following steps in a **fixed, invariant order** regardless of which module is being completed:

1. **progress_update** — Mark the module complete in `config/bootcamp_progress.json`
2. **recap_append** — Append a recap section to `docs/bootcamp_recap.md` (create file if first completion)
3. **journal_entry** — Append a journal entry to `docs/bootcamp_journal.md` (create file if first completion)
4. **completion_certificate** — Generate `docs/progress/MODULE_N_COMPLETE.md` and update the summary index
5. **next_step_options** — Present the bootcamper with concrete next-step choices

### Ordering Rules

- Each step **must complete** (or be skipped due to error) before the next step begins.
- This ordering is invariant — it applies to every module completion (Module 1 through Module 11), whether the module was completed normally or skipped.
- If a step fails (file system error, timeout exceeding 30 seconds, or unhandled exception), skip it with a logged warning and proceed to the next step. A failed predecessor does not block subsequent steps.

## Non-Blocking Error Handling

Every artifact-creation step (recap append, journal entry, completion certificate) MUST handle errors gracefully so that a single failure never blocks the bootcamper's flow.

### Per-Step Error Handling

For each of the following steps — **recap_append**, **journal_entry**, and **completion_certificate** — apply these rules:

1. **Catch file-system errors** (permission denied, disk full, path not found, or any OS-level I/O failure).
2. **Log a warning** visible to the bootcamper using this exact format:

   > ⚠️ [Step name] skipped: [reason]. This will be retried on next module completion.

   Examples:
   - `⚠️ recap_append skipped: Permission denied writing to docs/bootcamp_recap.md. This will be retried on next module completion.`
   - `⚠️ journal_entry skipped: Disk full. This will be retried on next module completion.`
   - `⚠️ completion_certificate skipped: Path not found for docs/progress/. This will be retried on next module completion.`

3. **Continue** to the next step in the defined order. Do NOT halt, raise an error, or prompt the bootcamper for intervention.
4. **Do NOT retry immediately** — the failed step will be retried on the next module completion.

### 30-Second Timeout

If any single step exceeds **30 seconds** of execution time (e.g., due to a hung file system or unresponsive disk), skip that step and log a warning:

> ⚠️ [Step name] skipped: Timed out after 30 seconds. This will be retried on next module completion.

### Predecessor Failure Does Not Block Subsequent Steps

If a predecessor step fails or is skipped:

- Subsequent steps **still execute** using only data available from previously successful steps.
- The journal entry does NOT depend on the recap append's output — it can proceed independently.
- The completion certificate does NOT depend on the journal entry — it can proceed independently.
- Even if **both** the recap append and journal entry fail, the **next_step_options** step MUST still execute and present the bootcamper with their choices.

### Retry on Next Module Completion

Failed steps are not retried within the same completion flow. Instead:

- The next time any module is completed, each step runs again from scratch.
- If the file-system issue has been resolved by then, the step will succeed normally.
- If the issue persists, the same skip-and-warn behavior applies again.

## Recap Append

The `hooks/module-recap-append.kiro.hook` hook handles this automatically as a `postTaskExecution` hook. When a module is marked complete in `config/bootcamp_progress.json`, the hook gathers session content and appends a structured Recap_Section to `docs/bootcamp_recap.md`.

### What is gathered

- **Information Shared:** Key concepts, explanations, and reference material presented during the module
- **Questions Asked:** All substantive questions the agent posed to the bootcamper
- **Answers Given:** The bootcamper's responses, maintaining 1:1 correspondence with questions
- **Actions Taken:** File creations, modifications, code generation, and commands executed
- **Duration:** Elapsed time from module start to completion

### Workflow position

The recap append executes after the progress file update (module marked complete) and before the journal entry below. It completes without requiring additional bootcamper confirmation and displays a single confirmation line (e.g., "Recap updated for Module N: [Name].").

### Non-blocking behavior

If the recap append fails for any reason (file system error, missing data), it logs a warning and continues the module completion flow. It does not halt execution, raise errors, or alter the behavior of existing hooks or the journal entry process.

### Recap File Creation

On first module completion, if `docs/bootcamp_recap.md` does not exist:

1. Create the `docs/` directory if absent
2. Read the bootcamper's name from `config/bootcamp_preferences.yaml`
   - If the file does not exist or the `name` field is missing, use **"Bootcamper"** as the default name
3. Create `docs/bootcamp_recap.md` with the following header:

```markdown
# Senzing Bootcamp Recap

**Bootcamper:** {name}
**Started:** {ISO 8601 timestamp with timezone offset, e.g. 2026-05-14T10:30:00-05:00}
**Total Duration:** {first module's session duration}

---
```

4. Append the first recap section immediately after the separator

If `docs/bootcamp_recap.md` already exists, append the new recap section at the end of the file without modifying any existing bytes in the file.

**Step ordering:** The recap append always executes after the progress file update and before the journal entry. This ensures the progress data is available when building the recap section, and the journal entry can reference a successful recap write.

### References

- Hook: `hooks/module-recap-append.kiro.hook`
- Output: `docs/bootcamp_recap.md`

## Bootcamp Journal

The journal entry step executes **after** the recap append and **before** the completion certificate. This step is **mandatory** regardless of module number (1 through 11) or completion method (normal completion or skip). It must never be omitted.

### Journal File Creation (First Module Completion)

On first module completion, if `docs/bootcamp_journal.md` does not exist:

1. Create the `docs/` directory if it does not already exist
2. Read the bootcamper's name from `config/bootcamp_preferences.yaml`
   - If the file does not exist or the `name` field is missing, use **"Bootcamper"** as the default name
3. Determine the start date as today's date in ISO 8601 format (`YYYY-MM-DD`)
4. Create `docs/bootcamp_journal.md` with the following header:

```markdown
# Bootcamp Journal

**Bootcamper:** {name from config/bootcamp_preferences.yaml}
**Started:** {YYYY-MM-DD}

---
```

5. Proceed immediately to appending the first journal entry (below)

### Journal Entry Append

After the recap append step completes (or is skipped due to error), append a journal entry to `docs/bootcamp_journal.md`. If the file already exists, append the new entry at the end **without modifying any existing content** — all prior entries must be preserved byte-for-byte.

Each journal entry uses this structure:

```markdown
## Module N: {Name} — Completed {ISO 8601 with timezone}

**What we did:** {summary}
**What was produced:** {comma-separated artifact paths}
**Why it matters:** {explanation}
**Bootcamper's takeaway:** {takeaway or N/A}

---
```

### Field Derivation Rules

| Field | Source |
|-------|--------|
| **Module number** | The module number just completed (from `config/bootcamp_progress.json`) |
| **Module name** | Derived from `config/module-dependencies.yaml` — use the `name` field for the corresponding module number |
| **Completion date** | Current timestamp in ISO 8601 format with timezone offset (e.g., `2026-05-14T10:30:00-05:00`) |
| **Summary** | 1–2 sentences describing what was accomplished during the module |
| **Artifacts** | Comma-separated list of file paths created or modified during the module session |
| **Why it matters** | Brief explanation of how this module enables subsequent work |
| **Takeaway** | The bootcamper's stated takeaway if provided during the session, otherwise `N/A` |

### Workflow Position

The journal entry step occupies position 3 in the fixed completion order:

1. progress_update
2. recap_append
3. **journal_entry** ← this step
4. completion_certificate
5. next_step_options

The journal entry does not depend on the recap append's output — if the recap append fails, the journal entry still executes using data from the progress file and session context.

### Non-blocking Behavior

If the journal file cannot be created or the entry cannot be appended (file system error, permission denied, disk full), log a warning identifying the failure reason and continue to the completion certificate step. Do not halt execution, raise errors, or retry immediately. Retry happens automatically on the next module completion.

### References

- Output: `docs/bootcamp_journal.md`
- Module names: `config/module-dependencies.yaml`
- Bootcamper name: `config/bootcamp_preferences.yaml`
- Validation: `scripts/validate_completion_artifacts.py --journal`

## Module Completion Certificate

After the journal entry, generate a completion certificate:

1. Create `docs/progress/MODULE_N_COMPLETE.md` (create `docs/progress/` directory if it doesn't exist)
2. Use the bootcamper's chosen language from `config/bootcamp_preferences.yaml` in artifact descriptions

### Certificate Template

```markdown
# Module [N]: [Title] — Complete ✅

**Completed**: [ISO 8601 date]
**Time Spent**: [duration from session analytics, or "not tracked"]
**Language**: [chosen language]

## Key Concepts Learned

- [Concept 1 — derived from module steering file steps]
- [Concept 2]
- [Concept 3]
- [Concept 4 (if applicable)]
- [Concept 5 (if applicable)]

## Artifacts Produced

| File | Description |
|------|-------------|
| [actual file path] | [language-aware description] |

## What This Enables

Now that you've completed Module [N], you can:
- [Capability — derived from module-dependencies.yaml unlocked modules]

## Session Stats

| Metric | Value |
|--------|-------|
| Total turns | [from session analytics] |
| Corrections | [from session analytics] |

---
*Generated by Senzing Bootcamp Power*
```

### Content Derivation Rules

- **Key Concepts:** Derive from the module's steering file section headings and step descriptions (3-5 concepts)
- **Artifacts:** Scan the file system for files created/modified during this module in the module's output directories
- **What This Enables:** Read `config/module-dependencies.yaml` to find which modules are now unlocked
- **Language:** Use the bootcamper's language in descriptions (e.g., "Built a Python loading script" not "Built a loading script")
- **Session Stats:** Include only if `config/session_log.jsonl` exists and has entries for this module. Omit the section entirely if no analytics are available.

### Summary Index

After generating the certificate, create or update `docs/progress/README.md`:

```markdown
# Bootcamp Progress

## Completed Modules

| Module | Title | Completed | Time |
|--------|-------|-----------|------|
| [N] | [Title] | [date] | [duration] |

## Track Progress

**[Track Name] ([Letter])**: [X]/[Y] modules complete ([Z]%)

## Total Time Invested

[total duration] across [count] modules
```

### Error Handling

Certificate generation should not block the completion flow. If it fails for any reason (file system error, missing data), log a warning and continue to the next-step options.

## Next-Step Options

After the journal entry, present 3-4 concrete options based on the module just completed. Don't just say "proceed to Module N" — give the user choices:

- **Proceed:** "Ready to move on to Module [N] ([name])?"
- **Iterate:** "Would you like to improve anything from this module first?"
- **Explore:** "Would you like to explore further — visualize entities, examine match explanations, or search by attributes? (For other modules: dig deeper into what we just produced.)"
- **Undo:** "Roll back this module's work with `python3 scripts/rollback_module.py --module N`"
- **Share:** "Would you like to prepare a summary to share with your team?"

When the bootcamper asks to roll back a module, always run `rollback_module.py --preview --module N` first and present the results conversationally (files affected, safety assessment, downstream impact) before asking whether they want to proceed. Only execute `rollback_module.py --yes --module N` after explicit confirmation.

Present these as a single list for the bootcamper to choose from.

### ⛔ Immediate Execution on Affirmative Response

**When the bootcamper says "yes" to "Ready to move on to Module [N]?", the agent MUST immediately execute the next module's startup sequence:**

1. Display the module banner
2. Show the journey map
3. Begin Step 1

**There are ZERO permitted steps between the affirmative response and the module startup sequence.**

⛔ **PROHIBITED between affirmative response and module startup:**

- Intermediate acknowledgment (e.g., "Great! Let's get started...", "Awesome, moving on...")
- Progress-saving behavior (e.g., "Let me save your progress first...", "Let me note where we left off...")
- Session-ending behavior (e.g., "We can pick this up next time...", "Let me wrap up this session...")
- Any text output that is not the module banner

The affirmative response IS the trigger. The module banner IS the next thing the bootcamper sees. Nothing else.

**Module 3 special case:** The visualization offer (web page with interactive features) should already have been presented before reaching this workflow. If the user declined, the Explore option above gives them another chance.

## Path Completion Detection

After each module, check if the user finished their track's last module:

| Track | Complete after |
|-------|----------------|
| Core Bootcamp    | Module 7  |
| Advanced Topics  | Module 11 |

## Path Completion Celebration

> **Note:** The completion-summary document (`docs/completion_summary.md`) is always created at track completion; the completion-summary offer in its existing position (between the celebration and the export option) governs only the shareable PDF/share, not the document's creation.

When track is complete, present:

- 🎉 "You've completed the [track name]!"
- Summary of all artifacts built (code, data, docs)
- Where everything lives (src/, data/transformed/, docs/, config/, database/)
- Reference to `docs/bootcamp_journal.md`
- Next options: switch to longer track (modules carry forward), harden for production, or start using the code
- Export option: "Would you like to export a shareable report of your bootcamp results?" — when accepted, run `python3 scripts/export_results.py` and present the output path to the bootcamper. This option appears only at track completion, not after every module.
- Record export offer (after the export option, before the analytics offer): "📋 Would you like a record of your bootcamp journey? You can share it with your team or use it to replay the same setup on another project." — when accepted, run `python3 scripts/record_export.py` and present the output path (`docs/bootcamp_record.yaml`) to the bootcamper. When declined, proceed to the next step without generating any export file.
- Analytics offer (after the record export offer, before the certificate generation): "📊 Would you like to see analytics on your bootcamp journey? I can show you time distribution, friction points, and how your pace compares to baselines." — when accepted, run `python3 scripts/bootcamp_analytics.py` and present the output conversationally.
- Certificate generation (after the analytics offer, before the graduation offer):
  Run `python3 senzing-bootcamp/scripts/generate_graduation_certificate.py` silently
  (no confirmation prompt). If it succeeds, display:
  "🎓 Graduation certificate generated at docs/graduation/"
  If it fails, log a warning and continue without blocking subsequent steps.
- Graduation offer (after the certificate generation, before the feedback reminder):
  1. Read `skip_graduation` from `config/bootcamp_preferences.yaml`. If `skip_graduation` is `true`, skip the graduation offer entirely.
  2. If not skipped, present: "🎓 Would you like to run the graduation workflow? It will help you turn your bootcamp project into a production-ready codebase — clean structure, production configs, CI/CD pipeline, and a migration checklist."
  3. If accepted: load `steering/graduation.md` and begin the workflow.
  4. If declined: ask "Would you like me to remember this choice so I don't ask again?" If the bootcamper confirms, set `skip_graduation: true` in `config/bootcamp_preferences.yaml`. Then continue with the remaining post-completion options.
- Feedback Submission Reminder (after the graduation offer sequence, before the retrospective):
  1. Check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists.
  2. If it exists, read the file and check for at least one `## Improvement:` heading below the `## Your Feedback` section (headings outside fenced code blocks count as real entries; the template block inside a fenced code block does not).
  3. If feedback entries exist, display: "📋 You have feedback saved in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`. Would you like to share it with the power author?"
  4. If the bootcamper accepts, present the sharing options:

     **How would you like to share your feedback?**

     1. **Email** — Send to <support@senzing.com> with subject "Senzing Bootcamp Power Feedback". I can format the content for easy copy-paste.
     2. **GitHub Issue** — Create an issue on the senzing-bootcamp power repository. I can format it as a markdown-ready issue body.
     3. **Copy path** — I'll show you the full file path so you can share it however you prefer.

     Do not automatically send emails or create GitHub issues — wait for explicit bootcamper confirmation before taking any external action.
  5. If the bootcamper declines (says "no", "skip", "not now", or any declining response), proceed to the next step without re-prompting about feedback. Do not ask about feedback sharing again during this track completion sequence.
  6. If the feedback file does not exist or contains no entries beyond the template header, display the fallback: "Say 'bootcamp feedback' to share your experience"

Load `lessons-learned.md` and offer the retrospective.
