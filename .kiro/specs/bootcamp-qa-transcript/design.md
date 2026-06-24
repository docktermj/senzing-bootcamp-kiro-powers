# Design Document

## Overview

This feature assembles an ordered, replayable Q&A transcript from events the agent already has a schema
for. `session_logger.py` defines `question` and `answer` completion events; what is missing is (a) the
behavioral rule that emits them turn-by-turn and (b) a renderer that turns the logged events into
`docs/bootcamp_transcript.md`.

The design has three parts:

1. **Emission rules (steering)** — a steering file that tells the agent to log a `question` event when
   it presents a 👉 Leading_Question and an `answer` event when the bootcamper replies, keyed by a
   shared `question_id`. This is event-driven (only on questions/answers), never per file write.
2. **Renderer script** — a new stdlib-only `generate_transcript.py` that reads `config/session_log.jsonl`,
   pairs answers to questions by `question_id`, orders by timestamp, and writes
   `docs/bootcamp_transcript.md`.
3. **Graduation integration** — the graduation flow generates the transcript as a discoverable artifact.

No new event schema is introduced: the feature reuses `build_completion_entry`,
`append_completion_entry`, and `generate_question_id` exactly as they exist.

## Architecture

```text
   TURN-BY-TURN (agent behavior, governed by steering/qa-transcript.md)
     agent presents 👉 question ──▶ build_completion_entry("question", module,
                                       {text, question_id}) ──▶ append to session_log.jsonl
     bootcamper replies         ──▶ build_completion_entry("answer", module,
                                       {text, question_id}) ──▶ append to session_log.jsonl
                       (event-driven only — NOT tied to fs_write/str_replace)

   GRADUATION / ON DEMAND
     python scripts/generate_transcript.py
        read config/session_log.jsonl (skip non-JSON / non-Q&A lines)
        ├─ collect question events  (question_id → text, module, ts)
        ├─ collect answer events    (question_id → text, module, ts)
        ├─ order by timestamp, then file order
        ├─ pair answers to questions; mark unanswered; collect orphan answers
        ├─ redact secret-looking answer values
        └─ write docs/bootcamp_transcript.md  (grouped by module)
```

## Components and Interfaces

### Emission rules — `senzing-bootcamp/steering/qa-transcript.md`

A new steering file (Markdown + YAML frontmatter), token budget recorded in
`steering/steering-index.yaml`. It specifies:

- **When to emit a question event**: immediately when the agent presents a Leading_Question (a
  👉-prefixed, single-question-per-turn decision point). Use `generate_question_id()` for the id;
  build via `build_completion_entry("question", module, {"text": <question text>, "question_id": <id>})`
  and append via `append_completion_entry("config/session_log.jsonl", entry)`. The logged `text`
  matches the displayed prompt (Requirement 1.4). Do NOT emit for internal/rhetorical text (1.5).
- **When to emit an answer event**: when the bootcamper replies to the most recent unanswered
  Leading_Question, reusing that question's `question_id`; record the bootcamper's actual response text
  (Requirement 2.4). If a reply maps to no pending question, do not fabricate an id and skip (2.5).
- **Event-driven constraint** (Requirement 3): this logging fires only on question/answer moves. It
  MUST NOT be wired to write tools and MUST NOT modify the `session-log-events` hook (the shell
  `runCommand` per-write append from `session-log-hook-performance`).
- A short note that the current `question_id` is tracked across the turn (the agent holds the id it
  generated for the pending question so the answer can reference it).

Because emission is agent behavior, correctness is verified by the conversational-eval harness style of
test plus the static presence test in Requirement 9 — not by a runtime hook.

### Renderer — `senzing-bootcamp/scripts/generate_transcript.py`

Project script pattern: `#!/usr/bin/env python3`, `from __future__ import annotations`, stdlib-only,
`main(argv=None)`, argparse, exit 0 / 1.

```python
@dataclass
class QAPair:
    question_id: str
    module: int
    question_text: str
    answer_text: str | None        # None when unanswered
    q_timestamp: str
    a_timestamp: str | None

@dataclass
class TranscriptModel:
    pairs: list[QAPair]            # ordered by question timestamp/file order
    orphan_answers: list[dict]     # answer events with no matching question
    question_count: int
    answered_count: int

def read_events(log_path: str) -> list[dict]:
    """Read JSONL; skip lines that are not valid JSON or not question/answer
    completion events (Requirement 5.1). Never raises on a bad line."""

def build_model(events: list[dict]) -> TranscriptModel:
    """Order by timestamp then file order (5.2); pair answers to questions by
    question_id; first unmatched question per id; mark unanswered (4.6); collect
    orphan answers (5.4)."""

def redact_secrets(text: str) -> str:
    """Redact token/connection-string/api-key patterns in answer text (Req 8.2)."""

def render_markdown(model: TranscriptModel, generated_at: str) -> str:
    """Metadata header (ISO timestamp, totals) + per-module grouping; each question
    followed by its answer (or 'unanswered'); orphan answers in a labeled section."""

def parse_args(argv=None):  # --log (default config/session_log.jsonl), --output
                            # (default docs/bootcamp_transcript.md)
def main(argv=None) -> int:
    """Regenerate from scratch (overwrite, never append — Req 7.3). If no Q&A
    events: warn and do NOT write a misleading file (Req 5.3); return 0."""
```

