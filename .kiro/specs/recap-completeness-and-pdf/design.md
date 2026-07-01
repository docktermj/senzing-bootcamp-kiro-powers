# Recap Completeness and PDF Bugfix Design

## Overview

The bootcamp recap deliverable consists of `docs/bootcamp_recap.md` and the PDF
rendered from it (`docs/bootcamp_recap.pdf`). Two related defects let the recap be
reported as successfully produced while it silently omits content — the most
dangerous failure mode, because exit-code and file-exists checks pass and the loss
is only visible when a human opens the file.

There are two content-loss paths:

1. **Missing per-module recap sections.** The `module-recap-append` agentStop hook
   appends a `## Module N:` section on boundary detection, but the append is
   unverified: a write that does not persist across a session boundary, or a hook
   that does not actually write on the final module, leaves the section silently
   absent. Track completion never reconciles `docs/bootcamp_recap.md` against
   `config/bootcamp_progress.json` `modules_completed`, so the gap survives into the
   final deliverable.

2. **PDF rendered only the outline.** The shared renderer draws cells with
   `multi_cell(0, ...)`, which derives width from the current x-position. After
   certain cells the x-position advances toward the right margin, so any line that
   needs to wrap raises `FPDFException: Not enough horizontal space to render a
   single character`. In `generate_recap_pdf.py` that exception is caught by a broad
   `except (OSError, Exception)` fallback and the run still reports success, so
   wrapping body lines vanish while short single-line headings survive.

The fix makes recap append synchronous and verified, reconciles and backfills the
recap at track completion using the existing `completion_artifacts.py` planner,
renders PDF cells at full width from the left margin (`set_x(l_margin)` then
`multi_cell(epw, ...)`), stops swallowing rendering exceptions, and verifies the
rendered PDF by round-tripping its text before reporting success. Correct behavior —
sections that already exist and persisted, idempotent reconciliation, PDFs whose
body content fits within width, graceful degradation when `fpdf2` is absent, and the
behavior of unrelated completion hooks — must be preserved.

## Glossary

- **Bug_Condition (C)**: The condition that triggers either content-loss path —
  a completed module lacking a verified recap section at append or track-completion
  time, OR a recap PDF whose body content is dropped during rendering while success
  is still reported.
- **Property (P)**: The desired behavior — every completed module has a persisted
  `## Module N:` section, and the rendered PDF contains all body lines (or fails
  loudly), with success reported only after verification.
- **Preservation**: Existing recap content kept byte-for-byte, idempotent
  reconciliation, PDFs that already fit rendering unchanged, graceful `fpdf2`-absent
  degradation, and unrelated hooks behaving exactly as before.
- **Recap_Append_Hook**: The `module-recap-append` agentStop hook in
  `senzing-bootcamp/hooks/module-recap-append.kiro.hook` that appends a
  `## Module N:` section on `modules_completed` boundary detection.
- **Reconciliation**: The track-completion step that compares
  `docs/bootcamp_recap.md` against `config/bootcamp_progress.json`
  `modules_completed` and backfills any missing per-module section, driven by the
  `completion_artifacts.py` planner (`plan_backfill` / `detect_artifact_gaps`).
- **Shared_Renderer**: `senzing-bootcamp/scripts/recap_pdf_render.py`, whose
  `render_heading`, `render_generic_blocks`, `render_markdown_body`, and
  `render_markdown_pdf` primitives currently call `multi_cell(0, ...)`.
- **Bundled_Generator**: `senzing-bootcamp/scripts/generate_recap_pdf.py`, whose
  `render_pdf` is wrapped by a broad `except (OSError, Exception)` in `main`.
- **Inline_Generator**: `senzing-bootcamp/scripts/generate_recap_pdf_inline.py`,
  the self-contained fallback that reuses the Shared_Renderer.
- **epw / l_margin**: fpdf2's effective page width and left margin; rendering a cell
  with `set_x(l_margin)` then `multi_cell(epw, ...)` guarantees full available width.
