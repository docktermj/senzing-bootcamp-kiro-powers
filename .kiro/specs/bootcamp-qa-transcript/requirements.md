# Requirements Document

## Introduction

As bootcampers work through the Senzing Bootcamp, the agent asks a sequence of questions (the
👉-prefixed prompts at each decision point) and the bootcamper answers them. Today there is no
artifact that captures that exchange as an ordered, replayable record. The raw materials exist but
none of them produce an ordered question→answer transcript:

- `config/session_log.jsonl` accumulates mostly generic write entries. After the `session-log-events`
  hook was converted to a shell `runCommand` (per the `session-log-hook-performance` spec), each
  entry is a fixed "auto-logged write operation" with a timestamp and module — it contains no
  question or answer text.
- `senzing-bootcamp/scripts/session_logger.py` already defines `question` and `answer`
  completion-event types (with `question_id`, `text`, and `module` fields and full validation via
  `build_completion_entry` / `append_completion_entry`, plus `generate_question_id`), but nothing in
  the turn-by-turn flow actually emits these events as questions are asked and answered.
- `docs/bootcamp_recap.md` is a narrative per-module summary, not an ordered Q&A record, and is
  typically only assembled at graduation.

This feature closes the gap in two parts. First, it defines the behavioral rules (steering) that make
the agent emit a `question` event when it presents a 👉 question and an `answer` event when the
bootcamper replies, keyed by `question_id`. Second, it adds a stdlib-only renderer script that reads
the logged events and produces an ordered, human-readable `docs/bootcamp_transcript.md` for replay and
audit.

A critical constraint shapes the design: the Q&A logging must be **event-driven** — it fires only when
a question is asked or answered, not on every file write. This is deliberately distinct from the
per-write logging that the `session-log-hook-performance` spec optimized away; this feature must not
reintroduce a per-write agent round-trip or per-write Python process spawn.

## Glossary

- **Transcript_Renderer**: The stdlib-only Python script in `senzing-bootcamp/scripts/` that reads
  logged Q&A events and produces the Q&A_Transcript document.
- **Q&A_Transcript**: The ordered Markdown artifact at `docs/bootcamp_transcript.md` rendering each
  question and its paired answer in the order they occurred, grouped by module.
- **Question_Event**: A `question`-type completion event (per `session_logger.py`) carrying
  `question_id`, `text`, and `module`, emitted when the agent presents a 👉 question.
- **Answer_Event**: An `answer`-type completion event carrying `question_id`, `text`, and `module`,
  emitted when the bootcamper replies to a question.
- **Question_Id**: The short unique identifier (from `generate_question_id`) that links an
  Answer_Event to its originating Question_Event.
- **Session_Log**: The append-only JSONL file at `config/session_log.jsonl` where Q&A events and other
  session events are recorded, one JSON object per line.
- **Session_Logger**: The existing module `senzing-bootcamp/scripts/session_logger.py` providing the
  event schema, validation, and append functions.
- **QA_Steering**: The steering guidance (Markdown with YAML frontmatter in
  `senzing-bootcamp/steering/`) that instructs the agent when and how to emit Question_Events and
  Answer_Events.
- **Leading_Question**: A 👉-prefixed question the agent presents at a decision point and then stops to
  wait for the bootcamper's reply (the single-question-per-turn convention used throughout the
  bootcamp).

## Requirements

### Requirement 1: Emit Question Events on Leading Questions

**User Story:** As a power maintainer, I want a `question` event logged whenever the agent presents a
👉 question, so that the transcript captures exactly what the bootcamper was asked.

#### Acceptance Criteria

1. WHEN the agent presents a Leading_Question to the bootcamper, THE agent SHALL emit a Question_Event
   to the Session_Log with the question text, the current module, and a newly generated Question_Id.
2. THE Question_Event SHALL be constructed via `session_logger.build_completion_entry` with
   `event_type` `"question"` and appended via `append_completion_entry`, reusing the existing schema
   and validation rather than a new format.
