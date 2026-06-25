# Bugfix Requirements Document

## Introduction

The recap PDF generator `senzing-bootcamp/scripts/generate_recap_pdf.py` converts
`docs/bootcamp_recap.md` into a shareable graduation PDF. It silently drops any recap
content that does not conform to a rigid, undocumented schema, producing a near-empty
PDF (cover page only) even when `bootcamp_recap.md` contains a full header and several
module sections of prose.

There are three root causes:

1. The module-heading regex requires the exact form `## Module N: <name> — <timestamp>`
   (em-dash plus a trailing timestamp). A natural heading like `## Module 1: Business
   Problem` does not match, so `_parse_sections` returns zero sections.
2. Within a matched module, the parser only extracts five fixed `### ` subsections
   (Information Shared, Questions Asked, Answers Given, Actions Taken, Duration) and only
   their list items. Prose paragraphs, code blocks, and any other headings are discarded.
3. When nothing matches, rendering still succeeds and emits only the cover page, with no
   warning that the body was empty.

The result is invisible data loss: a recap authored as ordinary Markdown produces an
almost-empty PDF with no error, and the loss is only discovered when someone opens the
PDF. This bugfix makes the parser tolerant, adds a raw-Markdown fallback so content is
never silently dropped, emits a warning when the parsed body is empty or under-populated,
and documents the expected recap schema.

The fix is constrained to Python 3.11+ stdlib only. `fpdf2` remains an optional,
lazily-imported dependency that must degrade gracefully (keep Markdown output) when
absent. All existing passing recap tests — including the chronological-ordering behavior
established by the separate `bootcamp-suite-and-validator-fixes` spec — must continue to
pass.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `bootcamp_recap.md` contains module headings without the ` — <timestamp>`
suffix (e.g. `## Module 1: Business Problem`) THEN the system parses zero sections and
emits a PDF containing only the cover page.

1.2 WHEN a module section contains prose paragraphs, code blocks, or headings other than
the five hard-coded `### ` subsections THEN the system discards that content entirely and
it never appears in the PDF.

1.3 WHEN `_parse_sections` returns zero sections for a non-empty recap body THEN the
system renders a cover-page-only PDF and reports success with no warning that the body
was empty.

1.4 WHEN the number of parsed sections is far fewer than the modules present in the recap
THEN the system silently drops the unparsed modules with no warning.

### Expected Behavior (Correct)

2.1 WHEN `bootcamp_recap.md` contains module headings without the ` — <timestamp>` suffix
THEN the system SHALL recognize them as module sections (with an empty timestamp) and
render their content in the PDF.

2.2 WHEN a module section contains prose paragraphs, code blocks, or headings other than
the five known subsections THEN the system SHALL render that generic Markdown content
(paragraphs, bullet lists, code blocks) under the module rather than discarding it.

2.3 WHEN no structured module sections can be parsed from a non-empty recap body THEN the
system SHALL fall back to rendering the raw Markdown body so that no content is silently
dropped.

2.4 WHEN the parsed section count is zero, or substantially fewer than the modules present
in the recap, THEN the system SHALL emit a warning at generation time making the mismatch
visible.

2.5 WHEN the fix is delivered THEN the system SHALL document the exact recap schema the PDF
expects (heading format and recognized subsection names) so reconstructed recaps can
conform.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `bootcamp_recap.md` conforms to the strict schema (`## Module N: <name> —
<timestamp>` headings with the five `### ` subsections) THEN the system SHALL CONTINUE TO
parse every section and render the same structured PDF as before.

3.2 WHEN a recap document is formatted and parsed back (round-trip) THEN the system SHALL
CONTINUE TO preserve header fields, section count, section identity fields, list contents,
Q&A pairing, and durations exactly as the existing property tests require.

3.3 WHEN `fpdf2` is not installed THEN the system SHALL CONTINUE TO degrade gracefully —
keep the Markdown output, print the `pip install fpdf2` hint, and exit with code 1 without
a traceback.

3.4 WHEN the input recap file is missing or empty THEN the system SHALL CONTINUE TO report
the existing error message and exit with code 1.

3.5 WHEN module sections are present THEN the system SHALL CONTINUE TO preserve the
chronological-ordering behavior established by the `bootcamp-suite-and-validator-fixes`
spec and keep all existing passing recap tests green.

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type RecapMarkdown (the full text of bootcamp_recap.md)
  OUTPUT: boolean

  // The recap has real body content, but the strict parser drops some or all of it.
  hasBody        ← nonEmptyBodyAfterHeader(X)
  strictSections ← parseSectionsStrict(X)      // current _MODULE_HEADING_RE behavior
  bodyContent    ← extractRenderableContent(X) // headings + prose + lists + code blocks

  RETURN hasBody AND renderedContentOf(strictSections) LOSES bodyContent
END FUNCTION
```

Concrete counterexample: a `bootcamp_recap.md` with a valid header and seven sections
headed `## Module N: <name>` (no em-dash/timestamp) plus prose paragraphs produces a
cover-page-only PDF (`strictSections = []`), losing all body content.

### Property Specification

```pascal
// Property: Fix Checking — content is never silently dropped
FOR ALL X WHERE isBugCondition(X) DO
  result ← generateRecapPdf'(X)
  ASSERT renderedBodyIsNonEmpty(result)                 // 2.1, 2.2, 2.3
  ASSERT containsRenderableContentOf(result, X)          // 2.2, 2.3
  ASSERT warningEmittedWhenSectionsUnderpopulated(X)     // 2.4
END FOR
```

```pascal
// Property: Preservation Checking — strict-schema recaps are unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT generateRecapPdf(X) = generateRecapPdf'(X)      // 3.1, 3.2
END FOR
```

Where `F` = `generate_recap_pdf` before the fix and `F'` = `generate_recap_pdf` after the
fix.
