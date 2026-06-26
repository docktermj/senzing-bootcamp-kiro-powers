# Requirements Document

## Introduction

The `senzing-bootcamp` power ships two recap-PDF generator scripts in
`senzing-bootcamp/scripts/`:

- `generate_recap_pdf.py` — the bundled helper that parses recap Markdown into a structured model
  and renders a PDF, with a raw-Markdown fallback path (`render_markdown_body`, backed by helpers
  such as `_split_into_blocks`, `_render_generic_blocks`, `_render_heading`, `_render_list_items`,
  and `_safe_text`).
- `generate_recap_pdf_inline.py` — a self-contained inline fallback that reuses the bundled
  renderer when importable, and otherwise renders the raw Markdown body with its OWN embedded
  minimal renderer (`_render_inline_pdf`, plus helpers `_split_blocks` and `_safe_text`).

The embedded raw-Markdown rendering logic in the inline script (cover line, wrapped text, heading
blocks, fenced-code blocks, Latin-1-safe text, block splitting) duplicates the raw-Markdown
rendering concept that also lives in the bundled script's fallback path. As this area changes, the
duplication risks drift — the two renderers handling the same Markdown construct differently.

This feature is a **behavior-preserving refactor**. It factors the shared raw-Markdown → PDF
rendering logic into a single canonical shared helper module that both scripts import, eliminating
the duplication. The refactor MUST NOT change the externally observable behavior of either script:
the same CLI flags, the same `PDF generated:` stdout success contract, the same exit codes, the
same graceful degradation when `fpdf2` is absent (including the `pip install fpdf2` hint), the same
no-false-success rule, and the same non-empty PDF body containing recap content. The shared helper
must preserve lazy importing of `fpdf` (never importing it at module top level) and must not depend
on the structured parser/model, so the inline generator keeps its independence from the bundled
module.

## Glossary

- **Shared_Renderer_Module**: The new stdlib-only module (working name `recap_pdf_render.py`, in
  `senzing-bootcamp/scripts/`) that contains the single canonical raw-Markdown → PDF rendering
  logic imported by both generator scripts. Its exact name and public function signatures are an
  open design decision (see Open Design Decisions).
- **Shared_Renderer**: The canonical raw-Markdown → PDF rendering function(s) exported by the
  Shared_Renderer_Module, including block splitting, Latin-1-safe text handling, and rendering of
  cover line, headings, prose, and fenced-code blocks.
- **Bundled_Generator**: The script `senzing-bootcamp/scripts/generate_recap_pdf.py`.
- **Inline_Generator**: The script `senzing-bootcamp/scripts/generate_recap_pdf_inline.py`.
- **Structured_Module**: The structured recap parser/model exposed by the Bundled_Generator
  (`parse_recap_markdown`, `render_pdf`, the `Recap*` dataclasses).
- **Raw_Markdown_Body**: The unparsed recap Markdown text rendered when no structured module
  sections are available, so no recap content is dropped.
- **Success_Line**: The exact stdout line `PDF generated: <output_path>`, the only success signal a
  generator prints to stdout.
- **FPDF_Hint**: The user-facing message instructing installation of the optional dependency, of
  the form `pip install fpdf2`.
- **No_False_Success**: The rule that a generator prints the Success_Line and returns exit code 0
  only when a PDF file was actually written to the output path; every no-PDF outcome returns exit
  code 1 and prints no Success_Line.
- **Lazy_Import**: The pattern of importing `fpdf` only inside the rendering function body, never at
  module top level.
- **fpdf2**: The optional third-party dependency (`import fpdf`) used for PDF rendering.

## Requirements

### Requirement 1: Single canonical raw-Markdown renderer

**User Story:** As a power maintainer, I want one canonical raw-Markdown → PDF renderer, so that the
two generator scripts cannot drift apart in how they render Markdown.

#### Acceptance Criteria

