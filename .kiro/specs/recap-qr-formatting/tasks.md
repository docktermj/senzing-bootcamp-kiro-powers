# Implementation Plan: Recap Questions & Responses Formatting

## Overview

This plan implements the Paired_Schema authoring change and the indent-aware,
backward-compatible PDF rendering described in the design. Work proceeds from the pure
formatting helpers (the single source of truth for the schema), through the indent-aware
renderer primitives, into the schema-aware parser/renderer in the bundled generator, then
the atomic-write verification path, and finally the supporting `normalize_markdown.py` change
and the `module-recap-append` hook prompt update. Each of the 10 correctness properties from
the design is implemented as a single Hypothesis property test placed next to the code it
validates.

All code is stdlib-only Python 3.11+ following `senzing-bootcamp/` conventions: `fpdf` stays a
lazily-imported optional dependency, scripts are imported in tests via the `sys.path` pattern,
property tests use `@given` with the active Hypothesis profile (no hand-set `max_examples`), and
strategies are prefixed `st_`. Power tests live in `senzing-bootcamp/tests/`; the hook-prompt
content test lives in the repo-root `tests/`.

## Tasks

- [x] 1. Implement Paired_Schema formatting helpers (authoring source of truth)
  - [x] 1.1 Add `format_qr_pair` and `format_qr_section` to `recap_pdf_render.py`
    - Add `INDENT_UNIT = 4` module constant
    - Implement `format_qr_pair(question, response) -> list[str]`: line 1 `- **Q:** <question>` at Indent_Depth 0; line 2 `    - **R:** <response>` at Indent_Depth 4; substitute `(no response recorded)` when the response is absent or whitespace-only; prefix every continuation line of a multi-line response with at least four spaces
    - Implement `format_qr_section(pairs) -> str`: emit the `### Questions & Responses` heading, then each substantive pair (question has a non-whitespace char after strip) as Question_Item + Response_Item in order; when there are no substantive pairs emit the heading followed by exactly `- None`
    - No new top-level imports; keep helpers pure
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.2 Write property test for QR_Section structure
    - **Property 1: QR_Section has exactly one heading and no legacy headings**
    - Add `st_qr_pair()` / `st_qr_pairs()` strategies (question/response text incl. whitespace-only, multi-line, Latin-1-safe content)
    - New file `senzing-bootcamp/tests/test_qr_section_structure_properties.py`
    - **Validates: Requirements 1.1, 1.4**

  - [x] 1.3 Write property test for QR_Pair prefixes
    - **Property 2: Every QR_Pair carries the correct prefixes**
    - New file `senzing-bootcamp/tests/test_qr_prefixes_properties.py`
    - **Validates: Requirements 1.3**

  - [x] 1.4 Write property test for absent/whitespace response placeholder
    - **Property 3: Absent or whitespace responses render the placeholder**
    - New file `senzing-bootcamp/tests/test_qr_placeholder_properties.py`
    - **Validates: Requirements 1.6**

  - [x] 1.5 Write property test for fixed four-space indentation invariant
    - **Property 4: Fixed four-space indentation invariant**
    - Assert Question_Item Indent_Depth 0, Response_Item Indent_Depth exactly 4, delta exactly 4, no tab characters, uniform across pairs and sections
    - New file `senzing-bootcamp/tests/test_qr_indentation_properties.py`
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [x] 1.6 Write edge-case unit tests for empty and multi-line cases
    - Empty pair list and all-whitespace-question list → heading followed by exactly `- None`, zero pairs (Requirement 1.5)
    - Multi-line response → every continuation line has ≥ 4 leading spaces (Requirement 2.5)
    - New file `senzing-bootcamp/tests/test_qr_format_edge_unit.py`
    - _Requirements: 1.5, 2.5_

