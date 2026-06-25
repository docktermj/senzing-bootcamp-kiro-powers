# Bugfix Requirements Document

## Introduction

A deep-dive audit of branch `1-docktermj-4` (HEAD `56b91b4`) of the senzing-bootcamp Kiro Power found that the project is **not** in the green, fully-consistent state claimed by the recently-completed `bootcamp-consistency-fixes` spec. All 14 standalone CI validators pass and `validate_power.py` reports structural integrity, but the actual full test run

```text
python3 -m pytest senzing-bootcamp/tests/ tests/
```

reports `5 failed, 4816 passed, 86 skipped` (~158s on Python 3.12.3, pytest 9.0.3, Hypothesis 6.152.3). In addition, one validator (`validate_mandatory_gates.py`) passes **vacuously** because it cannot see the gates that actually ship, and the `CHANGELOG.md` `[Unreleased]` section omits work already committed on this branch.

This spec fixes the remaining "broken or incomplete" defects that the prior spec missed or knowingly deferred. The prior spec's `tasks.md` Task 7.4b explicitly EXCLUDED three of these test failures as "likely pre-existing independent property bugs, handle separately" — but they were never handled, yet the spec was marked complete. These are **independent** defects. This work is **additive**: it does not duplicate or revert anything from `bootcamp-consistency-fixes`.

The defects are organized into independent groups:

- **Group A** — Five failing tests (A1 real product bug; A2/A3/A4 test-logic bugs; A5 flaky timing).
- **Group B** — `validate_mandatory_gates.py` passes vacuously (validator coverage hole) plus a missing regression test.
- **Group C** — `CHANGELOG.md` `[Unreleased]` is out of sync with committed work.
- **Group D** — (Low severity) `validate_prerequisites.py` emits a spurious keyword-mismatch warning for the 3→4 gate.

### Global Constraints (apply to every fix below)

- Scripts MUST remain stdlib-only (PyYAML permitted only in `validate_dependencies.py`, unchanged).
- No currently-passing validator may be weakened or broken.
- The real per-file ±10% token tolerance enforced in `measure_steering.py` MUST NOT be relaxed.
- For A1–A4, the fix MUST explicitly land on the side (product code vs test) that encodes the correct contract, with justification (captured per-group below).

### Code-vs-Test Decision Summary (A1–A4)

| ID | Fix side | Justification |
|----|----------|---------------|
| A1 | **Product code** (`preferences_utils.py`) | Round-trip data fidelity is a product contract: a stored string value must survive write→read unchanged. Coercing the string `'FalSe'` to boolean `False` is genuine data loss. |
| A2 | **Test** (`test_assess_entry_point.py`) | `_normalize_path('.')` returning a `Path` whose `.parts == ()` is correct path semantics (`project_dir / Path('.')` == `project_dir`). The test's expectation that `parts == ['.']` encodes an incorrect contract for the degenerate `'.'` segment. |
| A3 | **Test** (`test_generate_recap_pdf.py`) | The `format → parse` round-trip faithfully preserves document (input) order. The `st_sorted_timestamps` strategy clamps month/day and draws `second` independently *after* sorting at minute granularity, so its claimed "sorted" invariant can break. The bug is in the strategy, not the product. |
| A4 | **Test** (`test_token_budget_optimization.py`) | The test self-generates a `stored` value that can deviate >10% from `measured` and then asserts deviation ≤10%. The flaw is in the test's own generation/threshold logic. The production ±10% check in `measure_steering.py` is correct and must be preserved. |

---

## Bug Analysis

### Current Behavior (Defect)

**Group A — Test suite is not green (5 failing tests)**

1.1 WHEN `test_session_persistence_properties.py::TestPropertyFieldPreservation::test_writing_one_field_preserves_others` runs with `prefs={'pacing_overrides': {'0': 'FalSe'}}` and then calls `write_preference('language', 'python')` THEN the system reloads `pacing_overrides` as `{'0': False}` instead of `{'0': 'FalSe'}`, failing with `Field 'pacing_overrides' was modified: expected {'0': 'FalSe'}, got {'0': False}` — the YAML-ish read/write path in `preferences_utils.py` coerces boolean-like strings (any case) to Python booleans.

