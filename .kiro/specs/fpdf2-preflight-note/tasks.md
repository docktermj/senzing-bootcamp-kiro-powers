# Implementation Plan: fpdf2 Preflight Note

## Overview

Implement `senzing-bootcamp/scripts/fpdf2_preflight.py`, a tiny stdlib-only helper that surfaces a
single, non-blocking informational note at Track_Completion — *before* any PDF render is attempted —
telling a bootcamper that installing the optional `fpdf2` dependency will produce a PDF (and that the
Markdown output is produced regardless), including the exact command `pip install fpdf2`. The note
appears **only** when `fpdf2` is not importable and is suppressed entirely when it is present. The
gating decision and note text are pure functions (`fpdf2_available()`, `preflight_note()`) driven by
a thin `main()` CLI; availability is detected exactly as the PDF scripts do (a guarded `import fpdf`
treating `ImportError` as absent), and `fpdf` is never imported at module top level.

Work proceeds bottom-up: scaffold the script (module note constant, argparse `main` stub, no
top-level `import fpdf`), then the pure `fpdf2_available()` detector (with its property test right
after), then the pure `preflight_note()` gate and content (with its property tests), then the
non-blocking `main()` (with its totality property test and example tests), then the graduation /
track-completion steering wiring, and finally the structural / no-regression / placement guardrail
tests. All code targets Python 3.11+ stdlib only and follows the project script/test conventions;
the existing PDF scripts are not modified.

## Tasks

- [x] 1. Scaffold the preflight helper script
  - [x] 1.1 Create `fpdf2_preflight.py` skeleton and note constant
    - Create `senzing-bootcamp/scripts/fpdf2_preflight.py` with shebang,
      `from __future__ import annotations`, module docstring with usage examples, stdlib-only
      imports, and **no top-level `import fpdf`**
    - Define a module-level note constant holding the single-line Preflight_Note text (no embedded
      newline) that states installing `fpdf2` enables the PDF, that the Markdown output is produced
      regardless, and contains the exact substring `pip install fpdf2` — a single source of truth
      shared by the note function and the tests
    - Add an `argparse`-based `main(argv=None) -> int` stub and an `if __name__ == "__main__":
      main()` entry point that always returns 0
    - _Requirements: 1.2, 2.3_

- [x] 2. Implement availability detection
  - [x] 2.1 Implement `fpdf2_available`
    - Implement `fpdf2_available() -> bool`: wrap `import fpdf` in `try/except ImportError`,
      returning `True` on success and `False` on `ImportError`, mirroring the detection used by the
      PDF scripts (`ensure_fpdf2` / the lazy `from fpdf import FPDF`)
    - Confine the `import fpdf` to the function body so importing `fpdf2_preflight` never requires
      `fpdf2` and `fpdf` is never a top-level or hard dependency
    - _Requirements: 2.3, 3.2_

  - [x] 2.2 Write property test for availability detection
    - **Property 3: Availability detection agrees with the real import outcome** — for any
      monkeypatched `import fpdf` outcome, `fpdf2_available()` returns `True` when `import fpdf`
      would succeed and `False` when it raises `ImportError`
    - Add an `st_availability()` custom strategy and helpers that control the `import fpdf` outcome
      via `sys.modules` / a `sys.meta_path` finder (stub `fpdf` module = available; rejecting finder
      = absent), the same technique the existing recap-PDF degradation tests use
    - **Validates: Requirements 3.2**

