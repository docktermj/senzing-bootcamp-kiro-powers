# Requirements Document

> **Status: DRAFT STUB.** Created from discrepancy D3 of the Senzing Bootcamp Experience Review.
> Requirements below are a starting point for refinement, not a finished spec.

## Introduction

The Q&A transcript (`docs/bootcamp_transcript.md`, produced by `scripts/generate_transcript.py`)
depends on the agent voluntarily emitting `question` / `answer` completion events into
`config/session_log.jsonl`, as instructed by the `qa-transcript.md` steering file. Unlike the recap
— which is backed by the `module-recap-append` hook plus a synchronous verify-and-backfill and a
track-completion reconciliation pass — nothing enforces or repairs the transcript's Q&A events. If
the agent omits them (a missed steering instruction, a compacted context, a session boundary),
`generate_transcript.py` warns and writes nothing, and the completion summary's Q&A content is thin
— silently.

This deliberate design (see `bootcamp-qa-transcript` Requirement 3) avoids per-write logging cost, so
the fix must NOT reintroduce a write-tool hook or a per-write process spawn. Instead, this feature
adds a graduation-time (and stopping-point) reconciliation pass that repairs the transcript from an
already-captured, enforced source — the recap's `### Questions & Responses` (QR) pairs — before the
transcript is rendered, mirroring the recap's own backfill safety net.

## Glossary

- **Transcript**: `docs/bootcamp_transcript.md`, the ordered Q&A record rendered by
  `scripts/generate_transcript.py` from `config/session_log.jsonl`.
- **QA_Event**: a `question` or `answer` completion event in `config/session_log.jsonl` (schema per
  `scripts/session_logger.py`).
- **Recap_QR_Pairs**: the interleaved `- **Q:**` / `- **R:**` pairs in the per-module
  `### Questions & Responses` sections of `docs/bootcamp_recap.md`.
- **Reconciliation_Pass**: the new pre-render step that detects a transcript/recap Q&A shortfall and
  backfills missing QA_Events (or renders the transcript from Recap_QR_Pairs) so the transcript is
  complete.

## Requirements

### Requirement 1: Detect a transcript/recap Q&A shortfall

**User Story:** As a maintainer, I want the graduation flow to detect when the logged Q&A events are
materially fewer than the recap's captured Q&R pairs, so that a silent transcript gap is caught
before the deliverable is produced.

#### Acceptance Criteria

1. WHEN the Reconciliation_Pass runs, THE system SHALL count QA_Events in `config/session_log.jsonl`
   and QR pairs across all `### Questions & Responses` sections in `docs/bootcamp_recap.md`.
2. IF the number of logged question events is materially fewer than the recap's QR-pair count for
   the completed modules, THEN the system SHALL treat the transcript as incomplete and trigger a
   backfill.
3. WHEN the counts are consistent, THE system SHALL make no changes (idempotent no-op).

### Requirement 2: Backfill from the recap without per-write cost

**User Story:** As a maintainer, I want the transcript reconstructed from the enforced recap source,
so that transcript completeness becomes a guarantee without coupling Q&A logging to file writes.

#### Acceptance Criteria

1. WHEN a shortfall is detected, THE system SHALL derive the missing Q&A content from the recap's
   Recap_QR_Pairs (grouped by module) and render the transcript from that reconciled source.
2. THE feature SHALL NOT add or modify any `postToolUse` write-tool hook and SHALL NOT change the
   `session-log-events` hook (preserve `bootcamp-qa-transcript` Requirement 3 and the
   `session-log-hook-performance` outcome).
3. THE Reconciliation_Pass SHALL run only at stopping points / graduation, never per file write.
4. WHERE reconstructed content is written back as QA_Events, THE system SHALL reuse
   `session_logger.build_completion_entry` / `append_completion_entry` rather than a new schema.

### Requirement 3: Ordering and non-blocking behavior

**User Story:** As a bootcamper, I want reconciliation to run before the transcript is rendered and
never to block graduation, so that I always get the most complete transcript available.

#### Acceptance Criteria

1. THE Reconciliation_Pass SHALL run before graduation Step 0b.4 (transcript render), analogous to
   Step 0a preceding the recap PDF.
2. IF the Reconciliation_Pass cannot run or fails, THEN the system SHALL log a warning and continue,
   falling back to the existing `generate_transcript.py` behavior.
3. WHEN the recap itself has no QR content, THE system SHALL preserve the existing behavior
   (`generate_transcript.py` warns and writes no misleading transcript).

### Requirement 4: Privacy and distribution safety

**User Story:** As a maintainer, I want reconciled content to stay secret-free and shippable-safe.

#### Acceptance Criteria

1. THE reconciled transcript SHALL contain only question and bootcamper-response text and SHALL NOT
   contain secrets, credentials, or connection strings (reuse the existing transcript redaction).
2. THE feature SHALL NOT ship test fixtures containing real PII; sample fixtures SHALL be synthetic.

### Requirement 5: Test coverage

**User Story:** As a maintainer, I want tests so reconciliation does not regress.

#### Acceptance Criteria

1. THE feature SHALL include pytest tests covering: shortfall detection, backfill from recap QR
   pairs, the idempotent no-op when counts are consistent, and the warn-and-continue fallback.
2. THE feature SHALL include a Hypothesis property test asserting that for any recap with N QR pairs,
   the reconciled transcript renders at least those N question/answer pairs in module order.
3. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`.
