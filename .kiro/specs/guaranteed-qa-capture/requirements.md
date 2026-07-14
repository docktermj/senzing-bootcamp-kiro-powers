# Requirements Document: Guaranteed Q&A Capture

## Introduction

The graduation recap and Q&A transcript depend on every 👉 question and its
answer being recorded to `config/session_log.jsonl`. Before this feature, that
recording was **voluntary**: `qa-transcript.md` instructed the agent to emit
`question`/`answer` events by discipline, and — for performance reasons
(`session-log-hook-performance`) — capture was deliberately decoupled from file
writes and never hook-forced. This left capture as a *probable* experience:
mid-module, an un-emitted pair could be lost until a stopping-point
reconciliation ran, and a module abandoned before completion could lose its
Q&A entirely (see the `experience-audit-remediation` D2 finding).

This feature makes Q&A capture **hook-enforced on the Q&A cadence** — driven by
the two existing critical hooks — so it is guaranteed in the same sense as every
other hook-enforced bootcamp behavior (given the hooks are installed), **without**
reintroducing the per-write cost that `session-log-hook-performance` removed.

It supersedes the *voluntary-capture* stance of `bootcamp-qa-transcript` (and its
`qa-transcript.md` steering). It preserves — and must not violate —
`session-log-hook-performance`, and keeps the module-completion recap,
`transcript-reconciliation`, and the `guaranteed-graduation-artifacts` /
`enforce-critical-artifacts` enforcement as defense-in-depth.

## Glossary

- **QA_Helper**: `senzing-bootcamp/scripts/log_qa_event.py`, the deterministic,
  non-blocking, stdlib-only helper that appends `question`/`answer` events.
- **Question_Pending**: `config/.question_pending`, the marker holding the
  outstanding question (type on line 1, text on lines 2+).
- **Capture_Sidecar**: `config/.qa_capture.json`, holding the current pending
  question's `question_id` and text hash for pairing and dedupe.
- **QA_Cadence**: firing once per question (Stop) and once per answer
  (UserPromptSubmit) — never per file write.

## Requirements

### Requirement 1: Deterministic question capture at ask time

**User Story:** As a bootcamper, I want every 👉 question recorded when it is
asked, so my graduation recap and transcript are complete even if I stop
mid-module.

#### Acceptance Criteria

1. WHEN a turn ends with a 👉 leading question, THE `ask-bootcamper` Stop hook SHALL invoke `QA_Helper record-question`.
2. WHEN `Question_Pending` exists, THE QA_Helper SHALL append one `question` event (text from lines 2+, module from `config/bootcamp_progress.json`) and record its `question_id` and text hash in the Capture_Sidecar.
3. WHEN the same pending question is presented again (same text hash), THE QA_Helper SHALL NOT append a duplicate `question` event.
4. WHEN `Question_Pending` is absent, THE QA_Helper `record-question` SHALL make no change.
5. THE question-capture side effect SHALL produce no bootcamper-visible output and SHALL NOT alter the `ask-bootcamper` DEFAULT-OUTPUT (single period) behavior.

### Requirement 2: Deterministic answer capture, paired to its question

**User Story:** As a bootcamper, I want my answer recorded and paired to its
question, so the transcript reads as an ordered exchange.

#### Acceptance Criteria

1. WHEN the bootcamper submits a message AND `Question_Pending` exists, THE `review-bootcamper-input` UserPromptSubmit hook SHALL invoke `QA_Helper record-answer`, passing the bootcamper's verbatim message on stdin.
2. THE QA_Helper SHALL append one `answer` event carrying the bootcamper's message text and the `question_id` from the Capture_Sidecar, then clear the sidecar.
3. WHERE no Capture_Sidecar exists but `Question_Pending` does (the question was not yet logged), THE QA_Helper SHALL self-heal by logging the question first and pairing the answer to it.
4. WHERE neither a Capture_Sidecar nor `Question_Pending` exists, THE QA_Helper SHALL NOT append an `answer` event (no orphan answers).
5. WHEN the submitted message is empty, THE QA_Helper SHALL make no change.
6. THE answer-capture side effect SHALL produce no bootcamper-visible output.

### Requirement 3: No per-write coupling (preserve session-log-hook-performance)

**User Story:** As a maintainer, I want capture to stay off the file-write path,
so the per-write performance regression is never reintroduced.

#### Acceptance Criteria

1. THE feature SHALL NOT add or modify any `PostToolUse` hook on the write tools (`fs_write`, `fs_append`, `str_replace`) for Q&A logging.
2. THE feature SHALL NOT alter the `session-log-events` hook.
3. WHEN a turn performs file writes but asks no question and receives no answer, THE feature SHALL add zero Q&A log entries.
4. THE feature SHALL add no new hook files — capture is folded into the two existing critical hooks (`ask-bootcamper`, `review-bootcamper-input`).

### Requirement 4: Non-blocking and consistent with the never-block principle

**User Story:** As a bootcamper, I never want logging to interrupt the bootcamp.

#### Acceptance Criteria

1. THE QA_Helper SHALL exit 0 on every path, swallowing all errors (missing files, parse errors, I/O errors).
2. THE missing-capture-hook safeguard SHALL remain a **Soft_Block** (advisory, non-blocking) — this feature SHALL NOT promote it to a mandatory gate.
3. THE guarantee level SHALL be documented as "hook-enforced given the hooks are installed," matching every other hook-based bootcamp guarantee, with the recap/reconciliation/enforcement layers as backstops.

### Requirement 5: Registry, steering, and catalog consistency

#### Acceptance Criteria

1. WHEN the two hook prompts change, THE hook registry (`hook-registry.md`, `hook-registry-critical.md`, module slices) and `hooks.lock.yaml` SHALL be regenerated via `sync_hook_registry.py --write` so `--verify` passes.
2. THE `qa-transcript.md` steering SHALL describe the hook-enforced mechanism and preserve the no-per-write-hook constraints; steering token counts and the budget total in `steering-index.yaml` SHALL be re-synced so `measure_steering.py --check` passes.
3. THE `bootcamp-qa-transcript` spec SHALL be recorded as superseded by this spec in `.kiro/spec-catalog.yaml`, and `.kiro/SPEC_CATALOG.md` regenerated.

## Non-Goals

- Reintroducing any per-write hook or per-write process spawn.
- Promoting the capture-hook safeguard to a hard (⛔) gate.
- Changing the event schema in `session_logger.py`.