**Ordering** (5.2): sort events by `timestamp`; for equal timestamps, preserve original file order
(stable sort over enumerated events).

**Pairing** (4.5, 2.2): build a map `question_id → QAPair`. Each `answer` event fills the
`answer_text`/`a_timestamp` of the matching question. An answer whose `question_id` has no question
becomes an orphan (5.4). A question with no answer renders as unanswered (4.6).

**Document shape** (Requirement 4): a metadata header (generation timestamp, total questions, answered
count), then one `## Module N` heading per module that has at least one pair, then each Q&A rendered
in order. Relative paths only (8.4); answer text passed through `redact_secrets` (8.2).

### Graduation integration — `senzing-bootcamp/steering/graduation.md`

Add a step (alongside the existing recap-PDF / completion-summary artifacts) that runs
`python scripts/generate_transcript.py` and lists `docs/bootcamp_transcript.md` among the graduation
artifacts (Requirements 7.1, 7.2, 7.4). Non-blocking, consistent with the other artifact steps. If the
`graduation-markdown-normalization` spec lands, the transcript generation runs after the normalization
pass like the other derived artifacts.

## Data Models

The persisted events reuse the existing `CompletionLogEntry` schema (`event_type`, `module`,
`timestamp`, `data`) with `data = {"text": ..., "question_id": ...}`. The only new types are the
in-memory `QAPair` and `TranscriptModel` above. No change to `session_logger.py` is required; if a
convenience wrapper is desired, it can be added without altering existing functions.

## Error Handling

| Condition | Handling |
|---|---|
| Malformed / non-JSON log line | Skip and continue (5.1) |
| Non-Q&A completion event (action/artifact) | Ignore for transcript purposes |
| Answer with unknown question_id | Render in a labeled "Unmatched answers" section (5.4) |
| Question with no answer | Render question, mark answer unanswered (4.6) |
| Log file missing / no Q&A events | Warn to stderr; do not write a misleading file (5.3); exit 0 |
| Secret-looking answer value | Redact before writing (8.2) |
| Existing transcript file | Regenerate (overwrite), never append to stale content (7.3) |

## Correctness Properties

### Property 1: Pairing integrity

*For all* sequences of `question` and `answer` events, every answered question (a question whose
`question_id` also appears on an answer event) renders with exactly its paired answer text, and no
answer is attached to a different question.

**Validates: Requirements 2.2, 4.5**

### Property 2: Order preservation

*For all* event sequences, the rendered questions appear in non-decreasing `timestamp` order, with
file order breaking ties — i.e. rendered order equals the stable timestamp order of the question
events.

**Validates: Requirements 4.4, 5.2**

### Property 3: No content dropped / no fabrication

*For all* event sequences, every question event yields a rendered question (answered or marked
unanswered) and every answer event is rendered either as its question's answer or as an orphan — no
question or answer is silently discarded, and no `question_id` is invented for an unmatched answer.

**Validates: Requirements 4.6, 5.4, 2.5**

### Property 4: Robust parsing

*For all* logs containing arbitrary interleavings of valid Q&A events with malformed or non-Q&A lines,
`read_events` returns exactly the valid Q&A events and never raises.

**Validates: Requirements 5.1**

### Property 5: Empty-input safety

*For all* logs with zero Q&A events (including a missing file), `main` emits a warning and writes no
misleading transcript file, returning 0.

**Validates: Requirements 5.3**

## Testing Strategy

Tests in `senzing-bootcamp/tests/test_generate_transcript.py` (pytest + Hypothesis), importing the
script via the documented `sys.path` pattern. Strategies (`st_qa_events`, etc.) generate ordered
question/answer event sequences with synthetic, PII-free text (Requirement 8.3).

- **Example tests**: a simple two-question session renders grouped-by-module with paired answers; an
  unanswered question renders as unanswered; an orphan answer renders in the labeled section; malformed
  lines are skipped; empty/missing log warns and writes nothing; an existing file is overwritten.
- **Property tests**: Properties 1–5 above, each a Hypothesis `@given` over generated event sequences.
- **Steering presence test**: assert `steering/qa-transcript.md` exists, is registered in
  `steering-index.yaml`, references the `session_logger` event types, and states the event-driven
  (not per-write) constraint (Requirements 6.1–6.5, 3).
- **Redaction test**: an answer containing a token/connection-string pattern is redacted in the output
  (Requirement 8.2).
```
