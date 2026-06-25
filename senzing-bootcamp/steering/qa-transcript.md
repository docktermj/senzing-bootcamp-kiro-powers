---
inclusion: auto
description: "Emit question/answer completion events for the replayable Q&A transcript
 when the agent asks a 👉 leading question and the bootcamper answers it"
---

# Q&A Transcript Emission

This steering governs how the agent records the question→answer exchange so it can be
rendered into an ordered, replayable transcript. It reuses the existing event schema in
`scripts/session_logger.py` — it does **not** define a new format.

The two event types come straight from `session_logger.py`:

- `question` — emitted when the agent presents a 👉 leading question.
- `answer` — emitted when the bootcamper replies to that question.

Both are built with `build_completion_entry(...)` and appended with
`append_completion_entry("config/session_log.jsonl", entry)`. Question IDs come from
`generate_question_id()`. Never hand-craft these structures or invent your own fields.

## Emit a `question` event when you present a 👉 leading question

A **leading question** is the single 👉-prefixed, bootcamper-facing decision point that ends a
yielding turn. When you present one:

1. Generate an id: `qid = generate_question_id()`.
2. Build the entry with the **same text you show the bootcamper** (verbatim, not a summary):
   `build_completion_entry("question", <current_module>, {"text": <question text>, "question_id": qid})`.
3. Append it: `append_completion_entry("config/session_log.jsonl", entry)`.
4. Hold `qid` as the **current question id** for the turn so the matching answer can reference it
   (it pairs naturally with the existing `config/.question_pending` marker).

`<current_module>` is the active module number (from `config/bootcamp_progress.json`,
`current_module`); use `0` only during onboarding before a module is set.

**Do not emit a `question` event for:**

- Internal, rhetorical, or narrative text that is not an actual decision point.
- Clarifying prose, recaps, or status lines that do not stop and wait for a reply.

The logged `text` must match the displayed prompt exactly so the transcript is faithful.

## Emit an `answer` event when the bootcamper replies

When the bootcamper answers the most recent unanswered leading question:

1. Reuse that question's `question_id` — the **current question id** you held from the
   `question` event. Do not generate a new one.
2. Record the bootcamper's **actual response text**, not a paraphrase or your interpretation of it:
   `build_completion_entry("answer", <current_module>, {"text": <bootcamper reply>, "question_id": qid})`.
3. Append it: `append_completion_entry("config/session_log.jsonl", entry)`.
4. Clear the current question id once the answer is logged.

This keeps the `answer` keyed to its originating `question`, so the pairing is recoverable by id.

## Skip rules — never fabricate

- If a bootcamper message does **not** correspond to any pending unanswered question (no current
  question id is held), do **not** invent or guess a `question_id` and do **not** emit an `answer`
  event for that message. Just skip it.
- Never emit a `question`/`answer` pair for text the bootcamper never actually saw or sent.

## Event-driven only — never coupled to file writes

Q&A logging is **event-driven**: it fires **only** when a leading question is asked or when the
bootcamper answers one. It is never triggered by a file-write tool call. Treat the following as
hard constraints when emitting events or editing this feature:

- **Triggered only by Q&A moves.** Emit a `question` event when you present a 👉 leading question
  and an `answer` event when the bootcamper replies — nothing else. A `fs_write`, `fs_append`, or
  `str_replace` call is **not** a trigger for Q&A logging.
- **Do not touch write-tool hooks.** Do **not** add or modify any `postToolUse` hook on the write
  tools (`fs_write`, `fs_append`, `str_replace`) to perform Q&A logging.
- **Do not change `session-log-events`.** Leave the `session-log-events` hook exactly as the
  `session-log-hook-performance` spec established it (the shell `runCommand` per-write append). Q&A
  logging is separate and must not alter or piggy-back on that hook.
- **Zero cost on write-only turns.** A turn that performs many file writes but asks no question and
  receives no answer adds **zero** additional Q&A log entries.

This constraint is stated here so future edits keep Q&A logging decoupled from file writes and never
reintroduce the per-write round-trip that `session-log-hook-performance` removed.