1. THE Shared_Renderer_Module SHALL provide the raw-Markdown → PDF rendering logic — block
   splitting, Latin-1-safe text handling, and rendering of the cover line, headings, prose
   paragraphs, and fenced-code blocks — as the single canonical implementation.
2. THE Shared_Renderer_Module SHALL import only Python standard-library modules at module top
   level.
3. THE Shared_Renderer SHALL render a non-empty Raw_Markdown_Body into a PDF whose body contains
   the recap content.
4. WHERE recap content contains characters outside the Latin-1 range, THE Shared_Renderer SHALL
   replace those characters so rendering with PDF core fonts succeeds without raising an encoding
   error.
5. WHERE recap content contains a fenced-code block, THE Shared_Renderer SHALL render the code
   content with the fence delimiter lines removed.

### Requirement 2: Inline generator uses the shared renderer

**User Story:** As a power maintainer, I want the Inline_Generator to use the shared renderer
instead of its own embedded copy, so that the duplicated renderer is removed.

#### Acceptance Criteria

1. THE Inline_Generator SHALL render the Raw_Markdown_Body by calling the Shared_Renderer.
2. THE Inline_Generator SHALL NOT define a private embedded raw-Markdown renderer equivalent to the
   removed `_render_inline_pdf`, `_split_blocks`, and `_safe_text` helpers.
3. WHEN the Structured_Module is importable, THE Inline_Generator SHALL reuse the Structured_Module
   parser and renderer exactly as before this refactor.
4. WHEN the Structured_Module is not importable, THE Inline_Generator SHALL render the
   Raw_Markdown_Body by calling the Shared_Renderer.

### Requirement 3: Bundled generator and the shared renderer

**User Story:** As a power maintainer, I want the relationship between the Bundled_Generator and the
shared renderer to be explicit, so that there is one canonical raw-Markdown renderer rather than
two.

#### Acceptance Criteria

1. THE Bundled_Generator SHALL continue to render structured recap documents through its existing
   structured rendering path without behavioral change.
2. WHERE the Bundled_Generator's raw-Markdown fallback path is migrated onto the Shared_Renderer,
   THE Bundled_Generator SHALL produce a raw-Markdown fallback PDF whose body contains the recap
   content.
3. THE Shared_Renderer_Module SHALL NOT import the Structured_Module parser or model.

### Requirement 4: Preserved CLI and stdout contract

**User Story:** As a bootcamper running a recap generator, I want the command-line interface and
output messages to be unchanged, so that existing usage and automation keep working.

#### Acceptance Criteria

1. THE Inline_Generator SHALL accept the `--input` flag with default `docs/bootcamp_recap.md` and
   the `--output` flag with default `docs/bootcamp_recap.pdf`.
2. THE Bundled_Generator SHALL accept the `--input` flag with default `docs/bootcamp_recap.md` and
   the `--output` flag with default `docs/bootcamp_recap.pdf`.
3. WHEN a generator writes a PDF to the output path, THE generator SHALL print the Success_Line to
   stdout.
4. THE generator SHALL print the Success_Line to stdout only when a PDF file was written to the
   output path.

### Requirement 5: Preserved exit codes and no-false-success

**User Story:** As an automation author, I want exit codes and the no-false-success rule preserved,
so that scripts that check exit status continue to behave correctly.

#### Acceptance Criteria

1. WHEN a generator writes a PDF to the output path, THE generator SHALL return exit code 0.
2. IF the input file does not exist, THEN THE generator SHALL print an error to stderr and return
   exit code 1.
3. IF the input file is empty, THEN THE generator SHALL print an error to stderr and return exit
   code 1.
4. IF no PDF file is present at the output path after rendering, THEN THE generator SHALL print an
   error to stderr and return exit code 1.
5. WHEN a generator returns exit code 1, THE generator SHALL NOT print the Success_Line to stdout.

### Requirement 6: Preserved graceful degradation when fpdf2 is absent