1.2 WHEN `test_assess_entry_point.py::TestPathSeparatorNormalization::test_result_is_valid_path` runs with input `'.'` (segments `['.']`) THEN `_normalize_path('.')` returns a `Path` whose `.parts` is `()`, and the test fails with `Path parts [] != segments ['.']`.

1.3 WHEN `test_generate_recap_pdf.py::TestModuleOrdering::test_sections_preserve_chronological_order` runs with two sections whose generated timestamps fall one second apart THEN after a `format_recap_document` → `parse_recap_markdown` round-trip the parsed order is reported as non-chronological (e.g. `'2026-08-28T00:00:01'` appears before `'2026-08-28T00:00:00'`) and the assertion fails — because the test's timestamp-generation strategy does not actually guarantee the sorted ordering it asserts.

1.4 WHEN `test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_stored_token_count_within_tolerance_of_measured` runs with `content_length=70` (→ `measured=18`, `tolerance_factor=0.0859`, `stored=round(18*1.0859)=20`) THEN the test asserts deviation `≤ 0.10` but the actual deviation is `2/18 = 11.11%`, so the test fails on a value it generated itself — the small-integer rounding allowance only forgives an absolute difference of 1, while this case produces an absolute difference of 2.

1.5 WHEN `test_track_reorganization.py::TestProperty1NoLegacyIdentifiersInFiles::test_no_legacy_id_in_bootcamp_files` runs in CI and per-example file scanning exceeds the Hypothesis deadline THEN the test fails intermittently with `hypothesis.errors.DeadlineExceeded` (e.g. `Test took 284.63ms, which exceeds the deadline of 200.00ms`) — a flaky timing failure, not a product defect.

**Group B — `validate_mandatory_gates.py` passes vacuously**

2.1 WHEN `python3 senzing-bootcamp/scripts/validate_mandatory_gates.py` is run against the shipped steering corpus THEN it prints `No mandatory gates found in steering files.` and exits `0`, even though module steering files contain `⛔ MANDATORY GATE` markers (e.g. `module-02-sdk-setup.md` `## Step 5: Configure License` and `module-03-phase2-visualization.md` `## Step 9`).

2.2 WHEN `_parse_gates_from_file` scans a steering file THEN its `step_pattern = re.compile(r"^###\s+Step\s+(\d+):", re.MULTILINE)` matches only H3 `### Step N:` headings, so gates living under H2 `## Step N:` headings (and bold-blockquote `> ⛔ **MANDATORY GATE` forms) are never seen, causing the validator to find zero gates and provide no protection.

2.3 WHEN the test suite runs THEN no test exercises the validator's own `parse_mandatory_gates` / `parse_file_gates` against the real steering corpus to assert a non-empty expected gate set, so the vacuous pass goes undetected (existing `test_mandatory_gate_preservation.py` and friends use their own regex `r"⛔\s*\**\s*MANDATORY\s*GATE"` and never call the validator's parser).

**Group C — CHANGELOG out of date**

3.1 WHEN a reader consults `senzing-bootcamp/CHANGELOG.md` `[Unreleased]` THEN it does not mention the consistency-fix work already committed on this branch (commit `56b91b4` "bootcamp-consistency-fixes"): the `lint_steering.py` union-registry-source fix, the `measure_steering.py` additive aggregate check (`parse_budget_total` + "Budget total mismatch" enforcement), the `steering-index.yaml` `budget.total_tokens` correction `169633 → 169576`, and the 147-test onboarding-split re-target — so the CHANGELOG does not accurately reflect shipped changes.

**Group D — (Low severity) prerequisites gate keyword warning**

4.1 WHEN `python3 senzing-bootcamp/scripts/validate_prerequisites.py` runs THEN it emits `WARNING: Gate '3->4': keyword 'including the step 9 web service + visualization (cannot be skipped)' not found in module 3 steering content`, because the requirement string in `config/module-dependencies.yaml` is split on commas into a keyword fragment that does not appear verbatim in module 3 steering content (a warning, not an error).

### Expected Behavior (Correct)

**Group A**

5.1 WHEN `test_writing_one_field_preserves_others` runs with `prefs={'pacing_overrides': {'0': 'FalSe'}}` and `write_preference('language', 'python')` THEN the system SHALL reload `pacing_overrides` as `{'0': 'FalSe'}` (string value preserved exactly), and the fix SHALL live in product code (`preferences_utils.py`) so that every string value written survives a write→read round-trip unchanged regardless of case.

