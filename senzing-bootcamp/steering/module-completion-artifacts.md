---
inclusion: manual
---

## Backfill for Already-Completed Modules

On a completion boundary — and before appending the new module's artifacts — reconcile the artifact set for **all** already-completed modules so modules finished before the artifact logic existed (or skipped by an earlier partial run) are not left behind.

1. Run the deterministic planner to discover exactly which artifacts are missing:

   ```text
   python senzing-bootcamp/scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --journal docs/bootcamp_journal.md --progress-dir docs/progress --plan
   ```

2. Parse the emitted JSON. It lists, by set difference only (never re-emitting existing artifacts):
   - `recap_modules` — completed modules missing a recap section
   - `journal_modules` — completed modules missing a journal entry
   - `certificate_modules` — completed modules missing a completion certificate (applying the uniform-certificate rule: either every completed module gets a certificate or none do)
   - `module_durations` — per-module Duration strings computed from `step_history` (only modules with reliable timing appear)
   - `total_duration` — the cumulative `Total Duration`, or `null` when timing is unreliable

3. For each module listed, generate the missing artifact(s) using the same templates and field-derivation rules defined below, sourcing Duration / Time Spent from the planner's `module_durations` (omit the field when the module is absent from `module_durations`). Apply certificates uniformly across the modules in `certificate_modules`.

4. The plan is idempotent: re-running on a complete, consistent set yields empty module lists, so backfill produces no duplicates. If the planner cannot be run (file-system error or timeout), log a warning and continue with the current module's artifacts rather than halting.

## Recap Append

The `hooks/module-recap-append.kiro.hook` hook handles this automatically as a `postTaskExecution` hook. When a module is marked complete in `config/bootcamp_progress.json`, the hook gathers session content and appends a structured Recap_Section to `docs/bootcamp_recap.md`.

### What is gathered

- **Information Shared:** Key concepts, explanations, and reference material presented during the module
- **Questions Asked:** All substantive questions the agent posed to the bootcamper
- **Answers Given:** The bootcamper's responses, maintaining 1:1 correspondence with questions
- **Actions Taken:** File creations, modifications, code generation, and commands executed
- **Duration:** The per-module elapsed time and cumulative `Total Duration` come from `scripts/completion_artifacts.py` (computed from the ISO 8601 timestamps in `step_history` and the top-level `started_at`), never from session context. When the planner returns no value for a module, omit the `### Duration` field entirely rather than writing a placeholder such as "Module N session".

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

The journal entry step executes **after** the recap append and **before** the completion certificate. It is driven by the **same boundary-detection trigger** as the recap append (see the Shared Boundary-Detection Trigger section above), so every newly completed module — including the final module of a track — gets a journal entry without the bootcamper having to invoke this workflow explicitly. This step is **mandatory** regardless of module number (1 through 11) or completion method (normal completion or skip). It must never be omitted.

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

The completion certificate is driven by the **same boundary-detection trigger** as the recap append and journal entry (see the Shared Boundary-Detection Trigger section above), so every newly completed module — including the final module of a track — gets a certificate. Certificates are applied **uniformly**: either every completed module has a `docs/progress/MODULE_N_COMPLETE.md` or none do (the planner's `certificate_modules` list enforces this).

After the journal entry, generate a completion certificate:

1. Create `docs/progress/MODULE_N_COMPLETE.md` (create `docs/progress/` directory if it doesn't exist)
2. Use the bootcamper's chosen language from `config/bootcamp_preferences.yaml` in artifact descriptions

### Certificate Template

```markdown
# Module [N]: [Title] — Complete ✅

**Completed**: [ISO 8601 date]
**Time Spent**: [per-module Duration from scripts/completion_artifacts.py — omit this line entirely when the planner returns no value for the module, rather than writing a placeholder]
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
- **Time Spent / Summary Index time:** Source the certificate `Time Spent`, the Summary Index `Time` column, and the `Total Time Invested` value from `scripts/completion_artifacts.py` (`module_durations` and `total_duration`). Omit the value when the planner returns none for that module rather than emitting a placeholder.

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
