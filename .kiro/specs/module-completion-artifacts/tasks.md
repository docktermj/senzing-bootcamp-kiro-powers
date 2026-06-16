# Implementation Plan

## Overview

This plan fixes the module-completion artifact generation bug using the two-phase bugfix
methodology from the design's Testing Strategy: first reproduce the bug with exploration
tests on the unfixed code (Property 1), capture baseline behavior with preservation tests
(Property 2), then implement the stdlib-only `completion_artifacts.py` planner plus
hook/steering alignment, and finally re-run the exploration tests (fix checking) and
preservation tests (preservation checking) before validating with property-based and
integration tests.

## Tasks

- [x] 1. Write bug condition exploration tests (BEFORE implementing the fix)
  - **Property 1: Bug Condition** - Complete artifact coverage for every completed module
  - **CRITICAL**: These tests MUST FAIL on the unfixed code/state - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: These tests encode the expected behavior - they will validate the fix when they pass after implementation
  - **GOAL**: Surface counterexamples that confirm or refute the four hypothesized root causes from the design
  - Create `senzing-bootcamp/tests/test_module_completion_artifacts_exploration.py`
  - Construct progress states + on-disk artifact inventories mirroring the reported defect (`modules_completed: [1..7]`, gate `7_complete: completed`, partial recap/journal/certificate sets, placeholder Durations) per the Bug Condition `isBugCondition(input)` formal spec in design
  - **Scoped PBT Approach**: For the deterministic reported state, scope assertions to the concrete failing cases below for reproducibility; broaden to property-based generation in task 5
  - Test case 1 — Final-module recap missing (Cause 1): completed `[1..7]`, recap has Modules 1–6 only → assert a Module 7 recap section is expected (fails on unfixed flow)
  - Test case 2 — Journal/certificate not bound to trigger (Cause 2): journal has `[3,6,7]`, certificates `[6,7]` → assert entries/certificates for all 7 modules (fails on unfixed flow)
  - Test case 3 — Placeholder per-module Duration (Cause 3): recap Module 3 Duration is `Module 3 session` while `step_history["3"].updated_at` and the prior timestamp are valid ISO 8601 → assert a real computed elapsed time (fails on unfixed flow)
  - Test case 4 — Placeholder Total Duration (Cause 3): header `Total Duration` is a placeholder while reliable per-module timing exists → assert a real cumulative time (fails on unfixed flow)
  - Test case 5 — No backfill mechanism (Cause 4): partial artifact set with no trigger → assert backfill fills the gap (fails on unfixed flow)
  - Test case 6 — Edge case, unreliable timing: `step_history["4"]` missing/unparseable → assert the Module 4 `### Duration` field is omitted, not a placeholder
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., "Module 7 recap section absent", "Duration reads `Module 3 session` instead of computed elapsed time", "certificates present only for `[6,7]`") to confirm which root causes hold
  - Mark task complete when tests are written, run, and failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2. Write preservation property tests (BEFORE implementing the fix)
  - **Property 2: Preservation** - Non-buggy inputs are unchanged
  - **IMPORTANT**: Follow observation-first methodology - observe behavior on the UNFIXED flow first, then encode it
  - Create `senzing-bootcamp/tests/test_module_completion_artifacts_preservation.py`
  - Observe and record unfixed-flow behavior for non-buggy inputs (cases where `isBugCondition` returns false), then assert those observed outputs
  - Test case 1 — No-new-entry no-op: `modules_completed` unchanged → assert no recap/journal/certificate output (Req 3.5)
  - Test case 2 — Byte-for-byte preservation: append to an existing recap/journal → assert all prior bytes are identical after the operation (Req 3.1)
  - Test case 3 — Question-pending deferral: `config/.question_pending` present → assert no artifact output (Req 3.4)
  - Test case 4 — Default name: preferences missing or `name` absent → assert `"Bootcamper"` used in headers (Req 3.7)
  - Test case 5 — Non-blocking errors: simulate a write failure → assert a warning is logged and the flow continues in the fixed step order `progress_update, recap_append, journal_entry, completion_certificate, next_step_options` (Req 3.2, 3.3)
  - Test case 6 — Celebration read-only: assert the `module-completion-celebration` hook writes no files (Req 3.6)
  - Use Hypothesis to generate non-buggy progress states / artifact inventories (empty `modules_completed`, missing files, `.question_pending` present, already-complete sets with real Durations) and assert no-op / preservation across the input domain
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3. Fix module-completion artifact generation (planner module + hook/steering alignment)

  - [x] 3.1 Create the stdlib-only planner module `completion_artifacts.py`
    - Create `senzing-bootcamp/scripts/completion_artifacts.py` following the project script pattern: shebang, module docstring with usage, `from __future__ import annotations`, dataclasses, `argparse`-based `main(argv=None)`, exit 0/1, Python 3.11+ stdlib only (no third-party deps)
    - Implement `compute_module_duration(step_history, started_at, module, prior_timestamp) -> str | None`: lower bound = prior module `updated_at` (or `started_at` for the first module), upper bound = `step_history[str(module)].updated_at`; parse with `datetime.fromisoformat` normalizing trailing `Z` to `+00:00`; return `None` if either bound is missing/unparseable/`end < start`; otherwise format the `timedelta` (e.g., `1h 12m`, `2d 3h`)
    - Implement `compute_total_duration(step_history, started_at, modules_completed) -> str | None`: roll up per-module elapsed times in ascending order; return `None` when no reliable timing; guarantee monotonic non-decrease
    - Implement `detect_artifact_gaps(modules_completed, inventory) -> ArtifactGapReport`: per-type sorted missing-module lists; uniform-certificate rule (if any certificate exists, every completed module requires one)
    - Implement `plan_backfill(progress_state, inventory) -> BackfillPlan`: deterministic, idempotent, set-difference-only plan combining gap detection with duration computation (never re-emit existing artifacts)
    - Implement `isBugCondition(progress_state, inventory, recap_durations, recap_total) -> bool` mirroring the formal spec (coverage gap OR non-uniform certificates OR placeholder duration OR placeholder total), with `isPlaceholder(text)` and `reliableTiming(...)` helpers
    - Implement `main(argv=None)` CLI: `--progress`, `--recap`, `--journal`, `--progress-dir` inputs; `--check` prints the gap/placeholder report and exits 1 when `isBugCondition` is true (CI-friendly); `--plan` emits the backfill plan as JSON
    - _Bug_Condition: isBugCondition(input) from design (coverage gap, non-uniform certificates, placeholder duration, placeholder total)_
    - _Expected_Behavior: expectedBehavior — complete uniform artifact set with real Durations computed from step_history (or omitted when unreliable) from design_
    - _Preservation: Preservation Requirements from design (byte-for-byte content, step order, deferral, no duplicates, celebration read-only, default name)_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

  - [x] 3.2 Align the recap-append hook to use the planner and fire on the final module
    - Edit `senzing-bootcamp/hooks/module-recap-append.kiro.hook` (and mirror text in `steering/hook-registry-modules.md`)
    - Replace the LLM-derived "Duration" step with one that obtains per-module Duration and cumulative `Total Duration` from `completion_artifacts.py` (reading `step_history`/`started_at`); when the helper returns no value, OMIT the `### Duration` field and the header `Total Duration` rather than writing a placeholder
    - Ensure boundary detection here also fires for the final module of a track (track completion must not suppress the per-module recap section)
    - Preserve byte-for-byte append and non-blocking error-handling constraints; validate hook JSON schema (`name`, `version`, `when`, `then`) before writing
    - _Bug_Condition: isBugCondition true via coverage-gap (final module) and placeholder-duration clauses_
    - _Expected_Behavior: recap section appended for every new modules_completed entry with real/omitted Duration from design_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Bind journal entry, certificate, and backfill to the shared trigger in steering
    - Edit `senzing-bootcamp/steering/module-completion.md`
    - Bind `journal_entry` and `completion_certificate` to the same boundary-detection trigger as `recap_append` so all four artifacts fire together on every new `modules_completed` entry (including the final module)
    - Add a backfill step: on a completion boundary, run `completion_artifacts.py --plan` and generate missing artifacts for already-completed modules, applying certificates uniformly
    - Source the certificate `Time Spent` and recap Duration from `completion_artifacts.py`; omit the field when timing is unreliable
    - Keep the fixed step order, non-blocking error handling, `.question_pending` deferral, the no-new-entry no-op, and the `"Bootcamper"` default unchanged
    - _Bug_Condition: isBugCondition true via coverage-gap and non-uniform-certificate clauses_
    - _Expected_Behavior: uniform certificates and journal entries for all completed modules; backfill completes the set without duplication from design_
    - _Preservation: step order, deferral, no-op, default name unchanged from design_
    - _Requirements: 2.4, 2.5, 2.6, 3.3, 3.4, 3.5, 3.7_

  - [x] 3.4 Confirm the celebration hook does not suppress the per-module path
    - Edit `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook` as needed
    - Make no behavioral change to the celebration itself (it must remain read-only and write no files)
    - Ensure the track-completion branch does not suppress the per-module artifact path for the final module
    - _Preservation: celebration hook remains read-only, writes no files (Req 3.6)_
    - _Requirements: 3.6_

  - [x] 3.5 Write unit tests for the planner module
    - Create `senzing-bootcamp/tests/test_module_completion_artifacts_unit.py`
    - `compute_module_duration`: valid bounds → formatted elapsed time; missing/unparseable/out-of-order bounds → `None`; first module uses `started_at` as lower bound
    - `compute_total_duration`: roll-up correctness; `None` when no reliable timing; monotonic non-decrease
    - `detect_artifact_gaps`: correct per-type missing-module lists; uniform-certificate rule
    - `plan_backfill`: idempotency (re-running on a complete set yields an empty plan); set-difference only
    - `isBugCondition`: each clause (coverage gap, non-uniform certificates, placeholder duration, placeholder total) toggles the result as specified
    - Run unit tests on the fixed code
    - **EXPECTED OUTCOME**: Tests PASS
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

  - [x] 3.6 Verify bug condition exploration tests now pass (fix checking)
    - **Property 1: Expected Behavior** - Complete artifact coverage for every completed module
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - The tests from task 1 encode the expected behavior; when they pass, they confirm the bug is fixed
    - Run `senzing-bootcamp/tests/test_module_completion_artifacts_exploration.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms recap/journal/certificate present for all completed modules including Module 7, real or omitted Durations, uniform certificates, backfill closes gaps)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 3.7 Verify preservation tests still pass (preservation checking)
    - **Property 2: Preservation** - Non-buggy inputs are unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run `senzing-bootcamp/tests/test_module_completion_artifacts_preservation.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions: no spurious artifacts, byte-for-byte content, invariant step order, deferral, celebration read-only, default name)
    - Confirm all tests still pass after the fix
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4. Write property-based tests for the correctness properties
  - Create `senzing-bootcamp/tests/test_module_completion_artifacts_properties.py` (pytest + Hypothesis)
  - **Property 1 / 6** - Generate random `modules_completed` subsets and artifact inventories; assert `plan_backfill` always yields a plan that completes the set with no duplicates (set difference only)
  - **Property 3** - Generate random valid/invalid `step_history` timestamp maps; assert `compute_module_duration` returns a parseable elapsed time exactly when bounds are valid/ordered, and `None` otherwise
  - **Property 4** - Generate increasing sequences of completed modules; assert `compute_total_duration` is monotonically non-decreasing and omits (returns `None`) rather than placeholders when unreliable
  - **Property 5** - Generate states with non-uniform certificates; assert the backfill plan yields a certificate for every completed module or none at all (never a partial subset)
  - **Property 2 (preservation)** - Generate states where `isBugCondition` is false; assert the fixed flow output equals the original (no change)
  - Run property-based tests on the fixed code
  - **EXPECTED OUTCOME**: All properties hold
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 3.5_

