# Implementation Plan

## Overview

This plan fixes silent content loss in the recap PDF generator
(`senzing-bootcamp/scripts/generate_recap_pdf.py`) using the exploratory bugfix workflow:
explore the bug with a failing property test, lock in current behavior with preservation tests,
apply the tolerant-parsing + fallback + warning fix, then validate.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"],
      "description": "Run BEFORE any fix on UNFIXED code. Task 1 must FAIL (proves the bug). Task 2 must PASS (baseline to preserve). Independent of each other."
    },
    {
      "wave": 2,
      "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5"],
      "description": "Implementation steps applied in order after wave 1 completes: tolerant heading matching, generic-content capture, raw-body fallback, warning emission, schema docs."
    },
    {
      "wave": 3,
      "tasks": ["3.6", "3.7"],
      "description": "Re-run the SAME tests from tasks 1 and 2. Task 1's test must now PASS; task 2's tests must still PASS."
    },
    {
      "wave": 4,
      "tasks": ["4"],
      "description": "Final checkpoint: full recap suite green, no regressions."
    }
  ]
}
```

- Tasks 1 and 2 are independent of each other but BOTH must be completed (1 failing, 2 passing) before task 3.
- Tasks 3.1–3.5 are the implementation steps; 3.6 and 3.7 re-run the tests from tasks 1 and 2.
- Task 4 is the final checkpoint and depends on all of task 3.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Content Silently Dropped by Strict Parser
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate recap content is silently dropped
  - **Scoped PBT Approach**: Use Hypothesis to generate free-form recaps that satisfy `isBugCondition(X)` — a valid header plus N module headings of the form `## Module N: <name>` (no ` — <timestamp>` suffix) interleaved with prose paragraphs and fenced code blocks. Also include a concrete deterministic counterexample: a header with seven `## Module N: <name>` sections plus prose.
  - Add the test to `senzing-bootcamp/tests/test_generate_recap_pdf.py` (pytest + Hypothesis), reusing the existing import pattern and strategies
  - Assert the Expected Behavior Properties from design: rendered body is non-empty AND contains the input's renderable text tokens (loose headings recognized, Generic_Content rendered, or Raw_Body_Fallback used), per `containsRenderableContentOf(result, X)`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS — `strictSections = []` yields a cover-page-only result that loses body content (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., "recap with 7 `## Module N: <name>` headings + prose produces an empty PDF body, losing all content") to understand the root cause
  - Mark task complete when the test is written, run, and the failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Strict-Schema Recaps Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (cases where `isBugCondition(X)` is false): strict-schema recaps with `## Module N: <name> — <timestamp>` headings and the five `### ` subsections
  - Observe and record on UNFIXED code: the `format → parse` round-trip preserves header fields, section count, section identity fields, list contents, Q&A pairing, and durations; `fpdf2`-absent prints the `pip install fpdf2` hint and exits 1; missing/empty input reports the existing error and exits 1
  - Write property-based tests (Hypothesis) capturing the observed behavior from the Preservation Requirements: strict-schema parse/render equivalence, graceful `fpdf2`-absent degradation (monkeypatch `fpdf` import to raise `ImportError`), and missing/empty-input handling
  - Property-based testing generates many test cases for stronger preservation guarantees ("for all non-buggy inputs")
  - Run tests on UNFIXED code (alongside the full existing recap suite: round-trip, structural completeness, Q&A pairing, append preservation, timestamp format, chronological ordering)
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for recap PDF content loss

  - [x] 3.1 Add tolerant module-heading matching
    - Add new `_MODULE_HEADING_LOOSE_RE = re.compile(r"^##\s+Module\s+(\d+):\s+(.+?)\s*$", re.MULTILINE)` alongside the unchanged strict `_MODULE_HEADING_RE`
    - In `_parse_sections`, try the strict pattern first (identical behavior for Strict_Schema recaps); otherwise fall back to the loose pattern with `timestamp = ""`
    - `_parse_sections` must never raise
    - _Bug_Condition: isBugCondition(X) — hasBody AND renderedContentOf(strictSections) LOSES bodyContent_
    - _Expected_Behavior: Loose_Headings recognized; N sections parsed with timestamp == "" (Req 2.1)_
    - _Preservation: Strict_Schema recaps parse exactly as today (Req 3.1, 3.2)_
    - _Requirements: 2.1, 3.1, 3.2_

  - [x] 3.2 Capture Generic_Content per module
    - Add a defaulted `generic_content: list[str]` field to `RecapSection` (back-compatible so `format_recap_section` and round-trip tests are unaffected)
    - Update `_split_subsections` to also return the leftover (non-known-subsection) text; store it as Generic_Content in `_parse_sections`
    - Render Generic_Content blocks in `_render_module_page` after the five known subsections
    - _Bug_Condition: isBugCondition(X) — prose/code/other headings discarded by strict parser_
    - _Expected_Behavior: Generic_Content rendered, not discarded (Req 2.2)_
    - _Preservation: Defaulted field keeps format/round-trip behavior unchanged (Req 3.2)_
    - _Requirements: 2.2, 3.2_

  - [x] 3.3 Add Raw_Body_Fallback rendering
    - Add `render_markdown_body(pdf, body_text)` to render arbitrary Markdown (headings/paragraphs/lists/code) as PDF blocks
    - Update `render_pdf` to render structured sections when present, else cover page + raw body
    - Route `main` through the fallback when sections are empty but the body is non-empty so no content is silently dropped
    - _Bug_Condition: isBugCondition(X) — non-empty body produces zero structured sections_
    - _Expected_Behavior: Raw_Body_Fallback renders the content (Req 2.3)_
    - _Preservation: Structured path unchanged when sections present (Req 3.1)_
    - _Requirements: 2.3, 3.1_

  - [x] 3.4 Emit warning on empty / under-populated parse
    - In `main`, count Loose_Heading occurrences in the source and compare to the parsed section count
    - When zero sections with a non-empty body, or parsed sections substantially fewer than detected headings, print a warning to stderr (preserving the stdout `PDF generated:` contract) and exit 0
    - _Bug_Condition: isBugCondition(X) — under-populated parse with no signal_
    - _Expected_Behavior: warning emitted at generation time making the mismatch visible (Req 2.4)_
    - _Preservation: stdout `PDF generated:` contract and exit code unchanged (Req 3.1, 3.5)_
    - _Requirements: 2.4_

  - [x] 3.5 Document the expected recap schema
    - Document the schema in the module docstring: heading format `## Module N: <name> [— <timestamp>]`, the five recognized subsection names (Information Shared, Questions Asked, Answers Given, Actions Taken, Duration), and that any other content renders generically
    - _Expected_Behavior: exact recap schema documented so reconstructed recaps conform (Req 2.5)_
    - _Requirements: 2.5_

  - [x] 3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Content Silently Dropped by Strict Parser
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (non-empty rendered body containing the input's renderable content; warning when under-populated)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run the bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms content is no longer silently dropped)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Strict-Schema Recaps Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from step 2 plus the full existing recap suite
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — strict parse/render equivalence, graceful `fpdf2`-absent degradation, missing/empty-input handling, chronological ordering)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full recap test suite in `senzing-bootcamp/tests/` and confirm Property 1 now passes, Property 2 still passes, and no existing test regresses
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Target code: `senzing-bootcamp/scripts/generate_recap_pdf.py`; tests extend
  `senzing-bootcamp/tests/test_generate_recap_pdf.py` (pytest + Hypothesis).
- Property 1 (Bug Condition / Expected Behavior) is encoded once in task 1 and re-run in task 3.6 —
  do not write a second test.
- Property 2 (Preservation) is encoded once in task 2 and re-run in task 3.7 — do not write new tests.
- Run tests as single executions (e.g., `pytest senzing-bootcamp/tests/test_generate_recap_pdf.py`),
  not in watch mode.
- Constraint: Python 3.11+ stdlib only; `fpdf2` stays an optional, lazily-imported dependency that
  degrades gracefully when absent.
