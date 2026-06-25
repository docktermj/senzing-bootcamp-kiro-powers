# Bugfix Requirements Document

## Introduction

The `senzing-bootcamp` Kiro Power's design is coherent and complete, and every standalone CI validator passes (`validate_power`, `validate_dependencies`, `validate_prerequisites`, `validate_mandatory_gates`, `validate_governance_rules`, `validate_yaml_schemas`, `compose_hook_prompts --verify`, `sync_hook_registry --verify`, `validate_commonmark`, `measure_steering --check`). However, an audit on feature branch `1-docktermj-4` found that the test suite and internal data have drifted away from the shipped steering content during an in-flight onboarding refactor (visible in the CHANGELOG `[Unreleased]` section).

This results in three distinct, independent defects:

1. **Onboarding-split test drift** — ~90+ of 147 failing tests still assert that onboarding content lives in the old file after it was intentionally moved to a new phase file. (147 total tests fail across `senzing-bootcamp/tests/` and `tests/`.)
2. **`steering-index.yaml` token-budget mismatch** — the declared aggregate `budget.total_tokens` is off by 57 from the sum of per-file token counts, caught by a property test but missed by `measure_steering --check`.
3. **`lint_steering.py` self-contradiction** — the linter emits false positives (claims 14 documented hooks are undocumented), contradicting `sync_hook_registry --verify`, and exits 0 even when it reports an error.

The fix corrects tests, data, and scripts to match the shipped design. The new onboarding file layout is correct and intentional and MUST be preserved — the onboarding split must NOT be reverted.

## Bug Analysis

### Current Behavior (Defect)

**BUG 1 — Onboarding-split test drift**

The welcome banner, the "Programming Language Selection" step, and comprehension-check steps (3, 4, 4b, 4c) were moved OUT of `senzing-bootcamp/steering/onboarding-flow.md` INTO `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`. The steering files are coherent and cross-reference each other correctly (`onboarding-flow.md` directs "After Step 2d, load `onboarding-phase1b-intro-language.md`"), but many tests and preservation snapshots still look in the old file.

1.1 WHEN the test suite runs `senzing-bootcamp/tests/` and `tests/` THEN 147 tests fail because they assert onboarding content (welcome banner, language-selection step, comprehension checks 3/4/4b/4c) lives in `onboarding-flow.md` instead of `onboarding-phase1b-intro-language.md`.
1.2 WHEN `test_comprehension_check.py` runs THEN it fails (27 failures) because it expects comprehension-check steps in the old file location / old heading sequence.
1.3 WHEN `test_disambiguate_language_prompt.py` runs THEN it fails (12 failures) because it expects the language-selection prompt in `onboarding-flow.md`.
1.4 WHEN `test_missing_pointer_marker_preservation.py` and `test_missing_pointer_marker_exploration.py` run THEN they fail (10 and 6 failures) against the old onboarding layout.
1.5 WHEN `test_onboarding_question_ownership.py` runs THEN it fails (7 failures) because question ownership is asserted against the old file.
1.6 WHEN `test_track_selection_gate_preservation.py`, `test_onboarding_ux_improvements.py`, and `test_onboarding_flow_restructuring.py` run THEN they fail (5 failures each) against old heading sequences / file locations.
1.7 WHEN `test_typescript_language_maturity.py` runs THEN it fails (3 failures) because the language-maturity content moved with the language-selection step.
1.8 WHEN `tests/test_bootcamp_ux_preservation.py` runs THEN it fails because it asserts the welcome banner text in the old file.
1.9 WHEN `test_version_unit.py` and the remaining tests in the 147-failure set run THEN they fail because their snapshots/assertions reference the pre-split onboarding structure.

**BUG 2 — `steering-index.yaml` token-budget mismatch**

`senzing-bootcamp/steering/steering-index.yaml` declares `budget.total_tokens: 169633`, but the sum of all `file_metadata` `token_count` entries is `169576` — a difference of 57.

1.10 WHEN `test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_actual_steering_index_total_tokens_equals_sum` runs THEN it fails because the declared `budget.total_tokens` (169633) does not equal the sum of per-file `token_count` values (169576).
1.11 WHEN `measure_steering.py --check` runs THEN it passes despite the mismatch, because it only validates per-file ±10% tolerance and never validates the aggregate total — so the inconsistency escapes the validator.

**BUG 3 — `lint_steering.py` self-contradiction / false positives**

`senzing-bootcamp/scripts/lint_steering.py` reports 1 error and 27 warnings. It reads the wrong hook-registry source, producing false "not documented in the hook registry" claims for hooks that are in fact documented, and it exits 0 even though it reports an error.

