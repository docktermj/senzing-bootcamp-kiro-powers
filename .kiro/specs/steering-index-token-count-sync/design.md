# Steering Index Token Count Sync Bugfix Design

## Overview

`senzing-bootcamp/steering/steering-index.yaml` stores per-file token counts in two
independent places: the authoritative `file_metadata.<file>.token_count` entries, and
the per-phase `modules.<N>.phases.<phase>.token_count` entries (plus the parallel
`onboarding.*` and `session-resume.*` phase maps). `scripts/measure_steering.py`
computes, writes, and validates `file_metadata` and `budget`, but it never inspects the
`phases` map. As a result the phase counts have silently drifted — in one case by 2.6x
(`module-03-phase2-visualization.md`: stored 2035 vs measured 5312). The agent uses the
phase counts for context-budget decisions on split modules, so an under-count causes it
to under-estimate load and exceed the 60%/80% thresholds the budget system exists to
enforce.

The fix extends `measure_steering.py` so both its `--check` (validation) path and its
update/write path additionally process every phase entry that has a `file` and a
`token_count`. Validation flags any phase whose stored `token_count` is outside the
existing 10% tolerance of its file's measured count (exiting non-zero so CI fails).
Update mode rewrites each drifted phase's `token_count` and dependent `size_category`
in place, using the same stdlib-only, regex/line-based string manipulation the script
already uses — no PyYAML is introduced. The corrected `steering-index.yaml` is then
produced authoritatively by running the fixed update mode, so the tool and the data
agree by construction rather than by hand-editing.

The fix is deliberately narrow: it touches only `phases.*.token_count` and the
dependent `phases.*.size_category`. All `file_metadata` behavior, the `budget` block,
the `keywords`/`languages`/`deployment` maps, and each module's `root` / `step_range` /
structure are preserved unchanged.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a phase entry whose
  stored `token_count` differs from the measured token count of its `file` by more than
  the 10% tolerance, with nothing detecting or correcting it.
- **Property (P)**: The desired behavior — every phase entry's stored `token_count` is
  within tolerance of its file's measured count, its `size_category` is consistent with
  that count, and `--check` validates the `phases` map.
- **Preservation**: Existing `file_metadata` validation/tolerance/missing-detection, the
  `budget` block, the non-phase maps, and each module's `root`/`step_range`/structure
  that must remain unchanged by the fix, along with phase entries already within
  tolerance.
- **`measure_steering.py`**: The script in `senzing-bootcamp/scripts/measure_steering.py`
  that scans steering `.md` files, computes token counts, and writes/validates
  `steering-index.yaml`.
- **`measured_tokens(file)`**: `round(len(read_text(file)) / 4)` — implemented as
  `calculate_token_count(file)`; the same measure the script already applies to
  `file_metadata`.
- **`classify_size(count)`**: The existing size-boundary function — `< 500` → `small`,
  `<= 2000` → `medium`, `> 2000` → `large`.
- **Phase entry**: Any `modules.<N>.phases.<phase>` (and analogously `onboarding.*` and
  `session-resume.*` phase) block that has both a `file:` and a `token_count:`. A phase
  entry is uniquely identifiable in the YAML by its `file:` line; `file_metadata` entries
  have no `file:` line and `root:` entries have no `token_count:`.
- **`check_counts` / `_parse_stored_metadata`**: The existing validation path that reads
  only the `file_metadata` block.
- **`update_index`**: The existing writer that rebuilds `file_metadata` and `budget`
  while preserving everything above the `file_metadata` section.
- **tolerance**: `0.10` — the same constant the script applies to `file_metadata`.

## Bug Details

### Bug Condition

The bug manifests when a split-module phase entry's stored `token_count` no longer
matches the measured token count of the `file` it points to. The original
`measure_steering.py` is either not validating phase entries at all (`--check` inspects
only `file_metadata`), not refreshing them (update mode rewrites only `file_metadata`
and `budget`), or leaving a phase's `size_category` inconsistent with a corrected count.
Because nothing reads the `phases` map, the drift is silent and never trips CI.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X — an entry in steering-index.yaml
  OUTPUT: boolean

  // Only phase entries (with a file + token_count) can be buggy.
  IF NOT isPhaseEntry(X) THEN
    RETURN false
  END IF

  measured ← measured_tokens(X.file)         // round(len(read_text(X.file)) / 4)
  RETURN abs(X.token_count - measured) / max(measured, 1) > tolerance   // tolerance = 0.10
