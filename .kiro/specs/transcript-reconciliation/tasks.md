# Implementation Plan: Transcript Reconciliation

## Overview

Implement `senzing-bootcamp/scripts/reconcile_transcript.py`, a stdlib-only pre-render pass that
repairs Q&A transcript shortfalls from the enforced recap source before `generate_transcript.py`
renders. The script reads the recap (via the existing `generate_recap_pdf.parse_recap_markdown`),
counts logged `question` events against recap QR pairs per module, and — on a material shortfall —
backfills paired `question`/`answer` completion events using the existing `session_logger`
writers. The pass is idempotent, non-blocking, and adds no write-tool hook.

Work proceeds bottom-up: scaffolding and dataclasses first, then the pure counting/planning
functions (each with a property test placed right after implementation), then the backfill writer
and orchestrating `main`, then the graduation steering wiring, and finally the end-to-end
integration test. All code targets Python 3.11+ stdlib only and follows the project script/test
conventions.

## Tasks

- [x] 1. Scaffold the reconciliation script
  - [x] 1.1 Create `reconcile_transcript.py` skeleton and dataclasses
    - Create `senzing-bootcamp/scripts/reconcile_transcript.py` with shebang,
      `from __future__ import annotations`, module docstring with usage examples, stdlib-only
      imports, and the `sys.path` insertion needed to import `generate_recap_pdf`,
      `session_logger`, and `generate_transcript` (scripts are not a package)
    - Define the `ModuleCounts`, `ModuleShortfall`, and `ReconcilePlan` dataclasses exactly as
      specified in the design's Components section
    - Add an `argparse`-based `main(argv=None) -> int` stub with `--recap` and `--log` options
      defaulting to the canonical paths (`docs/bootcamp_recap.md`, `config/session_log.jsonl`)
      and an `if __name__ == "__main__": main()` entry point
    - _Requirements: 2.4_

- [x] 2. Implement source-counting functions
  - [x] 2.1 Implement `count_logged_questions` and `count_recap_pairs`
    - Implement `count_logged_questions(log_path: str) -> dict[int, int]`: a tolerant JSONL scan
      (never raises; skips blank/malformed lines) returning per-module `question`-event counts,
      reusing the line-skipping approach from `generate_transcript.read_events`
    - Implement `count_recap_pairs(recap_doc) -> dict[int, int]`: count `qr_pairs` per
      `module_number` from a parsed `RecapDocument`
    - _Requirements: 1.1_

  - [x] 2.2 Write property test for accurate per-module counts
    - **Property 1: Accurate per-module counts** — for any generated recap and session log with
      known per-module tallies (including interspersed malformed/blank lines), both counters
      return exactly those per-module tallies
    - Add `st_recap_document()` and `st_session_log(recap)` custom strategies (synthetic,
      PII-free content) in the test module
    - **Validates: Requirements 1.1**

- [x] 3. Implement the shortfall predicate and plan builder
  - [x] 3.1 Implement `is_material_shortfall` and `build_plan`
    - Implement `is_material_shortfall(logged: int, recap: int) -> bool` using the per-module
      `max(0, recap - logged) > 0` deficit rule
    - Implement `build_plan(logged: dict[int, int], recap_doc) -> ReconcilePlan`: compute
      per-module shortfalls with derived missing `(question, response)` pairs in recap order
      (modules ascending, pairs in document order); set `is_noop=True` when the total deficit is
      zero; set `recap_has_qr=False` when the recap contributes zero QR pairs across all modules
    - _Requirements: 1.2, 1.3, 3.3_

  - [x] 3.2 Write property test for plan-equals-deficit
    - **Property 2: Plan equals the per-module deficit** — for any per-module logged/recap counts,
      the plan's total missing pairs equals `sum(max(0, recap(N) - logged(N)))` and `is_noop` is
      true iff that sum is zero
    - **Validates: Requirements 1.2, 1.3**

  - [x] 3.3 Write property test for the no-QR-content no-op
    - **Property 5: A recap with no QR content is a no-op** — for any recap with no QR content
      across all modules, the plan reports `recap_has_qr` false and yields no shortfalls
    - **Validates: Requirements 3.3**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the backfill writer
  - [x] 5.1 Implement `apply_plan`
    - Implement `apply_plan(plan: ReconcilePlan, log_path: str) -> int`: for each shortfall in
      module order, mint `qid = session_logger.generate_question_id()`, build paired
      `question`/`answer` entries via `session_logger.build_completion_entry` (question data
      `{"text", "question_id"}`, answer data `{"text", "question_id"}` sharing the same `qid`),
      and append question-then-answer via `session_logger.append_completion_entry`; return the
      number of pairs backfilled
    - Do not introduce a new schema or writer — reuse only the `session_logger` functions
    - _Requirements: 2.1, 2.4_

  - [x] 5.2 Write property test for schema conformance and pairing
    - **Property 4: Backfilled events conform to the existing schema and pair correctly** — every
      appended event is a valid `question`/`answer` completion entry, and re-reading with the
      existing `generate_transcript` reader pairs each backfilled question to its answer via
      `question_id`, increasing the answered-pair count by exactly the number of backfilled pairs
    - **Validates: Requirements 2.1, 2.4**

