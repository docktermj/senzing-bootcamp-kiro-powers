# Implementation Plan

## Overview

This plan remediates the failing "Lint Python (ruff)" CI gate (438 violations) using the bug-condition methodology. It establishes a baseline counterexample first, then applies the design's risk-ordered phases (A: correctness → B: safe auto-fixes → C: E402 triage → D: manual reflow/rename → E: documentation), re-running ruff and pytest after each phase so any regression localizes to the smallest change set. Property 1 (Fix Checking / Bug Condition) drives violations to 0 and resolves the 3 correctness defects; Property 2 (Preservation) keeps pytest at 0 failed with passing count ≥ 4,830.

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2"], "description": "Capture bug-condition and preservation baselines on unfixed code (parallel, independent)" },
    { "wave": 2, "tasks": ["3"], "description": "Phase A — correctness fixes (3.1 F811, 3.2 F601 individually; 3.3 full verify)", "dependsOn": ["1", "2"] },
    { "wave": 3, "tasks": ["4"], "description": "Phase B — safe auto-fixes (F841, W293)", "dependsOn": ["3"] },
    { "wave": 4, "tasks": ["5"], "description": "Phase C — E402 triage and suppression", "dependsOn": ["4"] },
    { "wave": 5, "tasks": ["6"], "description": "Phase D — manual reflow (E501) and rename (E741)", "dependsOn": ["5"] },
    { "wave": 6, "tasks": ["7"], "description": "Phase E — documentation reconciliation", "dependsOn": ["6"] },
    { "wave": 7, "tasks": ["8", "9"], "description": "Re-run baseline checks to confirm fix and preservation", "dependsOn": ["7"] },
    { "wave": 8, "tasks": ["10"], "description": "Final full-CI gate checkpoint", "dependsOn": ["8", "9"] }
  ]
}
```

- Tasks 1 and 2 (baseline capture) must complete before any fix.
- Phases A–E (tasks 3–7) are strictly sequential; each ends with ruff + pytest verification.
- Tasks 8–9 re-run the SAME baseline checks from tasks 1–2 to confirm the bug is resolved and preservation holds.
- Task 10 is the final full-CI checkpoint.

## Tasks

- [x] 1. Capture the bug-condition baseline (exploration — BEFORE any fix)
  - **Property 1: Bug Condition** - Ruff Gate Passes With Correctness Defects Resolved
  - **CRITICAL**: This step MUST surface failure on unfixed code — the failure confirms the bug exists
  - **DO NOT attempt to fix the code in this task** — only observe and document counterexamples
  - **GOAL**: Reproduce the documented counterexample and prove the 3 correctness defects empirically
  - Run the exact CI command on UNFIXED code: `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/ --statistics`
  - **EXPECTED OUTCOME**: ruff reports **438 violations** and exits non-zero, with per-code counts matching the design breakdown (E501=259, E402=141, F841=29, E741=5, F811=2, F601=1, W293=1)
  - Prove F811 shadowing: `python -m pytest senzing-bootcamp/tests/test_module_closing_question_ownership.py --collect-only -q` and confirm only one of each `test_module_07_no_inline_questions` / `test_module_07_no_wait_instructions` pair is collected (silent coverage loss)
  - Prove F601 dropped entry: inspect `senzing-bootcamp/tests/test_validate_module.py:55` and confirm key `6` resolves to the 3-lambda superset, proving the 2-lambda block was dropped
  - Confirm E402 legitimacy: inspect a sample of E402 sites to verify they are the documented `sys.path`-before-import pattern (validates the Phase C suppression decision)
  - Document the counterexamples found (438-violation baseline, the two shadowed tests, the dropped dict entry)
  - Mark complete when the baseline is captured, the defects are reproduced, and the counterexamples are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Capture the preservation baseline (BEFORE implementing fix)
  - **Property 2: Preservation** - Tests, Gates, and Script Runtime Unchanged
  - **IMPORTANT**: Follow observation-first methodology — record real behavior on UNFIXED code
  - Run the full suite on UNFIXED code: `python -m pytest senzing-bootcamp/tests/ tests/`
  - **EXPECTED OUTCOME**: `4830 passed, 86 skipped, 0 failed` (this is the baseline to preserve)
  - Observe and record the per-code violation counts from task 1 so the count can be tracked monotonically toward 0 after each phase
  - Spot-run representative scripts (e.g., `python senzing-bootcamp/scripts/validate_power.py`, `python senzing-bootcamp/scripts/measure_steering.py --check`) and record their output and exit codes as the runtime baseline
  - Confirm dependency posture on UNFIXED code: scripts are Python 3.11+ stdlib-only (PyYAML only in `validate_dependencies.py`)
  - Mark complete when the passing baseline (≥ 4,830 passed / 0 failed), script outputs, and dependency posture are recorded
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Phase A — Correctness fixes (highest risk, applied and verified individually)

  - [x] 3.1 Fix the 2 F811 redefinitions in `test_module_closing_question_ownership.py`
    - Inspect the duplicate block (lines ~270–287) against the original (lines ~250–267) and the `_AFFECTED_FILES` mapping before choosing the approach
    - **Default (byte-identical copy-paste, most likely):** delete the duplicate second block plus its stale `# -- Module 07: now Query and Visualize (was module-08) --` comment so the single surviving pair of tests runs normally
    - **Alternative (second block meant to test renamed content):** rename the second pair and repoint at the correct `_AFFECTED_FILES` key so both pairs assert distinct things
    - Verify: `python -m pytest senzing-bootcamp/tests/test_module_closing_question_ownership.py --collect-only -q` now shows two distinct, non-shadowing `test_module_07_no_*` tests
    - Verify: `python -m pytest senzing-bootcamp/tests/test_module_closing_question_ownership.py` passes
    - Verify: `ruff check senzing-bootcamp/tests/test_module_closing_question_ownership.py` reports no F811
    - _Bug_Condition: isBugCondition(X) where ruff reports F811 redefined-while-unused_
    - _Expected_Behavior: executes(test_module_07_no_inline_questions) AND executes(test_module_07_no_wait_instructions)_
    - _Preservation: 0 failed, passing count ≥ 4,830 (allow +up-to-2 delta from newly-running tests)_
    - _Requirements: 1.2, 2.2_

  - [x] 3.2 Fix the F601 duplicate dict key `6` in `test_validate_module.py:55`
    - Collapse the two `6:` entries to a single `6:` entry containing the 3-lambda superset (`loader.py`, `G2C.db`, `loading_strategy.md`); remove the 2-lambda block
    - Confirm against `validate_module.py` expectations that the module-6 fixture should include `loading_strategy.md`
    - Verify: `python -m pytest senzing-bootcamp/tests/test_validate_module.py` passes with the complete intended file set
    - Verify: `ruff check senzing-bootcamp/tests/test_validate_module.py` reports no F601
    - _Bug_Condition: isBugCondition(X) where ruff reports F601 multi-value-repeated-key-literal_
    - _Expected_Behavior: dictEntryForKey(test_validate_module, 6) is preserved (no intended value dropped)_
    - _Preservation: 0 failed, passing count ≥ 4,830_
    - _Requirements: 1.3, 2.3_

  - [x] 3.3 Verify Phase A with full ruff + pytest re-check
    - Run `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/ --statistics` — F811 (2) and F601 (1) gone; remaining count = 435
    - Run `python -m pytest senzing-bootcamp/tests/ tests/` — **0 failed**, passing count ≥ 4,830 (expect ~4,832 as the two shadowed tests now execute)
    - Confirm the +up-to-2 delta is the documented intended consequence, not a regression
    - _Requirements: 2.2, 2.3, 3.1_

