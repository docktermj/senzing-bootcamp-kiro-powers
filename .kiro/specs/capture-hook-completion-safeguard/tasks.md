# Implementation Plan: Capture-Hook Completion Safeguard

## Overview

Implement `senzing-bootcamp/scripts/capture_hook_safeguard.py`, a stdlib-only detection-and-decision
script that runs at each module-completion boundary, detects any absent Capture_Critical_Hook, and
returns a decision the completion steering renders: a silent no-op when all three hooks are present,
or a recurring, overridable Soft_Block reminder (never a Mandatory_Gate) when any are missing. The
script reuses `install_hooks.CAPTURE_CRITICAL` as the single source of truth for the three hook ids
and the two canonical install options, so it can never drift from the session-start
Warn_On_Absence_Check. It is non-blocking by contract and adds no `preToolUse` write-tool hook.

Work proceeds bottom-up: scaffolding and dataclasses first, then the pure detection functions
(`detect_missing_capture_hooks`, `outputs_for_hook`), then the decision builders (`build_reminder`,
`should_reprompt`), then the acknowledgment writer (`record_acknowledgment`), then the orchestrating
`main` with non-blocking error handling, then the module-completion steering wiring (no new hook),
and finally the property tests (Properties 1–5), example/consistency tests, and the repo-root
architecture guardrail test. All code targets Python 3.11+ stdlib only and follows the project
script/test conventions.

## Tasks

- [x] 1. Scaffold the safeguard script
  - [x] 1.1 Create `capture_hook_safeguard.py` skeleton and dataclasses
    - Create `senzing-bootcamp/scripts/capture_hook_safeguard.py` with shebang,
      `from __future__ import annotations`, module docstring with usage examples, stdlib-only
      imports, and the `sys.path` insertion needed to import `install_hooks` (scripts are not a
      package) so `install_hooks.CAPTURE_CRITICAL` is the single source of the three ids
    - Define the frozen `MissingHook` dataclass (`hook_id: str`, `outputs: tuple[str, ...]`) and the
      `ReminderPlan` dataclass (`missing: list[MissingHook]`, `install_options: tuple[str, str]`,
      `is_noop: bool`, `is_soft_block: bool`) exactly as specified in the design's Components section
    - Add the `HOOK_OUTPUTS` mapping (module-recap-append → recap; session-log-events → transcript,
      completion summary; ask-bootcamper → transcript, completion summary) and the two canonical
      install-option strings from the design's Data Models section
    - Add an `argparse`-based `main(argv=None) -> int` stub with `--hooks-dir` (default
      `.kiro/hooks`), `--progress` (default `config/bootcamp_progress.json`), `--record-ack`, and
      `--module N` options and an `if __name__ == "__main__": main()` entry point
    - _Requirements: 3.2_

- [x] 2. Implement detection functions
  - [x] 2.1 Implement `detect_missing_capture_hooks` and `outputs_for_hook`
    - Implement `detect_missing_capture_hooks(hooks_dir: Path) -> list[str]`: for each id in
      `install_hooks.CAPTURE_CRITICAL`, check for an `<id>.kiro.hook` file in `hooks_dir` and return
      the sorted ids whose file is absent; a missing/unreadable directory yields all three ids;
      presence of unrelated `*.kiro.hook` files never affects the result (never raises)
    - Implement `outputs_for_hook(hook_id: str) -> tuple[str, ...]`: map a capture-critical id to its
      non-empty outputs via the `HOOK_OUTPUTS` table
    - _Requirements: 1.1, 1.2_

  - [x] 2.2 Write property test for detection naming
    - **Property 1: Detection names exactly the missing capture-critical hooks and the outputs they
      feed** — for any `.kiro/hooks` directory holding an arbitrary subset of the three
      capture-critical hooks plus arbitrary unrelated `*.kiro.hook` files, `detect_missing_capture_hooks`
      returns exactly the absent capture-critical ids and `build_reminder` reports each with a
      non-empty output list drawn from {recap, transcript, completion summary}
    - Add the `st_hooks_dir_state()` custom strategy (synthetic empty files in a temp `.kiro/hooks`)
    - **Validates: Requirements 1.1, 1.2**

