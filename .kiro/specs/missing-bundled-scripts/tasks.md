# Implementation Plan

## Overview

This plan fixes the missing-bundled-scripts bug using the exploratory bugfix
workflow: explore (bug-condition tests before the fix), preserve (present-script
tests before the fix), implement (the four coordinated fix parts), then validate
(re-run both property sets). Tests use pytest + Hypothesis (Python 3.11+ stdlib
only; `fpdf2` lazily/optionally imported). Power tests live in
`senzing-bootcamp/tests/`; hook-invocation tests live in repo-root `tests/`.

- **Property 1 (Bug Condition / Fix Checking)**: for all missing-script
  invocations, the fixed system exits 0, emits no file-not-found error, and
  preserves the downstream effect (session event appended, recap PDF rendered
  when `fpdf2` present, else graceful Markdown-only degradation).
- **Property 2 (Preservation)**: for all present-script invocations, the fixed
  system behaves identically to the original.

## Tasks

- [x] 1. Write bug condition exploration tests (BEFORE implementing the fix)
  - **Property 1: Bug Condition** - Graceful Degradation and Self-Repair for Missing Scripts
  - **CRITICAL**: These tests MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the tests or the code when they fail**
  - **NOTE**: These tests encode the expected behavior - they will validate the fix when they pass after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists for missing-script invocations
  - **Tooling**: pytest + Hypothesis; Python 3.11+ stdlib only; `fpdf2` (`import fpdf`) lazily/optionally imported; place power tests in `senzing-bootcamp/tests/test_missing_bundled_scripts_exploration.py` and hook-invocation tests in repo-root `tests/test_missing_bundled_scripts_hook_exploration.py`
  - **Scoped PBT Approach**: Use a temp workspace with NO `senzing-bootcamp/scripts/` directory; generate inputs over the bug-condition domain (Hypothesis strategies for random module numbers / progress-file states, random recap Markdown bodies, and random sets of absent bundled scripts) so the property covers `FOR ALL X WHERE isBugCondition(X)` = `NOT fileExists(X.scriptPath)`
  - Bug Condition (from design): `isBugCondition(X)` returns true when a hook/step references `senzing-bootcamp/scripts/<name>.py` that does not exist in the workspace
  - The test assertions should match the Expected Behavior Properties (Property 1) from design: `result.exitCode == 0`, `NOT result.emittedFileNotFoundError`, and `downstreamEffectPreserved(X)`
  - Cover these exploratory cases from the design Testing Strategy:
    - Missing session logger: simulate the `session-log-events` runCommand when `log_write_event.py` is absent; assert a `{ts, action, module}` event is appended to `config/session_log.jsonl` (fails on unfixed code — no append, exit 2)
    - Missing recap generators with `fpdf2` present: run Step 0b with both `generate_recap_pdf.py` and `generate_recap_pdf_inline.py` absent; assert `docs/bootcamp_recap.pdf` is rendered from `docs/bootcamp_recap.md` (fails on unfixed code — no PDF)
    - Missing generic step script: invoke a step that shells out to an absent `senzing-bootcamp/scripts/<name>.py`; assert graceful degradation, no file-not-found error (fails on unfixed code)
    - Onboarding with absent scripts directory: run preflight with no scripts directory; assert a `warn` + self-repair result (may fail on unfixed code — no check)
    - Edge case — generators absent and `fpdf2` absent: run Step 0b; assert graceful Markdown-only degradation with a `pip install fpdf2` hint and no unhandled error (may already pass — informs the no-PDF path)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct - it proves the bug exists)
  - Document counterexamples found to confirm/refute the root-cause analysis, e.g. `python3: can't open file '.../log_write_event.py': [Errno 2] No such file or directory` (exit 2, no session event appended) and no `docs/bootcamp_recap.pdf` despite `fpdf2` being importable
  - Mark task complete when tests are written, run, and the failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Write preservation property tests (BEFORE implementing the fix)
  - **Property 2: Preservation** - Bundled Scripts Present
  - **IMPORTANT**: Follow observation-first methodology — run the UNFIXED code with present-script (non-bug-condition) inputs, record actual outputs, then assert those outputs
  - **Tooling**: pytest + Hypothesis; Python 3.11+ stdlib only; power tests in `senzing-bootcamp/tests/test_missing_bundled_scripts_preservation.py`, hook-invocation preservation in repo-root `tests/test_missing_bundled_scripts_hook_preservation.py`
  - **Why property-based**: Preservation is universal (`FOR ALL X WHERE NOT isBugCondition(X)` → `F(X) = F'(X)`); generate many present-script invocation/state combinations (varied module numbers, recap contents, present-script sets) to catch edge cases manual tests would miss
  - Observe behavior on UNFIXED code for present-script invocations and capture it as properties (from Preservation Requirements in design):
    - Bundled logger preservation: with `log_write_event.py` present, the bundled script is invoked and the recorded event matches the original (timestamp + current module read from `config/bootcamp_progress.json`, clamped 0–11) written to `config/session_log.jsonl`
    - Bundled recap generator preservation: with `generate_recap_pdf.py` present, Step 0b uses it first, then `generate_recap_pdf_inline.py` — preference order unchanged
    - Markdown-only degradation preservation: with generators absent and `fpdf2` absent, graceful Markdown-only degradation is unchanged (no unhandled error)
    - No-overwrite preservation: with valid scripts already present, onboarding materialization/verification leaves them byte-for-byte unchanged (idempotent, no clobber)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for missing bundled scripts (graceful degradation, self-repair, inline PDF path)

  - [x] 3.1 Onboarding materialization + preflight verification
    - Add a preflight check in `senzing-bootcamp/scripts/preflight.py` that verifies `senzing-bootcamp/scripts/` exists and contains the required scripts (`log_write_event.py`, `session_logger.py`, recap generators, etc.), emitting a `warn` (not `fail`) `CheckResult` with a remediation `fix` message when absent
    - Extend the `AutoFixer` so the scripts-directory check self-repairs under `--fix` (materialize/restore the bundled scripts directory) without overwriting already-present valid files (idempotent, no clobber)
    - Ensure onboarding runs this verification before any hook or step depends on the scripts directory
    - _Bug_Condition: isBugCondition(X) where NOT fileExists(X.scriptPath) for the scripts directory / required scripts_
    - _Expected_Behavior: Property 1 — exit 0, no file-not-found error, downstream effect preserved (scripts present/restored before use)_
    - _Preservation: Preservation Requirements 3.5 — already-present valid scripts left unchanged (no overwrite)_
    - _Requirements: 2.5, 3.5_

  - [x] 3.2 Session-logging graceful degradation (inline fallback)
    - Change `senzing-bootcamp/hooks/session-log-events.kiro.hook` so the `runCommand` no longer blindly runs `python3 .../log_write_event.py`: guard with an existence check and route to a self-contained inline appender when the bundled script is absent (or make the invocation path tolerant so a missing file results in exit 0 with the event still appended) — never a file-not-found error to the terminal
    - Inline fallback SHALL append a JSON event equivalent to the bundled output (`{ts, action, module}`, module read from `config/bootcamp_progress.json` clamped 0–11) to `config/session_log.jsonl`
    - Keep the hook JSON schema valid (`name`, `version`, `when`, `then`) and the prompt/command free of unescaped/injectable input, per hook-integrity and security rules
    - _Bug_Condition: isBugCondition(X) where NOT fileExists("senzing-bootcamp/scripts/log_write_event.py")_
    - _Expected_Behavior: Property 1 — exit 0, no file-not-found noise, session event still appended via inline fallback_
    - _Preservation: Preservation Requirements 3.1 — bundled log_write_event.py invoked unchanged when present_
    - _Requirements: 2.1, 2.2, 3.1_

  - [x] 3.3 Generic step degradation
    - Add a `fileExists` existence check before each bootcamp/onboarding step shells out to a bundled `senzing-bootcamp/scripts/<name>.py` (e.g. `preflight.py`, `install_hooks.py`, `completion_artifacts.py`, `status.py`, `backup_project.py`), using an inline/no-op fallback when absent rather than failing with a file-not-found error
    - _Bug_Condition: isBugCondition(X) where NOT fileExists(X.scriptPath) for a generic step script_
    - _Expected_Behavior: Property 1 — graceful degradation, exit 0, no file-not-found error_
    - _Preservation: Preservation Requirements 3.2 — present bundled step scripts execute unchanged with existing output_
    - _Requirements: 2.3, 3.2_

  - [x] 3.4 Self-contained inline recap-PDF path
    - In graduation Step 0b and `senzing-bootcamp/scripts/recap_pdf_render.py`, render `docs/bootcamp_recap.pdf` from `docs/bootcamp_recap.md` via the self-contained `recap_pdf_render.render_markdown_pdf` path when both bundled generators are absent (no dependency on a bundled generator file)
    - Preserve the existing preference order: bundled `generate_recap_pdf.py` first, then `generate_recap_pdf_inline.py`, then the file-independent inline path
    - Import `fpdf` lazily inside the render path only; when absent, degrade gracefully (retain Markdown recap, print `pip install fpdf2` hint), never import at module top level, never hard-fail
    - _Bug_Condition: isBugCondition(X) where both recap generators are absent (NOT fileExists)_
    - _Expected_Behavior: Property 1 — recap PDF rendered from Markdown when fpdf2 present, else graceful Markdown-only degradation_
    - _Preservation: Preservation Requirements 3.3, 3.4 — bundled generator preferred when present; Markdown-only degradation unchanged when fpdf2 absent_
    - _Requirements: 2.4, 3.3, 3.4_

  - [x] 3.5 Verify bug condition exploration tests now pass
    - **Property 1: Expected Behavior** - Graceful Degradation and Self-Repair for Missing Scripts
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - The tests from task 1 encode the expected behavior; when they pass, they confirm the expected behavior is satisfied
    - Run the bug condition exploration tests from step 1 on the fixed code
    - **EXPECTED OUTCOME**: Tests PASS (confirms the bug is fixed — exit 0, no file-not-found error, downstream effect preserved for all missing-script inputs)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Bundled Scripts Present
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from step 2 on the fixed code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — present-script invocations behave identically to the original)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full pytest + Hypothesis suite (power tests in `senzing-bootcamp/tests/`, hook tests in repo-root `tests/`)
  - Confirm both Property 1 (fix checking) and Property 2 (preservation checking) tests pass, plus unit and integration tests
  - Ensure all tests pass; ask the user if questions arise

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"],
      "description": "Write and run property-based tests on UNFIXED code: task 1 (bug condition) FAILS, task 2 (preservation) PASSES."
    },
    {
      "wave": 2,
      "tasks": ["3.1", "3.2", "3.3", "3.4"],
      "description": "Implement the four coordinated fix parts (independent of each other). Depends on wave 1.",
      "dependsOn": ["1", "2"]
    },
    {
      "wave": 3,
      "tasks": ["3.5", "3.6"],
      "description": "Re-run the SAME tests: Property 1 now PASSES, Property 2 still PASSES. Depends on all fix sub-tasks.",
      "dependsOn": ["3.1", "3.2", "3.3", "3.4"]
    },
    {
      "wave": 4,
      "tasks": ["4"],
      "description": "Checkpoint - full suite passes.",
      "dependsOn": ["3.5", "3.6"]
    }
  ]
}
```

- Tasks 1 and 2 must complete first (tests written and run on UNFIXED code: task 1 FAILS, task 2 PASSES).
- Fix sub-tasks 3.1–3.4 are independent of each other and can be done in any order; each maps to one of the four coordinated fix parts.
- Verification sub-tasks 3.5 and 3.6 require all of 3.1–3.4 complete (they re-run the tests from tasks 1 and 2).
- Task 4 requires 3.5 and 3.6 to pass.

## Notes

- Tasks 1 and 2 are STANDALONE property-based-test tasks placed BEFORE the fix,
  per the bugfix exploratory methodology.
- Property hover statuses: Property 1 (Bug Condition → Expected Behavior) and
  Property 2 (Preservation) — do not rename the `**Property N:**` headings.
- Tasks 3.5 and 3.6 re-run the SAME tests from tasks 1 and 2 — do not author new
  tests there.
- Honor workspace steering: Python 3.11+ stdlib only; `fpdf2` (`import fpdf`)
  optional and lazily imported inside the render path only; scripts in
  `senzing-bootcamp/scripts/`; hooks as `.kiro.hook` JSON with a valid schema
  (`name`, `version`, `when`, `then`) and no unescaped/injectable input; power
  tests in `senzing-bootcamp/tests/`, hook tests in repo-root `tests/`.
