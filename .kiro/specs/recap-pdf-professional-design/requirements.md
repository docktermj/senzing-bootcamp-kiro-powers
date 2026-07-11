# Requirements Document

## Introduction

The graduation-generated recap PDF (`docs/bootcamp_recap.pdf`) is the bootcamp's capstone
"trophy" — the single most distributable deliverable a bootcamper shares with colleagues and
leadership. Two High-priority feedback items (both 2026-07-10) report that this deliverable falls
short on two independent axes:

1. **Unprofessional appearance (UX).** The bundled `generate_recap_pdf.py` renderer produces a
   plain, poorly laid-out document that undercuts the sense of accomplishment and is not something
   a bootcamper would circulate.
2. **Content must not be condensed (Content).** When the recap PDF is restyled for a more
   professional look, the per-module detail sections — Information Shared, Questions & Responses,
   and Actions Taken — must NOT be reduced to short "highlights." These three sections are the
   essential substance of the document and must appear in full for every module.

This feature makes the recap PDF distribution-ready by default while guaranteeing that visual polish
wraps around the full per-module detail rather than replacing it. It covers a professional cover
page, a consistent typographic and heading hierarchy, generous margins and spacing, color accents,
page footers with page numbers, clean rendering of lists, code, and tables, and a visual
create/review loop in the graduation flow so quality is verified rather than assumed.

### Relationship to existing specs

This work builds on and extends prior recap-PDF specs; it does not duplicate them:

- **`recap-pdf-content-loss-fix`** delivered the tolerant module-heading parser and the
  raw-Markdown fallback so no recap content is ever silently dropped. The professional redesign
  MUST preserve that tolerant parsing and fallback behavior — the visual layer is added on top of
  it, not in place of it.
- **`recap-completeness-and-pdf`** delivered full-width cell rendering (no wrapping failures),
  the no-swallowed-exception rule, and round-trip PDF verification before reporting success. The
  full-content-preservation guarantee in this feature is enforced through that same round-trip
  verification and atomic publish.
- **`recap-qr-formatting`** delivered the Paired_Schema `### Questions & Responses` section with
  responses nested beneath their questions, plus backward compatibility with the legacy
  split-list schema. The redesign preserves both schemas.
- **`shared-markdown-renderer-refactor`** established the canonical rendering primitives in
  `senzing-bootcamp/scripts/recap_pdf_render.py`. New visual primitives introduced here belong in
  that shared module.
- **`graduation-recap-pdf-resilience`** established the inline fallback and the Non_Blocking
  graduation contract. The visual review loop added here keeps graduation Non_Blocking.

### Constraints

- Python 3.11+, standard library only, except `fpdf2` (`import fpdf`), which remains an OPTIONAL,
  lazily-imported dependency used only by `generate_recap_pdf.py` and
  `generate_completion_summary.py`. It MUST NOT be imported at module top level, and the renderer
  MUST degrade gracefully (keep the Markdown recap, print a `pip install fpdf2` hint) when it is
  absent.
- The renderer to improve is `senzing-bootcamp/scripts/generate_recap_pdf.py` together with the
  shared `senzing-bootcamp/scripts/recap_pdf_render.py`. The source content is
  `docs/bootcamp_recap.md`. The graduation flow is `senzing-bootcamp/steering/graduation.md`.
- Everything under `senzing-bootcamp/` ships to users as a distributed Kiro Power: no dev-only
  files, no PII, and no real data in test fixtures.
- Tests use pytest + Hypothesis and live in `senzing-bootcamp/tests/test_generate_recap_pdf.py`.

## Glossary

- **Recap_Markdown**: The bootcamp recap source document `docs/bootcamp_recap.md`, kept current
  per module.
- **Recap_PDF**: The shareable PDF artifact `docs/bootcamp_recap.pdf` rendered from Recap_Markdown.
- **Recap_Renderer**: The bundled renderer `senzing-bootcamp/scripts/generate_recap_pdf.py`
  together with the shared `senzing-bootcamp/scripts/recap_pdf_render.py`, which converts
  Recap_Markdown into Recap_PDF.
- **Cover_Page**: The first page of the Recap_PDF, carrying document identity and summary figures.
- **Content_Page**: Any page of the Recap_PDF after the Cover_Page that renders module content.
- **Required_Detail_Sections**: The three per-module sections that must always render in full for
  every module — Information Shared, Questions & Responses (including content authored in the
  legacy Questions Asked / Answers Given split-list schema), and Actions Taken.
