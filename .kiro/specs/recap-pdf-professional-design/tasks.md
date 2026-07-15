# Implementation Plan: Recap PDF Professional Design

## Overview

This plan upgrades the recap PDF renderer from a plain layout to a distribution-ready professional document. The implementation introduces a `RecapPDF` subclass with page footers, accent colors, and generous margins; updates heading rendering to use the new typographic hierarchy; adds a pipe-table renderer; upgrades the cover page; wires the generator to use the subclass; adds a visual review loop to the graduation flow; and covers everything with property-based and unit tests.

## Tasks

- [x] 1. Add RecapPDF subclass and professional layout constants
  - [x] 1.1 Add professional layout constants and the RecapPDF subclass to `senzing-bootcamp/scripts/recap_pdf_render.py`
    - Add constants: `ACCENT_COLOR = (0, 90, 156)`, `BODY_COLOR = (40, 40, 40)`, `MARGINS_MM = 20.0`, `TITLE_FONT_SIZE = 32`, `SUBTITLE_FONT_SIZE = 16`, `BOOTCAMPER_FONT_SIZE = 20`, `MODULE_HEADING_FONT_SIZE = 18`, `SUBSECTION_HEADING_FONT_SIZE = 14`, `BODY_FONT_SIZE = 11`, `CODE_FONT_SIZE = 10`, `FOOTER_FONT_SIZE = 9`
    - Add `class RecapPDF(FPDF)` with `__init__` setting margins to `MARGINS_MM` on all sides and auto page break
    - Implement `footer()` method rendering `Page {page_no}` centered at the bottom of every Content_Page (suppressed on page 1 via `is_cover_page()`)
    - Implement `is_cover_page()` returning `True` when `self.page_no() == 1`
    - Import `FPDF` lazily inside the class body or guard the class definition so the module still imports cleanly without fpdf2
    - _Requirements: 4.1, 4.3, 4.4, 5.1, 5.2, 5.3, 11.1_

  - [x] 1.2 Write unit tests for RecapPDF margins and footer
    - Test that `RecapPDF` sets margins >= 15mm on all sides
    - Test that `footer()` does not render on the cover page (page 1)
    - Test that `footer()` renders a page number on content pages
    - _Requirements: 4.1, 4.3, 12.6_

- [x] 2. Update render_heading with accent color and new font sizes
  - [x] 2.1 Update `render_heading` in `senzing-bootcamp/scripts/recap_pdf_render.py`
    - Set `pdf.set_text_color(*ACCENT_COLOR)` before rendering headings
    - Reset to `pdf.set_text_color(*BODY_COLOR)` after rendering
    - Change module-level heading (level 2) font size from 16 → 18
    - Change subsection-level heading (level 3) font size from 13 → 14
    - Preserve spacing behavior (ln(6) before module, ln(4) before subsection, ln(2) after)
    - _Requirements: 3.1, 3.2, 3.3, 5.1, 5.2, 5.3_

  - [x] 2.2 Write unit tests for heading hierarchy and accent color
    - Use recording stub to verify module heading size > subsection size > body size
    - Use recording stub to verify `set_text_color` called with `ACCENT_COLOR` before headings
    - Verify body text uses `BODY_COLOR` distinct from `ACCENT_COLOR`
    - _Requirements: 3.1, 3.2, 5.1, 5.3, 12.6_

- [x] 3. Add render_table for pipe tables
  - [x] 3.1 Implement `render_table` in `senzing-bootcamp/scripts/recap_pdf_render.py`
    - Parse pipe-delimited lines into rows and cells
    - Detect and skip alignment/separator row (matches `^[|\s:\-]+$`)
    - Compute column widths proportionally based on available page width
    - Render header row in bold, data rows in normal weight
    - All cell text rendered via `safe_text` (Latin-1 safe)
    - No cell text omitted
    - _Requirements: 6.4_

  - [x] 3.2 Add pipe-table detection to `render_markdown_body` in `senzing-bootcamp/scripts/recap_pdf_render.py`
    - Add `_is_pipe_table(lines)` helper that checks if the first line contains `|` and the second line is a separator row
    - Insert table-detection branch before prose-paragraph fallback in `render_markdown_body`
    - Malformed pipe tables fall through to prose rendering (no crash)
    - _Requirements: 6.4_

  - [x] 3.3 Write unit test for table rendering
    - Fixed pipe table input → render → extract text → all cell text present
    - _Requirements: 6.4, 12.6_

- [x] 4. Update _render_cover_page with professional layout
  - [x] 4.1 Update `_render_cover_page` in `senzing-bootcamp/scripts/generate_recap_pdf.py`
    - Title rendered at 32pt bold, accent color, centered ("Senzing Bootcamp Recap")
    - New subtitle line: "Bootcamp Completion Recap" at 16pt, body color, centered
    - Bootcamper name rendered at 20pt, centered
    - Start date and total duration rendered as labeled fields (skip if empty/missing without aborting)
    - New Headline_Stats block: "Modules completed: {count}" with count from `len(doc.sections)`
    - All fields optional — empty values simply skipped
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 4.2 Write unit tests for cover page
    - Test that cover page contains title, subtitle, bootcamper name, and Headline_Stats
    - Test that missing start date / duration fields do not abort rendering
    - _Requirements: 2.1, 2.2, 2.4, 2.7, 12.4_

