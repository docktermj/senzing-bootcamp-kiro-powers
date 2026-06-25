# Implementation Plan: Recap Q&A Pair Merge

## Overview

This plan merges the recap PDF's separate "Questions Asked" and "Answers Given" sections into a single
"Questions and responses" section that renders each question immediately followed by its answer. The
change is isolated to the PDF renderer in `generate_recap_pdf.py`; the Markdown schema, parser,
formatter, data model, and module-recap-append hook template are intentionally unchanged. Tests extend
the existing recap suite. Implementation language is Python 3.11+, stdlib-only with `fpdf2` as the
optional, lazily-imported PDF dependency.

## Tasks

- [x] 1. Implement the merged Q/A rendering helper
  - [x] 1.1 Add `_render_qa_pairs` and a testable line-builder seam
    - In `senzing-bootcamp/scripts/generate_recap_pdf.py`, add `_render_qa_pairs(pdf, questions, answers)`
      that renders `Q: <question>` immediately followed by `A: <answer>`, paired by index
    - Iterate `range(max(len(questions), len(answers)))` so unequal lengths never drop content; render
      an explicit placeholder for a missing counterpart (e.g. `A: (no answer recorded)` /
      `Q: (no question recorded)`)
    - Reuse the existing inline-code (`` `code` ``) handling from `_render_list_items`
    - Extract the ordered Q/A line construction into a small pure helper (e.g. `_build_qa_lines`) so it
      can be unit-tested without rendering binary PDF output
    - _Requirements: 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 2. Wire the merged section into `_render_module_page`
  - [x] 2.1 Replace the two sections with one "Questions and responses" section
    - Remove the separate "Questions Asked" and "Answers Given" heading/list blocks from
      `_render_module_page`
    - Render a single `_render_heading(pdf, "Questions and responses", level=3)`; when the module has any
      question or answer, call `_render_qa_pairs`; otherwise render the existing empty-state ("None")
    - Keep the Latin-1-safe (`_safe_text`) path for the `Q:`/`A:` labels
    - _Requirements: 1.1, 1.4, 2.4, 4.1, 4.3_

- [x] 3. Tests for the merged rendering
  - [x] 3.1 Test single merged section (Property 1)
    - Assert the rendered Q/A line sequence contains "Questions and responses" and does NOT contain
      "Questions Asked" or "Answers Given" headings for a module with questions
    - _Requirements: 5.1, 1.1, 1.4_

  - [x] 3.2 Test inline pairing by index (Property 2)
    - For equal-length lists, assert emitted lines are `Q: q0, A: a0, Q: q1, A: a1, ...` in order
    - _Requirements: 5.2, 1.2, 1.3, 2.1_

  - [x] 3.3 Test unequal-length handling (Property 3)
    - More questions than answers and vice versa: assert every question and answer text appears,
      placeholders fill missing counterparts, and later pairs are not misaligned
    - _Requirements: 5.3, 2.2, 2.3_

  - [x] 3.4 Test empty-state rendering
    - A module with no questions and no answers renders the existing "None" empty-state under the merged
      heading
    - _Requirements: 2.4_

  - [x] 3.5 Hypothesis property test for pairing and no-drop (Properties 2, 3)
    - Generate arbitrary question/answer lists including unequal lengths; assert the answer follows its
      question by index and no text is dropped
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 4. Verify Markdown round-trip is unchanged (Property 4)
  - [x] 4.1 Re-run the existing recap suite
    - Run the existing round-trip, Q&A pairing, and structural-completeness tests in
      `test_generate_recap_pdf.py` unchanged; confirm the Markdown schema still emits "### Questions
      Asked" and "### Answers Given" and the parser round-trips them
    - _Requirements: 5.4, 3.1, 3.2, 3.3, 3.4_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Run `pytest senzing-bootcamp/tests/test_generate_recap_pdf.py`; confirm the new merged-rendering
    tests pass and no existing recap test regresses. Ask the user if questions arise.

## Notes

- Target code: `senzing-bootcamp/scripts/generate_recap_pdf.py` (`_render_module_page`, new
  `_render_qa_pairs` / `_build_qa_lines`); tests extend
  `senzing-bootcamp/tests/test_generate_recap_pdf.py`.
- The Markdown schema, parser, formatter, `RecapSection` data model, and the module-recap-append hook
  template are intentionally NOT changed (Requirement 3).
- This feature pairs with `recap-pdf-content-loss-fix` (Markdown Q&A pairing preserved) and
  `graduation-recap-pdf-resilience` (inline fallback reuses this renderer, inheriting the merge).
- Run tests as single executions, not in watch mode.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5", "4.1"] },
    { "id": 3, "tasks": ["5"] }
  ]
}
```