1.12 WHEN `lint_steering.py` runs THEN it reports that 14 hook files (e.g. `verify-sdk-setup`, `security-scan-on-save`, `run-tests-after-change`, `gate-module3-visualization`) are "not documented in the hook registry", even though those hooks are documented in `hook-registry.md` and `hook-registry-modules.md`.
1.13 WHEN `lint_steering.py` and `sync_hook_registry.py --verify` are both run THEN they disagree: `sync_hook_registry --verify` passes (hooks are documented) while `lint_steering.py` reports them as undocumented.
1.14 WHEN `lint_steering.py` reports 1 or more errors THEN it still exits with code 0 instead of a non-zero exit code.

### Expected Behavior (Correct)

**BUG 1 — Onboarding-split test drift**

2.1 WHEN the test suite runs `senzing-bootcamp/tests/` and `tests/` THEN the full suite SHALL pass (green), validating the actual shipped onboarding structure.
2.2 WHEN `test_comprehension_check.py` runs THEN it SHALL assert comprehension-check steps (3, 4, 4b, 4c) in `onboarding-phase1b-intro-language.md` and pass.
2.3 WHEN `test_disambiguate_language_prompt.py` runs THEN it SHALL assert the language-selection prompt in `onboarding-phase1b-intro-language.md` and pass.
2.4 WHEN `test_missing_pointer_marker_preservation.py` and `test_missing_pointer_marker_exploration.py` run THEN they SHALL reference the new onboarding file layout and pass.
2.5 WHEN `test_onboarding_question_ownership.py` runs THEN it SHALL assert question ownership against the file that now owns each question and pass.
2.6 WHEN `test_track_selection_gate_preservation.py`, `test_onboarding_ux_improvements.py`, and `test_onboarding_flow_restructuring.py` run THEN they SHALL validate the post-split heading sequences / file locations and pass.
2.7 WHEN `test_typescript_language_maturity.py` runs THEN it SHALL assert language-maturity content in `onboarding-phase1b-intro-language.md` and pass.
2.8 WHEN `tests/test_bootcamp_ux_preservation.py` runs THEN it SHALL assert the welcome banner text in `onboarding-phase1b-intro-language.md` and pass.
2.9 WHEN `test_version_unit.py` and the remaining tests in the 147-failure set run THEN their snapshots/assertions SHALL reference the post-split onboarding structure and pass.

**BUG 2 — `steering-index.yaml` token-budget mismatch**

2.10 WHEN `test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_actual_steering_index_total_tokens_equals_sum` runs THEN it SHALL pass because `budget.total_tokens` equals the sum of per-file `token_count` values (169576).
2.11 WHEN `measure_steering.py --check` runs THEN it SHALL validate the aggregate total against the sum of per-file `token_count` entries and fail if they diverge, keeping the budget total in sync going forward.

**BUG 3 — `lint_steering.py` self-contradiction / false positives**

2.12 WHEN `lint_steering.py` runs THEN it SHALL read the correct hook-registry source (`hook-registry.md` / `hook-registry-modules.md`) so its hook-documentation checks produce no false positives for documented hooks.
2.13 WHEN `lint_steering.py` and `sync_hook_registry.py --verify` are both run THEN their hook-documentation conclusions SHALL agree.
2.14 WHEN `lint_steering.py` reports 1 or more errors THEN it SHALL exit with a non-zero exit code.
2.15 WHEN `lint_steering.py` evaluates `module-03-visualization-api-reference.md` THEN its legitimate findings (missing first-read instruction, missing Before/After block, missing success indicator) SHALL either be resolved in that steering file or correctly classified so the linter's output is accurate.

### Unchanged Behavior (Regression Prevention)

**Onboarding steering content (the intentional split must be preserved)**

3.1 WHEN onboarding content is referenced THEN the system SHALL CONTINUE TO keep the welcome banner, "Programming Language Selection" step, and comprehension-check steps (3, 4, 4b, 4c) in `onboarding-phase1b-intro-language.md` (the split is NOT reverted).
3.2 WHEN `onboarding-flow.md` is read THEN the system SHALL CONTINUE TO direct "After Step 2d, load `onboarding-phase1b-intro-language.md`" and keep the steering files' correct cross-references intact.
3.3 WHEN the onboarding steering files are inspected THEN the system SHALL CONTINUE TO present the coherent, complete post-split structure unchanged by this fix.

**Validators that currently pass**