END FUNCTION
```

`isPhaseEntry(X)` is true for any `modules.<N>.phases.<phase>`, `onboarding.phases.<phase>`,
or `session-resume.phases.<phase>` block that has both a `file:` and a `token_count:`.
In the YAML this is exactly the set of blocks reachable from a `file:` line, since
`file_metadata` entries are keyed by filename (no `file:` field) and `root:` entries
carry no `token_count:`.

### Examples

Measured with the script's own `round(len(content) / 4)` and its 10% tolerance, run
against the live steering files:

- **Module 3 visualization** — `modules.3.phases.phase2-visualization`,
  `module-03-phase2-visualization.md`: stored `token_count` 2035 vs measured 5312
  (61.7% drift, a 2.6x under-count). Expected: reconciled to 5312. `size_category`
  stays `large`.
- **Module 1 discovery** — `modules.1.phases.phase1-discovery`,
  `module-01-business-problem.md`: stored 3257 vs measured 4527 (28.1% drift). Expected:
  reconciled to 4527; `size_category` stays `large`. (Note this is the module root file;
  see "Phase→File Semantics" below.)
- **Module 5 data-mapping** — `modules.5.phases.phase2-data-mapping`,
  `module-05-phase2-data-mapping.md`: stored 1894 vs measured 3128 (39.5% drift, crosses
  the 2000 medium/large boundary). Expected: reconciled to 3128 **and** `size_category`
  updated `medium` → `large`.
- **Module 6 build-loading** — `modules.6.phases.phase1-build-loading-program`,
  `module-06-phaseA-build-loading.md`: stored 662 vs measured 1219 (45.7% drift).
  Expected: reconciled to 1219; `size_category` stays `medium`.
- **Module 7 query-visualize** — `modules.7.phases.phase1-query-visualize`,
  `module-07-query-visualize-discover.md`: stored 3183 vs measured 3591 (11.4% drift,
  just over tolerance). Expected: reconciled to 3591; `size_category` stays `large`.
- **Edge case (within tolerance, must NOT change)** —
  `modules.11.phases.phase1-packaging`, `module-11-deployment.md`: stored 3214 vs
  measured 3289 (2.3% drift). Expected: left unchanged.

The authoritative drift set is whatever the fixed tool flags when run against the
current files, not this snapshot. As of the latest run the complete set of violating
phase entries is exactly the five above; every `onboarding.*` and `session-resume.*`
phase entry, and all other `modules.*` phase entries, are already within tolerance.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- `file_metadata` validation, the 10% tolerance, and missing/removed-file detection
  behave exactly as before (Requirement 3.1).
- A phase entry whose file is already within tolerance is left byte-unchanged
  (Requirements 3.2, 3.6) — including `module-11-deployment.md` phase1 (3214 vs 3289).
- The `budget` block (`total_tokens`, `reference_window`, `warn_threshold_pct`,
  `critical_threshold_pct`, `split_threshold_tokens`), the `keywords`, `languages`, and
  `deployment` maps, and each module's `root`, `step_range`, and overall structure are
  preserved, except where a `token_count` (and dependent `size_category`) correction is
  required (Requirement 3.3).
- Scripts remain Python-standard-library only; no new third-party dependency, no PyYAML
  (Requirement 3.4).
- `validate_power.py`, `validate_commonmark.py`, and `sync_hook_registry.py --verify`
  continue to pass; all other scripts, steering files, and hooks remain untouched
  (Requirement 3.5).

**Scope:**
All entries that are NOT drifted phase entries should be completely unaffected by this
fix. This includes:
- Every `file_metadata` entry and the validation logic over it.
- The `budget` block and the `keywords`/`languages`/`deployment` maps.
- Each module's `root` filename and every phase's `file` and `step_range`.
- Phase entries already within the 10% tolerance.

**Note:** The actual expected correct behavior for the buggy inputs is defined in the
Correctness Properties section (Property 1). This section focuses on what must NOT change.

## Hypothesized Root Cause

Based on the bug analysis and a read of `measure_steering.py`, the cause is structural,
not a logic error in any single line:

1. **Validation reads only `file_metadata`**: `check_counts()` calls
   `_parse_stored_metadata()`, which locates the `file_metadata:` section via
   `_find_section_start()` and parses only that block. It compares the scanned steering
   files against stored `file_metadata` counts and never examines the `phases` map. So
   `--check` exits 0 even when phase counts have drifted far beyond tolerance.

2. **Update mode rewrites only `file_metadata` and `budget`**: `update_index()` finds the
   `file_metadata:` section, preserves everything above it verbatim, and rebuilds only
   `file_metadata` + `budget`. The `phases` entries live in the preserved region above
   `file_metadata`, so update mode copies them through untouched and cannot repair drift.

3. **No phase→file consistency check exists**: there is no code path that, for a phase
   entry, computes `measured_tokens(phase.file)` and compares it to the phase's stored
   `token_count`, nor that recomputes the phase's `size_category` from a corrected count.
   The script already has the building blocks — `calculate_token_count`, `classify_size`,
   and a phase `file:` regex inside `_parse_modules_section` — but never wires them
   together for the phases map.

The drift itself accumulates whenever a phase markdown file is edited (or a module is
split/rewritten) without manually updating the duplicated count in the `phases` map; the
absence of detection (#1) lets it persist indefinitely.

## Correctness Properties

Property 1: Bug Condition — Phase Token Counts Reconciled and Validated

_For any_ phase entry where the bug condition holds (`isBugCondition` returns true — its
stored `token_count` is outside the 10% tolerance of `measured_tokens(file)`), the fixed
`measure_steering.py` SHALL, in update mode, set that phase's `token_count` to the
measured count (bringing it within tolerance) and set its `size_category` to
`classify_size(measured_count)`; and `--check` SHALL report the phase mismatch and exit
non-zero on a drifted index while exiting 0 on a reconciled index. For every phase entry
`X`, after the fix: `abs(token_count - measured_tokens(file)) / max(measured, 1) <=
tolerance` AND `size_category == classify_size(token_count)`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Property 2: Preservation — Non-Drifted Entries and Existing Behavior Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition` returns false —
`file_metadata` entries, the `budget` block, the `keywords`/`languages`/`deployment`
maps, module `root`/`step_range`/structure, and phase entries already within tolerance),
the fixed `measure_steering.py` SHALL produce the same result as the original function,
preserving all existing `file_metadata` validation/tolerance/missing-detection behavior,
all non-phase content, and every already-in-tolerance phase value, using the Python
standard library only (no PyYAML), with `validate_power.py`, `validate_commonmark.py`,
and `sync_hook_registry.py --verify` still passing.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Phase→File Semantics

