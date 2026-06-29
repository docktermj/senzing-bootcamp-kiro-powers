# Implementation Plan: Graduation Recap PDF Resilience

## Overview

This plan makes recap PDF generation at graduation resilient to a missing or unrunnable bundled helper
script. It adds a self-contained `generate_recap_pdf_inline.py` (reuse the shared recap renderer when
importable, else an embedded raw-Markdown renderer; lazy `fpdf2`), rewrites `graduation.md` Step 0b.3 to
prefer the bundled helper and fall back inline with clear messaging that always points to the Markdown
recap, and adds pytest + Hypothesis coverage. Implementation language is Python 3.11+, stdlib-only with
`fpdf2` as an optional, lazily-imported dependency.

## Tasks

- [x] 1. Scaffold the inline fallback generator
  - [x] 1.1 Create `generate_recap_pdf_inline.py` skeleton and CLI
    - Create `senzing-bootcamp/scripts/generate_recap_pdf_inline.py` with `#!/usr/bin/env python3`,
      `from __future__ import annotations`, stdlib-only top-level imports
    - Implement `parse_args(argv)` with `--input` (default `docs/bootcamp_recap.md`) and `--output`
      (default `docs/bootcamp_recap.pdf`), mirroring `generate_recap_pdf.py`
    - Add a `main(argv=None)` skeleton returning exit 0 on success / 1 on error, following the project
      script pattern
    - _Requirements: 2.1, 2.2_

- [x] 2. Implement self-contained inline generation
  - [x] 2.1 Implement `generate_inline(input_path, output_path)`
    - Validate input exists and is non-empty; on missing/empty, print reason to stderr and return 1
    - Attempt to import `parse_recap_markdown` + `render_pdf` from the sibling `generate_recap_pdf`
      module; when importable, delegate so output matches the bundled helper
    - When `generate_recap_pdf` is NOT importable, render the raw Markdown body with an embedded minimal
      renderer (cover line + wrapped text/code blocks) so no recap content is dropped
    - Lazy-import `fpdf` inside the render path; on `ImportError`, print the `pip install fpdf2` hint to
      stderr and return 1 without a traceback
    - Print `PDF generated: <output>` to stdout ONLY when a PDF file was actually written; return 0
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.4_

  - [x] 2.2 Wire `main` orchestration and messaging contract
    - Call `generate_inline`; ensure all warnings go to stderr and the `PDF generated:` line is the only
      stdout success signal
    - Return 1 for any no-PDF outcome (missing input, `fpdf2` absent, write failure); return 0 only when
      a PDF was written
    - _Requirements: 2.5, 3.1, 3.4_

- [x] 3. Test the inline generator
  - [x] 3.1 Test inline non-empty PDF body (Property 1)
    - Add `senzing-bootcamp/tests/test_generate_recap_pdf_inline.py` (class-based, `sys.path` import
      pattern)
    - Assert `generate_inline` on a representative recap exits 0, writes a PDF, and (via a parse/render
      seam) yields a non-empty body containing the recap's text tokens
    - _Requirements: 5.1, 2.1, 2.3_

  - [x] 3.2 Test graceful degradation without fpdf2 (Property 2)
    - Monkeypatch the `fpdf` import to raise `ImportError`; assert the `pip install fpdf2` hint on
      stderr, exit 1, and no PDF written (no traceback)
    - _Requirements: 5.2, 2.4, 3.1_

  - [x] 3.3 Test helper independence (Property 4)
    - Simulate `generate_recap_pdf` not being importable (manipulate `sys.modules`/path); assert the
      embedded renderer still writes a non-empty PDF when `fpdf2` is present
    - _Requirements: 5.3, 2.2_

  - [x] 3.4 Test no-false-success contract (Property 3)
    - Assert the `PDF generated:` line appears only when a PDF file is written; assert no-PDF paths
      return 1 and do not print the success line
    - _Requirements: 3.4_

  - [x] 3.5 Hypothesis property test for inline body content (Property 1)
    - Generate free-form recap Markdown (loose headings + prose + fenced code); assert the inline path
      yields a non-empty body containing the input's renderable tokens
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 4. Checkpoint - Ensure all inline-generator tests pass
  - Run `pytest senzing-bootcamp/tests/test_generate_recap_pdf_inline.py`; ensure all tests pass, ask
    the user if questions arise

- [x] 5. Make graduation Step 0b.3 resilient
  - [x] 5.1 Rewrite Step 0b.3 in `steering/graduation.md`
    - Describe the helper-first decision: attempt `python scripts/generate_recap_pdf.py`; on
      success report the PDF location (today's behavior)
    - Describe the Inline_Fallback: when the bundled script cannot be located or run, run
      `python scripts/generate_recap_pdf_inline.py` against `docs/bootcamp_recap.md` and state plainly
      that an inline path was used
    - Describe `fpdf2`-absent graceful degradation (skip + `pip install fpdf2` hint)
    - Require pointing the bootcamper to `docs/bootcamp_recap.md` in every skip/failure case
    - State the no-false-success rule (only claim success when a PDF was written)
    - Keep 0b.1/0b.2/0b.4 and the Non_Blocking contract intact
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2_

  - [x] 5.2 Update steering index and cross-references
    - If `graduation.md` grows materially, update its token budget in `steering/steering-index.yaml`
    - Add a one-line note that this resilience work pairs with `recap-pdf-content-loss-fix` and
      `graduation-markdown-normalization`
    - _Requirements: 4.3, 4.4_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Run the recap test suites in `senzing-bootcamp/tests/`; confirm no regressions to existing
    `generate_recap_pdf` tests and that the new inline tests pass. Ask the user if questions arise.

## Notes

- Target code: NEW `senzing-bootcamp/scripts/generate_recap_pdf_inline.py`; steering
  `senzing-bootcamp/steering/graduation.md`; tests in `senzing-bootcamp/tests/`.
- Constraint: Python 3.11+ stdlib only; `fpdf2` stays an optional, lazily-imported dependency that
  degrades gracefully when absent (never imported at module top level).
- This feature depends on `recap-pdf-content-loss-fix` (tolerant parser + raw-Markdown fallback) and
  pairs with `graduation-markdown-normalization` (Step 0 normalization before Step 0b).
- Run tests as single executions, not in watch mode.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5"] },
    { "id": 3, "tasks": ["4"] },
    { "id": 4, "tasks": ["5.1", "5.2"] },
    { "id": 5, "tasks": ["6"] }
  ]
}
```