5.2 WHEN `test_result_is_valid_path` runs with the degenerate input `'.'` THEN the test SHALL accept the path-semantics-correct result (`_normalize_path('.')` yielding a path equivalent to "current directory"), with the fix landing in the test's segment expectation; `_normalize_path` SHALL remain unchanged because it already returns a semantically correct path.

5.3 WHEN `test_sections_preserve_chronological_order` runs THEN the test SHALL construct input sections whose timestamps are genuinely in non-decreasing chronological order (or sort the document by timestamp before formatting), so that the `format → parse` round-trip's faithful preservation of document order satisfies the assertion; the fix SHALL live in the test, and `format_recap_document` / `parse_recap_markdown` SHALL remain unchanged.

5.4 WHEN `test_stored_token_count_within_tolerance_of_measured` runs THEN the test SHALL generate `stored` values that cannot deviate more than the asserted threshold from `measured` (i.e. the generation and the assertion SHALL be mutually consistent so the test cannot self-falsify), with the fix in the test only; the real ±10% per-file check in `measure_steering.py` SHALL NOT be weakened.

5.5 WHEN `test_no_legacy_id_in_bootcamp_files` runs in CI THEN it SHALL complete deterministically without `DeadlineExceeded` — achieved by setting an appropriate `@settings(deadline=...)` (or `deadline=None`) and/or hoisting the bootcamp-file reads out of the per-example body — while still asserting that no legacy identifiers appear in bootcamp files.

**Group B**

6.1 WHEN `validate_mandatory_gates.py` runs against the shipped steering corpus THEN it SHALL parse the real mandatory gates by recognizing both H2 (`## Step N:`) and H3 (`### Step N:`) `Step N:` headings, and the bold-blockquote `> ⛔ **MANDATORY GATE` form, so that it finds the non-empty set of gates that actually ship and does not print `No mandatory gates found`.

6.2 WHEN gates are found that map to known required checkpoints (e.g. Module 3 Step 9 → `web_service`, `web_page`) THEN the validator SHALL continue to perform its existing per-gate cross-reference checks against progress and exit with the correct code.

6.3 WHEN the test suite runs THEN a new regression test SHALL invoke the validator's own parser against the real steering corpus, assert it finds the expected non-empty set of mandatory gates, and fail (non-zero/assertion) if zero gates are found when some are expected — so a future regression to vacuous passing is caught.

**Group C**

7.1 WHEN a reader consults `CHANGELOG.md` `[Unreleased]` after the fix THEN it SHALL accurately describe the committed consistency-fix work: the `lint_steering.py` union-registry-source fix, the `measure_steering.py` additive aggregate check (`parse_budget_total` + "Budget total mismatch" enforcement), the `steering-index.yaml` `budget.total_tokens` `169633 → 169576` correction, and the 147-test onboarding-split re-target.

**Group D**

8.1 WHEN `validate_prerequisites.py` runs after the fix THEN it SHALL NOT emit the spurious `3->4` keyword-mismatch warning — achieved either by rewording the requirement string in `config/module-dependencies.yaml` so its comma-split keywords appear verbatim in module 3 steering, or by adjusting the keyword-extraction so config and steering are consistent — while continuing to surface genuine gate/keyword mismatches.

### Unchanged Behavior (Regression Prevention)

**Group A**

9.1 WHEN `write_preference` / `parse_yaml` processes a genuine boolean field (a value that was written as a Python `bool`, e.g. `license_guidance_deferred: true`) THEN the system SHALL CONTINUE TO round-trip it as a Python boolean.

9.2 WHEN `_normalize_path` receives a normal manifest path (e.g. `'data/raw/'` or `'data\\raw\\'`) THEN it SHALL CONTINUE TO return the same platform-native `Path` as before, and `test_result_is_valid_path` SHALL CONTINUE TO pass for all non-degenerate segment inputs.

9.3 WHEN `format_recap_document` → `parse_recap_markdown` processes any already-chronological document THEN it SHALL CONTINUE TO preserve section order, and every other test in `test_generate_recap_pdf.py` SHALL CONTINUE TO pass.

