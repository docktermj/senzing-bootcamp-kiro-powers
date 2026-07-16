# Bugfix Requirements Document

## Introduction

Throughout the Senzing Bootcamp, each question the agent asks and each answer the
bootcamper gives is supposed to be captured and retained so the graduation recap
(`docs/bootcamp_recap.pdf` / `docs/bootcamp_recap.md`) reflects the real Q&A of
the entire experience. The recap is the bootcamper's "trophy," so completeness
matters.

In practice, Q&A is being lost during the bootcamp. Capture depends on the agent
*voluntarily* running `senzing-bootcamp/scripts/log_qa_event.py` from within two
`type: agent` hooks — the Stop hook `ask-bootcamper` (`record-question`) and the
`UserPromptSubmit` hook `review-bootcamper-input` (`record-answer`). Because those
hooks only inject a prompt asking the agent to log, the events are not durably
written at ask/answer time. When a session boundary, context compaction, or a
restart intervenes, the events are never persisted to `config/session_log.jsonl`.

In the reported run, Modules 1-3 were completed in an earlier session and had no
captured Q&A at all. At graduation, the recap generator's deterministic backfill
could recreate section structure but could not recover words that were never
logged, so it inserted the honest placeholder "N/A (section backfilled at track
completion; original session content unavailable)." This has been reported
repeatedly and remains unresolved. The fix must make Q&A capture durable and
write-through (hook-backed, not agent-voluntary) so it survives session
boundaries, and must validate at graduation that every completed module has real
captured Q&A — failing loudly rather than silently backfilling with placeholder
text.

## Bug Analysis

### Current Behavior (Defect)

The current Q&A capture path is agent-voluntary and reconstruction-based, so
exchanges are lost across session boundaries and missing Q&A is silently masked
with placeholder text at graduation.

1.1 WHEN a question is asked or answered and the `type: agent` Q&A hooks (`ask-bootcamper` / `review-bootcamper-input`) do not actually invoke `log_qa_event.py` (because the agent skips it, or a session boundary, context compaction, or restart intervenes) THEN the system leaves `config/session_log.jsonl` with no corresponding `question`/`answer` events and the exchange is lost.

1.2 WHEN a module was completed in an earlier session (e.g., Modules 1-3) THEN the system produces a recap whose Q&A for those modules is unrecoverable because the exchanges were never durably persisted at capture time.

1.3 WHEN graduation rendering begins THEN the system does NOT verify that every completed module has real captured Q&A before rendering the recap.

1.4 WHEN a completed module has no captured Q&A at graduation THEN the system silently renders the recap with the placeholder "N/A (section backfilled at track completion; original session content unavailable)" instead of failing loudly.

### Expected Behavior (Correct)

Q&A capture must be durable and write-through at ask/answer time, and graduation
must validate completeness and fail loudly rather than mask gaps.

2.1 WHEN a question is asked or answered THEN the system SHALL durably persist the corresponding `question`/`answer` event to `config/session_log.jsonl` via a write-tool-backed (deterministic, non-agent-voluntary) hook at ask/answer time, so the event survives session boundaries, context compaction, and restarts.

2.2 WHEN modules are completed across multiple sessions THEN the system SHALL retain each completed module's Q&A because it was persisted at capture time, so no completed module ends with an unrecoverable Q&A gap.

2.3 WHEN graduation rendering begins THEN the system SHALL validate that every completed module has real captured Q&A before rendering the recap.

2.4 WHEN a completed module has no real captured Q&A at graduation THEN the system SHALL fail loudly (halt rendering and report the missing module(s)) rather than silently substituting placeholder text.

### Unchanged Behavior (Regression Prevention)

The durability and validation changes must not disturb existing capture
semantics, non-blocking guarantees, or the rendering of modules whose Q&A was
captured correctly.

3.1 WHEN a completed module's Q&A events were durably captured THEN the system SHALL CONTINUE TO render the real question/answer pairs in the recap in ascending ask order with each response paired to its own question.

3.2 WHEN the Q&A capture helper encounters an error THEN the system SHALL CONTINUE TO be non-blocking (swallow the error and never interrupt the bootcamp flow).

3.3 WHEN the same pending question is re-presented across turns or a session boundary THEN the system SHALL CONTINUE TO be idempotent and never double-log the question.

3.4 WHEN an answer is recorded THEN the system SHALL CONTINUE TO pair it to the pending question's id, self-healing by logging the question first if it was not already recorded.

3.5 WHEN existing `config/session_log.jsonl` entries and existing `docs/bootcamp_recap.md` sections are present THEN the system SHALL CONTINUE TO preserve them byte-for-byte (append-around, no overwrite).

3.6 WHEN the Q&A capture scripts run THEN the system SHALL CONTINUE TO use Python 3.11+ standard library only (no third-party dependencies).
