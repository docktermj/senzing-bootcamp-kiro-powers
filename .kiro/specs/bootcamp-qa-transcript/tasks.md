# Implementation Plan

## Overview

This plan implements the replayable Q&A transcript feature: a stdlib-only renderer
(`generate_transcript.py`) that reads `question`/`answer` completion events from
`config/session_log.jsonl` and produces `docs/bootcamp_transcript.md`, plus a steering file that
governs event-driven emission and graduation integration. The renderer is built bottom-up (read →
model → render → orchestrate) so each layer is tested in isolation; the steering and graduation work
follow once the script is proven.

## Tasks

- [x] 1. Create the transcript renderer script skeleton
  - Create `senzing-bootcamp/scripts/generate_transcript.py` following the project script pattern:
    `#!/usr/bin/env python3`, `from __future__ import annotations`, stdlib-only imports,
    `main(argv=None)`, argparse with `--log` (default `config/session_log.jsonl`) and `--output`
    (default `docs/bootcamp_transcript.md`), and `if __name__ == "__main__": sys.exit(main())`.
  - Define the `QAPair` and `TranscriptModel` dataclasses from the design.
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Implement resilient event reading
  - [x] 2.1 Implement `read_events(log_path)` that reads JSONL, skips lines that are not valid JSON
    or not `question`/`answer` completion events, and never raises on a bad line. Return only valid
    Q&A event dicts.
    - _Requirements: 5.1_
  - [x] 2.2 Write a property test (Property 4: Robust parsing): for any interleaving of valid Q&A
    events with malformed/non-Q&A lines, `read_events` returns exactly the valid Q&A events and never
    raises. [PBT]
    - _Requirements: 5.1_

- [x] 3. Implement the transcript model builder
  - [x] 3.1 Implement `build_model(events)`: order events by `timestamp` with stable file-order
    tie-breaking; pair `answer` events to `question` events by `question_id`; mark questions with no
    answer as unanswered; collect answers with no matching question as orphan answers; compute
    `question_count` and `answered_count`.
    - _Requirements: 2.2, 4.5, 4.6, 5.2, 5.4_
  - [x] 3.2 Write a property test (Property 1: Pairing integrity): every answered question renders
    with exactly its paired answer text and no answer is attached to a different question. [PBT]
    - _Requirements: 2.2, 4.5_
  - [x] 3.3 Write a property test (Property 2: Order preservation): rendered question order equals the
    stable timestamp order of the question events. [PBT]
    - _Requirements: 4.4, 5.2_
  - [x] 3.4 Write a property test (Property 3: No content dropped / no fabrication): every question is
    rendered (answered or unanswered), every answer is rendered (paired or orphan), and no
    `question_id` is invented for an unmatched answer. [PBT]
    - _Requirements: 2.5, 4.6, 5.4_

- [x] 4. Implement secret redaction
  - [x] 4.1 Implement `redact_secrets(text)` that redacts token / connection-string / API-key
    patterns in answer text before rendering.
    - _Requirements: 8.2_
  - [x] 4.2 Write a test asserting an answer containing a token/connection-string pattern is redacted
    in the rendered output.
    - _Requirements: 8.1, 8.2_

- [x] 5. Implement Markdown rendering
  - [x] 5.1 Implement `render_markdown(model, generated_at)`: a metadata header with the ISO 8601
    generation timestamp and total/answered question counts; one `## Module N` heading per module with
    at least one pair; each question followed by its answer (or an "unanswered" marker); orphan answers
    in a clearly labeled section. Use only relative paths.
    - _Requirements: 4.4, 4.5, 4.6, 4.7, 5.4, 8.4_
  - [x] 5.2 Write example tests: a two-question session renders grouped-by-module with paired answers;
    an unanswered question renders as unanswered; an orphan answer renders in the labeled section.
    - _Requirements: 4.4, 4.5, 4.6, 5.4_

- [x] 6. Implement `main` orchestration and empty-input safety
  - [x] 6.1 Wire `main` to read events, build the model, render, and write `--output` by full
    regeneration (overwrite, never append to stale content). When there are no Q&A events (including a
    missing log file), emit a warning to stderr and do NOT write a misleading transcript file; return 0.
    Return 1 only for argument/usage errors.
    - _Requirements: 4.2, 4.3, 5.3, 7.3_
  - [x] 6.2 Write tests: existing transcript file is overwritten on regeneration; empty/missing log
    warns and writes nothing (Property 5: Empty-input safety). [PBT]
    - _Requirements: 5.3, 7.3_