9.4 WHEN `measure_steering.py` checks per-file token counts THEN it SHALL CONTINUE TO enforce the real ±10% tolerance unchanged, and the additive aggregate "Budget total mismatch" check SHALL CONTINUE TO pass.

9.5 WHEN `test_track_reorganization.py` runs THEN it SHALL CONTINUE TO detect any real legacy identifier present in bootcamp files (the deadline/hoisting change SHALL NOT reduce its detection coverage).

9.6 WHEN the full suite `python3 -m pytest senzing-bootcamp/tests/ tests/` runs THEN all 4816 currently-passing tests SHALL CONTINUE TO pass (no regressions introduced by any fix).

**Group B**

10.1 WHEN `validate_mandatory_gates.py` runs against a steering file that genuinely contains no `⛔ MANDATORY GATE` markers THEN it SHALL CONTINUE TO report zero gates for that file and behave as before.

10.2 WHEN the validator performs its existing per-gate checkpoint cross-reference and `skipped_steps` / `NON_SKIPPABLE_GATES` logic THEN that behavior SHALL CONTINUE TO function unchanged.

10.3 WHEN the existing `test_mandatory_gate_preservation.py` and related suites run THEN they SHALL CONTINUE TO pass (the new regression test is additive and SHALL NOT alter their behavior).

**Group C**

11.1 WHEN the CHANGELOG is updated THEN existing `[Unreleased]`, `[0.12.0]`, and `[0.11.0]` entries SHALL CONTINUE TO remain accurate and SHALL NOT be removed or revert prior content (the C fix is additive documentation only).

11.2 WHEN `validate_commonmark.py` runs against the updated CHANGELOG THEN it SHALL CONTINUE TO pass.

**Group D**

12.1 WHEN `validate_prerequisites.py` evaluates all other gates THEN they SHALL CONTINUE TO pass with no new warnings or errors.

12.2 WHEN `module-dependencies.yaml` is consumed by any other script or test (e.g. `validate_dependencies.py`) THEN those consumers SHALL CONTINUE TO parse and pass unchanged.

**All groups**

13.1 WHEN the full CI validator set runs (`validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, and all 14 standalone validators) THEN every validator SHALL CONTINUE TO pass.

13.2 WHEN any script is changed THEN it SHALL CONTINUE TO be stdlib-only (no new third-party dependency introduced).

13.3 WHEN this spec's fixes are applied THEN they SHALL NOT duplicate or revert any change shipped by the prior `bootcamp-consistency-fixes` spec.

---

## Bug Condition Derivation

The bug condition `isBugCondition(X)` identifies the inputs that trigger each defect; the property `P` defines correct behavior on those inputs; the preservation goal pins all non-buggy inputs to be unchanged. **F** is the original code/test; **F'** is the fixed code/test.

### A1 — Boolean-like string coercion (product code)

```pascal
FUNCTION isBugCondition(X)
  INPUT: X = a stored preference value (possibly nested)
  OUTPUT: boolean
  // String whose lowercase form is a YAML boolean literal but whose
  // original casing/spelling must be preserved as a string.
  RETURN X is a string AND lower(X) IN {"true", "false"} AND X NOT IN {"true", "false"}
END FUNCTION
```

```pascal
// Property: Fix Checking — string fidelity through write->read round-trip
FOR ALL X WHERE isBugCondition(X) DO
  result <- read(write(X))          // F' = fixed preferences_utils round-trip
  ASSERT result = X AND type(result) = string
END FOR
```

```pascal
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT read_F(write_F(X)) = read_F'(write_F'(X))   // genuine bools, ints, plain strings unchanged
END FOR
```

### A2 — Degenerate "." path segment (test)

```pascal
FUNCTION isBugCondition(segments)
  INPUT: segments = list of path segments fed to the test
  OUTPUT: boolean
  RETURN segments yields a normalized path with no parts (e.g. ["."] or only "."/empty)
END FUNCTION
```

```pascal
// Property: Fix Checking — test accepts correct path semantics for degenerate input
FOR ALL segments WHERE isBugCondition(segments) DO
  ASSERT test_accepts(_normalize_path(join(segments)))   // F' = fixed test expectation
END FOR
// Preservation: for NOT isBugCondition, _normalize_path output AND test outcome unchanged.
```

### A3 — Chronological ordering round-trip (test)

```pascal
FUNCTION isBugCondition(sections)
  INPUT: sections produced by the test strategy
  OUTPUT: boolean
  RETURN the strategy emitted sections whose timestamps are NOT actually non-decreasing