3. THE Question_Id SHALL be generated using `session_logger.generate_question_id`.
4. THE agent SHALL emit the Question_Event for the same question text it shows the bootcamper, so that
   the logged `text` matches the displayed prompt.
5. THE agent SHALL NOT emit a Question_Event for internal/rhetorical text that is not an actual
   bootcamper-facing decision point.

### Requirement 2: Emit Answer Events Paired to Questions

**User Story:** As a power maintainer, I want an `answer` event logged when the bootcamper replies, so
that each answer is tied to the question that prompted it.

#### Acceptance Criteria

1. WHEN the bootcamper replies to a Leading_Question, THE agent SHALL emit an Answer_Event to the
   Session_Log with the bootcamper's response text, the current module, and the Question_Id of the
   question being answered.
2. THE Answer_Event SHALL carry the same Question_Id as its originating Question_Event, so the pairing
   is recoverable.
3. THE Answer_Event SHALL be constructed via `session_logger.build_completion_entry` with `event_type`
   `"answer"` and appended via `append_completion_entry`.
4. WHEN the bootcamper's reply is captured, THE Answer_Event `text` SHALL record the bootcamper's
   actual response, not a paraphrase generated by the agent.
5. IF a bootcamper reply does not correspond to any preceding unanswered Question_Event, THEN the agent
   SHALL NOT fabricate a Question_Id and SHALL skip emitting an Answer_Event for that reply.

### Requirement 3: Event-Driven Logging Only (No Per-Write Cost)

**User Story:** As a power maintainer, I want Q&A logging to fire only on questions and answers, so
that it does not reintroduce the per-write logging slowdown that was already fixed.

#### Acceptance Criteria

1. THE Q&A logging SHALL be triggered only by the agent asking a Leading_Question or the bootcamper
   answering one — never by file-write tool calls.
2. THE feature SHALL NOT add or modify any `postToolUse` hook on write tools (`fs_write`, `fs_append`,
   `str_replace`) to perform Q&A logging.
3. THE feature SHALL NOT change the `session-log-events` hook behavior established by the
   `session-log-hook-performance` spec (the shell `runCommand` per-write append).
4. WHEN a turn performs many file writes but asks no question and receives no answer, THE feature SHALL
   add zero additional log entries for that turn.

### Requirement 4: Render the Q&A Transcript Document

**User Story:** As a bootcamper or maintainer, I want a readable Markdown transcript of the whole Q&A
exchange, so that the session can be replayed or audited.

#### Acceptance Criteria

1. THE Transcript_Renderer SHALL be a Python 3.11+ stdlib-only script in
   `senzing-bootcamp/scripts/` following the project script pattern (`main(argv=None)`, argparse,
   exit code 0 on success and 1 on error).
2. THE Transcript_Renderer SHALL read Question_Events and Answer_Events from the Session_Log at
   `config/session_log.jsonl` (with the path overridable via a CLI argument).
3. THE Transcript_Renderer SHALL write the Q&A_Transcript to `docs/bootcamp_transcript.md` (with the
   output path overridable via a CLI argument).
4. THE Q&A_Transcript SHALL render questions and answers in the order they occurred and SHALL group
   them by module with a module heading for each module that has at least one Q&A pair.
5. FOR EACH Question_Event, THE Q&A_Transcript SHALL render the question text followed by the paired
   answer text (matched by Question_Id) directly beneath it.
6. WHEN a Question_Event has no matching Answer_Event, THE Q&A_Transcript SHALL render the question and
   mark the answer as unanswered rather than omitting the question.
7. THE Q&A_Transcript SHALL include a metadata header with the generation timestamp (ISO 8601) and the
   total count of questions and answered questions.

### Requirement 5: Resilient Parsing and Ordering

**User Story:** As a maintainer, I want the renderer to tolerate an imperfect log, so that a single bad
line or out-of-order event never produces an empty or misleading transcript.

