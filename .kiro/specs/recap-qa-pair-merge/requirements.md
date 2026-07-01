# Requirements Document

> **Status: Superseded by `recap-qr-formatting`.** This spec's premise — that the recap
> Markdown keeps separate `### Questions Asked` / `### Answers Given` subsections and that the
> `module-recap-append` hook template is left unchanged (Requirements 3.1 and 3.4) — no longer
> holds. A later spec (`recap-qr-formatting`) rewrote the hook to emit a single merged
> `### Questions & Responses` section of interleaved `- **Q:**` / `- **R:**` pairs. The current
> source of truth is `scripts/recap_pdf_render.py` (`format_qr_section`) and
> `hooks/module-recap-append.kiro.hook`, both of which forbid the two separate headings. The
> merged rendering this spec introduced only at the PDF layer is now the schema at the Markdown
> layer as well. This document is retained for history; do not treat Requirement 3 as current.

## Introduction

In the recap PDF, each module renders two separate sections — "Questions Asked" and "Answers Given" —
as positionally-aligned lists. A reader must mentally pair question N in one list with answer N in the
other, which gets harder as the number of questions per module grows. A bootcamper asked that the two
lists be merged so each question is shown immediately followed by its answer.

This feature changes how the recap PDF renders questions and answers: a single "Questions and
responses" section that pairs each question with its response inline (`Q: <question>` immediately
followed by `A: <response>`). The change is at PDF render time only. The recap Markdown schema
(`docs/bootcamp_recap.md`), the parser, the formatter (`format_recap_section` /
`format_recap_document`), and the `RecapSection` data model (`questions_asked` / `answers_given`) are
intentionally left unchanged so that the format->parse round-trip and Q&A pairing integrity guaranteed
by `recap-pdf-content-loss-fix` continue to hold. The module-recap-append hook continues to write the
two separate Markdown subsections; only the PDF presentation merges them.

This pairs with `recap-pdf-content-loss-fix` (which preserves Markdown Q&A pairing) and
`graduation-recap-pdf-resilience` (which governs when/how the PDF is produced at graduation). The
merged rendering applies to both the bundled helper and the inline fallback PDF paths.

## Glossary

- **Recap_PDF**: The shareable PDF artifact `docs/bootcamp_recap.pdf`.
- **Recap_Markdown**: The recap document `docs/bootcamp_recap.md`, which keeps separate "Questions
  Asked" and "Answers Given" subsections per module.
- **QA_Pair**: A single question and its corresponding answer at the same list index.
- **Merged_QA_Section**: A single PDF section titled "Questions and responses" that renders each
  QA_Pair inline (`Q: <question>` then `A: <response>`).
- **PDF_Renderer**: The per-module PDF rendering in `senzing-bootcamp/scripts/generate_recap_pdf.py`
  (`_render_module_page`) and any equivalent inline-fallback renderer.
- **Markdown_Schema**: The recap Markdown structure (the five `###` subsections) consumed by the
  parser — left unchanged by this feature.

## Requirements

### Requirement 1: Merge Questions and Answers in the PDF

**User Story:** As a reader of the recap PDF, I want each question shown immediately followed by its
answer, so that I do not have to cross-reference two separate lists by position.

#### Acceptance Criteria

1. WHEN the PDF_Renderer renders a module that has questions, THE PDF_Renderer SHALL render a single
   Merged_QA_Section titled "Questions and responses" instead of separate "Questions Asked" and
   "Answers Given" sections.
2. FOR EACH QA_Pair at index i, THE Merged_QA_Section SHALL render the question (`Q: <question>`)
   immediately followed by its answer (`A: <response>`).
3. THE Merged_QA_Section SHALL preserve the original ordering of questions (question at index i before
   question at index i+1).
4. THE Recap_PDF SHALL NOT render separate "Questions Asked" and "Answers Given" headings for a module.

### Requirement 2: Correct Pairing and Unequal-Length Handling

**User Story:** As a reader, I want pairing to be correct even when the counts differ, so that the PDF
never mislabels or drops a question or answer.

#### Acceptance Criteria

1. WHEN the number of questions equals the number of answers, THE Merged_QA_Section SHALL render exactly
   one answer per question, each answer paired with the question at the same index.
2. WHEN there are more questions than answers, THE Merged_QA_Section SHALL render every question and
   SHALL indicate the absence of an answer for unanswered questions rather than misaligning later pairs.
3. WHEN there are more answers than questions, THE Merged_QA_Section SHALL still render every answer
   rather than silently dropping the surplus.
4. WHEN a module has no questions and no answers, THE PDF_Renderer SHALL render the section's empty-state
   consistent with the existing "None" rendering for empty subsections.

### Requirement 3: Markdown Schema and Round-Trip Preserved

**User Story:** As a maintainer, I want the recap Markdown and its parser/formatter unchanged, so that
the existing round-trip and Q&A pairing guarantees are not broken.

#### Acceptance Criteria

1. THE Recap_Markdown Markdown_Schema SHALL continue to use separate "### Questions Asked" and "###
   Answers Given" subsections.
2. THE `RecapSection` data model SHALL retain the `questions_asked` and `answers_given` fields
   unchanged.
3. THE `format_recap_section` / `format_recap_document` output and the parser SHALL be unchanged, so the
   format->parse round-trip (section identity, list contents, Q&A pairing, durations) from
   `recap-pdf-content-loss-fix` continues to pass.
4. THE module-recap-append hook SHALL continue to write the two separate Markdown subsections; this
   feature SHALL NOT change the hook's recap-section template.

### Requirement 4: Apply to All PDF Paths

**User Story:** As a bootcamper, I want the merged rendering regardless of which PDF generation path
runs, so that the output is consistent.

#### Acceptance Criteria

1. THE Merged_QA_Section rendering SHALL apply to the bundled helper PDF path
   (`generate_recap_pdf.py`).
2. WHEN the inline fallback PDF path from `graduation-recap-pdf-resilience` reuses the shared renderer,
   THE Merged_QA_Section rendering SHALL apply there as well.
3. THE merged rendering SHALL be the single rendering behavior — there SHALL NOT be a mode that still
   renders the two separate sections in the PDF.

### Requirement 5: Test Coverage

**User Story:** As a maintainer, I want tests for the merged rendering, so that the pairing behavior does
not regress.

#### Acceptance Criteria

1. THE feature SHALL include a test asserting the rendered PDF body contains a single "Questions and
   responses" section and does not contain separate "Questions Asked"/"Answers Given" headings.
2. THE feature SHALL include a test asserting each rendered QA_Pair places the answer immediately after
   its question in index order.
3. THE feature SHALL include a test covering unequal-length questions/answers (more questions than
   answers and vice versa) without misalignment or dropped content.
4. THE feature SHALL include a test asserting the Markdown round-trip and Q&A pairing tests from
   `recap-pdf-content-loss-fix` still pass (no regression to the Markdown schema).
5. THE feature SHALL follow the project test pattern (pytest + Hypothesis where useful, class-based,
   `sys.path` import pattern) in `senzing-bootcamp/tests/`.