- [x] 3. Implement the decision builders
  - [x] 3.1 Implement `build_reminder` and `should_reprompt`
    - Implement `build_reminder(missing_ids: list[str]) -> ReminderPlan`: for an empty `missing_ids`
      set `is_noop=True`, `is_soft_block=False`, empty `missing`; otherwise set `is_noop=False`,
      `is_soft_block=True`, one `MissingHook` per id (with its outputs), and the two canonical
      install options
    - Implement `should_reprompt(missing_ids: list[str], progress: dict) -> bool`: return `True`
      whenever `missing_ids` is non-empty, independent of any acknowledgment recorded in `progress`
      (an acknowledgment authorizes the current transition but never suppresses a future reminder)
    - _Requirements: 1.2, 1.3, 2.1, 2.3, 2.4_

  - [x] 3.2 Write property test for the all-present silent no-op
    - **Property 2: All hooks present is a silent no-op** — for any `.kiro/hooks` directory
      containing all three capture-critical hooks (plus any unrelated hook files),
      `detect_missing_capture_hooks` returns the empty list and `build_reminder` yields a plan with
      `is_noop` true, `is_soft_block` false, and no missing entries
    - **Validates: Requirements 1.3**

  - [x] 3.3 Write property test for the overridable Soft_Block
    - **Property 3: A missing hook always yields an overridable Soft_Block with both install
      options** — for any non-empty set of missing capture-critical hooks, `build_reminder` yields a
      plan with `is_soft_block` true (never a Mandatory_Gate) carrying exactly the two canonical
      install options
    - Add the `st_missing_set()` custom strategy (a non-empty subset of the three ids)
    - **Validates: Requirements 2.1, 2.4**

  - [x] 3.4 Write property test for recurring, never-suppressed re-prompt
    - **Property 5: The reminder recurs at every boundary while a hook stays missing and is never
      suppressed** — for any non-empty missing set and any prior acknowledgment history in progress
      (including repeated acknowledgments of the same ids), `should_reprompt` returns true
    - Add the `st_progress_mapping()` custom strategy (well-formed progress dicts, optionally
      pre-seeded with prior `capture_hook_safeguard.acknowledgments`)
    - **Validates: Requirements 2.3, 2.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the acknowledgment writer
  - [x] 5.1 Implement `record_acknowledgment`
    - Implement `record_acknowledgment(progress_path: Path, module: int, missing_ids: list[str]) ->
      dict`: read `config/bootcamp_progress.json` (starting from an empty mapping when missing or
      unreadable), append exactly one entry (module, sorted acknowledged ids, ISO-8601 timestamp) to
      the `capture_hook_safeguard.acknowledgments` list, write the updated mapping back, and return
      it; preserve all pre-existing progress keys and values unchanged
    - Write to `config/bootcamp_progress.json` only — do not introduce a new file
    - _Requirements: 2.2_

  - [x] 5.2 Write property test for acknowledgment recording
    - **Property 4: An explicit override records an acknowledgment and permits the transition** — for
      any existing progress mapping and any non-empty missing set, `record_acknowledgment` appends
      exactly one acknowledgment entry (module, acknowledged ids, timestamp) to
      `capture_hook_safeguard.acknowledgments`, preserves all pre-existing progress keys byte-for-byte
      in value, and returns a state in which the transition is permitted
    - **Validates: Requirements 2.2**

