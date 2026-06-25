# Requirements Document

## Introduction

At graduation the bootcamp keeps a Markdown recap (`docs/bootcamp_recap.md`) current per module and is
expected to also produce a shareable PDF recap (`docs/bootcamp_recap.pdf`) during Step 0b of the
`graduation.md` flow. A bootcamper reported that at graduation the Markdown recap was produced but the
PDF was not generated — and it was not obvious that the Markdown recap already existed. The workaround
was to generate a PDF inline from the Markdown recap after the fact.

The root cause is a brittle coupling: Step 0b invokes a bundled helper script with a workspace-relative
path (`python scripts/generate_recap_pdf.py`). The power's scripts live in the installed-power
directory, not necessarily in the bootcamper's workspace at that relative path, so the invocation can
silently fail to run, or run against a path that does not resolve. When the helper cannot be located or
run, today's flow has no self-contained fallback and gives the bootcamper no clear signal that (a) the
PDF step was skipped and why, and (b) the Markdown recap already exists and is complete.

This feature makes recap PDF generation at graduation resilient. When the bundled helper can be located
and run, it is used exactly as today. When it cannot, the flow falls back to a self-contained inline
Markdown→PDF generation path that does not depend on the bundled `generate_recap_pdf.py`, and in all
skip/failure cases it clearly points the bootcamper to the existing Markdown recap. The recap PDF step
remains **non-blocking**: graduation always continues regardless of the PDF outcome.

This work builds on `recap-pdf-content-loss-fix` (tolerant parser + raw-Markdown fallback) and is
paired with `graduation-markdown-normalization` (Step 0 normalization before Step 0b). It changes the
graduation workflow's resilience and messaging; it does not change the recap Markdown schema.

## Glossary

- **Recap_Markdown**: The bootcamp recap document `docs/bootcamp_recap.md`, kept current per module.
- **Recap_PDF**: The shareable PDF artifact `docs/bootcamp_recap.pdf` generated at graduation.
- **Bundled_Helper**: The power's PDF generation script `senzing-bootcamp/scripts/generate_recap_pdf.py`.
- **Inline_Fallback**: A self-contained Markdown→PDF generation path used at graduation when the
  Bundled_Helper cannot be located or run, not depending on the Bundled_Helper.
- **Graduation_Flow**: The workflow in `senzing-bootcamp/steering/graduation.md`; its Step 0b generates
  the Recap_PDF.
- **Non_Blocking**: A step whose failure logs a warning and lets graduation continue, consistent with
  the always-generated `GRADUATION_REPORT.md`.

## Requirements

### Requirement 1: Recap PDF Generation Runs at Graduation

**User Story:** As a bootcamper, I want a PDF recap produced at graduation alongside the Markdown
recap, so that I have a polished, shareable artifact for stakeholders.

#### Acceptance Criteria

1. WHEN the Graduation_Flow reaches Step 0b AND a usable Recap_Markdown exists, THE Graduation_Flow
   SHALL attempt to generate the Recap_PDF.
2. WHEN the Bundled_Helper can be located and run, THE Graduation_Flow SHALL generate the Recap_PDF
   using the Bundled_Helper exactly as it does today.
3. WHEN the Recap_PDF is generated successfully, THE Graduation_Flow SHALL inform the bootcamper of the
   PDF location (`docs/bootcamp_recap.pdf`).
4. THE Recap_PDF step SHALL remain Non_Blocking: any failure SHALL log a warning and allow graduation
   to continue.

### Requirement 2: Self-Contained Fallback When the Bundled Helper Is Unavailable

**User Story:** As a bootcamper whose workspace does not contain the bundled script, I want the PDF
generated anyway, so that a missing helper path does not cost me the shareable artifact.

#### Acceptance Criteria

1. WHEN the Bundled_Helper cannot be located or run at the expected path, THE Graduation_Flow SHALL use
   the Inline_Fallback to generate the Recap_PDF from the Recap_Markdown rather than skipping silently.
2. THE Inline_Fallback SHALL NOT depend on the Bundled_Helper being present in the bootcamper's
   workspace.
3. THE Inline_Fallback SHALL read content from the existing Recap_Markdown so the PDF reflects the same
   recap the bootcamper already has.
4. WHEN `fpdf2` (`import fpdf`) is not installed, THE Inline_Fallback SHALL degrade gracefully: it SHALL
   NOT raise, SHALL inform the bootcamper that PDF generation was skipped, and SHALL suggest
   `pip install fpdf2`.
5. THE Inline_Fallback SHALL preserve the Non_Blocking contract: a failure SHALL log a warning and allow
   graduation to continue.

### Requirement 3: Clear Messaging and Pointer to the Markdown Recap

**User Story:** As a bootcamper, I want to know whether the PDF step succeeded or was skipped and where
my recap content already lives, so that I am never left wondering if the recap step silently failed.

#### Acceptance Criteria

1. WHEN the Recap_PDF cannot be generated (helper unavailable AND Inline_Fallback also unavailable, e.g.
   `fpdf2` absent), THE Graduation_Flow SHALL tell the bootcamper that the PDF was not generated and the
   reason.
2. IN every PDF skip or failure case, THE Graduation_Flow SHALL point the bootcamper to the existing
   Recap_Markdown at `docs/bootcamp_recap.md` so they know the recap content already exists.
3. WHEN the Bundled_Helper is unavailable and the Inline_Fallback is used, THE Graduation_Flow SHALL make
   the fallback visible to the bootcamper (state that an inline generation path was used) rather than
   implying the bundled script ran.
4. THE Graduation_Flow SHALL NOT report PDF success when no PDF was actually written.

### Requirement 4: Steering and Documentation Updates

**User Story:** As a power maintainer, I want the resilient behavior reflected in steering, so that the
agent behaves consistently and the fallback is discoverable.

#### Acceptance Criteria

1. THE `senzing-bootcamp/steering/graduation.md` Step 0b SHALL describe the helper-vs-inline decision,
   the Inline_Fallback, the `fpdf2`-absent degradation, and the pointer-to-Markdown messaging.
2. THE Step 0b description SHALL preserve and reference the existing recap recovery/validation
   sub-steps (0b.1/0b.2) and the Non_Blocking contract.
3. WHEN steering files are added or their size changes, THE steering token budgets in
   `steering/steering-index.yaml` SHALL be updated accordingly.
4. THE documentation SHALL note the relationship to `recap-pdf-content-loss-fix` (tolerant parser +
   fallback) and `graduation-markdown-normalization` (Step 0 normalization) so the changes are
   understood as paired.

### Requirement 5: Test Coverage

**User Story:** As a maintainer, I want tests for the resilient generation behavior, so that it does not
regress.

#### Acceptance Criteria

1. THE feature SHALL include a test asserting the Inline_Fallback produces a non-empty Recap_PDF body
   from a representative Recap_Markdown (consistent with `recap-pdf-content-loss-fix` expectations).
2. THE feature SHALL include a test asserting that when `fpdf2` is absent, the Inline_Fallback degrades
   gracefully (no traceback) and surfaces the `pip install fpdf2` hint.
3. THE feature SHALL include a test asserting the Inline_Fallback does not import or depend on the
   Bundled_Helper module being importable from the workspace.
4. THE feature SHALL follow the project test pattern (pytest + Hypothesis where useful, class-based,
   `sys.path` import pattern) and live in `senzing-bootcamp/tests/`.
