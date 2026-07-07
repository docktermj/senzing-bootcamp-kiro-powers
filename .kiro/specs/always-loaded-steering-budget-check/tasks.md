# Implementation Plan: Always-Loaded Steering Budget Check

## Overview

Add an **Always_Loaded_Check** to `senzing-bootcamp/scripts/measure_steering.py` so that
`--check` (the existing CI gate) fails when the always-loaded steering baseline creeps toward the
warn threshold. The check derives the Always_Loaded_Set from the steering files'
`inclusion: always` frontmatter (the single authoritative source), computes the Baseline_Footprint
from measured `token_count` values, and fails CI (exit non-zero) when that footprint exceeds a
configurable ceiling (`budget.always_loaded_ceiling_pct` of the Warn_Threshold), reporting the
footprint, the warn-threshold, the percent consumed, and — on failure — the contributing files.

Work proceeds bottom-up: add the ceiling config key (and preserve it in update mode) first, then the
pure frontmatter/set-collection functions, then footprint and ceiling parsing, then the result
dataclass + decision function + reporting helper, then wire the check into `main --check` and
refactor `simulate_context_load` to share the same authoritative set. Each pure function is followed
by its property test so errors surface early, and example/regression and integration tests close the
loop. All additions live in `measure_steering.py`, are pure reads, and stay Python 3.11+ stdlib-only
with custom minimal YAML/frontmatter parsing (no PyYAML). The existing `file_metadata`, phase, and
budget-total checks and their 10% tolerance are preserved exactly, and no new CI step is added.

## Tasks

- [x] 1. Add the ceiling configuration key
  - [x] 1.1 Add `always_loaded_ceiling_pct` to the budget block and preserve it in `update_index`
    - Add `always_loaded_ceiling_pct: 25` to the `budget` block of
      `senzing-bootcamp/steering/steering-index.yaml`, beside `warn_threshold_pct` /
      `critical_threshold_pct`
    - Update `update_index` so the rebuilt `budget` block emits `always_loaded_ceiling_pct`
      (preserving it the same way `split_threshold_tokens` and `router_ceiling` are preserved), so
      update mode never drops the key
    - _Requirements: 2.4_

- [x] 2. Derive the authoritative always-loaded set
  - [x] 2.1 Implement `parse_inclusion` and `collect_always_loaded_set`
    - Implement `parse_inclusion(filepath) -> str | None`: read only the leading `---`-fenced
      frontmatter block and match `^\s*inclusion:\s*["']?(\w+)["']?\s*$` with a stdlib regex;
      return `None` on missing/malformed frontmatter (never raise), no PyYAML
    - Implement `collect_always_loaded_set(steering_dir) -> list[str]`: glob `*.md` files (mirroring
      `scan_steering_files`), call `parse_inclusion` on each, return the sorted filenames whose
      `inclusion` is exactly `always`; skip unreadable files with a stderr warning
      (`PermissionError` handling like `scan_steering_files`)
    - _Requirements: 1.1_

  - [x] 2.2 Refactor `simulate_context_load` to use the shared set
    - Replace the hard-coded `always_loaded = [...]` list with
      `always_loaded = collect_always_loaded_set(steering_dir)` so `--simulate` and the check share
      one definition; keep the representative language file (`lang-python.md`) as a
      simulation-only assumption
    - Add a `steering_dir` parameter defaulting to `DEFAULT_STEERING_DIR` and update existing call
      sites so they keep working
    - _Requirements: 1.2_

  - [x] 2.3 Write property test for the authoritative set and shared definition
    - **Property 1: The always-loaded set is exactly the `inclusion: always` files, and one source
      drives both paths**
    - Add `st_inclusion_value()` and `st_steering_corpus()` strategies (synthetic, PII-free files
      written to a temp dir) recording the expected always-subset; assert
      `collect_always_loaded_set` returns exactly that subset and that `simulate_context_load` draws
      its always-loaded list from the same set
    - **Validates: Requirements 1.1, 1.2**

