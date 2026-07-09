---
inclusion: manual
---

## Markdown Authoring: Free-Form During the Bootcamp, Normalized at Graduation

While the bootcamper is working through the modules, write every Markdown_Artifact
(`docs/bootcamp_recap.md`, mapper docs, progress notes) **free-form**:
capture the content first and defer structural formatting. Do **not** stop to make in-flight Markdown
match a downstream tool's exact schema (for example the recap-PDF heading/subsection schema), and do
**not** gate or block a module step on an artifact conforming to a Consumer_Schema. Getting the right
content down naturally matters more than matching a rigid shape mid-session.

A single **normalization pass at graduation** rewrites each artifact into the schema its consumer
expects, applies CommonMark style fixes once across all files, and only then generates derived
artifacts (the recap PDF). See `steering/graduation.md` Step 0 (Markdown Normalization Pass) and the
`scripts/normalize_markdown.py` script for the graduation-time behavior.

This deferral is safe because it is paired with the tolerant recap parser and raw-Markdown fallback
delivered by the `recap-pdf-content-loss-fix` spec: even if normalization is skipped or only partially
maps a file to its schema, the downstream parser falls back to the raw Markdown so a schema or style
mismatch **never silently drops content**. The two changes are designed as a pair — free-form authoring
here, tolerant consumption plus a graduation normalization pass there.

Keep capturing all the content the modules rely on during the run: the recap section (including its
`### Journal` subsection) and mapper docs are still written for every completed module exactly as
described below. Only the *structural formatting* moves to graduation; nothing about *what* gets
captured changes.

## Backfill for Already-Completed Modules

On a completion boundary — and before appending the new module's artifacts — reconcile the artifact set for **all** already-completed modules so modules finished before the artifact logic existed (or skipped by an earlier partial run) are not left behind.

1. Run the deterministic planner to discover exactly which artifacts are missing:

   ```text
   python senzing-bootcamp/scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --progress-dir docs/progress --plan
   ```

2. Parse the emitted JSON. It lists, by set difference only (never re-emitting existing artifacts):
   - `recap_modules` — completed modules missing a recap section (each backfilled section includes the `### Journal` subsection)
   - `certificate_modules` — completed modules missing a completion certificate (applying the uniform-certificate rule: either every completed module gets a certificate or none do)
   - `module_durations` — per-module Duration strings computed from `step_history` (only modules with reliable timing appear)
   - `total_duration` — the cumulative `Total Duration`, or `null` when timing is unreliable

3. For each module listed, generate the missing artifact(s) using the same templates and field-derivation rules defined below, sourcing Duration / Time Spent from the planner's `module_durations` (omit the field when the module is absent from `module_durations`). Apply certificates uniformly across the modules in `certificate_modules`.

4. The plan is idempotent: re-running on a complete, consistent set yields empty module lists, so backfill produces no duplicates. If the planner cannot be run (file-system error or timeout), log a warning and continue with the current module's artifacts rather than halting.

## Recap Append

The recap append is a **synchronous, verified step of the module-completion workflow** (step 2 in the fixed order), not solely an asynchronous `Stop` hook. The `hooks/module-recap-append.json` hook still appends the structured section on boundary detection, but the workflow now treats the append as complete only after it has **read back** the file and confirmed the section persisted — so a write that does not persist across a session boundary, or a hook invocation that does not write on the final module, is detected and repaired instead of silently lost.

When a module is marked complete in `config/bootcamp_progress.json`, gather session content and append a **consolidated** Recap_Section to `docs/bootcamp_recap.md`, then verify and (if needed) backfill before reporting success. A single consolidated append now carries both the structured recap content and the narrative `### Journal` subsection that was formerly written to the retired `docs/bootcamp_journal.md` — there is no separate journal step.

### What is gathered