END FUNCTION
```

```pascal
// Property: Fix Checking — strategy guarantees its own invariant
FOR ALL sections GENERATED BY F'(strategy) DO
  ASSERT timestamps(sections) are non-decreasing
  ASSERT order_preserved(parse(format(sections)))
END FOR
// Preservation: format_recap_document / parse_recap_markdown unchanged; all other recap tests pass.
```

### A4 — Self-falsifying tolerance test (test)

```pascal
FUNCTION isBugCondition(measured, tolerance_factor)
  INPUT: generated measured count and tolerance_factor
  OUTPUT: boolean
  // stored = round(measured * (1 + tolerance_factor)) can deviate > threshold
  // for small measured where abs(stored - measured) >= 2.
  RETURN deviation(round(measured*(1+tolerance_factor)), measured) > 0.10
END FUNCTION
```

```pascal
// Property: Fix Checking — generated stored cannot exceed the asserted threshold
FOR ALL (measured, tolerance_factor) GENERATED BY F'(test) DO
  stored <- generate_stored(measured, tolerance_factor)
  ASSERT deviation(stored, measured) <= asserted_threshold
END FOR
// Preservation: production +/-10% per-file check in measure_steering.py is UNCHANGED.
```

### A5 — Flaky deadline (test)

```pascal
FUNCTION isBugCondition(run)
  INPUT: a CI test run of test_no_legacy_id_in_bootcamp_files
  OUTPUT: boolean
  RETURN per_example_wall_time(run) > hypothesis_deadline
END FUNCTION
```

```pascal
// Property: Fix Checking — determinism
FOR ALL runs UNDER F' DO
  ASSERT no DeadlineExceeded
  ASSERT detection_coverage(F') = detection_coverage(F)   // still finds any real legacy id
END FOR
```

### B — Vacuous mandatory-gate validator (product code + test)

```pascal
FUNCTION isBugCondition(corpus)
  INPUT: shipped steering corpus
  OUTPUT: boolean
  // Gates exist under H2 "## Step N:" or bold-blockquote form that the
  // H3-only regex cannot see.
  RETURN exists gate in corpus NOT matched by current step_pattern
END FUNCTION
```

```pascal
// Property: Fix Checking — non-vacuous parsing + regression test
FOR ALL corpus WHERE isBugCondition(corpus) DO
  gates <- parse_mandatory_gates'(corpus)     // F' recognizes H2, H3, and blockquote forms
  ASSERT gates is non-empty AND includes the known shipped gates
END FOR
```

```pascal
// Property: Preservation Checking
FOR ALL corpus WHERE NOT isBugCondition(corpus) DO        // files with genuinely no gates
  ASSERT parse_mandatory_gates(corpus) = []               // unchanged
  ASSERT per_gate_cross_reference_checks unchanged
END FOR
```

### C — CHANGELOG sync (documentation)

```pascal
FUNCTION isBugCondition(changelog)
  OUTPUT: boolean
  RETURN [Unreleased] omits any of: lint_steering union fix,
         measure_steering additive aggregate check,
         steering-index total_tokens 169633->169576,
         147-test onboarding-split re-target
END FUNCTION
// Property: after fix, [Unreleased] documents all four; prior entries unchanged; CommonMark still passes.
```

### D — Prerequisites keyword warning (config / extraction)

```pascal
FUNCTION isBugCondition(gate)
  OUTPUT: boolean
  RETURN gate = "3->4" AND a comma-split keyword fragment is absent verbatim from module 3 steering
END FUNCTION
// Property: after fix, no spurious 3->4 warning; genuine mismatches still reported; other gates unchanged.
```

### Success Criterion (overall)

```text
python3 -m pytest senzing-bootcamp/tests/ tests/   ->  0 failed (deterministically, incl. A5)
validate_mandatory_gates.py                        ->  parses shipped gates (non-vacuous), covered by a test
CHANGELOG.md [Unreleased]                          ->  reflects committed consistency-fix work
all 14 standalone validators + CI validator set    ->  continue to pass
scripts                                            ->  remain stdlib-only; +/-10% per-file token check unchanged
```
