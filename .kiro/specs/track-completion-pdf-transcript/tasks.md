# Implementation Plan: Track-Completion Recap PDF & Q&A Transcript

## Overview

Move recap-PDF and Q&A-transcript generation so it **always** runs at track completion, mirroring
the always-generate pattern already used for the completion summary and recap Markdown. This is
**primarily a steering re-sequencing** that reuses existing, tested scripts verbatim — no new
generation logic, no new hooks, no changes to any reused script's internals. The work touches two
steering files and adds a small, test-only reference model plus its tests.

`module-completion-track.md` gains a transcript reconciliation pass (`reconcile_transcript.py`)
after the existing recap Markdown reconciliation, then an **always-run** "Shareable Deliverables:
Recap PDF & Q&A Transcript" subsection (`generate_recap_pdf.py` + `generate_transcript.py`) that
runs independent of graduation acceptance and regardless of `skip_graduation`, non-blocking, with
the stale "produced later, in the graduation flow" note updated. `graduation.md` Step 0b gains an
idempotent-reuse note (overwrite in place, no conflicting duplicates) while its Step 0a/0b
reconcile-then-render safety nets are preserved.

Because the guarantees (ordering, idempotence, non-blocking) are pure, universally-quantified
statements over the flow's inputs, the tests include a pure Python **reference model** of the
completion/graduation sequence (`SequenceInput`/`SequenceResult`, `run_completion_sequence`/
`run_graduation_sequence`) with Hypothesis property tests (Properties 1–4), plus steering-content
tests that keep the shipped steering files in agreement with the model. All code targets Python
3.11+ stdlib only and follows the project script/test conventions; property tests draw their
example count from the registered Hypothesis profiles (no hand-set `max_examples`).

## Tasks

- [x] 1. Build the test-only reference model of the completion/graduation sequence
  - [x] 1.1 Create the reference model module with dataclasses and sequence functions
    - Create `senzing-bootcamp/tests/completion_sequence_model.py` (a pure test-only helper
      co-located with the tests, **not** shipped as a power script) with
      `from __future__ import annotations`, stdlib-only imports, the `Step` alias, and the
      `SequenceInput` and `SequenceResult` frozen dataclasses exactly as specified in the design's
      Components and Interfaces section
    - Implement `run_completion_sequence(inp) -> SequenceResult` modeling the
      `module-completion-track.md` order: `recap_reconcile` → `transcript_reconcile` →
      `recap_pdf`, `transcript_render`, then the graduation offer; renders are attempted
      regardless of `graduation_accepted` / `skip_graduation`; any step in `failing_steps` is
      still "attempted" and never aborts remaining steps (non-blocking); `fpdf2_available=False`
      suppresses only the `recap_pdf` artifact, never the ordering
    - Implement `run_graduation_sequence(inp) -> SequenceResult` modeling `graduation.md` Step
      0a/0b idempotent reuse (`recap_reconcile` → `recap_pdf`, `transcript_reconcile` →
      `transcript_render`, overwriting in place), performing no real I/O
    - Encode the ordering constraints in both functions: `index(recap_reconcile) <
      index(recap_pdf)` and `index(transcript_reconcile) < index(transcript_render)`
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2_

  - [x] 1.2 Write the input strategy and property test for always-generate at track completion
    - Add the `st_sequence_input()` custom strategy (random `graduation_accepted`,
      `skip_graduation`, `fpdf2_available`, and a random `failing_steps` subset of
      `{recap_reconcile, transcript_reconcile, recap_pdf, transcript_render}`) to
      `test_track_completion_pdf_transcript.py`
    - **Property 1: Recap PDF and transcript are always generated at track completion** — over
      `st_sequence_input()`, `run_completion_sequence` attempts both the `recap_pdf` and
      `transcript_render` steps for every flag combination, and produces
      `docs/bootcamp_recap.pdf` / `docs/bootcamp_transcript.md` when their steps do not fail
      (and `fpdf2` is available for the PDF)
    - **Validates: Requirements 1.1, 1.3**

  - [x] 1.3 Write property test for reconcile-then-render ordering in both flows
    - **Property 2: Reconcile-then-render ordering is preserved in both flows** — over
      `st_sequence_input()`, in the `executed` order of both `run_completion_sequence` and
      `run_graduation_sequence`, `recap_reconcile` precedes `recap_pdf` and
      `transcript_reconcile` precedes `transcript_render`
    - **Validates: Requirements 1.2, 2.2**

  - [x] 1.4 Write property test for idempotent graduation reuse
    - **Property 3: Graduation after track completion is idempotent — no conflicting duplicates**
      — over `st_sequence_input()`, running `run_completion_sequence` then
      `run_graduation_sequence` yields the same final artifact set as track completion alone, and
      the graduation reconciliation steps are no-ops on the already-consistent recap and log
    - **Validates: Requirements 2.1**

  - [x] 1.5 Write property test for non-blocking behavior under failure
    - **Property 4: Generation is non-blocking under any failure** — over `st_sequence_input()`
      with an arbitrary `failing_steps` subset (including `fpdf2_available=False`), the sequence
      still attempts every subsequent step in order and reaches the graduation offer, every
      artifact whose step did not fail is still produced, and the Markdown recap is retained when
      the recap PDF is skipped
    - **Validates: Requirements 3.1, 3.2**

  - [x] 1.6 Write unit / example tests for the reference model
    - Cover: exact executed order at track completion with graduation declined (recap_reconcile →
      transcript_reconcile → recap_pdf/transcript_render); `skip_graduation=True` still produces
      both renders while the graduation workflow is skipped; `fpdf2` absent skips the recap PDF,
      retains the Markdown recap, and still renders the transcript; idempotent reuse running
      completion then graduation yields a single overwritten copy of each deliverable with no
      conflicting duplicate paths
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.2_

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Re-sequence `module-completion-track.md` to always render deliverables
  - [x] 3.1 Add the transcript reconciliation pass, always-run render subsection, and note update
    - Edit `senzing-bootcamp/steering/module-completion-track.md`, keeping the existing
      `### Recap Reconciliation & Backfill (Path A final safety net)` section
      (`completion_artifacts.py --backfill`) unchanged as the first step
    - Add a transcript reconciliation pass (`reconcile_transcript.py`) after the recap
      reconciliation, mirroring graduation Step 0b.4's reconcile-before-render ordering
    - Add a `### Shareable Deliverables: Recap PDF & Q&A Transcript` subsection that **always**
      runs after both reconciliation passes and before the graduation offer, invoking
      `generate_recap_pdf.py` from the reconciled recap and `generate_transcript.py` from the
      reconciled session log; state it runs independent of graduation acceptance
      (Requirement 1.1) and regardless of `skip_graduation` (Requirement 1.3), and that it is
      non-blocking — on any failure or when `fpdf2` is absent, warn, point to
      `docs/bootcamp_recap.md`, and continue (Requirements 3.1, 3.2)
    - Update the stale note that reads the recap PDF is "produced later, in the graduation flow"
      to state the PDF and transcript are produced here at track completion, and that graduation
      re-runs the same reconcile-then-render as an idempotent safety net
    - Make no changes to any `postToolUse` write-tool hook, the `session-log-events` hook, or any
      reused script internals; preserve the existing `fpdf2` graceful degradation rather than
      duplicating it; use no external URLs
    - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2_

  - [x] 3.2 Write steering-content tests for `module-completion-track.md`
    - In `test_steering_module_completion.py`, assert the always-run render subsection exists and
      invokes both `generate_recap_pdf.py` and `generate_transcript.py` after the recap and
      transcript reconciliation passes, states it runs independent of graduation acceptance and
      regardless of `skip_graduation`, is marked non-blocking, and that the stale "produced
      later, in the graduation flow" note has been updated; assert no external URLs were
      introduced
    - _Requirements: 4.1_