- [x] 3. Implement the note gate and content
  - [x] 3.1 Implement `preflight_note`
    - Implement `preflight_note() -> str | None` as a pure function of `fpdf2_available()`: return
      `None` when `fpdf2` is available (no noise), and return the module note constant (a single
      line) when `fpdf2` is absent
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 3.2 Write property test for the gating decision
    - **Property 1: A note is produced exactly when fpdf2 is unavailable** — for any availability
      state, `preflight_note()` returns `None` when `fpdf2` is importable and a single non-empty
      line when it is not (note present iff `fpdf2` unavailable)
    - **Validates: Requirements 1.1, 1.3**

  - [x] 3.3 Write property test for the absent-branch note content
    - **Property 2: The absent-branch note states both facts and the exact install command** — for
      any environment where `fpdf2` is unavailable, `preflight_note()` returns a single line
      (contains no newline) communicating that installing `fpdf2` enables the PDF, that the Markdown
      output is produced regardless, and containing the exact substring `pip install fpdf2`
    - **Validates: Requirements 1.1, 1.2**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the non-blocking `main`
  - [x] 5.1 Implement `main` output and exit behavior
    - Implement `main(argv=None) -> int`: call `preflight_note()`; when it returns a string, print
      that single line to stdout; when it returns `None`, print nothing. Never read stdin, never
      prompt or pause, and always return 0
    - _Requirements: 2.1, 1.3_

  - [x] 5.2 Write property test for totality and non-blocking behavior
    - **Property 4: The helper is total and non-blocking across all import outcomes** — for any
      `import fpdf` outcome (including a forced unexpected error), `fpdf2_available()` returns a
      `bool`, `preflight_note()` returns `str | None`, and `main()` returns `0` — each without
      prompting, pausing, or raising
    - **Validates: Requirements 2.1**

  - [x] 5.3 Write unit tests for the absent and present branches
    - Absent branch (concrete): with `fpdf` forced unimportable, `preflight_note()` equals the
      module note constant and contains `pip install fpdf2`, and `main` prints exactly that one line
      and returns 0 (capture stdout)
    - Present branch (concrete): with a stub `fpdf` in `sys.modules`, `preflight_note()` is `None`
      and `main` prints nothing and returns 0
    - _Requirements: 1.1, 1.2, 1.3, 2.1_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Wire the preflight note into the steering flow
  - [x] 7.1 Add the preflight invocation to the graduation and track-completion steering
    - Edit `senzing-bootcamp/steering/graduation.md` so `python3
      senzing-bootcamp/scripts/fpdf2_preflight.py` is invoked immediately before Step 0b (Recap PDF
      Generation): surface the printed line if any, otherwise continue silently; document that the
      step is non-blocking regardless of exit code and the PDF render always runs afterward
    - Edit `senzing-bootcamp/steering/module-completion-track.md` so the same invocation runs at
      Track_Completion before the completion-summary PDF / export offer, with the same non-blocking,
      surface-if-printed behavior
    - Introduce no external URLs (only the `pip install fpdf2` command string); make no changes to
      any `postToolUse` write-tool hook and do not modify the PDF scripts
    - _Requirements: 2.2, 2.3, 3.1_

  - [x] 7.2 Write structural, no-regression, and placement guardrail tests
    - Lazy/optional import (Req 2.3): importing `fpdf2_preflight` succeeds while `fpdf` is
      unimportable, and a structural scan of the module source finds no top-level `import fpdf`
    - No-regression of PDF degradation (Req 2.2): the helper neither imports nor modifies
      `generate_recap_pdf` / `generate_completion_summary`, and their existing degradation behavior
      is untouched
    - Steering placement (Req 3.1): assert `graduation.md` invokes `fpdf2_preflight` immediately
      before Step 0b (Recap PDF Generation) and `module-completion-track.md` invokes it before the
      completion-summary / export offer
    - _Requirements: 2.2, 2.3, 3.1, 4.1, 4.2_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/test_fpdf2_preflight_note.py`, are class-based, and import
  scripts via the `sys.path` convention.
- Availability is controlled without installing/uninstalling `fpdf2` by monkeypatching the
  `import fpdf` outcome (stub module in `sys.modules` = available; a rejecting `sys.meta_path`
  finder / `builtins.__import__` shim = absent).
- Each property task references its property number and the requirement clause it validates for
  traceability.
- All fixtures are synthetic and PII-free (Requirement 4.2); the existing PDF scripts are not
  modified and no external URLs are introduced in the steering.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "5.1"] },
    { "id": 4, "tasks": ["3.3", "7.1"] },
    { "id": 5, "tasks": ["5.2"] },
    { "id": 6, "tasks": ["5.3"] },
    { "id": 7, "tasks": ["7.2"] }
  ]
}
```
