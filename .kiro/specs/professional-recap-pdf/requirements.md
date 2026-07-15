# Requirements Document

## Introduction

The `bootcamp_recap.pdf` is the culminating "trophy" deliverable of the Senzing Bootcamp. This feature guarantees that the PDF is always generated at bootcamp completion, contains complete per-module content (Information Shared, Questions & Responses, Actions Taken), and presents a polished, professional appearance. The feature addresses reported issues where the PDF was sometimes skipped, rendered without styling, contained "N/A" stubs for modules 3–6, or used incorrect subsection headings.

## Glossary

- **Recap_PDF**: The generated `docs/bootcamp_recap.pdf` file produced by `generate_recap_pdf.py`
- **Generator**: The `senzing-bootcamp/scripts/generate_recap_pdf.py` script responsible for parsing the recap Markdown and rendering the PDF
- **Shared_Renderer**: The `senzing-bootcamp/scripts/recap_pdf_render.py` module providing canonical PDF rendering primitives
- **Recap_Markdown**: The source file `docs/bootcamp_recap.md` containing per-module recap content
- **Module_Section**: A `## Module N: <name>` section within the Recap_Markdown, containing subsections for that module's content
- **Required_Subsections**: The three mandatory subsections within each Module_Section: "Information Shared", "Questions & Responses", "Actions Taken"
- **QR_Pair**: A question/response pair formatted as `- **Q:** ...` followed by indented `    - **R:** ...`
- **Backfill_Stub**: Placeholder content such as "N/A" or "backfilled at track completion" inserted when real content was unavailable
- **Stop_Hook**: The Phase 0 module-boundary hook that captures recap content at module completion
- **Verification_Pass**: The post-generation step that extracts PDF text and confirms all expected content is present
- **Cover_Page**: The first page of the Recap_PDF containing title, metadata, and headline results
- **Content_Page**: Any page after the Cover_Page containing per-module recap content
- **Color_Palette**: The defined set of colors used throughout the PDF: primary blue (31,78,121), accent (13,110,168), ink (33,37,41), muted (110,110,110)
- **Track_Completion**: The point at which all modules in the bootcamper's selected track have been completed
- **Graduation**: The optional workflow that follows Track_Completion to produce production-ready artifacts

## Requirements

### Requirement 1: Guaranteed PDF Generation at Bootcamp Completion

**User Story:** As a bootcamper, I want the recap PDF to always be generated when I complete the bootcamp, so that I always receive my trophy deliverable without manual intervention.

#### Acceptance Criteria

1. WHEN Track_Completion occurs, THE Generator SHALL produce the Recap_PDF at `docs/bootcamp_recap.pdf`
2. WHEN Graduation runs, THE Generator SHALL produce the Recap_PDF at `docs/bootcamp_recap.pdf`
3. IF the Generator exits with a non-zero code, THEN THE orchestrating workflow SHALL report the specific failure reason to the bootcamper
4. IF the Recap_Markdown file does not exist at generation time, THEN THE Generator SHALL exit with code 1 and report "Recap file not found" to stderr
5. IF the Recap_Markdown file is empty at generation time, THEN THE Generator SHALL exit with code 1 and report "Recap file is empty" to stderr
6. WHEN generation succeeds, THE Generator SHALL verify the output file exists and is non-empty before reporting success

### Requirement 2: Professional Cover Page Presentation

**User Story:** As a bootcamper, I want the recap PDF to have a professional cover page, so that the document looks polished and suitable for sharing with colleagues.

#### Acceptance Criteria

1. THE Cover_Page SHALL display a colored banner area using primary blue (31,78,121)
2. THE Cover_Page SHALL display the title "Senzing Bootcamp" in accent color (13,110,168) at 32pt bold
3. THE Cover_Page SHALL display the subtitle "Completion Recap" at 16pt below the title
4. WHEN the Recap_Markdown contains a Bootcamper field, THE Cover_Page SHALL display the bootcamper name at 20pt centered below the subtitle
5. WHEN the Recap_Markdown contains a Started field, THE Cover_Page SHALL display "Started: {value}" centered below the bootcamper name
6. WHEN the Recap_Markdown contains a Total Duration field, THE Cover_Page SHALL display "Total Duration: {value}" centered below the Started field
7. THE Cover_Page SHALL display a "Headline Results" card showing the count of completed modules
8. THE Cover_Page SHALL suppress the page footer (no page number on the cover)

### Requirement 3: Per-Module Professional Styling

**User Story:** As a bootcamper, I want each module section to be visually distinct and professionally styled, so that the document is easy to navigate and read.

#### Acceptance Criteria