- **Headline_Stats**: The summary figures shown on the Cover_Page — the number of completed module
  sections, the total duration, and the start date.
- **Heading_Hierarchy**: The ordered set of heading levels (module-level and subsection-level),
  each rendered with an assigned, distinct font size.
- **Page_Footer**: The footer region rendered on each Content_Page that displays the page number.
- **Accent_Color**: A defined, non-black color applied to headings to visually distinguish them
  from body text.
- **Content_Verification**: The round-trip check (`verify_rendered_pdf` in `recap_pdf_render.py`)
  that re-extracts text from the written Recap_PDF and asserts expected per-module content is
  present before the artifact is published.
- **Visual_Review_Loop**: The graduation-flow create/review cycle that verifies the Recap_PDF's
  content completeness and layout quality before reporting the Recap_PDF as distribution-ready.
- **Graduation_Flow**: The workflow in `senzing-bootcamp/steering/graduation.md`; its Step 0b
  generates the Recap_PDF.
- **Tolerant_Parser**: The recap parser (delivered by `recap-pdf-content-loss-fix`) that recognizes
  module headings with or without the `— <timestamp>` suffix and falls back to raw-Markdown
  rendering when no module sections parse.
- **fpdf2**: The optional third-party dependency (`import fpdf`), imported lazily inside the
  rendering function, used to construct the Recap_PDF.
- **Non_Blocking**: A step whose failure logs a warning and allows graduation to continue,
  consistent with the always-generated `GRADUATION_REPORT.md`.

## Requirements

### Requirement 1: Distribution-ready output by default

**User Story:** As a bootcamper, I want the recap PDF to look distribution-ready without any extra
flags or steps, so that the artifact I share reflects well on me and on Senzing.

#### Acceptance Criteria

1. WHEN the Recap_Renderer renders the Recap_PDF from a Recap_Markdown that has parseable module
   sections, THE Recap_Renderer SHALL apply the professional layout defined in Requirements 2
   through 7 without requiring any additional command-line flag.
2. THE Recap_Renderer SHALL accept the `--input` flag with default `docs/bootcamp_recap.md` and the
   `--output` flag with default `docs/bootcamp_recap.pdf`.
3. WHEN no module sections parse from a non-empty Recap_Markdown, THE Recap_Renderer SHALL render
   the raw Markdown body via the Tolerant_Parser fallback so that no recap content is dropped.
4. WHEN the Recap_Renderer writes the Recap_PDF, THE Recap_Renderer SHALL print the line
   `PDF generated: <output_path>` to standard output and return exit code 0.

### Requirement 2: Professional cover page

**User Story:** As a bootcamper, I want a proper cover page identifying the recap and summarizing my
achievement, so that the first impression of the document is polished.

#### Acceptance Criteria

1. THE Recap_Renderer SHALL render a Cover_Page as the first page of the Recap_PDF.
2. THE Recap_Renderer SHALL render the document title `Senzing Bootcamp Recap` on the Cover_Page.
3. THE Recap_Renderer SHALL render a subtitle on the Cover_Page that identifies the document as a
   bootcamp completion recap.
4. THE Recap_Renderer SHALL render the bootcamper name from the Recap_Markdown header on the
   Cover_Page.
5. WHERE the Recap_Markdown header specifies a start date, THE Recap_Renderer SHALL render the start
   date on the Cover_Page.
6. WHERE the Recap_Markdown header specifies a total duration, THE Recap_Renderer SHALL render the
   total duration on the Cover_Page.
7. THE Recap_Renderer SHALL render the Headline_Stats on the Cover_Page, including the count of
   module sections present in the Recap_Markdown.
8. IF rendering the start date or total duration on the Cover_Page fails, THEN THE Recap_Renderer
   SHALL continue rendering the remainder of the Cover_Page without that field rather than aborting
   the Recap_PDF.

### Requirement 3: Consistent typography and heading hierarchy

**User Story:** As a reader of the recap, I want a consistent visual hierarchy, so that I can
distinguish module titles, subsection headings, and body text at a glance.

#### Acceptance Criteria

1. THE Recap_Renderer SHALL render every module-level heading using one font size and render every
   subsection-level heading using one font size, so that all headings at the same level share the
   same font size.
2. THE Recap_Renderer SHALL render module-level headings at a font size strictly greater than the
   subsection-level heading font size.
3. THE Recap_Renderer SHALL render subsection-level headings at a font size strictly greater than
   the body-text font size.
4. THE Recap_Renderer SHALL render body text throughout the Content_Pages using a single font
   family.
