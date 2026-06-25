# Bugfix Requirements Document

## Introduction

The senzing-bootcamp power is supposed to produce a consistent set of per-module
completion artifacts every time a bootcamper finishes a module: a recap section
in `docs/bootcamp_recap.md`, a journal entry in `docs/bootcamp_journal.md`, a
completion certificate at `docs/progress/MODULE_N_COMPLETE.md`, and a real
elapsed-time Duration value within the recap. In practice these artifacts are
generated for only some modules, not all of them.

This bug groups four related feedback items (from `SENZING_BOOTCAMP_POWER_FEEDBACK.md`)
that share a single root cause: the per-module artifact generation governed by
the module-completion boundary-detection logic does not fire reliably on every
module completion. A project whose `config/bootcamp_progress.json` shows
`modules_completed: [1, 2, 3, 4, 5, 6, 7]` with gate `7_complete: completed`
ends up with:

- A recap missing the Module 7 section (sections present only for Modules 1-6).
- "Duration" values that are meaningless placeholders ("Module N session") for
  every module and for the header "Total Duration".
- Completion certificates only for Modules 6 and 7, implying Modules 1-5 were
  skipped.
- Journal entries only for Modules 3, 6, and 7, missing Modules 1, 2, 4, and 5.

The fix is to make per-module artifact generation fire together on every module
completion via the same boundary-detection logic (triggering on every new entry
added to `modules_completed`, including the final module of a track), capture
real timing from the ISO timestamps already stored in `step_history`, and apply
each artifact type uniformly across all completed modules — including backfilling
artifacts for modules completed before the fix.

## Bug Analysis

### Current Behavior (Defect)

What currently happens when a module — especially the final module of a track or
a module completed before the artifact logic existed — is marked complete.

1.1 WHEN a module is marked complete in `config/bootcamp_progress.json` (a new entry is added to `modules_completed`) but the boundary detection does not fire for it (e.g., the final module of a track such as Module 7) THEN the system does not append a corresponding recap section to `docs/bootcamp_recap.md`, leaving the recap missing that module
1.2 WHEN the recap is rendered for any completed module THEN the system writes the placeholder text "Module N session" into that module's Duration section instead of an actual elapsed time
1.3 WHEN the recap header is rendered THEN the system writes a meaningless "Total Duration" value (e.g., "Module N session") rather than a real cumulative elapsed time
1.4 WHEN multiple modules have been completed THEN the system has produced `docs/progress/MODULE_N_COMPLETE.md` certificates for only some of them (e.g., Modules 6 and 7), leaving a partial set that implies the earlier modules were skipped
1.5 WHEN multiple modules have been completed THEN the system has appended journal entries to `docs/bootcamp_journal.md` for only some of them (e.g., Modules 3, 6, and 7), leaving entries missing for the others (Modules 1, 2, 4, and 5)
1.6 WHEN a project already has artifacts produced for only some completed modules THEN the system provides no mechanism to backfill the missing recap sections, journal entries, or certificates for the already-completed modules

### Expected Behavior (Correct)

What should happen instead. Each clause corresponds to the defect clause for the
same condition.

2.1 WHEN a module is marked complete in `config/bootcamp_progress.json` (a new entry is added to `modules_completed`), including the final module of a track THEN the system SHALL append a recap section for that module to `docs/bootcamp_recap.md`, with boundary detection triggering on every new entry in `modules_completed`
2.2 WHEN the recap is rendered for a completed module THEN the system SHALL compute the module's real elapsed time from the ISO 8601 timestamps stored for that module in `step_history` and write it into the Duration section; IF reliable timing cannot be derived THEN the system SHALL omit the Duration field entirely rather than emit a placeholder
2.3 WHEN the recap header is rendered THEN the system SHALL compute the cumulative Total Duration by rolling up the real per-module elapsed times; IF reliable timing cannot be derived THEN the system SHALL omit the Total Duration field rather than emit a placeholder
2.4 WHEN modules have been completed THEN the system SHALL apply completion certificates uniformly: produce a `docs/progress/MODULE_N_COMPLETE.md` for every completed module (or none at all), consistently across all modules
2.5 WHEN a module is marked complete THEN the system SHALL append a journal entry for that module to `docs/bootcamp_journal.md`, driven by the same boundary detection, so every completed module has an entry
2.6 WHEN a project already has artifacts produced for only some completed modules THEN the system SHALL backfill the missing recap sections, journal entries, and certificates so that the per-module artifact set is complete and consistent for all completed modules

### Unchanged Behavior (Regression Prevention)

Existing behavior that must be preserved.

3.1 WHEN a module completion appends a new recap section or journal entry THEN the system SHALL CONTINUE TO preserve all pre-existing content in `docs/bootcamp_recap.md` and `docs/bootcamp_journal.md` byte-for-byte, without overwriting or reordering already-correct entries
3.2 WHEN an artifact-creation step (recap append, journal entry, completion certificate) encounters a file-system error or timeout THEN the system SHALL CONTINUE TO handle the error non-blockingly — log a warning and proceed to the next step without halting the module-completion flow
3.3 WHEN a module is completed THEN the system SHALL CONTINUE TO execute the completion steps in the fixed, invariant order (progress_update, recap_append, journal_entry, completion_certificate, next_step_options)
3.4 WHEN `config/.question_pending` exists at completion-check time THEN the system SHALL CONTINUE TO defer to `ask-bootcamper` and produce no completion-artifact output
3.5 WHEN `modules_completed` has not gained a new entry since the previous state THEN the system SHALL CONTINUE TO produce no recap, journal, or certificate output (no spurious duplicate artifacts)
3.6 WHEN the module-completion-celebration hook runs THEN the system SHALL CONTINUE TO display its celebration and next-step guidance without writing files, unaffected by the artifact-generation changes
3.7 WHEN `config/bootcamp_preferences.yaml` is missing or lacks a `name` field THEN the system SHALL CONTINUE TO use "Bootcamper" as the default name in artifact headers