- [x] 5. Write integration tests for the full completion flow
  - Create `senzing-bootcamp/tests/test_module_completion_artifacts_integration.py`
  - Final module of a track (Module 7 Core, Module 11 Advanced): assert recap section, journal entry, and certificate all appear, and `validate_completion_artifacts.py` passes
  - Backfill on a project mirroring the reported state (`[1..7]` complete, partial artifacts): assert the artifact set is complete and consistent afterward
  - Context switching across modules then completing: assert correct per-module Durations and a monotonic `Total Duration`, with omission on modules lacking reliable timestamps
  - Run integration tests on the fixed code
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 6. Checkpoint - Ensure all tests pass
  - Run the full power test suite (`pytest` in `senzing-bootcamp/tests/`) plus repo-level hook tests
  - Run `validate_power.py`, `sync_hook_registry.py --verify`, and `measure_steering.py --check` to confirm hook/steering changes are consistent with CI
  - Ensure all tests pass; ask the user if questions arise
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"],
      "description": "Write exploration tests (fail on unfixed code) and preservation tests (pass on unfixed code) before any fix."
    },
    {
      "wave": 2,
      "tasks": ["3.1"],
      "description": "Create the stdlib-only completion_artifacts.py planner module that the hooks/steering and tests depend on."
    },
    {
      "wave": 3,
      "tasks": ["3.2", "3.3", "3.4", "3.5"],
      "description": "Align recap-append hook, bind journal/certificate/backfill in steering, verify celebration hook, and add planner unit tests (all depend on 3.1)."
    },
    {
      "wave": 4,
      "tasks": ["3.6", "3.7"],
      "description": "Fix checking (re-run exploration tests, now pass) and preservation checking (re-run preservation tests, still pass)."
    },
    {
      "wave": 5,
      "tasks": ["4", "5"],
      "description": "Property-based tests (Hypothesis) and integration tests against the fixed flow."
    },
    {
      "wave": 6,
      "tasks": ["6"],
      "description": "Checkpoint: run the full suite plus CI validators."
    }
  ]
}
```

- Tasks 1 and 2 are independent and must be completed before task 3 (write tests first).
- Task 3.1 (planner) must precede 3.2/3.3/3.5 (they depend on the planner API).
- Tasks 3.6 and 3.7 depend on the fix tasks 3.1–3.4 being complete.
- Tasks 4 and 5 depend on the fix (task 3) being complete.
- Task 6 depends on all prior tasks.

## Notes

- Exploration tests (task 1) MUST fail on unfixed code; preservation tests (task 2) MUST
  pass on unfixed code. Do not implement the fix until both baselines are recorded.
- Tasks 3.6 and 3.7 re-run the SAME tests from tasks 1 and 2 — do not author new tests.
- All Python is Python 3.11+ stdlib only (no third-party deps); tests use pytest + Hypothesis
  and live in `senzing-bootcamp/tests/`.
- Hook JSON changes must keep a valid schema (`name`, `version`, `when`, `then`) and the
  celebration hook must remain read-only.
- Run test commands with a single-execution flag (e.g., `pytest` without watch mode); start
  long-running processes manually rather than from the agent.
