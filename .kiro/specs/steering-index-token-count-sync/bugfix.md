# Bugfix Requirements Document

## Introduction

`senzing-bootcamp/steering/steering-index.yaml` stores per-file token counts in two
independent places that have drifted out of sync:

- The per-module phase entries: `modules.<N>.phases.<phase>.token_count` (and the
  parallel `onboarding.*` and `session-resume.*` phase maps). The agent uses these
  values for context-budget decisions on split modules, per `agent-instructions.md`
  ("Context Budget" — *"For split modules, use phase-level `token_count` from the
  `phases` map. Track cumulative tokens."*) and `phase-loading-guide.md`.
- The per-file authoritative entries: `file_metadata.<file>.token_count`. These are
  the counts computed and validated by `scripts/measure_steering.py`.

Each split-module phase entry has a `file:` that points to a distinct phase markdown
file, and that same file also appears in `file_metadata`. The two `token_count`
values for the same file should agree, but for several phases they do not — sometimes
by more than 2x.

Confirmed drift (phases value vs `file_metadata` value, using the script's
`round(len(content) / 4)` measure and its 10% tolerance):

| Phase entry | File | phases | file_metadata | drift |
|---|---|---|---|---|
| `modules.3.phases.phase2-visualization` | `module-03-phase2-visualization.md` | 2035 | 5312 | 61.7% (2.6x under-count) |
| `modules.1.phases.phase1-discovery` | `module-01-business-problem.md` | 3257 | 4422 | 26.3% |
| `modules.5.phases.phase2-data-mapping` | `module-05-phase2-data-mapping.md` | 1894 | 3128 | 39.4% (also crosses medium→large) |
| `modules.6.phases.phase1-build-loading-program` | `module-06-phaseA-build-loading.md` | 662 | 1219 | 45.7% |
| `modules.7.phases.phase1-query-visualize` | `module-07-query-visualize-discover.md` | 3183 | 3591 | 11.4% |

Note: `modules.11.phases.phase1-packaging` (`module-11-deployment.md`, phases=3214 vs
file_metadata=3289, 2.3%) is **within** the 10% tolerance — it is listed in the bug
report but is not a violating case under the existing tolerance rule. Module 6 and
module 7 phase1 drift were discovered during analysis and are not in the original
report. The fix MUST reconcile ALL drifted phase entries, not only the originally
reported subset, so the full set is determined by the bug condition (Section 4), not
by this snapshot.

The bug is silent because `measure_steering.py --check` validates ONLY the
`file_metadata` block and never inspects the `phases` map, so the drift never trips
CI. When a phases value under-counts the real file size (e.g. Module 3 visualization
reads as 2035 but is actually 5312), the agent under-estimates load cost and can blow
past the 60%/80% context-budget thresholds the system exists to enforce.

## Bug Analysis

### Current Behavior (Defect)

The stored `phases.*.token_count` values are stale relative to the real token counts
of the files they point to, and nothing detects or corrects the drift.

1.1 WHEN a split-module phase entry's `token_count` differs from the measured token
count of its `file` by more than the 10% tolerance THEN the system leaves the stored
phases value stale and reports no error.

1.2 WHEN `python senzing-bootcamp/scripts/measure_steering.py --check` runs against an
index whose `phases.*.token_count` values have drifted beyond tolerance THEN the
system exits 0 ("All token counts are within 10% tolerance.") because `check_counts`
inspects only the `file_metadata` block and never the `phases` map.

1.3 WHEN `python senzing-bootcamp/scripts/measure_steering.py` runs in update mode
THEN the system rewrites `file_metadata` and `budget` but leaves every
`phases.*.token_count` untouched, so update mode cannot repair phase drift.

1.4 WHEN the agent reads `phases.<phase>.token_count` for a split module to track
cumulative tokens against the context budget (per `agent-instructions.md` "Context
Budget") AND that value under-counts the real file size THEN the agent
under-estimates the load cost and can exceed the 60%/80% thresholds.

1.5 WHEN a corrected count would cross a `size_category` boundary (e.g.
`module-05-phase2-data-mapping.md` at a measured 3128 tokens exceeds the 2000
medium/large boundary) THEN the stored phases `size_category` remains inconsistent
with the stored phases `token_count` (it still reads `medium`).

### Expected Behavior (Correct)

2.1 WHEN a split-module phase entry's `token_count` differs from the measured token
count of its `file` by more than the 10% tolerance THEN the system SHALL update that
phases `token_count` to the measured count so it is within tolerance.

2.2 WHEN `python senzing-bootcamp/scripts/measure_steering.py --check` runs against an
index whose `phases.*.token_count` values have drifted beyond tolerance THEN the
system SHALL report the phase mismatch and exit non-zero (fail CI), validating both
the `file_metadata` block AND the `phases` map.

2.3 WHEN `python senzing-bootcamp/scripts/measure_steering.py` runs in update mode
THEN the system SHALL refresh every `phases.*.token_count` (and dependent
`size_category`) to match the measured count of each phase's `file`, in addition to
refreshing `file_metadata` and `budget`.

2.4 WHEN the agent reads `phases.<phase>.token_count` for a split module after the fix
THEN the system SHALL provide a value within tolerance of the real file size so the
agent's cumulative-token budget tracking is accurate.

2.5 WHEN a corrected phase `token_count` crosses a `size_category` boundary THEN the
system SHALL update that phase's `size_category` using the same boundaries
`measure_steering.py` already applies (`< 500` → small, `<= 2000` → medium, `> 2000`
→ large).

2.6 WHEN `python senzing-bootcamp/scripts/measure_steering.py --check` runs after the
reconciliation THEN the system SHALL pass with both the `file_metadata` block and the
`phases` map validated, and the documented 10% tolerance SHALL apply to phases too.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `measure_steering.py --check` validates the `file_metadata` block THEN the
system SHALL CONTINUE TO apply the existing 10% tolerance and the existing
missing/removed-file detection exactly as before.

3.2 WHEN a phase entry maps 1:1 to a file whose `file_metadata.token_count` is already
within tolerance of the measured count THEN the system SHALL CONTINUE TO leave that
phases `token_count` value unchanged.

3.3 WHEN update mode writes the index THEN the system SHALL CONTINUE TO preserve the
`budget` block (`total_tokens`, `reference_window`, `warn_threshold_pct`,
`critical_threshold_pct`, `split_threshold_tokens`), the `keywords`, `languages`, and
`deployment` maps, and each module's `root`, `step_range`, and structure, except where
a `token_count` (and its dependent `size_category`) correction is required.

3.4 WHEN the scripts are run THEN the system SHALL CONTINUE TO use the Python standard
library only (no new third-party dependencies), per `tech.md`.

3.5 WHEN the CI pipeline runs THEN `validate_power.py`, `validate_commonmark.py`, and
`sync_hook_registry.py --verify` SHALL CONTINUE TO pass, and all other scripts,
steering files, and hooks SHALL remain untouched.

3.6 WHEN a phase `token_count` is already within the 10% tolerance of its file's
measured count (e.g. `modules.11.phases.phase1-packaging` at 3214 vs 3289) THEN the
system SHALL CONTINUE TO treat it as valid and SHALL NOT flag it.

## Bug Condition Derivation

### Definitions

- **F**: the original (unfixed) `measure_steering.py` — `--check` validates only
  `file_metadata`; update mode rewrites only `file_metadata` and `budget`.
- **F'**: the fixed `measure_steering.py` — `--check` and update mode also process the
  `phases.*.token_count` (and dependent `size_category`) entries.
- **X**: an entry in `steering-index.yaml`. A *phase entry* is any
  `modules.<N>.phases.<phase>` (and analogously `onboarding.*` / `session-resume.*`
  phase entries) that has a `file` and a `token_count`.
- **measured_tokens(file)**: `round(len(read_text(file)) / 4)` — the same measure the
  script already uses for `file_metadata`.
- **tolerance**: `0.10` — the same tolerance the script applies to `file_metadata`.

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X — an entry in steering-index.yaml
  OUTPUT: boolean

  // Only split-module phase entries (with a file + token_count) can be buggy.
  IF NOT isPhaseEntry(X) THEN
    RETURN false
  END IF

  measured ← measured_tokens(X.file)
  RETURN abs(X.token_count - measured) / max(measured, 1) > tolerance
END FUNCTION
```

Example (Module 3 visualization):

```pascal
// X.file = "module-03-phase2-visualization.md", X.token_count = 2035
// measured = 5312
// abs(2035 - 5312) / 5312 = 0.617 > 0.10  → isBugCondition = true
```

### Fix-Checking Property

```pascal
// Property: Fix Checking — phase token counts are reconciled and validated
FOR ALL X WHERE isPhaseEntry(X) DO
  measured ← measured_tokens(X.file)
  // After the fix, every phase entry is within tolerance...
  ASSERT abs(F'(X).token_count - measured) / max(measured, 1) <= tolerance
  // ...and its size_category is consistent with the corrected count.
  ASSERT F'(X).size_category = classify_size(F'(X).token_count)
END FOR

// And the CLI now validates the phases block:
ASSERT run("measure_steering.py --check") reports the phases map as validated
       AND exits 0 on a reconciled index
       AND exits non-zero (with a phase mismatch report) on a drifted index
```

### Preservation-Checking Property

```pascal
// Property: Preservation Checking — everything that is not a drifted phase entry
// behaves identically under F and F'.
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Concretely, this means:

- `file_metadata` validation, tolerance, and missing/removed detection are identical
  under F and F'.
- The `budget` block, `keywords`, `languages`, `deployment`, and each module's
  `root` / `step_range` / structure are byte-preserved except where a `token_count`
  (and dependent `size_category`) correction is required.
- Phase entries already within tolerance (e.g. `module-11-deployment.md` phase1 at
  3214 vs 3289) are left unchanged.

### Counterexample (demonstrates the bug)

```
$ python senzing-bootcamp/scripts/measure_steering.py --check
All token counts are within 10% tolerance.   # exits 0

# ...yet modules.3.phases.phase2-visualization.token_count = 2035
#    while module-03-phase2-visualization.md measures 5312 (61.7% drift).
# The agent budgeting on 2035 under-counts the real 5312-token load.
```
