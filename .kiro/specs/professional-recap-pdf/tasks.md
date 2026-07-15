# Implementation Plan: Professional Recap PDF

## Overview

The core implementation (`generate_recap_pdf.py`, `recap_pdf_render.py`, `completion_artifacts.py`) already exists and functions correctly. This plan focuses on:
1. Writing property-based tests (Hypothesis) for the 4 design correctness properties not yet covered by existing PBT test files
2. Addressing the implementation gap where Requirement 2.1 specifies a colored banner area using primary blue (31,78,121) on the Cover_Page — not present in the current `_render_cover_page`
3. Adding a verification check ensuring no placeholder stubs or legacy headings appear in rendered output (Requirements 5.5, 5.6)

Existing PBT coverage already validates:
- Property 2 (Per-module content preservation) → `test_generate_recap_pdf.py::TestPropertyContentRoundTripCompleteness`
- Property 3 (QR format canonical round-trip) → `test_qr_roundtrip_properties.py`
- Property 4 (Split-schema merge correctness) → `test_split_schema_render_properties.py`
- Property 7 (Backfill append-around preservation) → `test_consolidated_log_properties.py` Property 5/6

## Tasks

- [x] 1. Implement Cover_Page colored banner (Requirement 2.1 gap)
  - [x] 1.1 Add colored banner rendering to `_render_cover_page` in `generate_recap_pdf.py`
    - Draw a filled rectangle using primary blue (31,78,121) as a banner area at the top of the Cover_Page before the title
    - The banner should span the full page width (edge-to-edge) and provide a professional visual anchor
    - Adjust title vertical offset so existing content renders below or overlaid on the banner
    - _Requirements: 2.1_

  - [x] 1.2 Write unit test for Cover_Page banner rendering
    - Verify `_render_cover_page` calls `set_fill_color(31, 78, 121)` and `rect()` before emitting the title
    - Use a recording stub PDF (same pattern as existing `test_generate_recap_pdf.py` heading tests)
    - _Requirements: 2.1_

- [x] 2. Property-based test: Cover page metadata round-trip (Property 1)
  - [x] 2.1 Write property test for Cover_Page metadata round-trip
    - **Property 1: Cover page metadata round-trip**
    - **Validates: Requirements 2.4, 2.5, 2.6, 2.7**
    - Create `test_recap_cover_page_properties.py` in `senzing-bootcamp/tests/`
    - Generate random RecapDocument instances with non-empty bootcamper, Started, Total Duration, and 1–5 sections
    - Render to PDF via `render_pdf`, extract text via `extract_pdf_text`
    - Assert: bootcamper name token survives, Started value token survives, Total Duration value token survives, and "Modules completed: N" string (where N = len(sections)) is present in extracted text
    - Use the existing `st_recap_document` strategy pattern from `test_generate_recap_pdf.py`
    - Tag: `Feature: professional-recap-pdf, Property 1: Cover page metadata round-trip`
    - _Requirements: 2.4, 2.5, 2.6, 2.7_