- [x] 6. Implement `main` orchestration with non-blocking error handling
  - [x] 6.1 Wire read → plan → apply in `main`
    - In `main`, read the recap (`generate_recap_pdf.parse_recap_markdown`) and log counts, call
      `build_plan`, and call `apply_plan` when the plan is neither a no-op nor `recap_has_qr` false
    - Wrap the body in a top-level guard that, on any exception (missing/unreadable recap,
      corrupt Markdown, missing/malformed log, write failure), logs a warning to stderr and
      returns without raising; return 0 on clean run/no-op and 1 only on an internally handled
      error path
    - Treat a missing/unreadable recap as zero recap QR pairs (`recap_has_qr=False`, no-op) so the
      subsequent render proceeds on the existing log
    - _Requirements: 1.3, 3.2, 3.3_

  - [x] 6.2 Write property test for idempotence
    - **Property 3: Reconciliation is idempotent** — for any recap and log, running the pass then
      running it again leaves the log identical to its post-first-run state and the second run's
      plan is a no-op
    - **Validates: Requirements 1.3**

  - [x] 6.3 Write property test for warn-and-continue on malformed input
    - **Property 8: Any malformed input warns and continues** — for any malformed/unreadable recap
      or session log, `main` never raises, returns to its caller, and leaves the log readable by
      the transcript renderer
    - **Validates: Requirements 3.2**

  - [x] 6.4 Write unit tests for `main` behavior
    - Cover: shortfall detection on hand-built consistent/short/over-logged logs; backfill from a
      small fixed recap asserting exact backfilled content and ordering; idempotent no-op on an
      already-consistent log; warn-and-continue on a missing recap file and on an OS/permission
      error (assert a warning is emitted and no exception escapes)
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.2_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Wire reconciliation into the graduation steering flow
  - [x] 8.1 Add the reconcile step to `graduation.md` Step 0b.4
    - Edit `senzing-bootcamp/steering/graduation.md` so Step 0b.4 invokes
      `reconcile_transcript.py` immediately before `generate_transcript.py`, mirroring how Step 0a
      reconciles the recap before the recap PDF; document that the step is non-blocking regardless
      of exit code and that the render always runs afterward
    - Make no changes to any `postToolUse` write-tool hook and no changes to the
      `session-log-events` hook (preserve the no-per-write-cost architecture)
    - _Requirements: 2.2, 2.3, 3.1_

  - [x] 8.2 Write architecture-guardrail tests
    - Assert the feature adds no `postToolUse` write-tool hook and does not modify the
      `session-log-events` hook, and that `graduation.md` Step 0b.4 invokes `reconcile_transcript`
      immediately before `generate_transcript.py`
    - _Requirements: 2.2, 2.3, 3.1_

- [x] 9. End-to-end reconciliation and rendering
  - [x] 9.1 Write property test for the reconciled render ordering
    - **Property 6: Reconciled transcript renders at least N pairs in module order** — for any
      recap with N QR pairs, reconciling against an empty/short log then rendering yields at least
      N answered pairs whose text matches the recap, grouped by module in ascending module order
    - **Validates: Requirements 2.1, 5.2**

  - [x] 9.2 Write property test for secret redaction
    - **Property 7: Secrets in reconciled content are redacted** — add an
      `st_secret_bearing_response()` strategy; for any recap response embedding a
      token/key/connection-string, the reconciled-and-rendered transcript contains the redaction
      placeholder and not the original secret value
    - **Validates: Requirements 4.1**

  - [x] 9.3 Write the end-to-end integration test
    - Wire the real recap parser, real `session_logger`, real `reconcile_transcript`, and real
      `generate_transcript` render against a temp workspace: seed a recap + empty log, run
      reconcile, run render, and assert the resulting `bootcamp_transcript.md` contains the
      recap's Q&A grouped by module. Use synthetic, PII-free fixtures only
    - _Requirements: 4.2, 5.1, 5.2_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/` (suggested `test_reconcile_transcript.py`), are
  class-based, and import scripts via the `sys.path` convention.
- Each property task references its property number and the requirement clause it validates for
  traceability.
- All fixtures are synthetic and PII-free (Requirement 4.2); reuse the existing
  `generate_transcript` redaction rather than adding new redaction logic (Requirement 4.1).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "5.1"] },
    { "id": 4, "tasks": ["5.2", "6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3", "6.4", "8.1"] },
    { "id": 6, "tasks": ["8.2", "9.1", "9.2", "9.3"] }
  ]
}
```