- [x] 4. Add the idempotent-reuse note to `graduation.md`
  - [x] 4.1 Add the Step 0b idempotent-reuse note while preserving the safety nets
    - Edit `senzing-bootcamp/steering/graduation.md` to preserve Step 0a (recap reconciliation),
      Step 0b.3 (recap PDF render with its helper-first / inline-fallback / `fpdf2`
      graceful-degradation decision), and Step 0b.4 (transcript reconcile-then-render) exactly
      as the graduation-time safety nets (Requirement 2.2)
    - Add a short note at Step 0b clarifying that when track completion has already generated
      these deliverables, Step 0a/0b re-runs the same idempotent reconcile-then-render and
      **overwrites in place**, refreshing rather than duplicating them (no conflicting
      duplicates); moving generation earlier does not remove or skip the graduation-time
      reconciliation safety nets (Requirement 2.1)
    - _Requirements: 2.1, 2.2_

  - [x] 4.2 Write steering-content tests for `graduation.md`
    - In `test_steering_graduation.py`, assert Step 0a/0b (reconcile-then-render) are still
      present and that the idempotent-reuse note (overwrite in place, no conflicting duplicates)
      has been added
    - _Requirements: 4.2_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast` locally,
  `thorough` in CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/`, are class-based, and the reference model
  (`completion_sequence_model.py`) is a test-only helper — it is never shipped as a power script
  and performs no real I/O.
- Each property task references its property number and the requirement clause it validates for
  traceability; steering-content tests keep the shipped steering files in agreement with the
  model (Requirements 4.1, 4.2).
- No reused script internals change (`generate_recap_pdf.py`, `reconcile_transcript.py`,
  `generate_transcript.py`, `completion_artifacts.py`); the `fpdf2` graceful degradation is
  reused, not re-implemented; steering files contain no external URLs (power-distribution safety).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1", "4.1"] },
    { "id": 1, "tasks": ["1.2", "3.2", "4.2"] },
    { "id": 2, "tasks": ["1.3", "1.4"] },
    { "id": 3, "tasks": ["1.5", "1.6"] }
  ]
}
```
