# Requirements Document

## Introduction

The bootcamp graduation recap PDF (`docs/bootcamp_recap.pdf`) is the bootcamper's "trophy" — a keepsake to keep and share with their team. Today, even when the professional fpdf2 renderer runs, the output reads as a basic fpdf2 layout rather than a genuinely designed document, and there is no automated loop that verifies or improves the PDF's *visual* quality (unlike the D3 entity-graph visualization, which has an image-review loop that renders, inspects, and refines). Separately, the graduation-time Markdown normalization pass routes free-form recap lines into a generic `## Unmapped Content` catch-all, which then leaks into the shareable trophy.

This feature focuses on three things:

1. Upgrade the fpdf2 "rich" renderer to a single, standardized, professionally designed template (cover page, consistent typography, section styling, spacing, branding) so every generated PDF is a guaranteed polished production rather than a variable per-run layout.
2. Add a visual review-and-refine loop to recap PDF generation (render → inspect → improve layout), mirroring the visualization guide's image-review loop.
3. Keep the `## Unmapped Content` catch-all out of the shareable PDF (or fold its lines into the correct sections) so normalization artifacts never surface in the trophy.

Scope boundaries: The recap Markdown (`docs/bootcamp_recap.md`) remains the source of truth; the PDF is the polished shareable rendering. Q&A data-loss durability (missing captured questions/responses) is out of scope here — it is covered by the separate `durable-qa-capture` spec. This spec addresses PDF look-and-feel, the visual review loop, and keeping normalization artifacts out of the PDF.

## Glossary

- **Recap_PDF**: The generated `docs/bootcamp_recap.pdf`, the shareable "trophy" rendering.
- **Recap_Markdown**: The source file `docs/bootcamp_recap.md`, the authoritative source of recap content.
- **Generator**: The `senzing-bootcamp/scripts/generate_recap_pdf.py` script that parses the Recap_Markdown and renders the Recap_PDF.
- **Rich_Renderer**: The fpdf2-based renderer (`generate_recap_pdf.render_pdf` plus the primitives in `recap_pdf_render.py`) used at Tier 1 of the Tier_Strategy when fpdf2 is importable.
- **Shared_Renderer_Module**: The `senzing-bootcamp/scripts/recap_pdf_render.py` module providing the canonical Markdown-to-PDF rendering primitives and layout constants.
- **Tier_Strategy**: The `senzing-bootcamp/scripts/pdf_render_strategy.py` module (`ensure_recap_pdf`) that guarantees a valid PDF via Tier 1 (Rich_Renderer), Tier 2 (best-effort fpdf2 autoinstall), or Tier 3 (Stdlib_Writer).
- **Stdlib_Writer**: The `senzing-bootcamp/scripts/recap_pdf_minimal.py` stdlib-only Tier 3 fallback writer.
- **Designed_Template**: The single, standardized, professionally designed layout the Rich_Renderer applies to every Recap_PDF: cover page, defined Color_Palette, defined typography scale, section styling, spacing, and page footers.
- **Color_Palette**: The fixed set of colors used throughout the Designed_Template: primary blue `(31,78,121)` for the cover banner, accent blue `(0,90,156)` for headings, and body ink `(40,40,40)` for body text.
- **Typography_Scale**: The fixed set of font sizes used by the Designed_Template: title 32pt, subtitle 16pt, bootcamper name 20pt, module heading 18pt, subsection heading 14pt, body 11pt, code 10pt, footer 9pt.
- **Cover_Page**: The first page of the Recap_PDF, carrying the banner, title, subtitle, bootcamper name, optional metadata fields, and module-count headline.
- **Content_Page**: Any page after the Cover_Page carrying per-module recap content.
- **Module_Section**: A `## Module N: <name>` section in the Recap_Markdown, rendered as one or more Content_Pages.
- **Recap_Review_Loop**: The steering-driven render → inspect → refine loop, executed at recap PDF generation, that renders the Recap_PDF, inspects it against the Visual_Quality_Checklist, and refines the layout until the checklist passes or the iteration bound is reached.
- **Page_Image**: A rendered raster image of a single Recap_PDF page, produced for visual inspection during the Recap_Review_Loop.
- **Visual_Quality_Checklist**: The fixed set of pass/fail visual criteria the Recap_Review_Loop evaluates against each Page_Image.
- **Normalization_Pass**: The `senzing-bootcamp/scripts/normalize_markdown.py` graduation-time pass that rewrites the Recap_Markdown toward the recap Consumer_Schema.
- **Unmapped_Content_Section**: The `## Unmapped Content` section (and its accompanying HTML-comment marker) the Normalization_Pass appends for recap lines it cannot map to a recognized subsection.
- **Bootcamper**: The developer completing the bootcamp who receives the Recap_PDF.