- **Round-trip verification**: Extracting text from the written PDF and asserting it
  contains the expected per-module sections and a minimum body-line count before
  reporting success.

## Bug Details

### Bug Condition

The bug manifests in two situations. **(A)** When a module is completed, the recap
append either does not persist or is never written (final-module hook miss), and
nothing verifies that a `## Module N:` heading exists in `docs/bootcamp_recap.md`,
so the section is silently absent and track completion does not reconcile it back.
**(B)** When the recap PDF is rendered, a body line wide enough to wrap raises
`FPDFException` because `multi_cell(0, ...)` derives width from an advanced
x-position; the exception is swallowed by a broad fallback, dropping the body line
while success is still reported.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type RecapDeliverableState
         { progress: BootcampProgress,        // modules_completed, step_history
           recapFile: MarkdownText,            // docs/bootcamp_recap.md content
           pdfRender: PdfRenderObservation }   // body lines emitted vs. dropped
  OUTPUT: boolean

  // Path A: a completed module has no persisted recap section, OR
  //         the recap was not reconciled against modules_completed.
  missingSection := EXISTS m IN input.progress.modules_completed
                    SUCH THAT NOT hasHeading(input.recapFile, m)   // "## Module m:"

  // Path B: the PDF render dropped a body line that should have been drawn,
  //         yet the generator reported success.
  droppedBodyLine := input.pdfRender.bodyLinesDropped > 0
                     AND input.pdfRender.reportedSuccess = TRUE

  RETURN missingSection OR droppedBodyLine
END FUNCTION
```

### Examples

- **Module 6 lost across session boundary**: `modules_completed` contains `6`, the
  append tool reported success in an earlier session, but `docs/bootcamp_recap.md`
  has no `## Module 6:` heading. Expected: the section is present (backfilled at
  track completion if needed). Actual: silently absent, success reported.
- **Final module hook miss**: Module 7 is marked complete, the Recap_Append_Hook
  fires on boundary detection but does not write the section. Expected: a
  `## Module 7:` section exactly as for any other module. Actual: absent; track
  graduation proceeds.
- **No track-completion reconciliation**: `modules_completed = [1..7]` but the recap
  has sections only for 1–5. Expected: reconciliation backfills 6 and 7. Actual: the
  gap remains in the final deliverable.
- **Outline-only PDF**: A `### Information Shared` bullet long enough to wrap raises
  `FPDFException: Not enough horizontal space to render a single character`; the
  `except (OSError, Exception)` in `generate_recap_pdf.py:main` swallows it. Expected:
  the bullet renders on its own wrapped lines. Actual: the bullet is dropped, only
  the heading survives, exit code 0 and the file exists so success is reported.
- **Edge case — already complete and consistent**: every completed module already
  has a persisted section and the PDF body fits within width. Expected: no changes,
  full render. This is NOT the bug condition.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- A per-module recap section that already exists and persisted SHALL be preserved
  byte-for-byte — no duplication, overwrite, or reordering out of chronological
  order (Req 3.1).
- Reconciliation that runs when the recap is already consistent with
  `modules_completed` SHALL be idempotent and make no spurious changes (Req 3.2).
- Recap PDF body content that already fits within available width SHALL continue to
  render all headings and body lines exactly as today (Req 3.3).
- When the optional `fpdf2` dependency is absent, the system SHALL continue to
  degrade gracefully — keep the Markdown output and print a `pip install fpdf2`
  hint — without raising (Req 3.4).
- Any other completion hook (celebration, journal entry, etc.) SHALL continue to
  behave exactly as before; this fix SHALL NOT alter their behavior (Req 3.5).

**Scope:**
All inputs that do NOT involve a missing/unverified recap section or a dropped PDF
body line should be completely unaffected by this fix. This includes:
- Recaps already consistent with `modules_completed`.
- PDF documents whose every body line fits the available width.
- Runs where `fpdf2` is not installed (graceful Markdown-only degradation).
- Execution of unrelated completion hooks.

