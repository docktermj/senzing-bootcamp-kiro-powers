# Implementation Plan: Shared Markdown Renderer Refactor

## Overview

This is a behavior-preserving refactor implemented in **Python 3.11+ (stdlib only, lazy `fpdf`)**,
matching the existing `senzing-bootcamp/scripts/` conventions. The plan builds the canonical
`recap_pdf_render.py` module first, validates it with Hypothesis property tests, then rewires the
Bundled_Generator and Inline_Generator onto it and removes the duplicated embedded renderer.

Each task builds on the previous and ends with the generators wired to the shared module, leaving no
orphaned code. Property tests use the existing Hypothesis setup (`hypothesis_profiles`, the `st_`
strategy convention, and the documented `sys.path` import idiom); do not hand-set
`@settings(max_examples=...)` to restate the profile baseline.

## Tasks

- [x] 1. Create the Shared_Renderer_Module skeleton and shared primitives
  - [x] 1.1 Create `senzing-bootcamp/scripts/recap_pdf_render.py` with stdlib-only top-level imports
    - Add `from __future__ import annotations` and `import re`; do NOT import `fpdf` at top level
    - Implement `safe_text(text)` (encode `latin-1`, `errors='replace'`) and
      `split_blocks(text)` (paragraph grouping; fenced ```` ``` ```` blocks stay intact across blank
      lines), ported verbatim from the existing bundled helpers `_safe_text` / `_split_into_blocks`
    - _Requirements: 1.2, 1.4, 6.1_

  - [x] 1.2 Implement the per-block rendering primitives in `recap_pdf_render.py`
    - Implement `render_heading(pdf, text, level)`, `render_list_items(pdf, items, numbered=False)`,
      and `render_generic_blocks(pdf, blocks)` (fenced code rendered monospace with fence delimiter
      lines removed), ported from the bundled `_render_heading` / `_render_list_items` /
      `_render_generic_blocks` so behavior is preserved
    - Use the type-only `"FPDF"` annotation so no `fpdf` import is needed at module level
    - _Requirements: 1.1, 1.5_

  - [x] 1.3 Implement `render_markdown_body` and `render_markdown_pdf` entry points
    - `render_markdown_body(pdf, body_text)`: split via `split_blocks` and dispatch to the heading /
      list / generic primitives into the caller-provided FPDF instance; no page/cover management, no
      `fpdf` import
    - `render_markdown_pdf(body_text, output_path, *, title="Senzing Bootcamp Recap")`: lazily
      `import fpdf` inside the body, create the document, emit the single bold cover line, call
      `render_markdown_body`, and write the PDF
    - _Requirements: 1.1, 1.3, 6.1_

- [x] 1.4 Write property test for content survival through the Shared_Renderer
  - **Property 1: Raw body content survives rendering**
  - **Validates: Requirements 1.3, 2.4, 3.2, 7.1, 8.1**
  - Generate non-empty free-form recap Markdown with injected ASCII marker tokens; assert non-empty
    body and that every token survives via the `split_blocks` seam, and a valid `%PDF` file is
    written when `fpdf2` is present (this is the Req 8.1 direct test)
  - Tag: `# Feature: shared-markdown-renderer-refactor, Property 1: ...`

- [x] 1.5 Write property test for Latin-1 safety
  - **Property 2: Latin-1 safety never raises an encoding error**
  - **Validates: Requirements 1.4**
  - For arbitrary strings (including astral/non-Latin-1 code points), assert
    `safe_text(s).encode("latin-1")` succeeds and rendering a body containing `s` raises no encoding
    error
  - Tag: `# Feature: shared-markdown-renderer-refactor, Property 2: ...`

- [x] 1.6 Write property test for fenced-code delimiter stripping
  - **Property 3: Fenced-code rendering strips the fence delimiters**
  - **Validates: Requirements 1.5**
  - For fenced-code blocks with arbitrary inner content, assert the renderer drops the
    ```` ``` ```` delimiter lines and retains the inner code lines
  - Tag: `# Feature: shared-markdown-renderer-refactor, Property 3: ...`

- [x] 1.7 Write structural/smoke tests for the Shared_Renderer_Module
  - Assert the module imports only stdlib at top level and imports cleanly with
    `sys.modules["fpdf"] = None` (no top-level `fpdf` import)
  - Assert the module does NOT import the Structured_Module and is importable with
    `generate_recap_pdf` forced unimportable
  - _Requirements: 1.2, 3.3, 6.1, 7.2, 8.5_

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Migrate the Bundled_Generator onto the Shared_Renderer
  - [x] 3.1 Replace the Bundled_Generator's embedded raw helpers with shared imports
    - In `senzing-bootcamp/scripts/generate_recap_pdf.py`, remove the local `_safe_text`,
      `_split_into_blocks`, `_render_heading`, `_render_list_items`, `_render_generic_blocks`, and the
      body of `render_markdown_body`
    - Add `from recap_pdf_render import (safe_text, split_blocks, render_heading, render_list_items,
      render_generic_blocks, render_markdown_body)`
    - Repoint the structured path (`_render_cover_page`, `_render_module_page`, `_render_qa_pairs`,
      `_build_qa_lines`) to the shared `safe_text` / `render_heading` / `render_list_items` /
      `render_generic_blocks`, and the `render_pdf` raw-body fallback to the shared
      `render_markdown_body(pdf, body_text)`; leave cover page, `main`, `parse_args`, parser/model,
      and warnings untouched
    - _Requirements: 1.1, 3.1, 3.2_

- [x] 3.2 Verify Bundled_Generator regression and CLI/exit-code behavior
  - Run `senzing-bootcamp/tests/test_generate_recap_pdf.py` and confirm it passes WITHOUT
    modification to asserted behavior
  - Confirm CLI defaults (`--input docs/bootcamp_recap.md`, `--output docs/bootcamp_recap.pdf`),
    Success_Line on stdout only on written PDF, exit codes, and `fpdf2`-absent hint/no-traceback
  - _Requirements: 3.1, 4.2, 4.3, 4.4, 5.1, 5.5, 6.2, 6.3, 8.3_

- [x] 4. Migrate the Inline_Generator onto the Shared_Renderer
  - [x] 4.1 Remove the Inline_Generator's embedded renderer and call the shared module
    - In `senzing-bootcamp/scripts/generate_recap_pdf_inline.py`, delete `_render_inline_pdf`,
      `_split_blocks`, and `_safe_text` entirely
    - Add `from recap_pdf_render import render_markdown_pdf`; in `generate_inline`, the fallback
      branch (bundled module not importable) calls `render_markdown_pdf(content, output_path)`
    - Leave `_import_bundled_renderer`, input validation, the `fpdf` `ImportError` handling, the
      `OSError` handling, the post-render output-exists check, the Success_Line, and exit codes
      unchanged
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 7.1, 7.3_

- [x] 4.2 Update and verify the Inline_Generator regression tests
  - Edit `senzing-bootcamp/tests/test_generate_recap_pdf_inline.py` ONLY where it imported the
    removed embedded helpers: repoint `from generate_recap_pdf_inline import _split_blocks` (and its
    uses) to `recap_pdf_render.split_blocks`; change no asserted behavior
  - Confirm the test verifying inline rendering via the Shared_Renderer when the Structured_Module is
    not importable passes, and exit 0 with a valid PDF
  - _Requirements: 2.1, 2.4, 7.1, 7.3, 8.2, 8.4_

- [x] 4.3 Verify Inline_Generator CLI, exit-code, and graceful-degradation contract
  - Confirm CLI defaults (`--input`/`--output`), Success_Line on stdout only on written PDF, exit 0
    on success, exit 1 with no Success_Line for missing input, empty input, missing PDF, and
    `fpdf2`-absent (hint to stderr, no traceback)
  - _Requirements: 4.1, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 6.2, 6.3_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP.
- Each task references specific requirements (granular sub-requirements) for traceability.
- Property tests (1.4–1.6) validate the three universal Correctness Properties from the design and
  are placed immediately after the shared module is built to catch errors early.
- Property tests reuse the installed Hypothesis library and the active profile baseline (`fast`→10
  locally, `thorough`→100 in CI); do not implement property testing from scratch or hand-set
  `max_examples` to restate the baseline.
- Unit/smoke tests cover the CLI/stdout/exit-code contracts and the structural/dependency/lazy-import
  guarantees that are not property-based.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4", "1.5", "1.6", "1.7"] },
    { "id": 4, "tasks": ["3.1", "4.1"] },
    { "id": 5, "tasks": ["3.2", "4.2", "4.3"] }
  ]
}
```