#### Acceptance Criteria

1. WHEN the Session_Log contains lines that are not valid JSON or are not Q&A events, THE
   Transcript_Renderer SHALL skip those lines and continue rendering the valid Q&A events.
2. THE Transcript_Renderer SHALL preserve the chronological order of events using their `timestamp`
   field, falling back to file order when timestamps are equal.
3. WHEN the Session_Log does not exist or contains no Q&A events, THE Transcript_Renderer SHALL emit a
   warning and SHALL NOT create an empty or misleading transcript file.
4. WHEN an Answer_Event references a Question_Id that has no matching Question_Event, THE
   Transcript_Renderer SHALL render the orphan answer in a clearly labeled section rather than
   discarding it.

### Requirement 6: Agent Steering Guidance

**User Story:** As a power maintainer, I want the question/answer emission rules documented as steering,
so that the agent behaves consistently and the rules are testable.

#### Acceptance Criteria

1. THE QA_Steering SHALL be authored as a Markdown file with YAML frontmatter in
   `senzing-bootcamp/steering/`, following the steering file conventions.
2. THE QA_Steering SHALL specify that a Question_Event is emitted when a Leading_Question is presented
   and an Answer_Event is emitted when the bootcamper replies, keyed by Question_Id.
3. THE QA_Steering token budget SHALL be recorded in `steering/steering-index.yaml`, consistent with
   how other steering files are tracked.
4. THE QA_Steering SHALL state the event-driven constraint (Requirement 3) so future edits do not
   couple Q&A logging to file writes.
5. THE QA_Steering SHALL reference the existing `session_logger.py` event types rather than defining a
   new schema.

### Requirement 7: Transcript Offer at Graduation

**User Story:** As a bootcamper, I want the Q&A transcript available as a graduation artifact, so that I
can keep or share a complete record of my session.

#### Acceptance Criteria

1. WHEN the bootcamper reaches graduation, THE graduation flow SHALL generate (or offer to generate)
   the Q&A_Transcript via the Transcript_Renderer.
2. WHEN the Q&A_Transcript is generated at graduation, THE flow SHALL present its file path to the
   bootcamper.
3. WHEN `docs/bootcamp_transcript.md` already exists, THE Transcript_Renderer SHALL regenerate it from
   the current Session_Log rather than appending to stale content.
4. THE Q&A_Transcript SHALL be listed alongside the other graduation artifacts so its existence is
   discoverable.

### Requirement 8: Privacy and Distribution Safety

**User Story:** As a maintainer, I want the transcript free of secrets and shippable-safe, so that the
artifact and any test fixtures are safe to distribute.

#### Acceptance Criteria

1. THE Q&A_Transcript SHALL contain only question text and bootcamper-provided answer text — it SHALL
   NOT contain API keys, secrets, credentials, or connection strings.
2. WHEN a logged answer appears to contain a secret pattern (for example a token or connection string
   with embedded credentials), THE Transcript_Renderer SHALL redact the matched value before writing.
3. THE feature SHALL NOT ship test fixtures containing real PII; any sample Q&A fixtures SHALL use
   synthetic content.
4. THE Q&A_Transcript SHALL use only relative paths when referencing project files.

### Requirement 9: Test Coverage

**User Story:** As a maintainer, I want tests for the renderer and the schema usage, so that the
transcript behavior does not regress.

#### Acceptance Criteria

1. THE feature SHALL include pytest tests for the Transcript_Renderer covering ordering, Q&A pairing by
   Question_Id, unanswered questions, and orphan answers.
2. THE feature SHALL include a Hypothesis property test asserting that for any valid sequence of
   Question_Events and Answer_Events, every answered question renders with its paired answer and the
   rendered order matches event order.
3. THE feature SHALL include a test asserting the renderer skips malformed/non-Q&A log lines without
   failing.
4. THE feature SHALL include a test asserting that when there are no Q&A events the renderer warns and
   does not write a misleading transcript.