Each phase entry maps **1:1** to its own `file`: the phase's `token_count` should equal
`measured_tokens(phase.file)`, the measured count of THAT phase's file. This holds even
when multiple phases of the same module point to different files (e.g. module 6's
`phase1`..`phase4` each point to a distinct `module-06-phase*.md`), and even when a phase
file is also the module root file:

- `modules.1.phases.phase1-discovery.file` is `module-01-business-problem.md`, which is
  also `modules.1.root` and also has a `file_metadata` entry. The phase `token_count`
  is reconciled to `measured_tokens(module-01-business-problem.md)` (4527), the same
  measure used for that file's `file_metadata` entry.
- `modules.3.phases.phase1-verification.file`, `modules.2.phases.phase1-setup.file`,
  `onboarding.phases.phase1-setup-intro.file`, and `session-resume.phases.phase1-fast-path.file`
  are likewise the respective root files; each phase count is reconciled to that file's
  measured count.

Validation and reconciliation both recompute `measured_tokens(phase.file)` directly
(the same way `file_metadata` is validated against freshly-scanned counts), rather than
reading the stored `file_metadata` value. This keeps the two count locations independent
derivations of the same source of truth and avoids coupling phase correctness to
`file_metadata` staleness.

### Changes Required

**File**: `senzing-bootcamp/scripts/measure_steering.py`

