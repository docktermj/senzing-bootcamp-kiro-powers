# Requirements Document

## Introduction

A verification of the Senzing Bootcamp power found that the stated outcome "each question is only asked once unless the bootcamper asks to have it repeated" is only true *in spirit*. There are scattered "do not re-ask" rules (the Module 8 hardware question, verbosity/language on session resume, "whats-new" shown once per session, feedback not re-prompted) and per-step checkpoints that discourage re-asking, but there is no single, enforced guarantee. The agent can — especially after context compaction or a session resume — re-present a question the bootcamper already answered, and there is no explicit, reliable mechanism for the bootcamper to request that a question be repeated.

This feature makes "ask each question at most once, unless the bootcamper explicitly requests a repeat" a durable, enforced guarantee backed by a persisted ledger of asked-and-answered questions, so the guarantee survives context compaction and session resume.

## Glossary

- **Question**: A `👉`-prefixed prompt directed at the bootcamper that yields the turn and awaits a real response.
- **Question_Key**: A stable identifier for a Question, derived from its owning step (e.g., module + step/sub-step id, or a named onboarding step like `onboarding.language_selection`). Two prompts with the same Question_Key are considered "the same question."
- **Question_Ledger**: A persisted record of every Question that has been asked and whether it has been answered, keyed by Question_Key. Stored under `config/`.
- **Answered_Question**: A Question whose Question_Key is recorded in the Question_Ledger with an answer captured.
- **Repeat_Request**: An explicit bootcamper message asking to see the previous/current question again (e.g., "repeat that", "say that again", "what was the question", "ask me again").
- **Pending_Question**: The single currently-outstanding Question, tracked by the existing `config/.question_pending` marker.
- **Ask_Bootcamper_Hook**: The existing `ask-bootcamper` Stop-trigger hook that generates the closing `👉` question when the agent stops.
- **Review_Input_Hook**: The existing `review-bootcamper-input` UserPromptSubmit hook that classifies the bootcamper's message.

## Requirements

### Requirement 1: Persisted Ledger of Asked Questions

**User Story:** As a bootcamp maintainer, I want every asked question recorded durably with a stable key, so that "asked once" can be enforced across turns, context compaction, and session resume.

#### Acceptance Criteria

1. WHEN the agent presents a Question, THE agent SHALL record its Question_Key in the Question_Ledger before the turn ends.
2. WHEN the bootcamper answers a Question, THE agent SHALL mark that Question_Key as answered in the Question_Ledger.
3. THE Question_Ledger SHALL persist under `config/` (a new file, e.g. `config/question_ledger.jsonl`) so it survives session resume and context compaction.
4. THE Question_Ledger SHALL record, per entry, at minimum: the Question_Key, a status (`asked` or `answered`), and a timestamp.
5. WHERE team mode is active, THE Question_Ledger SHALL be scoped per member consistent with the existing per-member preferences/progress convention.

### Requirement 2: Ask Each Question At Most Once

**User Story:** As a bootcamper, I want to never be asked a question I already answered, so that the bootcamp respects my time and does not feel repetitive or broken.

#### Acceptance Criteria

1. BEFORE presenting a Question, THE agent SHALL check the Question_Ledger and SHALL NOT re-present a Question whose Question_Key is already an Answered_Question.
2. WHEN a step whose Question is already an Answered_Question is reached again, THE agent SHALL use the previously captured answer and proceed without re-asking.
3. IF a Question was recorded as `asked` but not answered (e.g., the session ended before a response), THEN THE agent MAY re-present it, because it was never answered.
4. THE guarantee SHALL hold across session resume: a resumed session SHALL consult the Question_Ledger and skip Answered_Questions.
5. THE guarantee SHALL hold after context compaction: the ledger, not conversational memory, is the source of truth for what has been asked.

### Requirement 3: Explicit Repeat Requests Are Honored

**User Story:** As a bootcamper, I want to be able to ask for the last question to be repeated, so that I can re-read it without it counting as a new or duplicate question.

#### Acceptance Criteria

1. WHEN the bootcamper issues a Repeat_Request, THE agent SHALL re-present the current Pending_Question verbatim (same `👉` text).
2. WHEN a Question is re-presented due to a Repeat_Request, THE agent SHALL NOT create a duplicate Question_Ledger entry and SHALL NOT change the Question's answered status.
3. WHEN there is no Pending_Question at the time of a Repeat_Request, THE agent SHALL state that there is no outstanding question rather than inventing one.
4. THE Review_Input_Hook SHALL recognize the Repeat_Request trigger phrases and route them to the repeat behavior.

### Requirement 4: Enforcement, Not Just Guidance

**User Story:** As a bootcamp maintainer, I want the "asked once" behavior enforced by the same machinery that already governs questions, so that it is reliable rather than advisory.

#### Acceptance Criteria

1. THE Ask_Bootcamper_Hook SHALL consult the Question_Ledger when generating a closing Question and SHALL NOT generate a Question that duplicates an Answered_Question for the current step.
2. THE steering rules (`conversation-protocol.md`, `agent-behavior-rules.md`, `agent-instructions.md`) SHALL state the "ask at most once unless a Repeat_Request" guarantee as a normative rule, replacing the current scattered, ad-hoc "do not re-ask" notes with a single referenced rule.
3. THE existing narrow "do not re-ask" notes (Module 8 hardware question, session-resume preference fields) SHALL be reframed as instances of the general guarantee.
4. WHERE a ledger read or write fails, THE behavior SHALL degrade safely: the agent falls back to existing checkpoint/preference state and never blocks the bootcamper, but SHALL NOT treat an unknown state as license to spam a previously answered Question when preferences already contain the answer.

### Requirement 5: A Ledger Helper Script

**User Story:** As a bootcamp maintainer, I want a small stdlib script to read/write the Question_Ledger, so that hooks and steps interact with it consistently.

#### Acceptance Criteria

1. THE power SHALL provide a stdlib-only Python script under `senzing-bootcamp/scripts/` (e.g., `question_ledger.py`) exposing operations to record an asked Question, mark a Question answered, and query whether a Question_Key is an Answered_Question.
2. THE script SHALL follow the repository Python conventions (shebang, `from __future__ import annotations`, `argparse` CLI with `main(argv=None)`, dataclasses, exit 0 success / 1 error, type hints, stdlib-only).
3. THE script SHALL be idempotent: recording the same asked Question_Key twice SHALL NOT create conflicting or duplicate answered state.
4. THE script SHALL tolerate a missing or malformed ledger file by treating it as empty and (on write) recreating it, without raising to the caller.

### Requirement 6: Tests

**User Story:** As a bootcamp maintainer, I want tests that prove the guarantee, so that it does not regress.

#### Acceptance Criteria

1. THE test suite SHALL include property-based tests for the ledger helper covering idempotent record/answer/query operations and malformed-file tolerance.
2. THE test suite SHALL assert that the steering rules contain the single normative "ask at most once unless a Repeat_Request" guarantee.
3. THE test suite SHALL assert that the Review_Input_Hook recognizes the Repeat_Request trigger phrases.
4. WHEN the full suite runs, THE suite SHALL pass.