- [x] 5. Wire generate_recap_pdf.py to use RecapPDF
  - [x] 5.1 Update `render_pdf` in `senzing-bootcamp/scripts/generate_recap_pdf.py` to use `RecapPDF` instead of bare `FPDF`
    - Import `RecapPDF` from `recap_pdf_render` (lazy, inside the function body)
    - Replace `pdf = FPDF()` with `pdf = RecapPDF()`
    - Remove the manual `set_auto_page_break(auto=True, margin=20)` call (RecapPDF handles this in `__init__`)
    - Ensure `_render_cover_page` and `_render_module_page` receive the `RecapPDF` instance
    - Verify existing CLI contract preserved: `--input`, `--output` flags, exit codes, `PDF generated:` output
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.3, 11.1_

  - [x] 5.2 Update `render_markdown_pdf` in `senzing-bootcamp/scripts/recap_pdf_render.py` to use `RecapPDF`
    - Replace `pdf = FPDF()` with `pdf = RecapPDF()` in the convenience function
    - _Requirements: 1.1, 4.1, 4.3_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Add visual review loop to graduation steering
  - [x] 7.1 Add visual review loop section to `senzing-bootcamp/steering/graduation.md` Step 0b
    - After the PDF generator exits 0, describe the visual review loop procedure
    - When image-rendering tooling (pdf2image or pymupdf) is available: render first and last content pages to images, inspect for Required_Detail_Section headings
    - If a Required_Detail_Section is missing or condensed: treat PDF as not distribution-ready, log warning
    - The loop is Non_Blocking: any failure logs a warning, points bootcamper to `docs/bootcamp_recap.md`, and allows graduation to continue
    - Graduation flow does not report PDF as generated when no PDF was written
    - Content_Verification (already embedded in generator) remains the mandatory gate
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 8. Add property-based tests for correctness properties
  - [x] 8.1 Write property test for Property 1: Cover page contains Headline_Stats
    - **Property 1: Cover page contains Headline_Stats**
    - **Validates: Requirements 2.1, 2.2, 2.4, 2.7, 12.4**
    - Use `st_recap_document()` → render PDF → extract text → assert title "Senzing Bootcamp Recap", bootcamper name (Latin-1 safe), and module section count present

  - [x] 8.2 Write property test for Property 2: Content round-trip completeness
    - **Property 2: Content round-trip completeness**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.5, 9.1, 12.1, 12.2**
    - Use `st_recap_document()` → render PDF → extract text → assert distinctive token of at least `min(M, MIN_BODY_LINES)` items present

  - [x] 8.3 Write property test for Property 3: Page footer presence on content pages
    - **Property 3: Page footer presence on content pages**
    - **Validates: Requirements 4.3**
    - Use `st_recap_document(min_size=3)` → render PDF → extract text → assert at least one "Page" token with N > 0

  - [x] 8.4 Write property test for Property 4: Table cell text preservation
    - **Property 4: Table cell text preservation**
    - **Validates: Requirements 6.4**
    - Custom strategy generating pipe tables → render → extract text → assert every cell's distinctive token present

  - [x] 8.5 Write property test for Property 5: Accent color consistency
    - **Property 5: Accent color consistency**
    - **Validates: Requirements 5.1, 5.3**
    - Use `st_recap_document()` → recording stub → assert every `set_text_color` call before module headings uses same RGB triple, and same for subsection headings

- [x] 9. Add unit tests for professional layout
  - [x] 9.1 Write unit tests for full-content preservation and verification rejection
    - Test that a representative multi-module Recap_Markdown renders PDF containing each module's Information Shared, Questions & Responses, and Actions Taken content
    - Test that Content_Verification rejects a PDF missing a Required_Detail_Section (exit code 1, no "PDF generated:" line, no published PDF)
    - _Requirements: 9.2, 9.3, 12.1, 12.3_

  - [x] 9.2 Write unit test for graceful degradation when fpdf2 is absent
    - Test that when fpdf2 is absent the renderer degrades gracefully (no traceback) and surfaces the `pip install fpdf2` hint
    - _Requirements: 11.2, 12.5_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All tests follow the project pattern: pytest + Hypothesis, class-based, `sys.path` import pattern, in `senzing-bootcamp/tests/test_generate_recap_pdf.py`
- The design uses Python throughout — no language selection needed
- The `RecapPDF` class must be guarded so `recap_pdf_render.py` remains importable without fpdf2

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "3.1"] },
    { "id": 2, "tasks": ["2.2", "3.2", "4.1"] },
    { "id": 3, "tasks": ["3.3", "4.2", "5.1", "5.2"] },
    { "id": 4, "tasks": ["7.1"] },
    { "id": 5, "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5"] },
    { "id": 6, "tasks": ["9.1", "9.2"] }
  ]
}
```