All changes use the script's existing stdlib-only, regex/line-based string manipulation
(the same mechanism as `_find_section_start`, `_parse_stored_metadata`, and the phase
`file:` regex already present in `_parse_modules_section`). No PyYAML.

1. **New helper `_parse_phase_entries(content)`**: Walk the YAML text line by line over
   the region above `file_metadata`. Each time a line matches
   `^(\s+)file:\s+([\w.-]+\.md)\s*$`, capture the indent, the filename, the line index,
   and the immediately-following `token_count:` and `size_category:` line indices/values
   within the same (more-indented) phase block. Return a list of phase-entry records
   (filename, stored `token_count`, stored `size_category`, and the line positions of the
   `token_count`/`size_category` lines). Keying on `file:` lines naturally restricts the
   walk to phase entries and excludes `root:` and `file_metadata` entries. This covers
   `modules.*.phases.*`, `onboarding.*.phases.*`, and `session-resume.*.phases.*`
   uniformly because all three use the same `file:`/`token_count:`/`size_category:` shape.

2. **New helper `check_phase_counts(index_path, steering_dir)`**: For each record from
   `_parse_phase_entries`, compute `measured = calculate_token_count(steering_dir / file)`
   and apply the existing tolerance test
   `abs(stored - measured) / max(measured, 1) > 0.10`. Return a list of mismatch tuples
   (e.g. `(file, stored_count, measured_count)`) for the violating phases. If a phase's
   `file` does not exist on disk, report it as a mismatch (mirroring `file_metadata`
   missing detection). This function does not modify the file.

3. **Extend the `--check` path in `main()`**: After the existing
   `check_counts(index_path, file_metadata)` call, also call
   `check_phase_counts(index_path, args.steering_dir)`. Merge both result lists; print a
   clearly-labeled "Phase token count mismatches (>10% difference)" report for the phase
   results in addition to the existing `file_metadata` report; exit non-zero if EITHER
   list is non-empty, and print the existing success message and exit 0 only when both
   are empty. The existing `file_metadata` report and exit semantics are unchanged when
   no phase drift exists.

4. **New helper `rewrite_phase_counts(content, steering_dir)`**: Produce updated YAML
   text by, for each phase record, computing `measured = calculate_token_count(file)` and
   `new_cat = classify_size(measured)`, then replacing only that phase block's
   `token_count:` value line and `size_category:` value line in place (preserving the
   exact indentation and the surrounding `file:` / `step_range:` lines and ordering). A
   phase already within tolerance is rewritten to the same value (no net change); the
   result is byte-identical for in-tolerance phases. This is an in-place line edit, not a
   section rebuild, so module/phase structure and ordering are preserved.

5. **Wire phase rewriting into update mode (`update_index` / `main`)**: In update mode,
   apply `rewrite_phase_counts` to the YAML content for the region above `file_metadata`
   **before** `update_index` rebuilds `file_metadata` + `budget` (or have `update_index`
   apply it to its `preserved` prefix). The existing `file_metadata`/`budget` rebuild and
   the preservation of `split_threshold_tokens` are unchanged. `budget.total_tokens`
   continues to be computed as the sum of `file_metadata` counts only — it does not
   include phase counts and is therefore unaffected by phase reconciliation (verified:
   the current `total_tokens` 166655 equals the sum of `file_metadata` counts).

### One-Time Data Reconciliation of `steering-index.yaml`

The corrected `steering-index.yaml` MUST be produced by running the fixed update mode
(`python senzing-bootcamp/scripts/measure_steering.py`) from the repo root, **not** by
hand-editing, so the tool and the data agree by construction. Running the fixed tool will
change exactly the drifted phase entries it flags. As of the latest measurement that set
is:

| Phase entry | File | stored → measured | size_category |
|---|---|---|---|
| `modules.3.phases.phase2-visualization` | `module-03-phase2-visualization.md` | 2035 → 5312 | large (unchanged) |
| `modules.1.phases.phase1-discovery` | `module-01-business-problem.md` | 3257 → 4527 | large (unchanged) |
| `modules.5.phases.phase2-data-mapping` | `module-05-phase2-data-mapping.md` | 1894 → 3128 | **medium → large** |
| `modules.6.phases.phase1-build-loading-program` | `module-06-phaseA-build-loading.md` | 662 → 1219 | medium (unchanged) |
| `modules.7.phases.phase1-query-visualize` | `module-07-query-visualize-discover.md` | 3183 → 3591 | large (unchanged) |