**User Story:** As a bootcamper without `fpdf2` installed, I want the generators to degrade
gracefully with an install hint, so that I am told how to proceed instead of seeing a crash.

#### Acceptance Criteria

1. THE Shared_Renderer_Module SHALL import `fpdf` only inside the rendering function body and SHALL
   NOT import `fpdf` at module top level (Lazy_Import).
2. IF `fpdf2` is not installed WHEN a generator attempts to render a PDF, THEN THE generator SHALL
   print the FPDF_Hint to stderr and return exit code 1.
3. IF `fpdf2` is not installed WHEN a generator attempts to render a PDF, THEN THE generator SHALL
   return without printing a traceback to stderr.

### Requirement 7: Preserved inline-generator independence

**User Story:** As a power maintainer, I want the Inline_Generator to keep working when the
Structured_Module is unavailable, so that the graduation fallback remains self-contained.

#### Acceptance Criteria

1. WHILE the Structured_Module is not importable, THE Inline_Generator SHALL produce a PDF from a
   non-empty Raw_Markdown_Body by calling the Shared_Renderer.
2. THE Shared_Renderer_Module SHALL be importable without the Structured_Module being importable.
3. THE Inline_Generator SHALL return exit code 0 when it writes a PDF via the Shared_Renderer while
   the Structured_Module is not importable.

### Requirement 8: Test coverage for the shared renderer and both callers

**User Story:** As a power maintainer, I want the shared renderer directly tested and both callers
verified to use it, so that regressions and drift are caught.

#### Acceptance Criteria

1. THE test suite SHALL include a test that directly exercises the Shared_Renderer against a
   Raw_Markdown_Body and asserts a non-empty PDF body containing recap content.
2. THE test suite SHALL include a test verifying that the Inline_Generator renders the
   Raw_Markdown_Body via the Shared_Renderer when the Structured_Module is not importable.
3. THE existing tests in `senzing-bootcamp/tests/test_generate_recap_pdf.py` SHALL pass without
   modification to their asserted behavior.
4. THE existing tests in `senzing-bootcamp/tests/test_generate_recap_pdf_inline.py` SHALL pass,
   updated only where they referenced the removed embedded renderer helpers.
5. THE test suite SHALL verify that the Shared_Renderer_Module does not import `fpdf` at module top
   level.

## Open Design Decisions

These are genuine decisions to resolve during the design phase. They do not change the
behavior-preserving intent of the refactor.

1. **Shared_Renderer_Module name and location.** Proposed: a new small module
   `senzing-bootcamp/scripts/recap_pdf_render.py`. Alternatives: relocating the embedded renderer
   into another existing stdlib-only module, or a differently named module. The chosen module must
   be importable via the documented `sys.path` pattern and must not depend on the Structured_Module.
2. **Public function signatures of the Shared_Renderer.** Whether the canonical entry point is a
   single `render_markdown_pdf(body_text: str, output_path: str) -> None` function, or a small set
   of functions (block splitting, Latin-1-safe text, per-block rendering) mirroring the existing
   helpers. Includes deciding whether the cover line / title is a parameter or fixed.
3. **Whether the Bundled_Generator's existing raw-Markdown fallback is also migrated onto the
   Shared_Renderer.** Options: (a) migrate the Bundled_Generator's `render_markdown_body` and its
   helpers onto the Shared_Renderer so there is exactly one canonical renderer; (b) migrate only the
   Inline_Generator now and leave the Bundled_Generator's fallback in place. Option (a) most fully
   eliminates duplication; option (b) is lower risk. The cover-line vs. cover-page difference
   between the two current renderers must be reconciled if option (a) is chosen.
4. **Reconciling cosmetic differences between the two current raw renderers.** The Inline_Generator
   emits a single cover line while the Bundled_Generator's fallback renders after a full cover page,
   and the two use slightly different heading/list handling. The design must decide which presentation
   the canonical renderer adopts while keeping each script's observable "non-empty PDF body containing
   recap content" contract satisfied.
