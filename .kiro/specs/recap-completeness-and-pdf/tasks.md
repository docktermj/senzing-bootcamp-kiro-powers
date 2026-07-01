# Implementation Plan

## Overview

This plan fixes two related content-loss paths in the bootcamp recap deliverable
(`docs/bootcamp_recap.md` and its rendered PDF) using the exploratory bug-condition
methodology: write tests that surface the bug first, then implement the fix, then
verify the bug is gone (fix checking) and existing behavior is preserved
(preservation checking). Path A is missing/unverified per-module recap sections;
Path B is the outline-only PDF caused by `multi_cell(0, ...)` width derivation and a
swallowed `FPDFException`.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"],
      "description": "Standalone test tasks written before the fix. Task 1 (Property 1) must FAIL on unfixed code; task 2 (Property 2) must PASS on unfixed code.",
      "dependencies": []
    },
    {
      "wave": 2,
      "tasks": ["3.1", "3.2", "3.3", "3.4"],
      "description": "Fix implementation. 3.1 (full-width cells) precedes 3.2 (loud failure + round-trip verification); 3.3 (synchronous verified append) and 3.4 (track-completion reconciliation) address the missing-section path.",
      "dependencies": ["1", "2"]
    },
    {
      "wave": 3,
      "tasks": ["3.5", "3.6"],
      "description": "Fix checking and preservation checking. Re-run the SAME tests from tasks 1 and 2 against fixed code: 3.5 expects Property 1 to PASS, 3.6 expects Property 2 to still PASS.",
      "dependencies": ["3.1", "3.2", "3.3", "3.4"]
    },
    {
      "wave": 4,
      "tasks": ["4"],
      "description": "Checkpoint — run the full suite plus integration flows and confirm all tests pass.",
      "dependencies": ["3.5", "3.6"]
    }
  ]
}
```

Tasks 1 and 2 must complete before task 3. Within task 3, 3.1 precedes 3.2; 3.5 and
3.6 require the implementation sub-tasks (3.1–3.4) and the tests from tasks 1 and 2.

## Tasks

- [x] 1. Write bug condition exploration tests
  - **Property 1: Bug Condition** - Recap Completeness and Full PDF Body
  - **CRITICAL**: These tests MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: These tests encode the expected behavior - they will validate the fix when they pass after implementation
  - **GOAL**: Surface counterexamples that demonstrate both content-loss paths exist
  - **Scoped PBT Approach**: For the deterministic paths, scope properties to concrete failing cases for reproducibility, then generalize
  - Place tests in `senzing-bootcamp/tests/` (pytest + Hypothesis, stdlib + optional `fpdf2`)
  - **Path A — Missing section, no reconciliation** (from `isBugCondition` `missingSection`):
    - Build a recap state where `config/bootcamp_progress.json` `modules_completed = [1..7]` but `docs/bootcamp_recap.md` contains only `## Module 1:`..`## Module 5:` sections
    - Property: for all `m` in `modules_completed`, `hasHeading(recapFile, m)` ("## Module m:") should hold after track completion
    - Run on UNFIXED code — assert no step backfills Modules 6 and 7 (sections remain absent while completion reports success)
  - **Path A — Final-module append miss**:
    - Simulate the Recap_Append_Hook not writing the last module's `## Module 7:` section on boundary detection
    - Run on UNFIXED code — assert completion proceeds with the section absent
  - **Path B — Wrapping body line drops** (from `isBugCondition` `droppedBodyLine`):
    - Render a recap whose `### Information Shared` bullet is long enough to wrap (triggers `multi_cell(0, ...)` width derivation in `recap_pdf_render.py`)
    - Run on UNFIXED code — assert the generated PDF's extracted text is missing that bullet while the heading survives, AND the generator still reported success (exit 0, file exists)
  - **Path B — Swallowed FPDFException**:
    - Confirm the broad `except (OSError, Exception)` in `generate_recap_pdf.py:main` absorbs the `FPDFException: Not enough horizontal space to render a single character` so the run does not fail loudly
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., "extracted PDF text missing wrapping bullet while heading remains"; "modules_completed entries 6,7 have no `## Module N:` heading after track completion")
  - Mark task complete when tests are written, run, and failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Already-Correct Recaps, Fitting PDFs, and Unrelated Behavior
  - **IMPORTANT**: Follow observation-first methodology — observe behavior on UNFIXED code first, then write tests asserting it
  - Property-based testing (pytest + Hypothesis) generates many recap/PDF inputs for stronger guarantees across the non-buggy input domain
  - **Existing section preservation** (Req 3.1):
    - Observe: a recap already containing all `## Module N:` sections is unchanged on unfixed code
    - Write property test: reconciliation leaves existing content byte-for-byte identical, with no duplication, overwrite, or reordering out of chronological order
  - **Idempotent reconciliation** (Req 3.2):
    - Observe: `plan_backfill` / `detect_artifact_gaps` in `completion_artifacts.py` return an empty plan for a recap already consistent with `modules_completed`
    - Write property test: re-running reconciliation on a consistent recap makes no changes
  - **Fitting-PDF preservation** (Req 3.3):
    - Observe: a recap whose body fits within available width renders all headings and body lines on unfixed code
    - Write property test: for all fitting body content, extracted PDF text contains every heading and body line
  - **fpdf2-absent degradation** (Req 3.4):
    - Observe: the `pip install fpdf2` hint is printed and Markdown output is preserved on unfixed code when `fpdf` import is absent
    - Write test: with `fpdf2` unavailable, the system degrades identically without raising
  - **Unrelated-hook preservation** (Req 3.5):
    - Write test: celebration/journal entry and other completion hooks behave exactly as before the fix
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for recap completeness (missing per-module sections) and outline-only PDF rendering

  - [x] 3.1 Render PDF cells at full width from the left margin
    - In `senzing-bootcamp/scripts/recap_pdf_render.py`, update `render_heading`, `render_generic_blocks`, `render_markdown_body`, and `render_markdown_pdf`
    - Before every `multi_cell` call that currently passes width `0`, call `pdf.set_x(pdf.l_margin)` then `pdf.multi_cell(pdf.epw, ...)` so wrapping always has full horizontal space
    - Preserve `write`-based list/Q&A indentation: `render_list_items` and the Q&A path keep `set_x(l_margin + 6)` + `write(...)`, but ensure they cannot leave x near the right margin for the next cell
    - _Bug_Condition: isBugCondition(input) where input.pdfRender.bodyLinesDropped > 0 AND reportedSuccess = TRUE_
    - _Expected_Behavior: expectedBehavior(result) — every body line renders within epw; no FPDFException for fitting content_
    - _Preservation: Fitting PDF bodies render identically (Req 3.3); write-based indentation unchanged_
    - _Requirements: 2.5_

  - [x] 3.2 Stop swallowing rendering exceptions and verify rendered PDF
    - In `senzing-bootcamp/scripts/generate_recap_pdf.py` (`render_pdf`, `main`): replace the broad `except (OSError, Exception)` so a genuine rendering failure (e.g. `FPDFException`) is not silently absorbed — log/fail loudly and return non-zero, never reporting success after dropping content
    - Keep the `ImportError` branch intact for graceful `fpdf2`-absent degradation
    - After `pdf.output(...)`, re-open the PDF, extract its text, and assert it contains a `Module N` section for each completed module plus at least `MIN_BODY_LINES` body lines; only print `PDF generated:` and return 0 when verification passes
    - In `senzing-bootcamp/scripts/generate_recap_pdf_inline.py` (`generate_inline`): mirror the loud-failure and round-trip verification (it inherits the width fix via the Shared_Renderer), while keeping the `fpdf2`-absent hint
    - _Bug_Condition: isBugCondition(input) where input.pdfRender.bodyLinesDropped > 0 AND reportedSuccess = TRUE_
    - _Expected_Behavior: expectedBehavior(result) — PDF contains all sections and body lines OR fails loudly; success reported only after round-trip verification_
    - _Preservation: ImportError/graceful degradation preserved (Req 3.4)_
    - _Requirements: 2.6, 2.7_

  - [x] 3.3 Make recap append synchronous and verified
    - Perform the recap append as a synchronous step of the module-completion workflow (not solely via the agentStop hook in `senzing-bootcamp/hooks/module-recap-append.kiro.hook`)
    - Verify a `## Module N:` heading for the just-completed module exists in `docs/bootcamp_recap.md`, retrying/backfilling if absent, before reporting success
    - Append the final module of a track exactly as any other module; graduation/celebration must not suppress the per-module recap section
    - _Bug_Condition: isBugCondition(input) where EXISTS m IN modules_completed SUCH THAT NOT hasHeading(recapFile, m)_
    - _Expected_Behavior: expectedBehavior(result) — append is synchronous and verified; missing sections detected and backfilled rather than reporting silent success_
    - _Preservation: Existing persisted sections preserved byte-for-byte (Req 3.1); unrelated hooks unchanged (Req 3.5)_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.4 Reconcile and backfill the recap at track completion
    - At track completion, run `completion_artifacts.py --plan`, consume `recap_modules` from the `BackfillPlan`, and backfill any missing per-module section so every completed module has a `## Module N:` section
    - Compare `docs/bootcamp_recap.md` against `config/bootcamp_progress.json` `modules_completed`
    - Because `plan_backfill` returns a pure set difference, re-running on a consistent recap yields an empty plan and no changes; existing sections are appended-around, never rewritten
    - _Bug_Condition: isBugCondition(input) where recap not reconciled against modules_completed_
    - _Expected_Behavior: expectedBehavior(result) — reconciliation backfills every missing per-module section_
    - _Preservation: Idempotent reconciliation makes no spurious changes (Req 3.2); existing sections preserved byte-for-byte (Req 3.1)_
    - _Requirements: 2.4_

  - [x] 3.5 Verify bug condition exploration tests now pass
    - **Property 1: Expected Behavior** - Recap Completeness and Full PDF Body
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - The tests from task 1 encode the expected behavior (every completed module has a persisted `## Module N:` section; PDF extracted text contains all sections and body lines, or fails loudly)
    - Run the bug condition exploration tests from step 1 against the fixed code
    - **EXPECTED OUTCOME**: Tests PASS (confirms both content-loss paths are fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Already-Correct Recaps, Fitting PDFs, and Unrelated Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from step 2 against the fixed code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — byte-for-byte content, idempotent reconciliation, fitting PDFs, graceful degradation, unrelated hooks unchanged)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full pytest + Hypothesis suite (`fast`/`thorough` profiles) plus unit and integration tests
  - Confirm Property 1 (Bug Condition / Expected Behavior) tests pass and Property 2 (Preservation) tests pass
  - Run the full module-completion and track-completion integration flows: synchronous verified append, reconciliation backfills missing late modules, final PDF round-trips and contains every section and body line
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- **Test-first ordering is mandatory.** Tasks 1 and 2 are standalone and run BEFORE
  any fix. Task 1 (Property 1) MUST fail on unfixed code; task 2 (Property 2) MUST
  pass on unfixed code. Do not modify code to make task 1 pass before task 3.
- **Property 1** maps to the Bug Condition / Expected Behavior and validates
  Requirements 2.1–2.7. **Property 2** maps to Preservation and validates
  Requirements 3.1–3.5.
- **Tooling**: pytest + Hypothesis (`fast`/`thorough` profiles). Scripts are Python
  3.11+ stdlib-only; `fpdf2` is an optional, lazily-imported dependency — never
  import it at module top level and always preserve graceful degradation (Req 3.4).
- **Round-trip verification** means extracting text from the written PDF and
  asserting it contains every expected per-module section plus at least
  `MIN_BODY_LINES` body lines before reporting success.
- Files touched by the fix: `senzing-bootcamp/scripts/recap_pdf_render.py`,
  `generate_recap_pdf.py`, `generate_recap_pdf_inline.py`, `completion_artifacts.py`
  wiring, and `senzing-bootcamp/hooks/module-recap-append.kiro.hook`.
