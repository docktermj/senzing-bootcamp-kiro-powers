---
inclusion: always
description: "How the question/answer exchange is captured for the replayable Q&A transcript — hook-enforced on the Q&A cadence, still decoupled from file writes"
---

# Q&A Transcript Capture

This steering governs how the question→answer exchange is recorded so it can be
rendered into an ordered, replayable transcript (`docs/bootcamp_transcript.md`)
and reconciled into the graduation recap. Capture is **hook-enforced** and reuses
the existing event schema in `scripts/session_logger.py` — it does **not** define
a new format.

## Hook-enforced capture (guaranteed on the Q&A cadence)

Capture is performed by the two critical hooks via the helper
`scripts/log_qa_event.py`, which appends `question` / `answer` completion events
to `config/session_log.jsonl`. Both fire on the **Q&A cadence** — once per
question, once per answer — never on file writes:

- **Question — `ask-bootcamper` (Stop hook).** When a turn ends with a 👉 leading
  question, `config/.question_pending` holds that question's text. The Stop hook
  runs `log_qa_event.py record-question`, which logs the question idempotently (a
  re-presented question is not double-logged) and records its `question_id` in a
  small sidecar (`config/.qa_capture.json`).
- **Answer — `review-bootcamper-input` (UserPromptSubmit hook).** When the
  bootcamper answers (i.e. `config/.question_pending` exists), the hook runs
  `log_qa_event.py record-answer`, passing the bootcamper's verbatim message on
  stdin. The helper pairs the answer to the pending question's `question_id` and
  self-heals by logging the question first if it was not already recorded — so an
  answer is never orphaned from its question.

Because both capture points are driven by critical hooks (installed and verified
during onboarding, reminded by the capture-hook safeguard), Q&A capture is
guaranteed in the same sense as every other hook-enforced bootcamp behavior —
given the hooks are present. It no longer depends on the agent remembering to emit
events. The module-completion recap (`ask-bootcamper` Phase 0), the stopping-point
reconciliation (`reconcile_transcript.py`), and the graduation enforcement
(`enforce-critical-artifacts` → `ensure_graduation_artifacts.py`) remain as
defense-in-depth layers.

## The event schema is fixed — never fabricate

`log_qa_event.py` builds entries with `session_logger.build_completion_entry(...)`
and appends them with `append_completion_entry(...)`; question IDs come from
`generate_question_id()`. The two event types are `question` and `answer`. Never
hand-craft these structures, invent fields, or log a `question`/`answer` pair for
text the bootcamper never actually saw or sent. The helper already no-ops when
there is no pending question, so it never orphan-logs an answer.

## Event-driven only — never coupled to file writes

Q&A logging is **event-driven:** it fires **only** on the Q&A cadence — a question
asked (Stop) or an answer given (UserPromptSubmit). It is never triggered by a
file-write tool call.
Treat the following as hard constraints when editing this feature:

- **Triggered only by Q&A moves.** A `fs_write`, `fs_append`, or `str_replace`
  call is **not** a trigger for Q&A logging.
- **Do not touch write-tool hooks.** Do **not** add or modify any `PostToolUse`
  hook on the write tools to perform Q&A logging.
- **Do not change `session-log-events`.** Leave it exactly as the
  `session-log-hook-performance` spec established it (the shell `command`
  per-write append). Q&A logging is separate and must not alter or piggy-back on
  that hook.
- **Zero cost on write-only turns.** A turn that performs many file writes but
  asks no question and receives no answer adds **zero** Q&A log entries.

This keeps Q&A capture decoupled from file writes and never reintroduces the
per-write round-trip that `session-log-hook-performance` removed. Capture is folded
into the two existing critical hooks — no new hooks, and no per-write hook.

## Cross-reference — guaranteed transcript

The rendered transcript (`docs/bootcamp_transcript.md`) is guaranteed at
track-completion and graduation stopping points by the `enforce-critical-artifacts`
hook via `ensure_graduation_artifacts.py`, which reconstructs it from always-present
sources (the session log, and the recap's `### Questions & Responses` pairs). That
stopping-point reconstruction is unchanged and adds no per-write hook.

In short, the capture guarantee boundary is this: Q&A capture is best-effort and
event-driven mid-module (hook-enforced on the Q&A cadence, only as strong as the
installed hooks, and never triggered by a file write), reconciled at every
stopping point via `reconcile_transcript.py`, and hard-guaranteed at track
completion / graduation via `enforce-critical-artifacts` →
`ensure_graduation_artifacts.py`.