- [x] 2. Implement indent-aware rendering primitives in `recap_pdf_render.py`
  - [x] 2.1 Add indentation and wrapping primitives and route list rendering through them
    - Add `PER_LEVEL_INDENT_MM = 6.0` module constant
    - Implement `indent_depth(line)` (count leading ASCII 0x20, ignore tabs) and `nesting_level(depth, unit=INDENT_UNIT)` (`depth // unit`, `>= 0`)
    - Implement `parse_list_block(block)` returning `(level, numbered, text)` triples that preserve indentation and fold unmarked continuation lines into the preceding item
    - Implement `render_indented_list_items(pdf, items)` that sets each item's horizontal start to `l_margin + level * PER_LEVEL_INDENT_MM` and renders text with `multi_cell` using width `right_margin - start_x` so text wraps within the margins; render Latin-1-safe text verbatim
    - Factor the horizontal-start computation and the text-wrapping computation into small pure helpers (e.g. `start_x(level)` and a wrap function) so the geometry/wrapping properties can test them directly
    - Change `render_markdown_body`'s list branch so it no longer strips leading spaces before classifying/measuring a list block; compute each item's level from `indent_depth` and route to `render_indented_list_items`
    - Keep the legacy `render_list_items` for flat-list callers
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 2.2 Write property test for per-level horizontal offset geometry
    - **Property 6: Per-level horizontal offset geometry**
    - Add `st_level()` strategy; assert start = left margin + N × fixed positive offset, constant spacing, within `[l_margin, right_margin)`, and level-1 start > level-0 start
    - New file `senzing-bootcamp/tests/test_recap_indent_geometry_properties.py`
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [x] 2.3 Write property test for text wrapping within margins
    - **Property 7: Text wraps within margins without dropping content**
    - Add `st_wrap_text()` and `st_width()` strategies; assert each wrapped line fits the width and rejoining reproduces every token with none truncated or dropped
    - New file `senzing-bootcamp/tests/test_recap_wrap_properties.py`
    - **Validates: Requirements 3.4**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Add schema-aware parsing to `generate_recap_pdf.py`
  - [x] 4.1 Add `QRPair`, extend `RecapSection`, and implement classification and paired parsing
    - Add `QRPair` dataclass (`question: str`, `response: str`)
    - Extend `RecapSection` with `qr_pairs: list[QRPair]` and `schema: str` (`"paired"` | `"split"` | `"none"`); retain `questions_asked` / `answers_given`
    - Implement `classify_section`: `"paired"` when the section has a `### Questions & Responses` heading; `"split"` when it has both `### Questions Asked` and `### Answers Given`; else `"none"` — applied per section
    - Implement `parse_qr_section`: pair each Question_Item with the immediately following Response_Item, drop the `- **Q:** ` / `- **R:** ` prefixes and response indentation while preserving remaining text character-for-character; `- None` yields zero pairs; tolerate responses indented more than four spaces
    - Keep existing Split_List two-list extraction unchanged
    - _Requirements: 4.1, 4.3, 4.4, 5.5_

  - [x] 4.2 Write property test for paired round-trip
    - **Property 5: Paired round-trip preserves text, order, adjacency, and count**
    - Format substantive pairs with `format_qr_section`, parse back with `parse_qr_section`, assert same pairs, same order, response immediately follows its question, text reproduced character-for-character over Latin-1-safe input
    - New file `senzing-bootcamp/tests/test_qr_roundtrip_properties.py`
    - **Validates: Requirements 1.2, 4.1, 4.3, 4.4**

  - [x] 4.3 Write property test for per-section schema classification
    - **Property 10: Per-section schema classification is independent**
    - Add `st_mixed_recap()` strategy interleaving paired and split sections; assert each section classified independently by its own headings
    - New file `senzing-bootcamp/tests/test_section_classification_properties.py`
    - **Validates: Requirements 5.5**

  - [x] 4.4 Write edge-case unit test for `- None` parse-back
    - A QR_Section whose body is `- None` parses back to zero QR_Pairs
    - New file `senzing-bootcamp/tests/test_qr_none_parse_unit.py`
    - _Requirements: 1.5_

- [x] 5. Implement schema-aware rendering in `generate_recap_pdf.py`
  - [x] 5.1 Render paired and split sections through the indent-aware renderer
    - Paired: render each QR_Pair as a Question_Item at level 0 and Response_Item at level 1 via `render_indented_list_items`, under a single `Questions & Responses` heading
    - Split: pair answer N with question N, render in ascending numeric order; render unmatched items with the placeholder `(no matching entry)` for the missing counterpart, never dropping the item; reconcile any existing placeholders to the requirement-specified value
    - Wire both paths into `_render_module_page` based on `section.schema`
    - _Requirements: 3.5, 4.4, 5.1, 5.3, 5.4_

  - [x] 5.2 Write property test for Split_List completeness, number-pairing, and order
    - **Property 8: Split_List rendering is complete, number-paired, and ordered**
    - Add `st_split_section()` strategy (numbered question/answer lists with arbitrary order and asymmetric numbering gaps); assert every item preserved, paired by number, ordered ascending
    - New file `senzing-bootcamp/tests/test_split_schema_render_properties.py`
    - **Validates: Requirements 5.1, 5.3**

  - [x] 5.3 Write property test for Split_List unmatched-item retention
    - **Property 9: Split_List unmatched items are retained with a placeholder**
    - Assert an unmatched question or answer is rendered with its text plus `(no matching entry)` for its missing counterpart and is never dropped
    - New file `senzing-bootcamp/tests/test_split_unmatched_properties.py`
    - **Validates: Requirements 5.4**