- [x] 7. Author the Q&A emission steering file
  - [x] 7.1 Create `senzing-bootcamp/steering/qa-transcript.md` (Markdown + YAML frontmatter) that
    instructs the agent to: emit a `question` completion event when presenting a 👉 Leading_Question
    (using `generate_question_id` and `build_completion_entry("question", module, {"text","question_id"})`
    appended via `append_completion_entry`), emit an `answer` event keyed to that `question_id` when the
    bootcamper replies, record actual displayed/response text, skip emitting for non-question text and
    for replies with no pending question, and never fabricate a `question_id`.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.5_
  - [x] 7.2 State the event-driven constraint in the steering file: Q&A logging fires only on
    question/answer moves, never on file writes, and must not modify the `session-log-events` hook.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.4_
  - [x] 7.3 Register the steering file's token budget in `senzing-bootcamp/steering/steering-index.yaml`
    (run `measure_steering.py` to compute the count) and verify with `measure_steering.py --check`.
    - _Requirements: 6.3_
  - [x] 7.4 Write a steering presence test asserting `qa-transcript.md` exists, is registered in
    `steering-index.yaml`, references the `session_logger` event types, and states the event-driven
    (not per-write) constraint.
    - _Requirements: 6.1, 6.2, 6.4, 6.5, 3.1_

- [x] 8. Integrate transcript generation into graduation
  - [x] 8.1 Update `senzing-bootcamp/steering/graduation.md` to run
    `python scripts/generate_transcript.py` as a non-blocking step, present the output path, and list
    `docs/bootcamp_transcript.md` among the graduation artifacts.
    - _Requirements: 7.1, 7.2, 7.4_
  - [x] 8.2 Update `steering-index.yaml` token budget for `graduation.md` if its size changed and
    verify with `measure_steering.py --check`.
    - _Requirements: 6.3, 7.1_

- [x] 9. Final verification
  - Run the full power test suite (`python3 -m pytest senzing-bootcamp/tests/ -q`) plus
    `validate_commonmark.py` and `measure_steering.py --check`; confirm no regressions and that any
    new fixtures use synthetic, PII-free content.
  - _Requirements: 8.3, 9.1, 9.2, 9.3, 9.4_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "4.1", "7.1"] },
    { "id": 2, "tasks": ["2.2", "3.1", "4.2", "7.2"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "5.1", "7.3"] },
    { "id": 4, "tasks": ["5.2", "6.1", "7.4"] },
    { "id": 5, "tasks": ["6.2", "8.1"] },
    { "id": 6, "tasks": ["8.2"] },
    { "id": 7, "tasks": ["9"] }
  ]
}
```

- **Wave 0** — `[1]`: script skeleton + dataclasses (foundation for all renderer work).
- **Wave 1** — `read_events` (2.1), `redact_secrets` (4.1), and the steering file (7.1) start in
  parallel (7.x is independent of the script).
- **Wave 2** — robust-parsing PBT (2.2), `build_model` (3.1), redaction test (4.2), event-driven
  constraint in steering (7.2).
- **Wave 3** — pairing/order/no-drop PBTs (3.2–3.4), `render_markdown` (5.1), steering budget (7.3).
- **Wave 4** — render example tests (5.2), `main` orchestration (6.1), steering presence test (7.4).
- **Wave 5** — empty-input PBT (6.2) and graduation integration (8.1, needs `main` + steering).
- **Wave 6** — graduation steering budget update (8.2).
- **Wave 7** — final verification (9).

Critical path: 1 → 2.1 → 3.1 → 5.1 → 6.1 → 8.1 → 9.

## Notes

- All code is Python 3.11+ stdlib-only; the renderer reuses the existing `session_logger` event
  schema (`question`/`answer` with `text`/`question_id`) — no new schema and no changes to
  `session_logger.py` are required.
- Q&A logging is event-driven by design (Requirement 3): do not wire it to write tools and do not
  modify the `session-log-events` hook from `session-log-hook-performance`.
- Tasks tagged `[PBT]` are property-based tests (pytest + Hypothesis, `@settings(max_examples=20)`,
  `st_`-prefixed strategies) and validate the correctness properties in design.md.
- All test fixtures must use synthetic, PII-free content (Requirement 8.3); the transcript and any
  references use relative paths only.
- This feature pairs with `graduation-markdown-normalization`: if that spec lands, transcript
  generation runs after the normalization pass like the other derived artifacts.