5. THE Recap_Renderer SHALL render inline code spans and fenced code blocks in a monospace font
   distinct from the body-text font.

### Requirement 4: Margins, spacing, and page footers

**User Story:** As a bootcamper sharing the recap, I want generous margins and page numbers, so that
the document reads cleanly and looks professionally paginated.

#### Acceptance Criteria

1. THE Recap_Renderer SHALL render every Content_Page with top, bottom, left, and right margins of
   at least 15 millimetres.
2. THE Recap_Renderer SHALL insert vertical spacing of at least 2 millimetres between each heading
   and the content that follows it.
3. THE Recap_Renderer SHALL render a Page_Footer on every Content_Page that displays the page
   number.
4. WHEN rendered content reaches the bottom margin of a Content_Page, THE Recap_Renderer SHALL
   continue the content on a new page rather than overprinting the Page_Footer.

### Requirement 5: Color accents

**User Story:** As a reader, I want tasteful color accents on headings, so that the document looks
designed rather than plain.

#### Acceptance Criteria

1. THE Recap_Renderer SHALL render module-level and subsection-level headings in the Accent_Color.
2. THE Recap_Renderer SHALL render body text in a color distinct from the Accent_Color.
3. THE Recap_Renderer SHALL apply the same Accent_Color to every heading of the same level across
   all Content_Pages.

### Requirement 6: Clean rendering of lists, code, and tables

**User Story:** As a reader, I want lists, code, and tables to render cleanly, so that the recap's
content is legible and correctly structured.

#### Acceptance Criteria

1. WHEN the Recap_Renderer renders a bulleted or numbered list, THE Recap_Renderer SHALL render each
   list item on its own line with a consistent leading marker.
2. WHEN a list item's text is wider than the available line width, THE Recap_Renderer SHALL wrap the
   text within the page margins rather than truncating or dropping the text.
3. WHEN the Recap_Renderer renders a fenced code block, THE Recap_Renderer SHALL render the code
   content in a monospace font with the fence delimiter lines removed.
4. WHERE a module's content contains a Markdown pipe table, THE Recap_Renderer SHALL render every
   cell's text from that table, omitting no cell.

### Requirement 7: Nested Questions & Responses rendering preserved

**User Story:** As a reader, I want each response nested beneath its question, so that the
question-and-answer hierarchy is obvious in the professionally styled PDF.

#### Acceptance Criteria

1. WHEN the Recap_Renderer renders a module authored in the Paired_Schema, THE Recap_Renderer SHALL
   render the Questions & Responses content under a single heading labeled `Questions & Responses`.
2. WHEN the Recap_Renderer renders a paired question and response, THE Recap_Renderer SHALL render
   the response at a greater horizontal start position than its question.
3. WHERE a module section is authored in the legacy split-list schema (`Questions Asked` and
   `Answers Given`), THE Recap_Renderer SHALL render each question and each answer, pairing answer
   N with question N and rendering a placeholder for any unmatched counterpart.

### Requirement 8: Mandatory full-content per-module detail sections

**User Story:** As a bootcamper, I want every module's Information Shared, Questions & Responses, and
Actions Taken rendered in full, so that the recap preserves the substance of what I learned, decided,
and did.

#### Acceptance Criteria

1. WHEN the Recap_Renderer renders a module section that is present in the Recap_Markdown, THE
   Recap_Renderer SHALL render all three Required_Detail_Sections for that module.
2. WHEN the Recap_Renderer renders a Required_Detail_Section for a module, THE Recap_Renderer SHALL
   render a number of items equal to the number of items present in that section of the
   Recap_Markdown.
3. WHEN the Recap_Renderer renders an item of a Required_Detail_Section, THE Recap_Renderer SHALL
   reproduce the item text character-for-character as it appears in the Recap_Markdown, excluding
   Markdown list markers and the `- **Q:**` / `- **R:**` prefixes.
4. WHERE a Required_Detail_Section in the Recap_Markdown contains no items, THE Recap_Renderer SHALL
   render the section heading followed by an explicit empty indicator rather than omitting the
   section.
5. THE Recap_Renderer SHALL render each Required_Detail_Section's items at their full text length,
   applying no summarization, truncation, or reduction of the item count.

### Requirement 9: Content verification gates publication

**User Story:** As a bootcamper, I want the recap PDF to be published only when its full content
survived rendering, so that a restyled PDF can never silently drop my detail sections.

#### Acceptance Criteria

1. WHEN the Recap_Renderer finishes writing a candidate Recap_PDF, THE Recap_Renderer SHALL run
   Content_Verification against the candidate before publishing it to the output path.