- [x] 6. Implement atomic write and round-trip verification in `generate_recap_pdf.py`
  - [x] 6.1 Make PDF write atomic and verify every pair/item before publishing
    - Implement `collect_verification_targets` to include the question and response text of every QR_Pair (Paired) and every number-paired item (Split)
    - Render to a temporary file, run `verify_rendered_pdf`, then move into place on success; on failure delete the temporary file (no recap PDF written), print an error to stderr identifying the specific QR_Pair / numbered item, and return exit code 1
    - Preserve existing handling for missing/empty input, absent `fpdf2` (lazy import, `pip install fpdf2` hint, Markdown left intact), and `OSError` on write/move
    - _Requirements: 4.1, 4.2, 5.1, 5.2_

  - [x] 6.2 Write edge/error unit test for unrenderable content
    - Inject an unrenderable pair / omitted item → non-zero exit, no output PDF exists, stderr identifies the offending content
    - New file `senzing-bootcamp/tests/test_recap_render_failure_unit.py`
    - _Requirements: 4.2, 5.2_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Teach `normalize_markdown.py` the new subsection
  - [x] 8.1 Recognize `Questions & Responses` as a known recap subsection
    - Add `"questions & responses"` to the recognized recap subsection set so normalization preserves the QR_Section instead of treating it as unknown content
    - _Requirements: 5.5_

  - [x] 8.2 Write unit test for QR_Section normalization stability
    - Normalizing a recap containing a `### Questions & Responses` section leaves the section intact across a normalization pass
    - New file `senzing-bootcamp/tests/test_normalize_qr_subsection_unit.py`
    - _Requirements: 5.5_

- [x] 9. Update the `module-recap-append` hook prompt to emit the Paired_Schema
  - [x] 9.1 Rewrite the hook prompt's gather/append steps for QR_Section
    - Gather questions and responses as an ordered list of pairs preserving ask order
    - Emit a single `### Questions & Responses` heading, then for each pair `- **Q:** <question>` immediately followed by `    - **R:** <response>` (four-space indent), matching exactly what `format_qr_section` produces
    - Zero substantive questions → heading followed by exactly `- None`; absent/whitespace response → `    - **R:** (no response recorded)`
    - Never emit `### Questions Asked` or `### Answers Given`
    - Keep the hook JSON schema valid (`name`, `version`, `when`, `then`)
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2_

  - [x] 9.2 Write hook-prompt content test (repo-root `tests/`)
    - Assert the prompt describes the Paired_Schema (`### Questions & Responses`, `- **Q:**`, `- **R:**`, four-space indentation, `- None`, `(no response recorded)`) and no longer instructs writing `### Questions Asked` / `### Answers Given`
    - New file `tests/test_module_recap_append_qr_prompt.py`
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 2.1_

- [x] 10. Integration and wiring
  - [x] 10.1 Write end-to-end integration test for both generators
    - When `fpdf2` is present, `generate_recap_pdf.py` and `generate_recap_pdf_inline.py` produce a PDF for a recap mixing paired and split sections and round-trip verification passes
    - Confirm the inline generator inherits the indent-aware rendering and wrapping fixes with no duplicated schema logic
    - New file `senzing-bootcamp/tests/test_recap_qr_integration.py`
    - _Requirements: 3.1, 4.1, 5.1, 5.5_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP.
- Each task references specific requirements (and, for property tests, the design property) for traceability.
- Property tests use Hypothesis with the active profile baseline; do not hand-set `@settings(max_examples=...)` to restate the baseline. Each property test carries the comment `# Feature: recap-qr-formatting, Property N: <property text>`.
- Each property test lives in its own new file so property sub-tasks can run in parallel without file-write conflicts.
- Checkpoints ensure incremental validation between the authoring, rendering, verification, and supporting-change stages.
- `recap_pdf_render.py` is edited by tasks 1.1 then 2.1; `generate_recap_pdf.py` is edited by tasks 4.1 then 5.1 then 6.1 — these are sequenced across waves to avoid conflicts.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "8.1", "9.1"] },
    { "id": 1, "tasks": ["2.1", "1.2", "1.3", "1.4", "1.5", "1.6", "8.2", "9.2"] },
    { "id": 2, "tasks": ["4.1", "2.2", "2.3"] },
    { "id": 3, "tasks": ["5.1", "4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["6.1", "5.2", "5.3"] },
    { "id": 5, "tasks": ["6.2", "10.1"] }
  ]
}
```