- [x] 3. Property-based test: Verification detects missing content (Property 5)
  - [x] 3.1 Write property test for verification failure detection
    - **Property 5: Verification detects missing content**
    - **Validates: Requirements 5.1, 5.2**
    - Create `test_recap_verification_properties.py` in `senzing-bootcamp/tests/`
    - Generate sets of module numbers (1–6 modules) and expected body lines (3–10 substantive Latin-1-safe lines)
    - Construct a minimal PDF (uncompressed stream with `(text) Tj` operators) that deliberately omits one or more "Module N" headings
    - Assert: `verify_rendered_pdf` raises `PdfVerificationError` when a module heading is missing
    - Generate a PDF with module headings present but fewer than `min_body_lines` distinctive tokens surviving
    - Assert: `verify_rendered_pdf` raises `PdfVerificationError` when body content is insufficient
    - When all headings and sufficient body lines are present, assert no exception is raised
    - Tag: `Feature: professional-recap-pdf, Property 5: Verification detects missing content`
    - _Requirements: 5.1, 5.2_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Property-based test: No placeholder stubs in substantive recaps (Property 6)
  - [x] 5.1 Write property test for placeholder-stub absence
    - **Property 6: No placeholder stubs in substantive recaps**
    - **Validates: Requirements 4.5**
    - Create `test_recap_no_placeholder_properties.py` in `senzing-bootcamp/tests/`
    - Generate RecapDocument instances where every section's content is substantive: no "N/A" items, no "backfilled at track completion" strings in any field
    - Render to PDF via `render_pdf`, extract text via `extract_pdf_text`
    - Assert: extracted text contains zero occurrences of "N/A", "backfilled at track completion", "Questions Asked", "Answers Given" (the legacy headings that should be absent per Requirement 5.6)
    - Strategy must guarantee substantive content: filter out items matching placeholder patterns
    - Tag: `Feature: professional-recap-pdf, Property 6: No placeholder stubs in substantive recaps`
    - _Requirements: 4.5, 5.5, 5.6_

- [x] 6. Property-based test: Atomic output safety (Property 8)
  - [x] 6.1 Write property test for atomic output safety
    - **Property 8: Atomic output safety**
    - **Validates: Requirements 8.2, 8.3**
    - Create `test_recap_atomic_output_properties.py` in `senzing-bootcamp/tests/`
    - Generate valid recap Markdown content (1–4 modules with substantive QR_Pairs and Information Shared)
    - Write content to a temp input file, run `main(["--input", input_path, "--output", output_path])`
    - Assert: when main returns 0, output file exists and is non-empty
    - For the failure path: monkeypatch `render_pdf` to raise `OSError` (or monkeypatch fpdf import to fail)
    - Write a pre-existing output file with known sentinel bytes before running main
    - Assert: when main returns 1, the pre-existing output file is byte-for-byte unchanged
    - Assert: no `.tmp` files linger in the output directory after either success or failure
    - Tag: `Feature: professional-recap-pdf, Property 8: Atomic output safety`
    - _Requirements: 8.2, 8.3_

- [x] 7. Add placeholder/legacy heading verification to the Generator (Requirements 5.5, 5.6)
  - [x] 7.1 Add post-render verification checks for placeholder stubs and legacy headings
    - In `generate_recap_pdf.py`, after `verify_rendered_pdf` passes, extract PDF text and scan for forbidden strings: "N/A" in body context, "backfilled at track completion", "Questions Asked", "Answers Given"
    - If any forbidden string is found, raise `PdfVerificationError` with a descriptive message naming the first occurrence
    - This ensures no recap PDF passes verification while containing stub content
    - _Requirements: 4.5, 5.5, 5.6_

  - [x] 7.2 Write unit tests for placeholder verification
    - Test that a recap with "N/A" in Information Shared triggers verification failure
    - Test that a recap with "backfilled at track completion" triggers verification failure
    - Test that a recap with "Questions Asked" heading text in the PDF triggers verification failure
    - Test that a substantive recap (no placeholders) passes verification cleanly
    - _Requirements: 4.5, 5.5, 5.6_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The design uses Python — all test code uses Hypothesis with the project's centralized profiles (`fast` for local, `thorough` for CI)
- Existing test files already provide extensive coverage for Properties 2, 3, 4, and 7 — no duplicated effort
- The colored banner (Task 1) is the only implementation code change; all other tasks are test-only
- The `ACCENT_COLOR` constant (0,90,156) is used for headings per Requirement 3.2; the banner uses a distinct primary blue (31,78,121) per Requirement 2.1 — these are intentionally different colors in the Color_Palette

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1"] },
    { "id": 1, "tasks": ["1.2", "5.1", "6.1"] },
    { "id": 2, "tasks": ["7.1"] },
    { "id": 3, "tasks": ["7.2"] }
  ]
}
```
