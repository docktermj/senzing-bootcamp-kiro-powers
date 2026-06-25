---
inclusion: manual
---

# Module Completion Workflow

Load this after completing any module. This file is the **Module_Completion_Root** — a lightweight router. It holds the completion-step ordering overview and the Shared Boundary-Detection Trigger rules, then points to the cohesive slices that carry each completion concern (artifact generation, non-blocking error handling, next-step flow, and track completion).

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

## Shared Boundary-Detection Trigger

The **recap_append**, **journal_entry**, and **completion_certificate** steps all fire from the **same boundary-detection trigger** — the comparison of the current `modules_completed` array against the prior state. There is no longer a split where the recap is appended by a hook while the journal entry and certificate run only when the bootcamper explicitly invokes this workflow. When boundary detection observes a newly completed module, all three artifact steps run together (followed by `next_step_options`), so a completed module never ends up with only a subset of its artifacts.

### Trigger Rules

- **Fire on every new entry.** Whenever a module number is added to `modules_completed`, run the recap section, journal entry, and completion certificate for that module — in the fixed step order above.
- **Include the final module of a track.** Track completion (graduation or celebration) MUST NOT suppress the per-module artifact path. If the newly completed module is the last module of the bootcamper's track (Module 7 for Core, Module 11 for Advanced), still produce its recap section, journal entry, and certificate exactly as for any other module. The celebration path runs in addition to — never instead of — the per-module artifacts.
- **Defer when a question is pending.** If `config/.question_pending` exists at completion-check time, produce no completion-artifact output at all (no recap, journal, or certificate) and defer to `ask-bootcamper`. This deferral is unchanged.
- **No-op when nothing new completed.** If `modules_completed` has not gained a new entry since the previous state, produce no recap, journal, or certificate output — no spurious duplicate artifacts. This no-op behavior is unchanged.

### Final-Message Ordering (recap vs. forward transition)

A module-completion turn that expects input must end with exactly one live pending question (👉) as its **final message** (per the Final-Message Invariant in `conversation-protocol.md`). Run the recap/confirmation BEFORE the forward transition question, or re-surface the forward "Ready for Module X" prompt (👉) as the final message after any recap/confirmation, with `config/.question_pending` (re)written for it. A recap/confirmation line (e.g., "Recap updated for Module N") must never be the final message of a completion turn.

This ordering rule does not change the fixed completion step order above, the defer-when-pending / no-op trigger rules, or the affirmative-transition commitment: an affirmative answer to "Ready for Module X?" still immediately starts the next module in the same turn with its banner, journey map, before/after framing, and Step 1.

## Completion Slice Manifest

The detailed completion behavior lives in cohesive slices under `senzing-bootcamp/steering/`. Each completion concern maps to exactly **one** slice. Load only the slice you need for the concern at hand:

| Slice file | Single concern |
|---|---|
| `module-completion-artifacts.md` | Artifact generation — backfill, recap append, bootcamp journal entry, module completion certificate, and summary index |
| `module-completion-error-handling.md` | Non-blocking error handling — per-step file-system error handling, the 30-second timeout, predecessor-failure independence, and retry-on-next-completion |
| `module-completion-next-steps.md` | Per-module next-step flow — next-step options and immediate execution on an affirmative response |
| `module-completion-track.md` | Track completion — path/track completion detection and the path completion celebration (export, record, analytics, certificate, graduation, and feedback offers) |

### Slice Fallback

If a referenced slice cannot be found at its expected path under `senzing-bootcamp/steering/`, fall back to this Root: use the ordering and trigger rules above to proceed as best you can, and report that the slice is missing (name the expected file path) so the gap can be fixed. Never silently skip a completion concern because its slice is absent.