- [x] 3. Compute the footprint and read the ceiling
  - [x] 3.1 Implement `compute_baseline_footprint`
    - Implement `compute_baseline_footprint(always_loaded, file_metadata) -> int`: sum the measured
      `token_count` of the files in the set; files absent from `file_metadata` contribute 0;
      order-independent
    - _Requirements: 2.1_

  - [x] 3.2 Write property test for the footprint sum
    - **Property 2: Baseline footprint equals the sum of measured counts**
    - Add `st_token_metadata(names)` (a `file_metadata`-shaped map of non-negative counts with some
      names optionally omitted); assert the footprint equals the sum over exactly the set, absent
      files contributing 0, independent of set order
    - **Validates: Requirements 2.1**

  - [x] 3.3 Implement `parse_always_loaded_ceiling_pct`
    - Implement `parse_always_loaded_ceiling_pct(content, default=25) -> int`: localized
      `re.search(r"always_loaded_ceiling_pct:\s*(\d+)", content)` (same style as
      `parse_budget_total`), returning the documented default when the key is absent
    - _Requirements: 2.4_

  - [x] 3.4 Write property test for config-driven ceiling
    - **Property 4: The ceiling is read from configuration**
    - Generate `budget` YAML text declaring `always_loaded_ceiling_pct: N`; assert the parser
      returns exactly `N`, and returns the documented default when the key is absent
    - **Validates: Requirements 2.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the check and reporting
  - [x] 5.1 Implement `AlwaysLoadedResult` and `check_always_loaded_budget`
    - Define the `AlwaysLoadedResult` dataclass exactly as in the design (`always_loaded`,
      `footprint_tokens`, `warn_threshold_tokens`, `ceiling_pct`, `ceiling_tokens`, `pct_of_warn`,
      `over_budget`)
    - Implement `check_always_loaded_budget(index_path, steering_dir, file_metadata) ->
      AlwaysLoadedResult`: derive the set (`collect_always_loaded_set`), footprint
      (`compute_baseline_footprint`), warn threshold in tokens (from `reference_window` x
      `warn_threshold_pct`, defaulting `200000` / `60` via localized regex), and ceiling
      (`parse_always_loaded_ceiling_pct`); set `over_budget` when footprint exceeds
      `ceiling_pct/100 * warn_threshold_tokens`; pure read, no print/exit
    - _Requirements: 2.2, 2.3_

  - [x] 5.2 Write property test for the pass/fail boundary
    - **Property 3: The pass/fail decision matches the ceiling boundary**
    - Add `st_budget_params()` generating `(footprint, always_loaded_ceiling_pct,
      warn_threshold_pct, reference_window)` spanning below-, at-, and above-ceiling; assert
      `over_budget` is true iff footprint exceeds
      `always_loaded_ceiling_pct/100 * warn_threshold_pct/100 * reference_window`
    - **Validates: Requirements 2.2, 2.3**

  - [x] 5.3 Implement `format_always_loaded_report`
    - Implement `format_always_loaded_report(result) -> list[str]`: always render the
      Baseline_Footprint in tokens, the Warn_Threshold in tokens, the percent-of-warn consumed, and
      the ceiling; on `over_budget`, additionally name each contributing always-loaded file with its
      token count
    - _Requirements: 3.1, 3.2_

  - [x] 5.4 Write property test for the report figures and naming
    - **Property 5: The report states the required figures and names contributors on failure**
    - Assert the rendered report always contains the footprint tokens, warn-threshold tokens, and
      percent consumed; and whenever over budget, names every file in the Always_Loaded_Set
    - **Validates: Requirements 3.1, 3.2**

- [x] 6. Integrate into `main --check` and cover with examples
  - [x] 6.1 Wire the always-loaded check into the `--check` aggregate exit
    - In `main`'s `--check` branch, call `check_always_loaded_budget(...)` alongside the existing
      `check_counts` / `check_phase_counts` / budget-total logic, print
      `format_always_loaded_report(...)` lines, and fold `always_result.over_budget` into the single
      `sys.exit(1)` decision so it can only add a failure reason
    - Leave `check_counts`, `check_phase_counts`, the budget-total check, and their 10% tolerance
      untouched
    - _Requirements: 4.1, 4.2, 2.3_

  - [x] 6.2 Write example and regression tests
    - Under-ceiling pass: fixture whose always-files sum below the ceiling → report passes and
      `main(["--check"])` exits 0
    - Over-ceiling fail with naming: fixture whose always-files exceed the ceiling → `over_budget`
      true, report names each contributing file, `main(["--check"])` exits non-zero
    - Config-driven ceiling honored vs. documented default; authoritative derivation
      (`collect_always_loaded_set` returns exactly the `inclusion: always` files and
      `simulate_context_load` uses the same list); non-interference regression (existing
      `check_counts` / `check_phase_counts` / budget-total examples still pass, in-budget baseline
      exits 0); `update_index` retains `always_loaded_ceiling_pct` in the rebuilt budget block
    - _Requirements: 5.1, 5.2, 4.1, 4.2, 2.4, 3.2, 1.1, 1.2_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. End-to-end integration
  - [x] 8.1 Write the end-to-end integration test
    - Wire the real script against a temp steering directory and index: write synthetic
      always/manual/fileMatch files (PII-free) plus a `budget` block with a ceiling, run
      `main(["--check", ...])`, and assert the exit code and report reflect the baseline footprint
      versus the configured ceiling — the same path CI exercises
    - _Requirements: 4.1, 5.1, 5.2_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- All additions live in `senzing-bootcamp/scripts/measure_steering.py` and are pure reads that never
  write the index; the check rides the existing `--check` CI invocation (no new CI step).
- Python 3.11+ stdlib only, no PyYAML — frontmatter and `budget` values are read with custom minimal
  regex parsing consistent with the existing `parse_budget_total` / `simulate_context_load` style
  (Requirement 4.3).
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)`.
- Tests live in `senzing-bootcamp/tests/` (suggested `test_always_loaded_budget_check.py`), are
  class-based, and import `scripts/` via the `sys.path` convention. Fixtures are synthetic and
  PII-free (power-distribution safety).
- The always-loaded overage is purely additive to the exit condition — it never suppresses the
  existing `file_metadata`, phase, or budget-total failures, preserving current behavior and the 10%
  tolerance exactly (Requirement 4.2).
- Each property task references its property number and the requirement clause it validates for
  traceability.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3", "3.1"] },
    { "id": 4, "tasks": ["3.2", "3.3"] },
    { "id": 5, "tasks": ["3.4", "5.1"] },
    { "id": 6, "tasks": ["5.2", "5.3"] },
    { "id": 7, "tasks": ["5.4", "6.1"] },
    { "id": 8, "tasks": ["6.2", "8.1"] }
  ]
}
```
