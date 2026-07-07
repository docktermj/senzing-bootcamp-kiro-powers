# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion K ("Graduation") of the Senzing Bootcamp
> improvement review (`x.md`). Requirements below are a starting point for refinement, not a
> finished spec. Closely related to `track-completion-pdf-transcript` (suggestion J).

## Introduction

The recap PDF (and the completion-summary PDF) quietly require the optional `fpdf2` dependency
(`import fpdf`), which is lazily imported and degrades gracefully — when it is absent, the scripts
keep the Markdown output and print a `pip install fpdf2` hint. Today that hint fires only *after* a
PDF is attempted, inside the graduation flow (`graduation.md` Step 0b.3 / the PDF scripts). A
bootcamper therefore learns they needed `fpdf2` only at the moment the PDF silently degrades — too
late to have installed it beforehand.

The review suggests a **one-line preflight note at track completion** that sets expectations before
the PDF is attempted: a brief, non-blocking heads-up that installing `fpdf2` will produce a PDF
(otherwise the Markdown recap/summary is still produced). This gives the bootcamper the chance to
install the optional dependency before the deliverables are generated.

## Glossary

- **fpdf2**: the optional third-party dependency (`import fpdf`) used only by
  `generate_recap_pdf.py` and `generate_completion_summary.py` for PDF rendering.
- **Preflight_Note**: a brief, non-blocking one-line message at track completion indicating whether
  `fpdf2` is available and how to install it for a PDF.
- **Track_Completion**: the point where completion deliverables (recap, completion summary, and —
  per suggestion J — recap PDF/transcript) are produced.

## Requirements

### Requirement 1: Surface fpdf2 availability before PDF generation

**User Story:** As a bootcamper, I want to know at track completion whether a PDF will be produced,
so that I can install `fpdf2` before the deliverables are generated if I want the PDF.

#### Acceptance Criteria

1. WHEN Track_Completion is reached AND `fpdf2` is not importable, THE system SHALL display a
   one-line Preflight_Note stating that installing `fpdf2` enables the PDF and that the Markdown
   output is produced regardless.
2. THE Preflight_Note SHALL include the exact install command (`pip install fpdf2`).
3. WHEN `fpdf2` is already available, THE system SHALL NOT display the Preflight_Note (no noise when
   the PDF will succeed).

### Requirement 2: Non-blocking and consistent

**User Story:** As a bootcamper, I want the note to inform me without interrupting the flow.

#### Acceptance Criteria

1. THE Preflight_Note SHALL be informational and non-blocking — it SHALL NOT prompt for input or
   pause the track-completion flow.
2. THE Preflight_Note SHALL NOT change the existing graceful-degradation behavior of the PDF scripts
   (Markdown is still produced; the post-attempt hint remains as the final fallback).
3. THE feature SHALL keep `fpdf2` an optional, lazily-imported dependency (never a hard dependency
   and never imported at module top level), per `python-conventions.md` and `tech.md`.

### Requirement 3: Placement

**User Story:** As a maintainer, I want the note placed where it precedes PDF generation.

#### Acceptance Criteria

1. THE Preflight_Note SHALL appear at Track_Completion before the recap PDF / completion-summary PDF
   generation is attempted (aligning with the always-generate ordering in
   `track-completion-pdf-transcript` when that feature is adopted).
2. THE availability check SHALL detect `fpdf2` the same way the scripts do (attempting `import fpdf`)
   so the note never contradicts the actual render outcome.

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want tests so the note does not regress or become noisy.

#### Acceptance Criteria

1. THE feature SHALL include tests asserting the Preflight_Note appears when `fpdf2` is absent (with
   the install command) and does not appear when `fpdf2` is present, and that it never blocks the
   flow.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`.