## Requirements

### Requirement 1: Single Standardized Professional Template

**User Story:** As a bootcamper, I want the recap PDF to use one professionally designed template, so that my trophy always looks polished and consistent rather than varying from run to run.

#### Acceptance Criteria

1. WHEN the Rich_Renderer renders the Recap_PDF, THE Rich_Renderer SHALL apply the Designed_Template as the single template with no alternate template selection.
2. THE Rich_Renderer SHALL apply the Color_Palette to every rendered Recap_PDF.
3. THE Rich_Renderer SHALL apply the Typography_Scale to every rendered Recap_PDF.
4. WHEN the Rich_Renderer renders the same Recap_Markdown input twice with the same Rich_Renderer version and the same rendering configuration, THE Rich_Renderer SHALL produce Recap_PDF content that is byte-for-byte identical.
5. THE Rich_Renderer SHALL apply 20-millimeter margins on all four sides of every page.
6. THE Rich_Renderer SHALL render each Module_Section beginning at the top of a new page such that no two Module_Sections share a page.

### Requirement 2: Professional Cover Page

**User Story:** As a bootcamper, I want a designed cover page, so that the first impression of my trophy is polished and identifies the document.

#### Acceptance Criteria

1. THE Cover_Page SHALL render a full-width banner in primary blue `(31,78,121)` anchored at the top edge of the page.
2. THE Cover_Page SHALL render the title "Senzing Bootcamp Recap" in accent blue `(0,90,156)` at 32-point bold, positioned below the banner.
3. THE Cover_Page SHALL render the subtitle "Bootcamp Completion Recap" at 16-point positioned below the title.
4. WHERE the Recap_Markdown provides a non-empty bootcamper name, THE Cover_Page SHALL render the bootcamper name at 20-point centered below the subtitle.
5. IF the Recap_Markdown provides an empty or absent bootcamper name, THEN THE Cover_Page SHALL omit the bootcamper name line and render the next present field in its position.
6. WHERE the Recap_Markdown provides a non-empty Started value, THE Cover_Page SHALL render "Started: {value}" centered below the bootcamper name.
7. WHERE the Recap_Markdown provides a non-empty Total Duration value, THE Cover_Page SHALL render "Total Duration: {value}" centered below the Started value.
8. THE Cover_Page SHALL render a headline line stating the count of Module_Sections present in the Recap_Markdown, rendering a count of 0 when no Module_Sections are present.
9. IF rendering an individual optional Cover_Page metadata field (bootcamper name, Started value, or Total Duration value) raises an error, THEN THE Rich_Renderer SHALL skip that field, continue rendering the remaining Cover_Page content, and produce no error output that halts Cover_Page rendering.
10. THE Rich_Renderer SHALL suppress the page footer on the Cover_Page.

### Requirement 3: Consistent Typography and Section Styling

**User Story:** As a bootcamper, I want consistent headings, spacing, and page numbering, so that the document is easy to read and navigate.

#### Acceptance Criteria

