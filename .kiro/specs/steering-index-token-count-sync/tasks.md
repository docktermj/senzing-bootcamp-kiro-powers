# Implementation Plan

## Overview

This bugfix extends `senzing-bootcamp/scripts/measure_steering.py` so both its `--check`
(validation) path and its update/write path additionally process every **phase entry** in
`steering-index.yaml` — any `modules.*.phases.*`, `onboarding.*.phases.*`, or
`session-resume.*.phases.*` block that has a `file:` and a `token_count:`. Today those phase
counts have silently drifted out of sync with the authoritative `file_metadata` counts (in one
case by 2.6x — `module-03-phase2-visualization.md`: stored 2035 vs measured 5312) because the
script validates and rewrites only the `file_metadata` block and never inspects the `phases` map.

The fix is narrow: it touches only `phases.*.token_count` and the dependent
`phases.*.size_category`. All `file_metadata` behavior, the `budget` block (incl.
`split_threshold_tokens`), the `keywords`/`languages`/`deployment` maps, and each module's
`root`/`step_range`/structure are preserved unchanged. All new helpers reuse the script's
existing stdlib-only, regex/line-based string manipulation — **no PyYAML, no MCP URLs**. The
corrected `steering-index.yaml` is produced **by running the fixed update mode**, not by
hand-editing, so the tool and the data agree by construction.

Two new property-based test files (pytest + Hypothesis, stdlib + Hypothesis only, per
`python-conventions.md`) validate the fix: an exploration suite (Property 1 — Fix Checking)
authored to FAIL on the unfixed code, and a preservation suite (Property 2 — Preservation
Checking) authored to PASS on the unfixed code. The bug condition mirrors `bugfix.md`/`design.md`:

```python
# isBugCondition(X): only phase entries (with a file + token_count) can be buggy.
#   measured = round(len(read_text(X.file)) / 4)
#   bug      = abs(X.token_count - measured) / max(measured, 1) > 0.10
```

## Tasks