- [x] 4. Phase B — Safe auto-fixes (F841 ×29, W293 ×1)
  - Run `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/ --fix` to apply ruff's **safe** fixes only
  - Review the diff to confirm only F841/W293 lines changed and no script logic was altered
  - Use `--unsafe-fixes` only on a per-occurrence basis after reviewing the diff (e.g., where an unused assignment wraps a side-effecting call)
  - Verify: `ruff check ... --statistics` shows F841 and W293 at 0 (remaining count = 405)
  - Verify: `python -m pytest senzing-bootcamp/tests/ tests/` — 0 failed, passing count ≥ 4,830
  - _Bug_Condition: isBugCondition(X) where ruff reports F841 / W293_
  - _Expected_Behavior: ruff reports no F841 or W293_
  - _Preservation: identical script runtime; 0 failed, passing ≥ 4,830; no new dependencies_
  - _Requirements: 2.4, 3.1, 3.3_

- [x] 5. Phase C — E402 module-import-not-at-top (×141)
  - Triage each E402 site: **legitimate** (documented `sys.path.insert(...)`-before-import pattern from `python-conventions.md`) vs **fixable** (import simply placed late and safe to move up)
  - For fixable cases: move the import to the top of the file
  - For legitimate whole-file cases: add a narrowly-scoped `[tool.ruff.lint.per-file-ignores]` entry in `pyproject.toml` (e.g., `"senzing-bootcamp/tests/*" = ["E402"]`), preferring explicit globs over a repo-wide ignore
  - For the small number of scripts where only one or two imports are affected: use per-line `# noqa: E402`
  - Document the chosen per-file-ignore vs `# noqa` mapping and rationale (tradeoff: per-file-ignore centralizes policy but suppresses E402 for all lines in the file; per-line noqa is precise but repeated)
  - Verify: `ruff check ... --statistics` shows E402 at 0 (remaining count = 264)
  - Verify: `python -m pytest senzing-bootcamp/tests/ tests/` — 0 failed, passing ≥ 4,830
  - _Bug_Condition: isBugCondition(X) where ruff reports E402_
  - _Expected_Behavior: ruff reports no E402 (via per-file-ignore and/or targeted # noqa for legitimate cases)_
  - _Preservation: scripts-as-modules imports still resolve; identical runtime; 0 failed; stdlib-only posture_
  - _Requirements: 2.4, 3.1, 3.3, 3.4_

- [x] 6. Phase D — Manual reflow and rename (E501 ×259, E741 ×5)
  - **E501**: manually reflow each line >100 chars to ≤100 — wrap calls/arguments, split long strings with implicit concatenation, break long comprehensions
  - **CRITICAL for scripts**: preserve exact runtime behavior — reflow source layout only; never change emitted string values or format output
  - **E741**: rename the 5 ambiguous single-char names (`l`, `I`, `O`) to descriptive names using `semantic_rename` so all references update consistently
  - Verify: `ruff check ... --statistics` shows E501 and E741 at 0 (remaining count = 0)
  - Verify: `python -m pytest senzing-bootcamp/tests/ tests/` — 0 failed, passing ≥ 4,830
  - Diff scripts to confirm only formatting changed, not logic; spot-run a representative script to confirm identical output
  - _Bug_Condition: isBugCondition(X) where ruff reports E501 / E741_
  - _Expected_Behavior: ruff reports no E501 or E741_
  - _Preservation: identical emitted strings/output; 0 failed, passing ≥ 4,830_
  - _Requirements: 2.4, 3.1, 3.3_

- [x] 7. Phase E — Reconcile documentation (no code change)
  - Record the remediation in the `[Unreleased]` section of `senzing-bootcamp/CHANGELOG.md`
  - Reconcile any stale "all CI green" claims in `POWER.md` that predate this fix
  - Confirm this changes documentation only — no script behavior altered
  - Verify: `python -m pytest senzing-bootcamp/tests/ tests/` — 0 failed (documentation edits do not affect tests)
  - _Preservation: identical script runtime; 0 failed, passing ≥ 4,830_
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 8. Verify bug condition is resolved (re-run exploration check)
  - **Property 1: Expected Behavior** - Ruff Gate Passes With Correctness Defects Resolved
  - **IMPORTANT**: Re-run the SAME commands from task 1 — do NOT write new checks
  - Run `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` exactly as CI runs it (no extra arguments)
  - **EXPECTED OUTCOME**: `All checks passed!`, **0 violations**, exit 0 (confirms the bug is fixed)
  - Confirm `pytest --collect-only` shows two distinct, non-duplicate `test_module_07_no_*` tests and both pass
  - Confirm the module-`6` fixture in `test_validate_module.py` contains the complete intended set and its dependent test passes
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 9. Verify preservation holds (re-run preservation check)
  - **Property 2: Preservation** - Tests, Gates, and Script Runtime Unchanged
  - **IMPORTANT**: Re-run the SAME baseline from task 2 — do NOT write new tests
  - Run `python -m pytest senzing-bootcamp/tests/ tests/`
  - **EXPECTED OUTCOME**: **0 failed**, passing count ≥ 4,830 (expect ~4,832 after Phase A)
  - Re-run the other CI gate scripts (or rely on the full CI run) and confirm all 13 still pass
  - Diff Phases B–D script changes to confirm only formatting changed, not logic; spot-run representative scripts to confirm output matches the task-2 baseline
  - Confirm no new third-party imports were introduced (stdlib-only, PyYAML only in `validate_dependencies.py`)
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 10. Checkpoint — Run the full CI gate sequence locally
  - Execute the gate sequence from `.github/workflows/validate-power.yml` locally in order
  - Confirm the "Lint Python (ruff)" step exits 0 with `All checks passed!`
  - Confirm the subsequent pytest step reports **0 failed** with passing count ≥ 4,830 (expect ~4,832 after Phase A)
  - Confirm the `[Unreleased]` CHANGELOG entry records the fix and no stale "all CI green" claim remains contradicted
  - Ensure all tests pass; ask the user if questions arise
  - _Requirements: 2.1, 3.1, 3.2_

## Notes

- **Property 1 (Fix Checking / Bug Condition)**: `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` reports 0 violations and exits 0, and the 3 correctness defects are resolved (both shadowed tests execute; dict key `6` preserved). Validated by tasks 1, 3, and 8.
- **Property 2 (Preservation)**: `python -m pytest senzing-bootcamp/tests/ tests/` reports 0 failed with passing count ≥ 4,830 (≈4,832 after Phase A), every other CI gate passes, scripts produce identical runtime output, and no new third-party dependency is added. Validated by tasks 2, 3.3, 4–7, and 9.
- **Expected passing delta**: the two F811 fixes cause two previously-shadowed tests to begin executing, raising the passing count by up to 2 (4,830 → ~4,832). This is intended, not a regression. The invariant is **0 failed** and passing ≥ 4,830.
- **Script safety**: everything under `senzing-bootcamp/` ships to users — Phases B–D change formatting only, never logic or emitted output. Diff and spot-run scripts to confirm.
- **Run all tests as single executions** (no watch mode). Run `ruff` and `pytest` from the repository root.

