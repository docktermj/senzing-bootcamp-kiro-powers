# Requirements Document

## Introduction

The bootcamp recap document (`docs/bootcamp_recap.md`) records each completed module's
interaction. Today, per-module questions and answers are written as two parallel sections —
`### Questions Asked` (a numbered list) and `### Answers Given` (a separate numbered list keyed
1:1 by number). Readers must cross-reference the two lists by number to reconstruct each
exchange, which becomes error-prone as the number of questions grows.

This feature changes the recap schema and the `module-recap-append` agentStop hook so that each
module records its exchanges in a single interspersed `### Questions & Responses` section, where
every question is immediately followed by its response. Each response is rendered as a nested
list item indented beneath its question so the question/response hierarchy is visually obvious.
The recap PDF renderer is updated to honor the leading indentation of Markdown list items so the
same nesting is visible in the generated PDF, keeping the Markdown recap and its PDF rendering
consistent.

Existing recaps written in the older split-list format must continue to render correctly, so the
renderer must remain backward compatible with both schemas.

## Glossary

- **Recap_Markdown**: The Markdown recap file at `docs/bootcamp_recap.md` that accumulates one
  section per completed module.
- **Recap_Append_Hook**: The `module-recap-append` agentStop hook
  (`senzing-bootcamp/hooks/module-recap-append.kiro.hook`) that appends a per-module recap
  section to Recap_Markdown when a module is completed.
- **Recap_PDF_Renderer**: The Python renderer under `senzing-bootcamp/scripts/`
  (`generate_recap_pdf.py` together with the shared `recap_pdf_render.py`) that converts
  Recap_Markdown into `docs/bootcamp_recap.pdf`.
- **QR_Section**: The single `### Questions & Responses` subsection that holds paired
  question/response entries for a module.
- **QR_Pair**: One question and its corresponding response within QR_Section.
- **Question_Item**: A top-level Markdown list item holding a question, prefixed `- **Q:**`.
- **Response_Item**: A Markdown list item holding the response to the immediately preceding
  Question_Item, prefixed `- **R:**` and indented four spaces beneath the Question_Item.
- **Indent_Depth**: The number of leading space characters on a Markdown list item line, used to
  determine nesting level when rendering.
- **Split_List_Schema**: The legacy recap format that records questions and answers as two
  parallel sections (`### Questions Asked` and `### Answers Given`) keyed 1:1 by number.
- **Paired_Schema**: The new recap format that records exchanges as a single QR_Section of
  interspersed QR_Pairs.

## Requirements

### Requirement 1: Paired Questions & Responses schema in the recap

**User Story:** As a bootcamper reading the recap, I want each question immediately followed by
its response, so that I can read each exchange without cross-referencing two separate lists.

#### Acceptance Criteria

1. WHEN the Recap_Append_Hook appends a module section that contains at least one substantive question (a question whose text contains at least one non-whitespace character after leading and trailing whitespace is removed), THE Recap_Append_Hook SHALL write exactly one QR_Section titled `### Questions & Responses` for that module.
2. WHEN the Recap_Append_Hook writes a QR_Section, THE Recap_Append_Hook SHALL emit each QR_Pair as a Question_Item immediately followed by its Response_Item, ordered by ascending sequence in which the questions were recorded during the module.
3. WHEN the Recap_Append_Hook writes a QR_Pair, THE Recap_Append_Hook SHALL prefix the question line with the literal text `- **Q:**` and prefix the response line with the literal text `- **R:**`.
4. WHEN the Recap_Append_Hook writes a module section, THE Recap_Append_Hook SHALL exclude any separate `### Questions Asked` section and any separate `### Answers Given` section for that module, regardless of the question count.
5. IF a module has zero substantive questions, THEN THE Recap_Append_Hook SHALL write the `### Questions & Responses` heading followed by exactly one Markdown list item consisting of the literal text `- None` and no QR_Pairs.
6. WHERE a question's recorded response is absent or contains only whitespace characters, THE Recap_Append_Hook SHALL write the Response_Item with the literal placeholder text `(no response recorded)` immediately following the `- **R:**` prefix.

### Requirement 2: Nested indentation of responses beneath questions

**User Story:** As a bootcamper scanning the recap, I want each response nested beneath its
question, so that the prompt-and-answer hierarchy is obvious at a glance.

#### Acceptance Criteria