- [x] 1. Write bug condition exploration test (Fix Checking)
  - **Property 1: Bug Condition** - Phase Token Counts Reconciled and Validated
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate phase `token_count` values have drifted beyond the 10% tolerance and that `--check` does not detect it today
  - **Scoped PBT Approach**: For the synthetic-fixture and live-index assertions use concrete cases; use Hypothesis to enumerate the phase-entry / drift input space (`@settings(max_examples=20)`)
  - Create `senzing-bootcamp/tests/test_steering_index_token_count_sync_exploration.py`
  - Per `python-conventions.md`: `from __future__ import annotations`, class-based organization, type hints (`X | None`, `list[str]`), `st_`-prefixed strategies, `@settings(max_examples=20)`, stdlib + Hypothesis only
  - Import `measure_steering` via the `sys.path` manipulation pattern (`_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")`); resolve the real steering dir + `steering-index.yaml`
  - Define a local phase-entry tolerance check mirroring `isBugCondition` from design: `is_phase_bug(stored, measured) -> bool` returning `abs(stored - measured) / max(measured, 1) > 0.10`, and a `measured_tokens(file)` helper delegating to `measure_steering.calculate_token_count`
  - Add `st_drift()` / `st_phase_entry()` strategies to drive the synthetic and PBT cases (stored vs file-content-length pairs straddling the 10% boundary and the 500/2000 size boundaries)
  - **Test 1 — `--check` flags a drifted phase (synthetic)**: build a temp steering dir + index where a phase `token_count` is ~2x the file's measured count; assert the (to-be-added) phase validation reports it and the CLI exits non-zero (will FAIL on unfixed code — no phase validation exists)
  - **Test 2 — Live-index phase tolerance (PBT over the real `steering-index.yaml`)**: for every phase entry in the real index, assert `abs(stored - measured_tokens(file)) / max(measured, 1) <= 0.10` (will FAIL on the five drifted phases — module-03 phase2-visualization, module-01 phase1, module-05 phase2, module-06 phaseA, module-07 phase1)
  - **Test 3 — Size-category consistency after correction (Module 5)**: assert `module-05-phase2-data-mapping` would be reclassified `medium → large` at its measured count (~3128, over the 2000 boundary) (will FAIL on unfixed code — category not recomputed for phases)
  - **Test 4 — Update mode repairs a drifted phase**: run update mode on a temp index with a drifted phase, then assert the phase `token_count`/`size_category` now equal `measured`/`classify_size(measured)` (will FAIL on unfixed code — update mode leaves phases untouched)
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it); no PyYAML import
  - Run on UNFIXED code: `pytest senzing-bootcamp/tests/test_steering_index_token_count_sync_exploration.py`
  - **EXPECTED OUTCOME**: Test FAILS (correct — it proves the bug exists)
  - Document counterexamples found (e.g., "`--check` exits 0 / prints 'All token counts are within 10% tolerance.' while `modules.3.phases.phase2-visualization` reads 2035 vs measured 5312"; the five drifted phases enumerated above)
  - Mark task complete when the test is written, run, and the failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Drifted Entries and Existing Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe behavior on UNFIXED code, snapshot it, then assert it is preserved
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Create `senzing-bootcamp/tests/test_steering_index_token_count_sync_preservation.py`
  - Per `python-conventions.md`: `from __future__ import annotations`, class-based organization, type hints (`X | None`, `list[str]`), `st_`-prefixed strategies, `@settings(max_examples=20)`, stdlib + Hypothesis only
  - Import `measure_steering` via the `sys.path` pattern; snapshot the relevant regions of the real `steering-index.yaml` (via SHA-256) on UNFIXED code as a `_BASELINE_HASHES` constant before asserting
  - **Test 1 — `file_metadata` validation unchanged (PBT)**: observe that `check_counts` flags `file_metadata` mismatches and honors the 10% tolerance and missing/removed detection on unfixed code; assert this is identical after the fix (PBT over generated `file_metadata` collections, mirroring `TestProperty7`/`TestProperty8` in `test_measure_steering.py`)
  - **Test 2 — Non-phase blocks byte-preserved by update mode**: run update mode on a temp index and assert `budget` (incl. `split_threshold_tokens`), `keywords`, `languages`, `deployment`, and each module's `root`/`step_range` are byte-preserved (extends `TestProperty5`)
  - **Test 3 — `budget.total_tokens` unchanged by phase reconciliation**: assert `total_tokens` equals the sum of `file_metadata` counts before AND after running the fixed update mode (phase counts are excluded from the budget total)
  - **Test 4 — Already-in-tolerance phases untouched**: assert `modules.11.phases.phase1-packaging` (3214 vs 3289, 2.3%) and all `onboarding.*` / `session-resume.*` phase entries are unchanged by update mode and are NOT flagged by `--check`
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it); no PyYAML import
  - Run on UNFIXED code: `pytest senzing-bootcamp/tests/test_steering_index_token_count_sync_preservation.py`
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix — reconcile and validate phase token counts in `measure_steering.py`

  - [x] 3.1 Add `_parse_phase_entries(content)` to `measure_steering.py`
    - Walk the YAML text line by line over the region above `file_metadata`; each time a line matches `^(\s+)file:\s+([\w.-]+\.md)\s*$`, capture the indent, filename, and the line index, then locate the immediately-following `token_count:` and `size_category:` line indices/values within the same (more-indented) phase block
    - Return a list of phase-entry records (filename, stored `token_count`, stored `size_category`, and the line positions of the `token_count`/`size_category` lines)
    - Keying on `file:` lines naturally restricts the walk to phase entries and excludes `root:` and `file_metadata` entries; covers `modules.*.phases.*`, `onboarding.*.phases.*`, and `session-resume.*.phases.*` uniformly (same `file:`/`token_count:`/`size_category:` shape)
    - Stdlib only — reuse the existing `re`/line-based mechanism (same style as `_find_section_start`, `_parse_stored_metadata`, and the phase `file:` regex in `_parse_modules_section`); no PyYAML
    - _Bug_Condition: isBugCondition(X) requires identifying phase entries (file + token_count) — no such parser exists in F_
    - _Expected_Behavior: phase entries are enumerable so their token_count/size_category can be validated and reconciled (Property 1)_
    - _Preservation: `file_metadata` / `root` entries excluded; existing parsing helpers untouched (Property 2)_
    - _Requirements: 2.1, 2.4_

  - [x] 3.2 Add `check_phase_counts(index_path, steering_dir)` to `measure_steering.py`
    - For each record from `_parse_phase_entries`, compute `measured = calculate_token_count(steering_dir / file)` and apply the existing tolerance test `abs(stored - measured) / max(measured, 1) > 0.10`
    - Return a list of mismatch tuples (e.g. `(file, stored_count, measured_count)`) for the violating phases; treat a phase whose `file` does not exist on disk as a mismatch (mirroring `file_metadata` missing detection)
    - This function does NOT modify the file
    - _Bug_Condition: isBugCondition(X) where abs(X.token_count - measured_tokens(X.file)) / max(measured,1) > 0.10_
    - _Expected_Behavior: drifted phase entries are detected and reported with the same 10% tolerance the script applies to file_metadata (Property 1 reqs 2.2, 2.6)_
    - _Preservation: pure read — no file mutation; in-tolerance phases produce no mismatch (Property 2)_
    - _Requirements: 2.2, 2.6_

  - [x] 3.3 Extend the `--check` path in `main()` to validate the phases map
    - After the existing `check_counts(index_path, file_metadata)` call, also call `check_phase_counts(index_path, args.steering_dir)`
    - Print a clearly-labeled "Phase token count mismatches (>10% difference)" report for the phase results IN ADDITION to the existing `file_metadata` report; exit non-zero if EITHER list is non-empty, and print the existing success message and exit 0 only when BOTH are empty
    - Preserve the existing `file_metadata` report and exit semantics exactly when no phase drift exists
    - _Bug_Condition: isBugCondition(X) — F's `--check` validates only file_metadata, so phase drift exits 0 (silent)_
    - _Expected_Behavior: `--check` reports phase mismatches and exits non-zero on a drifted index, exits 0 on a reconciled index (Property 1 reqs 2.2, 2.6)_
    - _Preservation: existing file_metadata report and success/exit-0 semantics unchanged when no phase drift (Property 2 reqs 3.1, 3.6)_
    - _Requirements: 2.2, 2.6_

  - [x] 3.4 Add `rewrite_phase_counts(content, steering_dir)` to `measure_steering.py`
    - For each phase record, compute `measured = calculate_token_count(file)` and `new_cat = classify_size(measured)`, then replace ONLY that phase block's `token_count:` value line and `size_category:` value line in place — preserving exact indentation, the surrounding `file:` / `step_range:` lines, and ordering
    - This is an in-place line edit, not a section rebuild, so module/phase structure and ordering are preserved; a phase already within tolerance is rewritten to identical bytes (no net change)
    - Stdlib only; no PyYAML
    - _Bug_Condition: isBugCondition(X) — update mode (F) leaves phases.*.token_count untouched_
    - _Expected_Behavior: each drifted phase's token_count is set to measured and size_category to classify_size(measured) (Property 1 reqs 2.1, 2.3, 2.5)_
    - _Preservation: in-tolerance phases byte-identical; file:/step_range:/indentation/ordering preserved (Property 2 reqs 3.2, 3.3, 3.6)_
    - _Requirements: 2.1, 2.3, 2.5_

  - [x] 3.5 Wire `rewrite_phase_counts` into update mode
    - In update mode, apply `rewrite_phase_counts` to the YAML region above `file_metadata` BEFORE `update_index` rebuilds `file_metadata` + `budget` (or have `update_index` apply it to its `preserved` prefix)
    - Leave the existing `file_metadata`/`budget` rebuild and the `split_threshold_tokens` preservation unchanged; confirm `budget.total_tokens` stays the sum of `file_metadata` counts only (phase counts excluded, so reconciliation does not change `total_tokens` — currently 166655)
    - _Bug_Condition: isBugCondition(X) — F's update mode cannot repair phase drift (phases live in the preserved prefix)_
    - _Expected_Behavior: update mode refreshes every phases.*.token_count (and dependent size_category) in addition to file_metadata + budget (Property 1 req 2.3)_
    - _Preservation: budget.total_tokens still equals the sum of file_metadata counts; budget/keywords/languages/deployment/root/step_range preserved (Property 2 reqs 3.3, 3.4)_
    - _Requirements: 2.3_

  - [x] 3.6 Reconcile the data: regenerate `steering-index.yaml` via the fixed update mode
    - Run `python senzing-bootcamp/scripts/measure_steering.py` (fixed update mode) from the repo root to regenerate `senzing-bootcamp/steering/steering-index.yaml` — **do NOT hand-edit**
    - Confirm exactly the flagged drifted phases changed (expected set per design: `modules.3.phases.phase2-visualization` 2035→5312, `modules.1.phases.phase1-discovery` 3257→4527, `modules.5.phases.phase2-data-mapping` 1894→3128 **medium→large**, `modules.6.phases.phase1-build-loading-program` 662→1219, `modules.7.phases.phase1-query-visualize` 3183→3591) — treat the tool's actual output as authoritative if it differs
    - Confirm `modules.11.phases.phase1-packaging` (3214 vs 3289) and all `onboarding.*` / `session-resume.*` phases are unchanged
    - _Bug_Condition: the live steering-index.yaml carries the drifted phase counts (the bug instances)_
    - _Expected_Behavior: every phase entry within tolerance and size_category consistent, produced by the tool not by hand (Property 1 reqs 2.1, 2.3, 2.5)_
    - _Preservation: in-tolerance phases and all non-phase content unchanged by the regeneration (Property 2 reqs 3.2, 3.3, 3.6)_
    - _Requirements: 2.1, 2.3, 2.5_

  - [x] 3.7 Update `tests/test_measure_steering.py` for the new phase code paths
    - Add a phases-validation case asserting `check_phase_counts` detects a drifted phase and that `--check` exits non-zero when a phase is out of tolerance (complementing the existing `file_metadata`-only cases); optionally cover `rewrite_phase_counts` (drifted corrected, in-tolerance byte-identical, `size_category` recomputed across the 2000 boundary)
    - Ensure all existing cases (`TestProperty1`–`TestProperty8`, `TestCheckModeDoesNotModifyYAML`, `TestIntegrationRealSteering`, etc.) still pass with the new code paths — do NOT break existing assertions
    - _Bug_Condition: the existing suite has no coverage of phase validation/rewrite_
    - _Expected_Behavior: the suite asserts phase drift is detected and `--check` fails on it (Property 1 req 2.2)_
    - _Preservation: existing file_metadata-focused assertions remain intact and passing (Property 2 reqs 3.1)_
    - _Requirements: 2.2, 3.1_

  - [x] 3.8 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Phase Token Counts Reconciled and Validated
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes, phase counts are reconciled, size categories are consistent, and `--check` validates the phases map
    - Run `pytest senzing-bootcamp/tests/test_steering_index_token_count_sync_exploration.py`
    - **EXPECTED OUTCOME**: Test PASSES (confirms the bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 3.9 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Drifted Entries and Existing Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run `pytest senzing-bootcamp/tests/test_steering_index_token_count_sync_preservation.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — file_metadata validation unchanged, non-phase blocks byte-preserved, budget.total_tokens unchanged, in-tolerance phases untouched)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the two new suites: `pytest senzing-bootcamp/tests/test_steering_index_token_count_sync_exploration.py senzing-bootcamp/tests/test_steering_index_token_count_sync_preservation.py`
  - Run the existing regression suites: `pytest senzing-bootcamp/tests/test_measure_steering.py senzing-bootcamp/tests/test_token_budget_optimization.py`
  - Run CI validators: `python senzing-bootcamp/scripts/measure_steering.py --check` (must exit 0 post-reconciliation, with both `file_metadata` and the phases map validated), `python senzing-bootcamp/scripts/validate_power.py`, `python senzing-bootcamp/scripts/validate_commonmark.py`, `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`
  - Confirm stdlib-only (no PyYAML import added to `measure_steering.py` or the tests) and no MCP server URL introduced into any edited surface
  - Ensure all tests pass; ask the user if questions arise.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3.1"] },
    { "id": 2, "tasks": ["3.2", "3.4"] },
    { "id": 3, "tasks": ["3.3", "3.5"] },
    { "id": 4, "tasks": ["3.6"] },
    { "id": 5, "tasks": ["3.7"] },
    { "id": 6, "tasks": ["3.8", "3.9"] },
    { "id": 7, "tasks": ["4"] }
  ]
}
```

- **Wave 0** — `[1, 2]`: the exploration suite (must FAIL on unfixed code) and the preservation suite (must PASS on unfixed code) are authored against the unfixed baseline and can run in parallel.
- **Wave 1** — `[3.1]`: `_parse_phase_entries` is the shared parser every consumer depends on; it must land first.
- **Wave 2** — `[3.2, 3.4]`: `check_phase_counts` (validation) and `rewrite_phase_counts` (in-place edit) both consume the parser from 3.1 and touch independent code paths.
- **Wave 3** — `[3.3, 3.5]`: the `--check` wiring depends on `check_phase_counts` (3.2); the update-mode wiring depends on `rewrite_phase_counts` (3.4).
- **Wave 4** — `[3.6]`: data reconciliation requires a working update mode (3.5 wired in).
- **Wave 5** — `[3.7]`: the existing-suite updates exercise the now-complete phase code paths against the reconciled index.
- **Wave 6** — `[3.8, 3.9]`: verification re-runs the unchanged task 1 / task 2 suites after the fix and reconciliation land.
- **Wave 7** — `[4]`: the final checkpoint runs all suites and CI validators after verification.

## Notes

- Tests use pytest + Hypothesis (property-based testing), stdlib + Hypothesis only, in `senzing-bootcamp/tests/` per `tech.md` and `python-conventions.md`.
- The exploration test (task 1) is authored to FAIL on unfixed code — `--check` exits 0 despite the five drifted phases, and update mode leaves phases untouched. This confirms the structural root cause (validation/update read only `file_metadata`).
- The preservation test (task 2) is authored to PASS on unfixed code — it captures the `file_metadata` validation, non-phase blocks, `budget.total_tokens`, and already-in-tolerance phases that must not change. After the fix (tasks 3.1–3.7), both suites PASS.
- The fix is confined to `measure_steering.py` (new helpers + `--check`/update-mode wiring) and the phase `token_count` / dependent `size_category` values in `steering-index.yaml`. `budget.total_tokens` is the sum of `file_metadata` counts only and is unaffected by phase reconciliation.
- `steering-index.yaml` is regenerated by running the fixed update mode (task 3.6), never hand-edited, so the tool and the data agree by construction; the implementer treats whatever the fixed tool flags as the authoritative drift set.
- All new helpers reuse the script's existing stdlib-only regex/line-based string manipulation — no PyYAML is introduced (`tech.md`, `python-conventions.md`), and no MCP server URL is added to any script or test (security hook blocks it; the power's `mcp.json` remains the single source of truth).
