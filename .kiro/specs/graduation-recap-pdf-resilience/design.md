# Design Document

## Overview

This feature makes recap PDF generation at graduation resilient to a missing or unrunnable bundled
helper script, so the shareable `docs/bootcamp_recap.pdf` is produced whenever possible and the
bootcamper always knows the state of the recap. Today `graduation.md` Step 0b runs
`python scripts/generate_recap_pdf.py` with a workspace-relative path. Because the power's scripts live
in the installed-power directory and may not exist at that relative path in the bootcamper's workspace,
the invocation can fail to run and the PDF is silently skipped.

The design has three parts:

1. **Helper-first, inline-fallback decision** in Step 0b: prefer the Bundled_Helper when it can be
   located and run; otherwise use a self-contained Inline_Fallback that converts the existing
   `docs/bootcamp_recap.md` to a PDF without depending on the bundled script being importable from the
   workspace.
2. **Graceful degradation and clear messaging**: when neither path can write a PDF (most commonly
   because `fpdf2` is absent), inform the bootcamper of the reason and always point them to the
   existing Markdown recap. Never report success when no PDF was written.
3. **A small, shippable inline generator** that the agent can run during graduation regardless of the
   bundled script's location — reusing the recap parsing/rendering logic from `generate_recap_pdf.py`
   when importable, and otherwise rendering the raw Markdown body so nothing is dropped.

This builds on `recap-pdf-content-loss-fix` (tolerant parser + raw-Markdown fallback) and pairs with
`graduation-markdown-normalization` (Step 0 normalization that feeds Step 0b normalized input). It does
not change the recap Markdown schema.

## Architecture

```text
              GRADUATION FLOW (steering/graduation.md) — Step 0b
   +------------------------------------------------------------------------------+
   |  0b.1 Recap recovery (unchanged)                                              |
   |  0b.2 Recap validation (unchanged)                                            |
   |  0b.3 PDF Generation (RESILIENT):                                             |
   |        - locate Bundled_Helper (senzing-bootcamp/scripts/...)                 |
   |              - found + runs -> use it (today's behavior)                      |
   |              - not found / fails -> Inline_Fallback                           |
   |        - Inline_Fallback: generate_recap_pdf_inline.py                        |
   |              - reuse recap parser/renderer if importable                      |
   |              - else render raw Markdown body (no content dropped)             |
   |              - fpdf2 absent -> skip gracefully + pip hint                     |
   |        - success -> "Recap PDF generated at docs/bootcamp_recap.pdf"          |
   |        - any skip/fail -> state reason + point to docs/bootcamp_recap.md      |
   |  0b.4 Q&A transcript (unchanged)                                              |
   +------------------------------------------------------------------------------+
        Non-blocking throughout: graduation always proceeds to Step 1.
```

## Components and Interfaces

### Inline fallback generator — `senzing-bootcamp/scripts/generate_recap_pdf_inline.py`

A self-contained, stdlib-only (plus lazily-imported optional `fpdf2`) script that converts
`docs/bootcamp_recap.md` to `docs/bootcamp_recap.pdf` without requiring the bundled
`generate_recap_pdf.py` to be present at a workspace-relative path. It follows the project script
pattern (`#!/usr/bin/env python3`, `from __future__ import annotations`, `main(argv=None)`, argparse,
exit 0 on success / 1 on error).

Design choices to keep it self-contained and DRY:

- **Reuse when available, inline when not.** The script attempts to import the recap
  parser/renderer (`parse_recap_markdown`, `render_pdf`) from the sibling `generate_recap_pdf` module.
  If that import succeeds, it delegates to the shared rendering so output matches the bundled helper.
  If the import fails (module not on path in the bootcamper's workspace), it uses an embedded minimal
  Markdown-to-PDF renderer that emits a cover line plus the raw Markdown body as wrapped text/code
  blocks, so no recap content is dropped (consistent with `recap-pdf-content-loss-fix`'s raw-body
  fallback).
- **Lazy `fpdf2` import inside the render function** (never at module top level). When `import fpdf`
  raises `ImportError`, print the `pip install fpdf2` hint to stderr and exit 1 without a traceback —
  the Markdown recap is left as the artifact of record.
- **CLI:** `--input` (default `docs/bootcamp_recap.md`), `--output` (default `docs/bootcamp_recap.pdf`).
  Mirrors `generate_recap_pdf.py` flags so the two are interchangeable.
- **Contract:** stdout `PDF generated: <path>` only when a PDF was actually written; all warnings to
  stderr; exit 1 (no PDF) vs exit 0 (PDF written), so the graduation step can distinguish success from
  skip and never report false success.

```python
def generate_inline(input_path: str, output_path: str) -> int:
    """Generate the recap PDF without depending on the bundled helper being
    importable. Reuse the shared recap renderer when available; otherwise render
    the raw Markdown body. Lazy-import fpdf2; return 1 (with a pip hint) when it
    is absent or no PDF could be written, 0 when a PDF was written."""

def main(argv: list[str] | None = None) -> int: ...
```

### Graduation flow change — `senzing-bootcamp/steering/graduation.md` Step 0b.3

Rewrite Step 0b.3 ("PDF Generation") to describe the resilient decision while keeping 0b.1/0b.2/0b.4
intact:

1. **Prefer the Bundled_Helper.** Attempt `python scripts/generate_recap_pdf.py`. If it runs and writes
   the PDF, report success with the PDF location (today's behavior).
2. **Fall back inline.** If the bundled script cannot be located or run (path does not resolve, file
   missing, or it errors before writing), run the Inline_Fallback
   (`generate_recap_pdf_inline.py`) against `docs/bootcamp_recap.md`. State plainly that an inline
   generation path was used.
3. **Degrade gracefully.** If `fpdf2` is not installed (either path reports it), inform the bootcamper
   PDF generation was skipped and suggest `pip install fpdf2`.
4. **Always point to the Markdown recap.** In every skip/failure case, tell the bootcamper the recap
   content already exists at `docs/bootcamp_recap.md`.
5. **Never claim false success.** Only emit the "Recap PDF generated" line when a PDF file was
   actually written.

The step stays **Non_Blocking**: regardless of outcome, proceed to Step 0b.4 then Step 1.

### Steering index and cross-references

If `graduation.md` grows materially, update its token budget in `steering/steering-index.yaml`. Add a
one-line cross-reference noting this resilience work pairs with `recap-pdf-content-loss-fix` and
`graduation-markdown-normalization`.

## Data Models

No new persistent data model. The inline generator reuses the recap data model
(`RecapHeader`/`RecapSection`/`RecapDocument`) from `generate_recap_pdf.py` when that module is
importable, and otherwise operates directly on Markdown text.

## Error Handling

| Condition | Handling |
|---|---|
| Bundled_Helper path does not resolve / file missing | Use Inline_Fallback; tell bootcamper inline path was used |
| Bundled_Helper runs but errors before writing | Use Inline_Fallback; warn with the reason |
| `generate_recap_pdf` module not importable in workspace | Inline generator uses embedded raw-Markdown renderer |
| `fpdf2` absent | Skip gracefully, print `pip install fpdf2` hint, exit 1, no traceback |
| Recap_Markdown missing/empty | Defer to existing 0b.1/0b.2 recovery/validation; if unrecoverable, skip with reason |
| PDF written successfully | Emit `PDF generated:` and the success message |

The PDF step is non-blocking by contract: graduation always proceeds regardless of outcome.

## Correctness Properties

### Property 1: Inline fallback produces a non-empty PDF body

*For all* representative non-empty `docs/bootcamp_recap.md` inputs, when `fpdf2` is available the
Inline_Fallback writes a PDF whose body is non-empty and contains the recap's renderable content (via
the shared renderer when importable, else the raw-Markdown renderer).
**Validates: Requirements 2.1, 2.2, 2.3, 5.1**

### Property 2: Graceful degradation without fpdf2

*For all* environments where `import fpdf` raises, the Inline_Fallback prints the `pip install fpdf2`
hint, exits 1 without a traceback, and writes no PDF. **Validates: Requirements 2.4, 3.1, 5.2**

### Property 3: No false success

*For all* runs, the success message / `PDF generated:` line is emitted only when a PDF file was actually
written; every skip/failure path instead surfaces the reason and points to `docs/bootcamp_recap.md`.
**Validates: Requirements 3.2, 3.4**

### Property 4: Independence from the bundled helper

*For all* workspaces where `generate_recap_pdf` is not importable, the Inline_Fallback still produces a
PDF (when `fpdf2` is present) using its embedded renderer. **Validates: Requirements 2.2, 5.3**

## Testing Strategy

Tests live in `senzing-bootcamp/tests/` (pytest + Hypothesis), class-based, importing scripts via the
documented `sys.path` pattern.

- **Inline non-empty body (Property 1):** run `generate_inline` on a representative recap; assert exit
  0, PDF written, and (via a parse/render seam) a non-empty body containing the recap's text tokens.
- **Graceful degradation (Property 2):** monkeypatch the `fpdf` import to raise `ImportError`; assert
  the hint on stderr, exit 1, and no PDF written.
- **No false success (Property 3):** assert the `PDF generated:` line appears only when a file is
  written; assert skip/failure paths print the pointer to `docs/bootcamp_recap.md`.
- **Helper independence (Property 4):** simulate `generate_recap_pdf` not being importable (e.g.
  manipulate `sys.modules`/path) and assert the embedded renderer still writes a non-empty PDF.
- **Hypothesis (Property 1):** generate free-form recap Markdown (loose headings + prose + code) and
  assert the inline path yields a non-empty body containing the input's renderable tokens.

## Requirements Traceability

| Requirement | Design element |
|---|---|
| 1 (PDF runs at graduation) | Step 0b.3 helper-first decision; success messaging; non-blocking |
| 2 (self-contained fallback) | `generate_recap_pdf_inline.py`; reuse-when-importable + embedded renderer; lazy fpdf2 |
| 3 (clear messaging / pointer) | Step 0b.3 messaging rules; no-false-success contract |
| 4 (steering & docs) | `graduation.md` Step 0b.3 rewrite; `steering-index.yaml`; cross-ref note |
| 5 (test coverage) | Properties 1-4 tests in `senzing-bootcamp/tests/` |