3.4 WHEN the standalone CI validators run (`validate_power`, `validate_dependencies`, `validate_prerequisites`, `validate_mandatory_gates`, `validate_governance_rules`, `validate_yaml_schemas`, `compose_hook_prompts --verify`, `sync_hook_registry --verify`, `validate_commonmark`, `measure_steering --check`) THEN they SHALL CONTINUE TO pass.
3.5 WHEN `measure_steering.py --check` validates per-file token counts THEN it SHALL CONTINUE TO enforce the existing per-file ±10% tolerance (the new aggregate check is additive, not a replacement).
3.6 WHEN tests that already pass run (the non-failing tests outside the 147-failure set) THEN they SHALL CONTINUE TO pass unchanged.

**Steering data and hook registry**

3.7 WHEN per-file `token_count` entries in `steering-index.yaml` are read THEN they SHALL CONTINUE TO hold their existing values (only the aggregate `budget.total_tokens` is corrected to 169576).
3.8 WHEN the hook registry is inspected THEN the 14 hooks flagged by the linter (e.g. `verify-sdk-setup`, `security-scan-on-save`, `run-tests-after-change`, `gate-module3-visualization`) SHALL CONTINUE TO be documented in `hook-registry.md` and `hook-registry-modules.md` (the fix corrects the linter's source, not the registry).
3.9 WHEN `sync_hook_registry.py --verify` runs after the fix THEN it SHALL CONTINUE TO pass with its current behavior.

## Bug Condition Summary

Each bug is a distinct condition `C(X)` over the codebase state; the fix `F'` must satisfy the property `P` for all `C(X)` inputs while preserving `F(X) = F'(X)` for all `¬C(X)` inputs.

**BUG 1 — Onboarding-split test drift**

```pascal
FUNCTION isBugCondition_1(test)
  INPUT: test of type TestCase
  OUTPUT: boolean

  // True when a test/snapshot asserts onboarding content
  // in the OLD file location/heading sequence
  RETURN test asserts welcome-banner OR language-selection-step
         OR comprehension-checks(3,4,4b,4c)
         AND test expects them in onboarding-flow.md (pre-split layout)
END FUNCTION
```

```pascal
// Property: Fix Checking — tests validate the shipped post-split layout
FOR ALL test WHERE isBugCondition_1(test) DO
  result <- run(test')   // test updated to reference onboarding-phase1b-intro-language.md
  ASSERT result = PASS
END FOR

// Property: Preservation — steering content is unchanged; only tests change
ASSERT onboarding-phase1b-intro-language.md content UNCHANGED
ASSERT onboarding-flow.md cross-references UNCHANGED
FOR ALL test WHERE NOT isBugCondition_1(test) DO
  ASSERT run(test) = run(test')   // previously-passing tests still pass
END FOR
```

**BUG 2 — Token-budget aggregate mismatch**

```pascal
FUNCTION isBugCondition_2(index)
  INPUT: index of type SteeringIndexYaml
  OUTPUT: boolean

  RETURN index.budget.total_tokens != SUM(index.file_metadata[*].token_count)
END FUNCTION
```

```pascal
// Property: Fix Checking — aggregate equals the sum
FOR ALL index WHERE isBugCondition_2(index) DO
  index' <- fix(index)   // set total_tokens = SUM(token_count) = 169576
  ASSERT index'.budget.total_tokens = SUM(index'.file_metadata[*].token_count)
  ASSERT measure_steering(--check) FAILS when aggregate diverges
END FOR

// Property: Preservation — per-file counts and per-file +/-10% check unchanged
FOR ALL file IN index'.file_metadata DO
  ASSERT file.token_count UNCHANGED
END FOR
```

**BUG 3 — Linter false positives and exit code**

```pascal
FUNCTION isBugCondition_3(hook)
  INPUT: hook of type HookFile
  OUTPUT: boolean

  // True when lint_steering.py claims a hook is undocumented
  // but the hook IS in the registry
  RETURN lint_steering reports hook "not documented in the hook registry"
         AND hook documented in (hook-registry.md OR hook-registry-modules.md)
END FUNCTION
```

```pascal
// Property: Fix Checking — no false positives; exit code reflects errors
FOR ALL hook WHERE isBugCondition_3(hook) DO
  ASSERT lint_steering'(hook) does NOT report "not documented"
END FOR
ASSERT lint_steering' agrees with sync_hook_registry --verify
ASSERT (error_count > 0) IMPLIES (exit_code != 0)

// Property: Preservation — registry contents and sync_hook_registry unchanged
ASSERT hook-registry.md UNCHANGED
ASSERT hook-registry-modules.md UNCHANGED
ASSERT sync_hook_registry(--verify) = PASS
END
```