1. WHEN the Shared_Renderer_Module renders a module heading, THE Shared_Renderer_Module SHALL render it in accent blue `(0,90,156)` at 18-point bold.
2. WHEN the Shared_Renderer_Module renders a subsection heading, THE Shared_Renderer_Module SHALL render it in accent blue `(0,90,156)` at 14-point bold.
3. THE Shared_Renderer_Module SHALL render body text in body ink `(40,40,40)` at 11-point.
4. THE Shared_Renderer_Module SHALL render code blocks and inline code spans in a monospace font at 10-point.
5. WHEN the Shared_Renderer_Module renders a Content_Page, THE Shared_Renderer_Module SHALL render a centered footer displaying "Page" followed by the page's sequential number at 9-point, where the number starts at 1 for the first Content_Page and increments by 1 for each subsequent Content_Page.
6. THE Shared_Renderer_Module SHALL render body text so that no line extends beyond the 20-millimeter page margins.
7. THE Shared_Renderer_Module SHALL render list items and question/response pairs with indentation that increases by 5 millimeters for each additional nesting level, up to a maximum of 5 nesting levels.
8. IF a code block or inline code span line's rendered width would extend beyond the 20-millimeter page margins, THEN THE Shared_Renderer_Module SHALL wrap the line so that no character extends beyond the margins.

### Requirement 4: Visual Review-and-Refine Loop

**User Story:** As a bootcamper, I want the system to inspect the generated PDF and improve its layout, so that visual defects are caught and fixed before I receive the trophy, just like the entity-graph visualization loop.

#### Acceptance Criteria

1. WHEN the Recap_PDF is generated during graduation, THE Recap_Review_Loop SHALL render each page of the Recap_PDF to a corresponding Page_Image.
2. WHEN Page_Images are available, THE Recap_Review_Loop SHALL evaluate each Page_Image against every item of the Visual_Quality_Checklist and record a pass or fail result per checklist item per page.
3. WHILE at least one Visual_Quality_Checklist item fails AND the iteration count is below the maximum of 3, THE Recap_Review_Loop SHALL adjust the layout inputs and regenerate the Recap_PDF, incrementing the iteration count by 1.
4. WHEN every Visual_Quality_Checklist item passes on all Page_Images, THE Recap_Review_Loop SHALL stop and retain the current Recap_PDF as the final trophy.
5. IF the iteration count reaches the maximum of 3 while one or more Visual_Quality_Checklist items still fail, THEN THE Recap_Review_Loop SHALL retain the best Recap_PDF, defined as the iteration whose Recap_PDF has the fewest failing Visual_Quality_Checklist items with ties resolved in favor of the earliest such iteration, and report to the bootcamper each remaining failing item together with the page on which it failed.
6. WHEN the Recap_Review_Loop adjusts layout inputs between iterations, THE Recap_Review_Loop SHALL preserve the Color_Palette and Typography_Scale of the Designed_Template.
7. IF a page-image rendering capability is not available in the environment, THEN THE Recap_Review_Loop SHALL fall back to the text-and-structure verification of the Generator, retain the generated Recap_PDF, and report to the bootcamper that visual inspection was skipped.

### Requirement 5: Visual Quality Criteria

**User Story:** As a bootcamper, I want the review loop to check for concrete layout problems, so that "professional" is verified against specific criteria rather than left to chance.

#### Acceptance Criteria

1. THE Visual_Quality_Checklist SHALL include a pass/fail criterion that no rendered text on any page extends beyond the defined top, bottom, left, or right page margins.
2. THE Visual_Quality_Checklist SHALL include a pass/fail criterion that no Content_Page is blank, where blank means the page contains no rendered text and no rendered visual elements.
3. THE Visual_Quality_Checklist SHALL include a pass/fail criterion that the Cover_Page renders all three of the title, subtitle, and module-count headline.
4. THE Visual_Quality_Checklist SHALL include a pass/fail criterion that each Module_Section begins at the top of a new page.
5. THE Visual_Quality_Checklist SHALL include a pass/fail criterion that no rendered page displays the Unmapped_Content_Section heading or its marker text.
6. THE Visual_Quality_Checklist SHALL include a pass/fail criterion that every module heading and subsection heading renders in the accent-blue heading color defined by the Color_Palette.

### Requirement 6: Exclude Normalization Artifacts From the Shareable PDF

**User Story:** As a bootcamper, I want normalization artifacts kept out of my trophy, so that a generic "Unmapped Content" dump never appears in the shareable document.

#### Acceptance Criteria

