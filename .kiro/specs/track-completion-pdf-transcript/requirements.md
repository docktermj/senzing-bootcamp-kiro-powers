# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion J ("Graduation") of the Senzing Bootcamp
> improvement review (`x.md`). Requirements below are a starting point for refinement, not a
> finished spec.

## Introduction

At track completion the bootcamp already **always** creates `docs/completion_summary.md` (see
`completion-summary-offer.md` and `always-create-completion-summary`) and reconciles the Markdown
recap (`docs/bootcamp_recap.md`) via `module-completion-track.md`. But the **recap PDF**
(`generate_recap_pdf.py`) and the **Q&A transcript** (`generate_transcript.py`) are generated only
inside the graduation flow (`graduation.md` Step 0b), which runs only if the bootcamper accepts the
graduation offer (and is skipped entirely when `skip_graduation: true`).

As a result, a bootcamper who declines graduation keeps the Markdown recap and completion summary
but never gets the shareable recap PDF or the Q&A transcript — two deliverables that would help them
share or reproduce their work. The review suggests generating the recap PDF and the transcript
**unconditionally at track completion**, mirroring the always-generate pattern already used for the
completion summary and recap Markdown, so declining graduation no longer forfeits a shareable
record.

## Glossary

- **Track_Completion**: reaching the end of a track (Module 7 for core, Module 11 for advanced) or
  another detected stopping point where the completion summary is generated.
- **Recap_PDF**: `docs/bootcamp_recap.pdf` produced by `scripts/generate_recap_pdf.py`.
- **Transcript**: `docs/bootcamp_transcript.md` produced by `scripts/generate_transcript.py`.
- **Graduation_Flow**: the `graduation.md` workflow, run only when the bootcamper accepts the
  graduation offer.

## Requirements

### Requirement 1: Always generate the recap PDF and transcript at track completion

**User Story:** As a bootcamper who declines graduation, I still want a shareable recap PDF and a
Q&A transcript, so that I keep a portable record of my bootcamp work.

#### Acceptance Criteria

1. WHEN Track_Completion is reached, THE system SHALL generate the Recap_PDF and the Transcript as
   part of the track-completion flow, independent of whether the bootcamper accepts graduation.
2. THE generation SHALL occur after the existing recap Markdown reconciliation (so the PDF reflects
   the reconciled recap) and after any transcript reconciliation pass, preserving the current
   ordering guarantees.
3. WHEN `skip_graduation` is `true`, THE system SHALL still generate the Recap_PDF and Transcript at
   Track_Completion (the skip applies to the graduation workflow, not to these deliverables).

### Requirement 2: Avoid duplicate work in graduation

**User Story:** As a maintainer, I want graduation to not redundantly regenerate deliverables that
track completion already produced.

#### Acceptance Criteria

1. WHEN the Graduation_Flow runs after Track_Completion, THE system SHALL reuse or idempotently
   regenerate the Recap_PDF and Transcript rather than producing conflicting duplicates.
2. THE existing graduation Step 0a/0b reconciliation-then-render ordering SHALL be preserved; moving
   generation earlier SHALL NOT skip the graduation-time reconciliation safety nets.

### Requirement 3: Non-blocking behavior

**User Story:** As a bootcamper, I want track completion to never stall on PDF/transcript generation.

#### Acceptance Criteria

1. IF Recap_PDF or Transcript generation fails or cannot run, THEN the system SHALL log a warning and
   continue the track-completion flow (non-blocking), consistent with the existing always-generate
   patterns.
2. THE feature SHALL preserve the existing graceful degradation of the Recap_PDF when `fpdf2` is
   absent (keep the Markdown recap, print the install hint) — see the related `fpdf2-preflight-note`
   spec.

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want tests so the always-generate behavior does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests asserting the Recap_PDF and Transcript are generated at
   Track_Completion when graduation is declined and when `skip_graduation` is true, and that
   generation is non-blocking on failure.
2. THE feature SHALL include tests asserting graduation does not produce conflicting duplicate
   deliverables.
3. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`.