`modules.11.phases.phase1-packaging` (3214 vs 3289, 2.3%) and all `onboarding.*` /
`session-resume.*` phases are within tolerance and MUST remain unchanged. The
implementer SHALL treat whatever the fixed tool flags at implementation time as the
authoritative set, not this table.

### `budget.total_tokens` Behavior

`budget.total_tokens` is derived as the sum of `file_metadata` token counts (confirmed:
166655 = sum of `file_metadata`), recomputed by `update_index` on every update from the
scanned files. It does not aggregate phase counts. Therefore the phase reconciliation
does not change `total_tokens`; it stays correct as long as `file_metadata` itself stays
within tolerance (which the unchanged `--check` continues to enforce). The design
explicitly does NOT add phase counts to the budget total.

## Testing Strategy

### Validation Approach

The strategy is two-phase. First, an exploration test suite authored to FAIL on the
current (unfixed) code surfaces the bug by asserting that `--check` flags the known
drifted phases and that phase counts are within tolerance — these fail today, confirming
the root cause. Second, a preservation suite authored to PASS on the current code
captures the behavior that must not change (`file_metadata` validation, non-phase blocks,
already-in-tolerance phases). After the fix, both suites pass.

All tests follow `python-conventions.md`: pytest + Hypothesis, standard library +
Hypothesis only, class-based organization, `st_`-prefixed strategies,
`@settings(max_examples=20)`, `from __future__ import annotations`, type hints
(`X | None`, `list[str]`). Scripts are imported via the documented `sys.path`
manipulation pattern. No PyYAML, no MCP URLs, no external URLs.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix,
and confirm the root-cause analysis. If they pass on unfixed code, the root cause is
refuted and must be re-hypothesized.

**Test Plan**: New file
`senzing-bootcamp/tests/test_steering_index_token_count_sync_exploration.py`. Author the
assertions against the bug condition so they FAIL on unfixed code: build YAML fixtures
with a phase entry whose `token_count` is far from the measured count of its `file`, and
assert that the (to-be-added) phase validation flags it and that `--check` exits
non-zero. Also assert against the live index that every phase entry is within tolerance
of its file (fails today on the five drifted phases). Run on the UNFIXED code to observe
the failures.

**Test Cases**:
1. **`--check` flags drifted phase (synthetic)**: Construct a temp steering dir + index
   where a phase `token_count` is 2x the file's measured count; assert the phase
   validation reports it and the CLI exits non-zero (will fail on unfixed code — no phase
   validation exists).
2. **Live index phase tolerance (PBT over the real phases map)**: For each phase entry in
   the real `steering-index.yaml`, assert
   `abs(stored - measured_tokens(file)) / max(measured,1) <= 0.10` (will fail on the five
   drifted phases).
3. **Size-category consistency after correction (Module 5)**: Assert
   `module-05-phase2-data-mapping` would be reclassified `medium → large` at 3128 tokens
   (will fail on unfixed code — category not recomputed for phases).
4. **Update mode repairs a drifted phase**: Run update mode on a temp index with a
   drifted phase, then assert the phase `token_count`/`size_category` now match
   `measured`/`classify_size(measured)` (will fail on unfixed code — update mode leaves
   phases untouched).

**Expected Counterexamples**:
- `--check` exits 0 and prints "All token counts are within 10% tolerance." despite
  `modules.3.phases.phase2-visualization` reading 2035 vs a measured 5312.
- Possible causes: validation parses only `file_metadata`; update mode rebuilds only
  `file_metadata`/`budget`; no phase→file consistency or size-category recomputation.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function
produces the expected behavior.