**Note:** The expected correct behavior for buggy inputs is defined in the
Correctness Properties section (Property 1 and Property 2). This section focuses on
what must NOT change.

## Hypothesized Root Cause

Based on the bug description and the current code, the most likely issues are:

1. **Unverified, asynchronous recap append**: The Recap_Append_Hook
   (`module-recap-append.kiro.hook`) appends on `agentStop` boundary detection and
   reports success without reading back a `## Module N:` heading. A write that does
   not persist across a session boundary, or a hook invocation that does not write
   on the final module, leaves the section absent with no detection.
   - The hook is the *sole* producer of the section; there is no synchronous,
     verified append in the module-completion workflow.

2. **No track-completion reconciliation**: Nothing compares
   `docs/bootcamp_recap.md` against `config/bootcamp_progress.json`
   `modules_completed` at track completion. `completion_artifacts.py` already
   computes `missing_recap` (via `detect_artifact_gaps`) and a `plan_backfill`, but
   the completion workflow does not consume the plan to actually backfill sections.

3. **Width-deriving `multi_cell(0, ...)` in the Shared_Renderer**: In
   `recap_pdf_render.py`, `render_heading`, `render_generic_blocks`,
   `render_markdown_body`, and `render_markdown_pdf` call `multi_cell(0, ...)`
   without first resetting x to the left margin. fpdf2 derives the cell width from
   the current x; after a cell that advances x toward the right margin, a wrapping
   line has too little horizontal space and raises `FPDFException`.

4. **Broad exception swallowing in the Bundled_Generator**: `generate_recap_pdf.py`
   `main` wraps `render_pdf` in `except (OSError, Exception)` and returns 1 only as a
   message — but partial output already written plus exit/file checks elsewhere let
   "success" be reported while body lines were dropped. The broad catch hides the
   real `FPDFException` rather than failing loudly.

5. **No artifact verification before reporting success**: Neither generator
   round-trips the written PDF to confirm it contains the expected per-module
   sections and a minimum body-line count; success is inferred from exit code and
   file existence only.

## Correctness Properties

Property 1: Bug Condition - Recap Completeness and Full PDF Body

_For any_ recap deliverable state where the bug condition holds (isBugCondition
returns true), the fixed system SHALL produce a recap in which every module in
`modules_completed` has a persisted `## Module N:` section AND a PDF whose extracted
text contains every expected per-module section and all body lines — or, if a
rendering failure occurs, SHALL fail loudly rather than reporting success with
dropped content. Recap append SHALL be synchronous and verified, and track
completion SHALL reconcile and backfill the recap against `modules_completed`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

Property 2: Preservation - Already-Correct Recaps, Fitting PDFs, and Unrelated Behavior

_For any_ input where the bug condition does NOT hold (isBugCondition returns false),
the fixed system SHALL produce the same result as the original system, preserving
existing recap content byte-for-byte, keeping reconciliation idempotent, rendering
already-fitting PDF bodies identically, degrading gracefully when `fpdf2` is absent,
and leaving the behavior of unrelated completion hooks unchanged.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming the root cause analysis is correct, the fix touches the renderer, the two
generators, the reconciliation wiring, and the append hook.

**File**: `senzing-bootcamp/scripts/recap_pdf_render.py`

**Functions**: `render_heading`, `render_generic_blocks`, `render_markdown_body`,
`render_markdown_pdf`

**Specific Changes**:
1. **Full-width cells from the left margin**: Before every `multi_cell` call that
   currently passes width `0`, reset x to the left margin and pass the effective
   page width — `pdf.set_x(pdf.l_margin)` then `pdf.multi_cell(pdf.epw, ...)`. This
   guarantees wrapping always has full horizontal space and never raises
   `FPDFException` for fitting content (Req 2.5).