2. IF Content_Verification finds that the candidate Recap_PDF omits any completed module's
   per-module section, THEN THE Recap_Renderer SHALL NOT publish the candidate as the Recap_PDF and
   SHALL return exit code 1.
3. IF Content_Verification finds that expected Required_Detail_Section content did not survive into
   the candidate Recap_PDF, THEN THE Recap_Renderer SHALL NOT publish the candidate as the
   Recap_PDF and SHALL produce an error identifying the omitted content.
4. WHEN Content_Verification fails, THE Recap_Renderer SHALL leave any previously existing Recap_PDF
   at the output path unchanged.
5. WHEN the Recap_Renderer returns exit code 1, THE Recap_Renderer SHALL NOT print the
   `PDF generated:` line.
6. WHEN Content_Verification passes, THE Recap_Renderer SHALL publish the verified candidate to the
   output path, replacing any existing Recap_PDF at that path.

### Requirement 10: Visual create/review loop in graduation

**User Story:** As a bootcamper graduating, I want the graduation flow to verify recap quality rather
than assume it, so that the delivered trophy is confirmed complete and well-formed.

#### Acceptance Criteria

1. WHEN the Graduation_Flow generates the Recap_PDF at Step 0b, THE Graduation_Flow SHALL confirm,
   through Content_Verification, that the Recap_PDF contains each completed module's three
   Required_Detail_Sections before reporting the Recap_PDF as generated.
2. WHERE tooling to render PDF pages to images is available, THE Visual_Review_Loop SHALL render the
   Recap_PDF pages to images and inspect them to confirm the layout renders the three
   Required_Detail_Sections for each module.
3. IF the Visual_Review_Loop determines that a Required_Detail_Section is missing or condensed, THEN
   THE Graduation_Flow SHALL treat the Recap_PDF as not distribution-ready and SHALL NOT report it
   as successfully generated.
4. THE Visual_Review_Loop SHALL remain Non_Blocking: any failure SHALL log a warning, point the
   bootcamper to the existing Recap_Markdown at `docs/bootcamp_recap.md`, and allow graduation to
   continue.
5. THE Graduation_Flow SHALL NOT report the Recap_PDF as generated when no Recap_PDF was written.

### Requirement 11: Preserved graceful degradation and non-blocking behavior

**User Story:** As a bootcamper without `fpdf2` installed, I want graduation to continue with my
Markdown recap intact, so that a missing optional dependency never costs me the bootcamp record.

#### Acceptance Criteria

1. THE Recap_Renderer SHALL import `fpdf` only inside the rendering function body and SHALL NOT
   import `fpdf` at module top level.
2. IF `fpdf2` is not installed WHEN the Recap_Renderer attempts to render the Recap_PDF, THEN THE
   Recap_Renderer SHALL print the `pip install fpdf2` hint to standard error and return exit code 1
   without printing a traceback.
3. WHEN the Recap_PDF cannot be generated for any reason, THE Graduation_Flow SHALL point the
   bootcamper to the existing Recap_Markdown at `docs/bootcamp_recap.md`.
4. IF the input recap file is missing or empty, THEN THE Recap_Renderer SHALL print the existing
   error message to standard error and return exit code 1.

### Requirement 12: Test coverage

**User Story:** As a maintainer, I want the professional redesign and the full-content guarantee
covered by tests, so that neither the visual layout nor the content preservation regresses.

#### Acceptance Criteria

1. THE feature SHALL include a test asserting that, for a representative multi-module Recap_Markdown,
   the rendered Recap_PDF contains each module's Information Shared, Questions & Responses, and
   Actions Taken content.
2. THE feature SHALL include a property-based test asserting that the count of rendered items in each
   Required_Detail_Section equals the count of items present in the Recap_Markdown, so no item is
   condensed away.
3. THE feature SHALL include a test asserting that Content_Verification rejects a Recap_PDF that
   omits a Required_Detail_Section, causing exit code 1 with no `PDF generated:` line and no
   published Recap_PDF.
4. THE feature SHALL include a test asserting that the Cover_Page contains the title, bootcamper
   name, and Headline_Stats.
5. THE feature SHALL include a test asserting that when `fpdf2` is absent the Recap_Renderer degrades
   gracefully (no traceback) and surfaces the `pip install fpdf2` hint.
6. THE tests SHALL follow the project test pattern (pytest + Hypothesis, class-based, `sys.path`
   import pattern) and live in `senzing-bootcamp/tests/test_generate_recap_pdf.py`.