**Pseudocode:**
```
FOR ALL X WHERE isPhaseEntry(X) DO
  measured := measured_tokens(X.file)
  ASSERT abs(F'(X).token_count - measured) / max(measured, 1) <= tolerance
  ASSERT F'(X).size_category = classify_size(F'(X).token_count)
END FOR

ASSERT run("measure_steering.py --check") validates the phases map
       AND exits 0 on the reconciled index
       AND exits non-zero (with a phase mismatch report) on a drifted index
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed
function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking
because:
- It generates many `file_metadata` and phase configurations automatically across the
  input domain.
- It catches edge cases (boundary tolerances, size-category boundaries, in-tolerance
  phases) that manual unit tests might miss.
- It gives strong guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: New file
`senzing-bootcamp/tests/test_steering_index_token_count_sync_preservation.py`. Author the
assertions to PASS on the UNFIXED code (they capture behavior that must not change), then
confirm they still pass after the fix.

**Test Cases**:
1. **`file_metadata` validation unchanged**: Observe that `check_counts` flags
   `file_metadata` mismatches and honors the 10% tolerance and missing/removed detection
   on unfixed code; assert this is identical after the fix (PBT over generated
   `file_metadata` collections, mirroring `TestProperty7`/`TestProperty8` in
   `test_measure_steering.py`).
2. **Non-phase blocks preserved**: Run update mode and assert `budget` (incl.
   `split_threshold_tokens`), `keywords`, `languages`, `deployment`, and each module's
   `root`/`step_range` are byte-preserved (extends `TestProperty5`).
3. **`budget.total_tokens` unchanged by phase reconciliation**: Assert
   `total_tokens` equals the sum of `file_metadata` counts before and after running the
   fixed update mode.
4. **Already-in-tolerance phases untouched**: Assert `modules.11.phases.phase1-packaging`
   (3214 vs 3289) and all `onboarding.*`/`session-resume.*` phases are unchanged by
   update mode and not flagged by `--check`.

### Unit Tests

- Extend `senzing-bootcamp/tests/test_measure_steering.py` with a case asserting
  `check_phase_counts` detects a drifted phase and that `--check` exits non-zero when a
  phase is out of tolerance (complementing the existing `file_metadata`-only cases).
- Test `rewrite_phase_counts` on a temp index: drifted phase corrected, in-tolerance
  phase left byte-identical, `size_category` recomputed across the 2000 boundary.
- Test that `--check` mode does not modify the YAML file (extends the existing
  `TestCheckModeDoesNotModifyYAML`).

### Property-Based Tests

- Generate phase entries with random (stored, file-content-length) pairs and verify the
  phase tolerance test flags exactly those outside 10% (Fix Checking).
- Generate indexes with random non-phase content and verify update mode preserves it
  (Preservation).
- Generate counts straddling the 500/2000 boundaries and verify the corrected
  `size_category` equals `classify_size(measured)` (Fix Checking, Requirement 2.5).

### Integration Tests

- Run `python senzing-bootcamp/scripts/measure_steering.py --check` from the repo root:
  it fails (non-zero, phase mismatch report) before reconciliation on the drifted phases
  and passes (exit 0) after running the fixed update mode.
- Run `python senzing-bootcamp/scripts/measure_steering.py` (update mode) then `--check`
  and assert no mismatches remain in either `file_metadata` or the phases map (extends
  `TestIntegrationRealSteering`).
- Run `validate_power.py`, `validate_commonmark.py`, and
  `sync_hook_registry.py --verify` to confirm the reconciled index and the script change
  keep the rest of CI green (Requirement 3.5).

## Security and Convention Compliance

- **Stdlib only / no PyYAML**: All new helpers reuse the script's existing regex and
  line-based string manipulation; no third-party dependency is added, honoring `tech.md`
  and `python-conventions.md` (Requirement 3.4).
- **No MCP URL**: No change references `mcp.json` or any MCP server URL; the single
  source of truth for MCP configuration is untouched.
- **No external URLs in steering files**: The only steering artifact modified is
  `steering-index.yaml` (data values), and no external URLs are introduced into any
  steering `.md` file.
- **No secrets**: No credentials, tokens, or keys are introduced.
- **Minimal blast radius**: Only `measure_steering.py` and the phase `token_count` /
  dependent `size_category` values in `steering-index.yaml` change; all other scripts,
  steering files, and hooks remain untouched (Requirement 3.5).
