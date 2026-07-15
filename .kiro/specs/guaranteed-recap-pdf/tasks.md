# Implementation Plan: Guaranteed Recap PDF

## Overview

Guarantee that `docs/bootcamp_recap.pdf` is always a valid PDF at every graduation/stopping point, via a three-tier strategy: rich `fpdf2` renderer → best-effort guarded autoinstall → stdlib-only PDF writer. Keep `fpdf2` optional and lazily imported; the stdlib writer is the actual guarantee. Update the orchestrator/`--check`, steering wording, and tests.

## Tasks

- [x] 1. Stdlib-only PDF writer
  - [x] 1.1 Implement `scripts/recap_pdf_minimal.py`
    - `render_minimal_pdf(doc, out_path)` emitting a valid PDF 1.4 (catalog/pages/content stream, Helvetica, xref, trailer) from the existing `RecapDocument` model; per-module headings + labeled subsections (Information Shared, Questions & Responses, Actions Taken, Journal); line wrapping and multi-page overflow. Stdlib-only, no fpdf2.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.2_
  - [x] 1.2 Property-based tests `test_recap_pdf_minimal.py`
    - Arbitrary `RecapDocument`s → output starts with `%PDF-`, has trailer, and `extract_pdf_text` contains each module name and subsection label.
    - _Requirements: 7.1_

- [x] 2. Central tier strategy
  - [x] 2.1 Implement `scripts/pdf_render_strategy.py`
    - `ensure_recap_pdf(doc, out_path, *, allow_autoinstall, timeout_s) -> tier`: lazy import probe → guarded `python -m pip install fpdf2` (bounded timeout, at most once) → dispatch rich vs stdlib. Resolve `allow_autoinstall` from `SENZING_BOOTCAMP_PDF_AUTOINSTALL` env and/or a preferences key (default on, always safe to fail).
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1_
  - [x] 2.2 Tests `test_pdf_render_strategy.py`
    - Monkeypatch probe/subprocess: present→rich; absent+off→stdlib(no subprocess); absent+on+fail→stdlib; absent+on+success→autoinstalled/rich; autoinstall at most once; timeout respected (mocked). No real network.
    - _Requirements: 7.3, 7.4_

- [x] 3. Route generators through the strategy
  - [x] 3.1 Update `scripts/generate_recap_pdf.py`
    - Produce the PDF via the tier strategy; keep the fpdf2 renderer as Tier 1; keep lazy import.
    - _Requirements: 1.1, 2.1, 2.5, 5.1, 6.1_
  - [x] 3.2 Update `scripts/generate_recap_pdf_inline.py`
    - Same tiering for the inline graduation fallback.
    - _Requirements: 1.1, 2.5, 5.1_

- [x] 4. Guarantee in the orchestrator
  - [x] 4.1 Update `scripts/ensure_graduation_artifacts.py`
    - Make `docs/bootcamp_recap.pdf` the guaranteed rendered-recap artifact via the tier strategy; regenerate when absent/empty/stale; keep idempotent (valid PDF untouched). HTML becomes supplementary, not the substitute.
    - `--check` reports the rendered-recap artifact satisfied only when a valid `.pdf` exists (reuse `verify_rendered_pdf`/`extract_pdf_text`).
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.5, 5.2, 5.3, 5.4_
  - [x] 4.2 Extend orchestrator tests
    - fpdf2 unavailable + autoinstall disabled → orchestrator yields a valid PDF; `--check` unsatisfied with only HTML, satisfied with valid PDF; idempotency.
    - _Requirements: 7.2, 7.4_

- [x] 5. Update messaging and steering
  - [x] 5.1 Update `scripts/fpdf2_preflight.py`
    - Reflect the guaranteed-PDF behavior (autoinstall may run; stdlib fallback otherwise).
    - _Requirements: 5.5_
  - [x] 5.2 Update graduation steering
    - In `steering/graduation.md` and `steering/module-completion-track.md`, replace "degrades to HTML/Markdown when fpdf2 absent" with the guaranteed-PDF tiered behavior; preserve reconcile-then-render ordering and the non-blocking posture.
    - _Requirements: 5.4, 5.5, 6.3_

- [x] 6. Align existing tests
  - Update `test_generate_recap_pdf.py`, `test_generate_recap_pdf_inline*`, and any `ensure_graduation_artifacts` / preflight test that asserts HTML fallback satisfies the guarantee → expect a guaranteed PDF; keep Tier 1 unchanged when fpdf2 present.
  - _Requirements: 7.3, 7.5_

- [x] 7. Checkpoint - Verify
  - Uninstall/simulate-absent `fpdf2`, disable autoinstall, run `ensure_graduation_artifacts.py` → confirm a valid `docs/bootcamp_recap.pdf` via `extract_pdf_text`.
  - Run `HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/` and full `python -m pytest senzing-bootcamp/tests/ tests/`; confirm green.
  - Run `validate_commonmark.py` on edited Markdown.
  - _Requirements: 1.1, 7.5_

## Notes

- `fpdf2` stays optional and lazily imported (python-conventions); the guarantee rests on the stdlib writer, not on installing anything.
- Autoinstall is a best-effort enhancement (Tier 3 → Tier 1) with an opt-out for locked-down environments; it never blocks graduation.
- Professional design of the rich PDF is owned by `professional-recap-pdf`; this spec adds the guarantee and a plainer-but-valid fallback.
- Tests never perform real network installs — autoinstall is always mocked.