- [x] 6. Implement `main` orchestration with non-blocking error handling
  - [x] 6.1 Wire detect → build_reminder → render/record in `main`
    - In `main`, resolve `--hooks-dir`, run `detect_missing_capture_hooks`, build the `ReminderPlan`,
      and print the plan (missing hooks, the outputs each feeds, and the two install options) or
      nothing when it is a no-op; when `--record-ack` is set, call `record_acknowledgment` with
      `--module`
    - Defer (produce no output) when `config/.question_pending` exists at the boundary, consistent
      with the artifact steps' defer-when-pending rule
    - Wrap the body in a top-level guard that, on any exception (missing/unreadable hooks dir,
      progress read/write failure, unexpected error), warns to stderr and returns without raising;
      return 0 on a clean run/no-op and 1 only on an internally handled error path (the steering
      treats the step as non-blocking regardless of exit code)
    - _Requirements: 1.3, 2.4_

  - [x] 6.2 Write unit tests for detection, no-op, recurrence, and override
    - Detection of each individual missing hook — three focused examples, each with exactly one
      capture-critical hook absent, asserting that hook and its outputs are named
    - All-present silent no-op — a concrete directory with all three present asserts `is_noop` and
      no output
    - Recurring re-prompt across multiple boundaries — simulate three successive boundaries with a
      hook still missing and prior acknowledgments recorded; assert the reminder fires each time
    - Explicit-override continue path — record an acknowledgment and assert the entry lands in
      progress and the transition proceeds
    - _Requirements: 4.1, 4.2_

  - [x] 6.3 Write consistency example test (single source of truth)
    - Assert the safeguard's capture-critical set equals `install_hooks.CAPTURE_CRITICAL` and its
      presented install options match the two canonical options offered by the session-start
      Warn_On_Absence_Check
    - _Requirements: 3.2_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Wire the safeguard into the module-completion steering (no new hook)
  - [x] 8.1 Add the safeguard step to the module-completion boundary steering
    - Edit `senzing-bootcamp/steering/module-completion.md` so the boundary runs
      `capture_hook_safeguard.py`, renders the `ReminderPlan` (silent no-op when all present; a
      single live `👉` Soft_Block pending question naming missing hooks, outputs, and the two install
      options when any are absent), and — on an explicit continue — re-invokes it with `--record-ack`
      before allowing the module transition; document that the step is non-blocking regardless of
      exit code and defers when `config/.question_pending` exists
    - Make no changes to any `preToolUse` write-tool hook and no changes to the capture-critical hook
      files; preserve the session-start Warn-on-Absence check text verbatim
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.3_

  - [x] 8.2 Write example test that the Warn-on-Absence check is preserved
    - Assert `senzing-bootcamp/steering/session-resume-phase2-setup-recovery.md` still contains the
      Capture-Critical Warn-on-Absence Check and its advisory-only / never-blocks language
    - _Requirements: 3.1_

- [x] 9. Repo-root architecture guardrail
  - [x] 9.1 Write the architecture-guardrail test (repo-root `tests/`)
    - In repo-root `tests/test_capture_hook_safeguard_architecture.py`, scan every `*.kiro.hook`;
      assert no `preToolUse` write-tool hook references the safeguard and that the feature adds no new
      write-tool hook; assert the three capture-critical hook files are unchanged by this feature
    - _Requirements: 3.3_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Script-behavior tests (properties + unit) live in `senzing-bootcamp/tests/` (suggested
  `test_capture_hook_safeguard.py`); tests that validate real hook files on disk live in repo-root
  `tests/` (suggested `test_capture_hook_safeguard_architecture.py`).
- Tests are class-based and import scripts via the `sys.path` convention; fixtures are synthetic and
  PII-free (power-distribution safety rule).
- Each property task references its property number and the requirement clause it validates for
  traceability.
- The safeguard reuses `install_hooks.CAPTURE_CRITICAL` and the two canonical install options as the
  single source of truth; `install_hooks.py` and the capture-critical hooks are unchanged.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1", "5.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "5.2", "6.1"] },
    { "id": 4, "tasks": ["6.2", "6.3", "8.1"] },
    { "id": 5, "tasks": ["8.2", "9.1"] }
  ]
}
```