1. WHEN the Recap_Append_Hook writes a Response_Item, THE Recap_Append_Hook SHALL prefix the Response_Item line with exactly four leading space characters (ASCII 0x20) and no tab characters, so it nests beneath its Question_Item at an Indent_Depth of 4.
2. WHEN the Recap_Append_Hook writes a Question_Item, THE Recap_Append_Hook SHALL write the Question_Item line with zero leading space characters and no leading tab characters, so its Indent_Depth is 0.
3. THE Recap_Append_Hook SHALL write each QR_Pair such that the Indent_Depth of the Response_Item is exactly 4 greater than the Indent_Depth of its Question_Item.
4. THE Recap_Append_Hook SHALL apply exactly four leading space characters (ASCII 0x20) per nesting level for every QR_Pair across all module sections, with no variation between QR_Pairs.
5. WHERE a Response_Item spans more than one line, THE Recap_Append_Hook SHALL prefix every continuation line of that Response_Item with at least four leading space characters (ASCII 0x20) so the continuation lines remain nested beneath the Question_Item.

### Requirement 3: PDF renderer honors indentation depth

**User Story:** As a bootcamper sharing the recap PDF, I want the response nesting to be visible
in the PDF, so that the PDF reads the same as the Markdown recap.

#### Acceptance Criteria

1. WHEN the Recap_PDF_Renderer renders a Markdown list item at nesting level N (where level 0 is an item with Indent_Depth 0), THE Recap_PDF_Renderer SHALL set the item's horizontal start position to the page's left margin plus N times a fixed, positive per-level offset that is identical for every level.
2. WHEN the Recap_PDF_Renderer renders a QR_Pair from the Paired_Schema, THE Recap_PDF_Renderer SHALL render the Response_Item at a greater horizontal start position than its Question_Item.
3. WHILE rendering items at nesting levels from 0 up to at least the maximum nesting level produced by the Paired_Schema, THE Recap_PDF_Renderer SHALL keep each rendered line within the page's left and right margins.
4. IF a list item's text would extend beyond the page's right margin, THEN THE Recap_PDF_Renderer SHALL wrap the text onto additional lines within the margins rather than dropping or truncating the text.
5. THE Recap_PDF_Renderer SHALL render the QR_Section under a single heading labeled `Questions & Responses`.

### Requirement 4: Consistency between Markdown recap and PDF rendering

**User Story:** As a bootcamper, I want the PDF to reflect the same questions and responses as the
Markdown recap, so that the two deliverables agree.

#### Acceptance Criteria

1. WHEN the Recap_PDF_Renderer renders a module's QR_Section, THE Recap_PDF_Renderer SHALL render a number of QR_Pairs equal to the number of QR_Pairs present in that module's Recap_Markdown, omitting no QR_Pair and duplicating no QR_Pair.
2. IF the Recap_PDF_Renderer cannot render a QR_Pair that is present in Recap_Markdown, THEN THE Recap_PDF_Renderer SHALL terminate with a non-zero exit code, SHALL NOT write a recap PDF, and SHALL produce an error indication identifying the QR_Pair that could not be rendered.
3. WHEN the Recap_PDF_Renderer renders a QR_Pair, THE Recap_PDF_Renderer SHALL reproduce the question text and the response text character-for-character as they appear in Recap_Markdown, excluding the `- **Q:**` and `- **R:**` prefixes and the Response_Item indentation.
4. WHEN the Recap_PDF_Renderer renders the QR_Pairs of a module, THE Recap_PDF_Renderer SHALL render them in the same relative first-to-last order in which they appear in Recap_Markdown.

### Requirement 5: Backward compatibility with the legacy split-list schema

**User Story:** As a bootcamper with an existing recap, I want my older split-list recap to still
render correctly, so that previously generated recaps remain usable.

#### Acceptance Criteria

1. WHERE a module section is written in the Split_List_Schema, THE Recap_PDF_Renderer SHALL render every question from that section's `### Questions Asked` list and every answer from that section's `### Answers Given` list, preserving each item's text and its 1:1 number, with no question or answer omitted.
2. IF rendering a Split_List_Schema module section would omit any question or answer present in Recap_Markdown, THEN THE Recap_PDF_Renderer SHALL terminate with a non-zero exit code and SHALL NOT write a recap PDF, producing an error indication identifying the omitted content.
3. WHEN the Recap_PDF_Renderer encounters a module section in the Split_List_Schema, THE Recap_PDF_Renderer SHALL pair the answer numbered N with the question numbered N for rendering, and SHALL render the resulting pairs in ascending numeric order.
4. WHERE a Split_List_Schema module section contains a question with no answer of the same number, or an answer with no question of the same number, THE Recap_PDF_Renderer SHALL render that unmatched item with an explicit placeholder value of `(no matching entry)` in place of its missing counterpart rather than dropping the item.
5. IF a recap contains both Split_List_Schema sections and Paired_Schema sections, THEN THE Recap_PDF_Renderer SHALL classify each module section independently — as Paired_Schema when the section contains a `### Questions & Responses` heading, and as Split_List_Schema when the section contains a `### Questions Asked` heading and an `### Answers Given` heading — and SHALL render each section according to its own classification.