1. WHEN the Generator renders the Recap_PDF, THE Generator SHALL exclude the Unmapped_Content_Section heading from the rendered output.
2. WHEN the Generator renders the Recap_PDF, THE Generator SHALL exclude the Unmapped_Content_Section marker comment from the rendered output.
3. WHERE a free-form Recap_Markdown line maps to a recognized Required_Subsection, THE Normalization_Pass SHALL route that line into the recognized subsection rather than into the Unmapped_Content_Section.
4. WHEN the Normalization_Pass appends an Unmapped_Content_Section containing one or more unmapped lines to the Recap_Markdown, THE Normalization_Pass SHALL emit a warning to stderr stating the exact integer count of unmapped lines.
5. IF the Normalization_Pass detects zero unmapped lines, THEN THE Normalization_Pass SHALL NOT append an Unmapped_Content_Section to the Recap_Markdown and SHALL NOT emit an unmapped-line warning.
6. THE rendered Recap_PDF SHALL contain zero occurrences, under case-insensitive matching, of the text "Unmapped Content".

### Requirement 7: Optional Dependency and Graceful Degradation

**User Story:** As a bootcamper, I want the recap generation to behave predictably whether or not the optional PDF library is present, so that I never lose my recap content.

#### Acceptance Criteria

1. THE Generator SHALL import fpdf2 only within rendering functions at call time and SHALL NOT reference or import fpdf2 at module top level.
2. WHEN fpdf2 is importable, THE Tier_Strategy SHALL render the Recap_PDF with the Rich_Renderer and its Designed_Template, producing a Recap_PDF that is a non-empty file openable by a standard PDF reader and containing every recap content section present in the Recap_Markdown.
3. IF fpdf2 is absent and autoinstall is disabled or fails, THEN THE Tier_Strategy SHALL render a Recap_PDF with the Stdlib_Writer that is a non-empty file openable by a standard PDF reader and containing every recap content section present in the Recap_Markdown.
4. WHEN fpdf2 is absent, THE Generator SHALL leave the Recap_Markdown byte-for-byte identical to its pre-generation state and available at `docs/bootcamp_recap.md`.
5. IF the Rich_Renderer raises an error during rendering, THEN THE Tier_Strategy SHALL discard any partial Rich_Renderer output, render the Recap_PDF with the Stdlib_Writer, and complete graduation without aborting.
6. IF both the Rich_Renderer and the Stdlib_Writer fail to produce a Recap_PDF, THEN THE Generator SHALL leave the Recap_Markdown byte-for-byte identical to its pre-generation state, complete graduation, and return an indication that Recap_PDF generation failed while the Recap_Markdown was preserved.

### Requirement 8: Distribution and Source-of-Truth Integrity

**User Story:** As a power author, I want all changes to ship cleanly to users with the Markdown recap as the source of truth, so that the distributed power stays consistent and free of dev-only artifacts.

#### Acceptance Criteria

1. THE feature SHALL derive all Recap_PDF content from the Recap_Markdown, such that no recap content appears in the Recap_PDF that is not present in the Recap_Markdown.
2. WHEN the Generator renders the Recap_PDF, THE Generator SHALL leave the Recap_Markdown file byte-for-byte identical to its state immediately before rendering.
3. THE feature SHALL place all runtime files required for recap generation under the `senzing-bootcamp/` directory.
4. THE feature SHALL exclude from the distributed power all dev-only files and all test fixtures that contain non-synthetic (real) data.
5. THE Recap_Review_Loop steering SHALL reside as a Markdown file with a `.md` extension under `senzing-bootcamp/steering/`.
6. THE feature SHALL restrict runtime third-party imports to fpdf2 and SHALL otherwise import only modules from the Python standard library.
7. THE Generator SHALL NOT import fpdf2 at module top level, importing it only at the point where Recap_PDF generation is invoked.
8. IF fpdf2 is unavailable when Recap_PDF generation is invoked, THEN THE Generator SHALL retain the Recap_Markdown output, produce no Recap_PDF, and return an indication that PDF generation was skipped due to the missing optional dependency.