2. **Preserve `write`-based list/Q&A indentation**: `render_list_items` and the
   Q&A path use `set_x(l_margin + 6)` + `write(...)`; keep their indentation but
   ensure they cannot leave x near the right margin for the next cell.

**File**: `senzing-bootcamp/scripts/generate_recap_pdf.py`

**Function**: `render_pdf`, `main`

**Specific Changes**:
3. **Stop swallowing rendering exceptions**: Replace the broad
   `except (OSError, Exception)` so a genuine rendering failure (e.g.
   `FPDFException`) is not silently absorbed — log/fail loudly and return a non-zero
   exit, never reporting success after dropping content (Req 2.6). Keep the
   `ImportError` branch (graceful `fpdf2`-absent degradation) intact (Req 3.4).
4. **Round-trip verification before success**: After `pdf.output(...)`, re-open the
   PDF, extract its text, and assert it contains a `Module N` section for each
   completed module plus at least a minimum body-line count. Only print
   `PDF generated:` and return 0 when verification passes (Req 2.7).

**File**: `senzing-bootcamp/scripts/generate_recap_pdf_inline.py`

**Function**: `generate_inline`

**Specific Changes**:
5. **Mirror loud-failure and verification**: Since the Inline_Generator reuses the
   Shared_Renderer, it inherits the width fix; add the same round-trip verification
   and loud-failure behavior so the fallback path cannot report success on a
   body-dropped PDF (Req 2.6, 2.7), while keeping the `fpdf2`-absent hint (Req 3.4).

**File**: `senzing-bootcamp/hooks/module-recap-append.kiro.hook` and the
module-completion workflow

**Specific Changes**:
6. **Synchronous, verified append**: Perform the recap append as a synchronous step
   of module completion (not solely via the agentStop hook) and verify a
   `## Module N:` heading for the just-completed module exists in
   `docs/bootcamp_recap.md`, retrying/backfilling if absent, before reporting
   success (Req 2.1, 2.2). The final module of a track is appended exactly as any
   other; graduation/celebration must not suppress it (Req 2.3).