1. WHEN rendering a Module_Section, THE Shared_Renderer SHALL start the module on a new page
2. WHEN rendering a Module_Section heading, THE Shared_Renderer SHALL display it in accent color (0,90,156) at 18pt bold
3. WHEN rendering a Required_Subsection heading, THE Shared_Renderer SHALL display it in accent color (0,90,156) at 14pt bold
4. THE Shared_Renderer SHALL use ink color (40,40,40) for all body text at 11pt
5. THE Shared_Renderer SHALL use Courier at 10pt for code blocks and inline code spans
6. WHEN rendering Content_Pages, THE Shared_Renderer SHALL display a centered "Page N" footer at 9pt
7. THE Shared_Renderer SHALL apply 20mm margins on all sides of every page
8. THE Color_Palette SHALL remain consistent throughout the entire document

### Requirement 4: Content Completeness Enforcement

**User Story:** As a bootcamper, I want every completed module to have its full content in the PDF, so that none of my bootcamp work is lost or represented by placeholder stubs.

#### Acceptance Criteria

1. WHEN a Module_Section is rendered, THE Generator SHALL include all three Required_Subsections: "Information Shared", "Questions & Responses", "Actions Taken"
2. THE Generator SHALL use the heading "### Questions & Responses" for the Q&R subsection
3. THE Generator SHALL format QR_Pairs as `- **Q:** ...` on one line followed by `    - **R:** ...` indented on the next line
4. IF a Module_Section contains a "Questions Asked" or "Answers Given" heading, THEN THE Generator SHALL merge them into a single "Questions & Responses" rendering
5. THE Recap_PDF SHALL contain zero instances of "N/A" stub text or "backfilled at track completion" placeholder text in any module's Required_Subsections
6. WHEN the source Recap_Markdown contains substantive content for a module, THE Generator SHALL preserve that content verbatim (Latin-1-safe) in the rendered PDF

### Requirement 5: Post-Generation Self-Verification

**User Story:** As a bootcamper, I want the system to verify the PDF after generation, so that incomplete or corrupted output is caught before being presented to me.

#### Acceptance Criteria

1. WHEN the Recap_PDF is generated, THE Generator SHALL extract text from the PDF and verify all N module section headings are present
2. WHEN the Recap_PDF is generated, THE Generator SHALL verify that the extracted text contains distinctive tokens from the source body lines
3. IF verification detects a missing module section, THEN THE Generator SHALL report which module(s) are missing and exit with code 1
4. IF verification detects fewer than 3 surviving body lines (when the source has at least 3), THEN THE Generator SHALL report the content-loss failure and exit with code 1
5. THE Generator SHALL verify the PDF contains no "backfilled at track completion" text strings
6. THE Generator SHALL verify the PDF contains no "Questions Asked" or "Answers Given" heading text (only "Questions & Responses" or the merged "Questions and responses" label)
7. IF any verification check fails, THEN THE Generator SHALL remove the temporary PDF file and leave the previous output unchanged

### Requirement 6: Real-Time Content Capture at Module Boundaries

**User Story:** As a bootcamper, I want my recap content captured at each module completion, so that the final PDF contains real session content rather than lossy backfill stubs.

#### Acceptance Criteria

1. WHEN a module completes, THE Stop_Hook SHALL append the module's "Information Shared", "Questions & Responses", and "Actions Taken" content to the Recap_Markdown
2. THE Stop_Hook SHALL write each QR_Pair using the canonical format: `- **Q:** ...` followed by `    - **R:** ...`
3. WHEN the Stop_Hook fires, THE system SHALL verify the appended Module_Section contains all three Required_Subsections before reporting success
4. IF the Stop_Hook cannot capture content for a module (session boundary loss), THEN THE system SHALL record an explicit note indicating the reason rather than inserting a generic "N/A" stub
5. THE backfill reconciliation pass (completion_artifacts.py) SHALL serve only as a safety net for modules missed by the Stop_Hook, appending sections that do not yet exist without rewriting sections that already persisted

### Requirement 7: Graceful Degradation When fpdf2 Is Absent

**User Story:** As a bootcamper, I want the system to handle a missing fpdf2 dependency gracefully, so that I still retain my recap content in Markdown form even when a PDF cannot be produced.

#### Acceptance Criteria

1. IF fpdf2 is not installed, THEN THE Generator SHALL print "fpdf2 is required. Install with: pip install fpdf2" to stderr and exit with code 1
2. IF fpdf2 is not installed, THEN THE Generator SHALL leave the Recap_Markdown file unchanged and accessible to the bootcamper
3. WHEN fpdf2 is absent, THE orchestrating workflow SHALL inform the bootcamper that the Markdown recap is available at `docs/bootcamp_recap.md` as an alternative

### Requirement 8: Atomic Output and Failure Safety

**User Story:** As a bootcamper, I want the PDF generation to be atomic, so that a failed generation never leaves a corrupted or incomplete file in place of a valid previous output.

#### Acceptance Criteria

1. THE Generator SHALL render the PDF to a temporary file in the same directory as the output path before moving it into place
2. WHEN rendering and verification both succeed, THE Generator SHALL atomically replace the output file using `os.replace`
3. IF rendering fails or verification fails, THEN THE Generator SHALL remove the temporary file and leave any existing output file unchanged
4. IF the temporary file cannot be created (missing directory, permissions), THEN THE Generator SHALL report the OS error and exit with code 1
