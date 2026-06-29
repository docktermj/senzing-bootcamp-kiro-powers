# Design Document

## Overview

The recap PDF currently renders each module's questions and answers as two separate, positionally
aligned sections ("Questions Asked" and "Answers Given"), forcing the reader to cross-reference by
index. This feature merges them into a single "Questions and responses" section where each question is
immediately followed by its answer.

The change is isolated to PDF rendering. The recap Markdown schema, the parser
(`parse_recap_markdown`), the formatter (`format_recap_section` / `format_recap_document`), and the
`RecapSection` data model (`questions_asked` / `answers_given`) are deliberately unchanged so the
format->parse round-trip and Q&A pairing guarantees from `recap-pdf-content-loss-fix` keep passing. The
`RecapSection` already stores questions and answers as parallel lists, which is exactly the input a
pairing renderer needs — so the merge is a presentation-layer transform over data that already exists.

This pairs with `graduation-recap-pdf-resilience`: because its inline fallback reuses the shared
renderer when importable, the merged rendering naturally applies there too.

## Architecture

```text
   RecapSection (unchanged)
     questions_asked: [q0, q1, q2]
     answers_given:   [a0, a1, a2]
            |
            v
   _render_module_page (generate_recap_pdf.py)   <-- CHANGED (presentation only)
            |
            +-- "Questions and responses"  (single heading; replaces the two headings)
                  Q: q0
                  A: a0
                  Q: q1
                  A: a1
                  Q: q2
                  A: a2

   Markdown schema / parser / formatter         <-- UNCHANGED
     ### Questions Asked  +  ### Answers Given still written and round-tripped
```

## Components and Interfaces

### `_render_module_page` in `senzing-bootcamp/scripts/generate_recap_pdf.py`

Replace the two blocks that render "Questions Asked" (numbered) and "Answers Given" (numbered) with a
single block that renders a "Questions and responses" heading followed by paired Q/A entries built from
`section.questions_asked` and `section.answers_given`.

Add a small helper to render the merged section:

```python
def _render_qa_pairs(
    pdf: "FPDF",
    questions: list[str],
    answers: list[str],
) -> None:
    """Render questions and answers as inline Q/A pairs under one section.

    Pairs by index: question i is rendered as 'Q: <question>' immediately
    followed by 'A: <answer>'. Iterates over the longer of the two lists so
    nothing is dropped; a missing counterpart renders an explicit placeholder
    (e.g. 'A: (no answer recorded)' / 'Q: (no question recorded)') rather than
    misaligning later pairs. Reuses the existing inline-code handling used by
    _render_list_items.
    """
```

`_render_module_page` then calls, in place of the old two sections:

```python
_render_heading(pdf, "Questions and responses", level=3)
if section.questions_asked or section.answers_given:
    _render_qa_pairs(pdf, section.questions_asked, section.answers_given)
else:
    # existing empty-state rendering ("None")
    ...
```

Notes:

- The "Q:"/"A:" labels are plain ASCII, safe for the Latin-1 core-font path (`_safe_text`).
- Inline code spans inside a question or answer continue to render in the monospace font, reusing the
  same `re.split(r"`([^`]+)`", item)` handling that `_render_list_items` uses.
- Pairing iterates `range(max(len(questions), len(answers)))` so unequal lengths never drop content
  (Requirements 2.2, 2.3).

### Markdown formatter, parser, data model — unchanged

`format_recap_section` keeps emitting "### Questions Asked" and "### Answers Given"; the parser keeps
reading them into `questions_asked` / `answers_given`. This preserves every existing round-trip,
structural-completeness, and Q&A-pairing test (Requirement 3). The module-recap-append hook template in
`steering/hook-registry-module-any.md` is unchanged (Requirement 3.4).

### Inline fallback path

`graduation-recap-pdf-resilience`'s inline generator reuses `generate_recap_pdf`'s renderer when it is
importable, so it inherits the merged rendering automatically (Requirement 4.2). When the inline
generator falls back to its embedded raw-Markdown renderer (module not importable), it renders the
Markdown body verbatim — which still shows the questions and answers content (just in the Markdown
schema's two-section form); this feature does not require the embedded raw renderer to merge, since the
merge is a property of the structured renderer.

## Data Models

No data model changes. The merge consumes the existing parallel `questions_asked` / `answers_given`
lists on `RecapSection`.

## Error Handling

| Condition | Handling |
|---|---|
| Equal-length Q and A | One A per Q, paired by index (Req 2.1) |
| More questions than answers | Render every Q; missing A renders an explicit placeholder (Req 2.2) |
| More answers than questions | Render every A; missing Q renders an explicit placeholder (Req 2.3) |
| No questions and no answers | Existing empty-state ("None") rendering (Req 2.4) |
| Inline code in a Q or A | Monospace span via existing inline-code handling |

## Correctness Properties

### Property 1: Single merged section

*For all* sections with at least one question or answer, the rendered PDF body contains the heading
"Questions and responses" and does not contain the "Questions Asked" or "Answers Given" headings.
**Validates: Requirements 1.1, 1.4**

### Property 2: Inline pairing by index

*For all* equal-length question/answer lists, each rendered answer immediately follows its question and
corresponds to the same index, preserving question order. **Validates: Requirements 1.2, 1.3, 2.1**

### Property 3: No content dropped on unequal lengths

*For all* question/answer lists of differing lengths, every question text and every answer text appears
in the rendered body, with explicit placeholders for missing counterparts and no misalignment of
later pairs. **Validates: Requirements 2.2, 2.3**

### Property 4: Markdown round-trip unchanged

*For all* valid `RecapDocument` values, `format → parse` preserves section identity, list contents, Q&A
pairing, and durations exactly as before (the Markdown schema and parser/formatter are untouched).
**Validates: Requirements 3.1, 3.2, 3.3**

## Testing Strategy

Tests extend `senzing-bootcamp/tests/test_generate_recap_pdf.py` (pytest + Hypothesis), reusing the
existing strategies and `sys.path` import pattern. Because the PDF is binary, assert against a
render seam — render to a temp PDF and assert via the structured render path, or refactor the merged
rendering text-building into a testable pure helper that returns the ordered Q/A lines and assert on
that.

- **Single merged section (Property 1):** assert the rendered Q/A line sequence contains a "Questions
  and responses" section and no "Questions Asked"/"Answers Given" headings.
- **Inline pairing (Property 2):** for equal-length lists, assert the emitted lines are
  `Q: q0, A: a0, Q: q1, A: a1, ...` in order.
- **Unequal lengths (Property 3):** more questions than answers and vice versa — assert all texts
  present, placeholders for missing counterparts, no misalignment.
- **Empty state (Req 2.4):** a module with no Q and no A renders the existing "None" empty-state.
- **Markdown round-trip preserved (Property 4):** re-run the existing round-trip / Q&A pairing /
  structural-completeness tests unchanged; they must still pass.
- **Hypothesis (Properties 2, 3):** generate arbitrary question/answer lists (including unequal
  lengths) and assert the pairing/no-drop invariants.

## Requirements Traceability

| Requirement | Design element |
|---|---|
| 1 (merge in PDF) | `_render_qa_pairs` + `_render_module_page` single "Questions and responses" section |
| 2 (pairing / unequal lengths) | `_render_qa_pairs` iterates the longer list with placeholders |
| 3 (schema/round-trip preserved) | formatter/parser/data model/hook template unchanged |
| 4 (all PDF paths) | shared renderer reused by inline fallback; single rendering behavior |
| 5 (tests) | Properties 1-4 tests in `senzing-bootcamp/tests/test_generate_recap_pdf.py` |