7. **Track-completion reconciliation**: At track completion, run
   `completion_artifacts.py --plan`, consume `recap_modules` from the
   `BackfillPlan`, and backfill any missing per-module section so every completed
   module has a `## Module N:` section (Req 2.4). Because `plan_backfill` returns a
   pure set difference, re-running on a consistent recap yields an empty plan and no
   changes (Req 3.2). Existing sections are appended-around, never rewritten
   (Req 3.1).

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples
that demonstrate the bug on unfixed code, then verify the fix works correctly and
preserves existing behavior. Property-based tests (pytest + Hypothesis, per the
repo's `fast`/`thorough` profiles) drive both fix checking and preservation
checking.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the
fix. Confirm or refute the root-cause analysis. If we refute, we re-hypothesize.

**Test Plan**: Build recap states and PDF inputs that trigger each path, run them
against the UNFIXED renderer/generators and the current (no-reconciliation)
completion flow, and assert the failures.

**Test Cases**:
1. **Wrapping body line drops** (will fail on unfixed code): Render a recap whose
   `### Information Shared` bullet is long enough to wrap; assert the generated PDF's
   extracted text is missing that bullet while the heading survives, and that the
   generator still reported success.
2. **Swallowed FPDFException** (will fail on unfixed code): Confirm the broad
   `except (OSError, Exception)` in `generate_recap_pdf.py` absorbs the
   `FPDFException` so the run does not fail loudly.
3. **Missing section, no reconciliation** (will fail on unfixed code): With
   `modules_completed = [1..7]` and a recap containing only sections 1–5, confirm no
   step backfills 6 and 7.
4. **Final-module append miss** (may fail on unfixed code): Simulate the
   Recap_Append_Hook not writing the last module's section and confirm completion
   proceeds with the section absent.

**Expected Counterexamples**:
- Extracted PDF text missing wrapping body lines while headings remain.
- `modules_completed` entries with no corresponding `## Module N:` heading after
  track completion.
- Possible causes: `multi_cell(0, ...)` width derivation, broad exception swallow,
  absent reconciliation, unverified append.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed system
produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  // Path A: recap completeness
  reconciledRecap := completeAndReconcile(input.progress, input.recapFile)
  FOR ALL m IN input.progress.modules_completed DO
    ASSERT hasHeading(reconciledRecap, m)            // "## Module m:" present
  END FOR

  // Path B: full PDF body or loud failure
  result := generateRecapPdf_fixed(reconciledRecap)
  ASSERT result.failedLoudly
         OR (containsAllSections(extractText(result.pdf), input.progress.modules_completed)
             AND bodyLineCount(extractText(result.pdf)) >= MIN_BODY_LINES)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed
system produces the same result as the original system.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT reconcile_original(input) = reconcile_fixed(input)        // idempotent, byte-for-byte
  ASSERT extractText(renderPdf_original(input)) = extractText(renderPdf_fixed(input))
  ASSERT fpdfAbsentBehavior_original(input) = fpdfAbsentBehavior_fixed(input)
  ASSERT unrelatedHookBehavior_original(input) = unrelatedHookBehavior_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking
because:
- It generates many recap/PDF inputs automatically across the input domain.
- It catches edge cases (already-consistent recaps, exactly-fitting body lines) that
  manual unit tests might miss.
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: Observe behavior on UNFIXED code first for already-consistent recaps,
fitting PDFs, `fpdf2`-absent runs, and unrelated hooks, then write property-based
tests capturing that behavior.

**Test Cases**:
1. **Existing section preservation**: Observe that a recap already containing all
   sections is unchanged on unfixed code; verify reconciliation leaves it
   byte-for-byte identical and in chronological order after the fix (Req 3.1).
2. **Idempotent reconciliation**: Observe that `plan_backfill` returns an empty plan
   for a consistent recap; verify re-running reconciliation makes no changes
   (Req 3.2).
3. **Fitting-PDF preservation**: Observe that a recap whose body fits within width
   renders all headings and body lines on unfixed code; verify the fixed renderer
   produces equivalent extracted text (Req 3.3).
4. **fpdf2-absent degradation**: Observe the `pip install fpdf2` hint and preserved
   Markdown on unfixed code; verify the fixed code degrades identically without
   raising (Req 3.4).
5. **Unrelated-hook preservation**: Verify celebration/journal hooks behave exactly
   as before the fix (Req 3.5).

### Unit Tests

- Renderer: a single long line wraps within `epw` from `l_margin` and never raises
  `FPDFException`; headings and prose render at full width.
- Generator: round-trip verification fails (non-zero exit) when a body line is
  missing; succeeds when all sections and the minimum body-line count are present.
- Generator: a rendering exception fails loudly rather than being swallowed.
- Reconciliation: `detect_artifact_gaps` / `plan_backfill` return correct
  `missing_recap` for a recap missing modules 6 and 7.
- Reconciliation: empty plan for an already-consistent recap (idempotence).

### Property-Based Tests

- Generate random `modules_completed` sets and recap contents; assert that after
  reconciliation every completed module has a `## Module N:` section (fix checking).
- Generate random recap body content (varying line widths) and assert the fixed
  renderer's extracted PDF text contains every body line, or fails loudly
  (fix checking).
- Generate already-consistent recaps and fitting PDF bodies and assert the fixed
  output equals the original output (preservation checking).

### Integration Tests

- Full module-completion flow: complete a module, assert the recap append is
  synchronous and verified, then generate the PDF and round-trip its text.
- Track-completion flow with a recap missing late modules: assert reconciliation
  backfills the missing sections and the final PDF contains every section and body
  line.
- Final-module completion: assert the last module's section is appended exactly as
  any other and graduation does not suppress it; confirm unrelated hooks still run
  unchanged.