- **Information Shared:** Key concepts, explanations, and reference material presented during the module
- **Questions & Responses:** Each substantive question the agent posed, immediately paired with the bootcamper's response, in ascending ask order. This is rendered as the single `### Questions & Responses` section of interleaved `- **Q:**` / `- **R:**` pairs that the `module-recap-append` hook and `format_qr_section` emit (never as separate "Questions Asked" / "Answers Given" headings).
- **Actions Taken:** File creations, modifications, code generation, and commands executed
- **Duration:** The per-module elapsed time and cumulative `Total Duration` come from `scripts/completion_artifacts.py` (computed from the ISO 8601 timestamps in `step_history` and the top-level `started_at`), never from session context. When the planner returns no value for a module, omit the `### Duration` field entirely rather than writing a placeholder such as "Module N session".
- **Journal:** The narrative `### Journal` subsection carrying the four fields formerly written to the Legacy_Journal_File — `**What we did:**` (1–2 sentence summary of what was accomplished), `**What was produced:**` (comma-separated artifact paths created or modified), `**Why it matters:**` (how this module enables subsequent work), and `**Bootcamper's takeaway:**` (the bootcamper's stated takeaway, or `N/A` when none was provided). See `config/module-dependencies.yaml` for module names and `config/bootcamp_preferences.yaml` for the bootcamper name used elsewhere in the header.

### Consolidated Recap_Section format

Each Recap_Section appended to `docs/bootcamp_recap.md` follows this structure — the `### Journal` subsection is appended after `### Duration`:

```markdown
## Module N: {Name} — {ISO 8601 timestamp}

### Information Shared
- {content}

### Questions & Responses
- **Q:** {question}
    - **R:** {response}

### Actions Taken
- {content}

### Duration
{value from planner — omit this subsection entirely when the planner returns no value}

### Journal
**What we did:** {summary}
**What was produced:** {comma-separated artifact paths}
**Why it matters:** {explanation}
**Bootcamper's takeaway:** {takeaway or N/A}

---
```

### Synchronous verification and backfill (before reporting success)

After appending (or after the hook reports it appended), confirm the section actually landed:

1. Read `docs/bootcamp_recap.md` and check for a `## Module N:` heading for the **just-completed** module N.
2. If the heading is **present**, the append is verified — display the confirmation line and proceed.
3. If the heading is **absent** (write lost, hook miss, or session boundary), do NOT report success. Backfill it deterministically by running the applier, which appends a `## Module N:` section (including its `### Journal` subsection scaffold) for every completed module that is missing one (append-around, never rewriting existing bytes; idempotent when nothing is missing):

   ```text
   python senzing-bootcamp/scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --progress-dir docs/progress --backfill
   ```

   The applier exits non-zero and prints which modules remain missing if verification still fails after the write, so a silent gap can never be reported as success. Re-read the file and confirm the `## Module N:` heading is now present before continuing.

This append-and-verify cycle applies to **every** completed module, **including the final module of a track**: track completion (graduation or celebration) MUST NOT suppress the per-module recap section. The final module's section is appended and verified exactly as for any other module (see `module-completion-track.md`).

### Workflow position

The consolidated recap append executes after the progress file update (module marked complete) and before the completion certificate. It completes without requiring additional bootcamper confirmation and displays a single confirmation line (e.g., "Recap updated for Module N: [Name].") only after the section is verified present.

### Non-blocking behavior

If the consolidated recap append or its backfill fails for any reason (file system error, missing data), it logs a warning and continues the module completion flow. It does not halt execution, raise errors, or alter the behavior of existing hooks. The track-completion reconciliation pass (see below and `module-completion-track.md`) is the final safety net: it re-runs the same applier so any section still missing at graduation is backfilled before the deliverable is rendered.

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

**Step ordering:** The consolidated recap append always executes after the progress file update and before the completion certificate. This ensures the progress data is available when building the recap section.

### References

- Hook: `hooks/module-recap-append.json`
- Output: `docs/bootcamp_recap.md`

## Module Completion Certificate

The completion certificate is driven by the **same boundary-detection trigger** as the consolidated recap append (see the Shared Boundary-Detection Trigger section above), so every newly completed module — including the final module of a track — gets a certificate. Certificates are applied **uniformly**: either every completed module has a `docs/progress/MODULE_N_COMPLETE.md` or none do (the planner's `certificate_modules` list enforces this).

After the consolidated recap append, generate a completion certificate:

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
