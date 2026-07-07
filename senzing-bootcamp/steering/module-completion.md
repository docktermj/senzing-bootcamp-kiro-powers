---
inclusion: manual
---

# Module Completion Workflow

Load this after completing any module. This file is the **Module_Completion_Root** — a lightweight router. It holds the completion-step ordering overview and the Shared Boundary-Detection Trigger rules, then points to the cohesive slices that carry each completion concern (artifact generation, non-blocking error handling, next-step flow, and track completion).

## Completion Step Ordering

The module completion process executes the following steps in a **fixed, invariant order** regardless of which module is being completed:

1. **progress_update** — Mark the module complete in `config/bootcamp_progress.json`
2. **recap_append** — Synchronously append a recap section to `docs/bootcamp_recap.md` (create file if first completion), then verify the `## Module N:` heading persisted and backfill it if absent before reporting success
3. **journal_entry** — Append a journal entry to `docs/bootcamp_journal.md` (create file if first completion)
4. **completion_certificate** — Generate `docs/progress/MODULE_N_COMPLETE.md` and update the summary index
5. **capture_hook_safeguard** — Run `capture_hook_safeguard.py` to detect any absent capture-critical hook; a silent no-op when all three are present, or a recurring, overridable Soft_Block reminder surfaced before the module transition when any are missing (see the Capture-Critical Hook Safeguard section below)
6. **next_step_options** — Present the bootcamper with concrete next-step choices

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

## Capture-Critical Hook Safeguard

At the module-completion boundary — after the artifact steps and **before** the forward module-transition question is finalized — run the safeguard to catch any capture-critical hook (`session-log-events`, `module-recap-append`, `ask-bootcamper`) whose absence would silently thin the recap, transcript, and completion summary:

```text
python3 senzing-bootcamp/scripts/capture_hook_safeguard.py --module N
```

Render the resulting `ReminderPlan`:

- **All three hooks present — silent no-op.** The script emits nothing. Produce no safeguard output and do not delay the transition; proceed straight to `next_step_options`.
- **Any hook missing — Soft_Block.** The script names each missing hook, the output(s) it feeds (recap, transcript, and/or completion summary), and the two install options. Surface this as a **single live `👉` Soft_Block pending question** that is the **final message** of the turn (per the Final-Message Invariant in `conversation-protocol.md`). The question names the missing hook(s) and the degraded output(s) each feeds, offers the two install options, and offers an explicit continue:
  - Re-create them with `createHook` from the Hook Registry (`ask-bootcamper` in `hook-registry-critical.md`; `module-recap-append` and `session-log-events` in `hook-registry-module-any.md`), **or**
  - Run the file-copy installer: `python3 senzing-bootcamp/scripts/install_hooks.py --essential` (its `--essential` set includes all three), **or**
  - Explicitly continue without installing.

  Write `config/.question_pending` for this Soft_Block question and wait. The reminder **recurs at every subsequent module boundary** while a hook stays missing — a prior acknowledgment authorizes only the current transition and never suppresses a future reminder.

### On explicit continue

When the bootcamper explicitly chooses to continue without installing, re-invoke the safeguard with `--record-ack` to record the acknowledgment **before** allowing the module transition:

```text
python3 senzing-bootcamp/scripts/capture_hook_safeguard.py --module N --record-ack
```

Then proceed to the forward transition. The acknowledgment authorizes **this** transition only; the reminder still re-presents at the next boundary if the hook remains missing.

### Non-blocking and defer rules

- **Non-blocking regardless of exit code.** The safeguard is advisory: whether it exits 0 or 1, never let it block or stall the module transition. It is a Soft_Block, never a Mandatory_Gate (⛔), and never permanently blocks progress.
- **Defer when a question is pending.** If `config/.question_pending` already exists at the boundary, the safeguard produces no output and defers to `ask-bootcamper`, exactly as the artifact steps do.
- **Complements the session-start check.** This safeguard reuses the same capture-critical hook list and the same two install options as the advisory Capture-Critical Warn-on-Absence Check in `session-resume-phase2-setup-recovery.md`; it neither replaces nor weakens that check.

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
