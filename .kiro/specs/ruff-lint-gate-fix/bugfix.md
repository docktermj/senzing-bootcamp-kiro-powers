# Bugfix Requirements Document

## Introduction

The CI pipeline (`.github/workflows/validate-power.yml`) includes a "Lint Python (ruff)" step that runs:

```
ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/
```

This step currently fails with **438 ruff violations**, leaving the CI pipeline red and blocking release. Every other CI gate passes (validate_power, measure_steering --check, validate_commonmark, validate_dependencies, compose_hook_prompts --verify, sync_hook_registry --verify, lint_steering, validate_prerequisites, validate_progress_ci, validate_mandatory_gates, validate_governance_rules, validate_yaml_schemas, eval_conversations, and pytest at 4,830 passed / 86 skipped / 0 failed).

Among the 438 violations, **3 are genuine correctness defects** (two `F811` redefinitions silently shadow earlier test functions, and one `F601` repeated dict key silently drops a value). The remaining 435 are style violations (E501, E402, F841, E741, W293) configured via `pyproject.toml` (the single source of truth: `target-version = py311`, `line-length = 100`, `lint.select = ["F", "E", "W", "I"]`).

The fix must drive the ruff violation count to zero so the gate exits 0 when run exactly as CI runs it, resolve the 3 correctness defects so that previously-shadowed tests run and the dropped dict entry is restored, and preserve all 4,830 passing tests and every other passing CI gate. Per workspace steering, scripts remain Python 3.11+ stdlib-only (except `validate_dependencies.py` uses PyYAML), tests use pytest + Hypothesis, and everything under `senzing-bootcamp/` ships to users — so the runtime behavior of scripts must not change; only formatting and correctness.

### Violation Breakdown (verified via `ruff check ... --statistics`)

| Count | Code | Description | Category |
|-------|------|-------------|----------|
| 259 | E501 | line-too-long (>100 chars) | Style |
| 141 | E402 | module-import-not-at-top-of-file | Style |
| 29 | F841 | unused-variable | Style |
| 5 | E741 | ambiguous-variable-name | Style |
| 2 | F811 | redefined-while-unused | **Correctness** |
| 1 | F601 | multi-value-repeated-key-literal | **Correctness** |
| 1 | W293 | blank-line-with-whitespace | Style |

### The 3 Correctness Defects (must be fixed first, prioritized over style)

1. `senzing-bootcamp/tests/test_module_closing_question_ownership.py:270` — F811: function `test_module_07_no_inline_questions` redefined (original at line 250 never runs / silent coverage loss).
2. `senzing-bootcamp/tests/test_module_closing_question_ownership.py:279` — F811: function `test_module_07_no_wait_instructions` redefined (original at line 259 never runs).
3. `senzing-bootcamp/tests/test_validate_module.py:55` — F601: dictionary key literal `6` repeated, so one value is silently dropped.

## Bug Analysis

### Current Behavior (Defect)

When CI runs the ruff lint gate exactly as configured, ruff reports 438 violations and the step exits non-zero, turning the pipeline red. Three of those violations represent real correctness defects in the test suite.

1.1 WHEN the CI "Lint Python (ruff)" step runs `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` THEN the system reports 438 violations and exits with a non-zero status, failing the gate and blocking release.

1.2 WHEN `test_module_closing_question_ownership.py` is collected THEN the system silently shadows the first definitions of `test_module_07_no_inline_questions` (line 250) and `test_module_07_no_wait_instructions` (line 259) with the redefinitions at lines 270 and 279, so the original two test bodies never execute (F811).

1.3 WHEN `test_validate_module.py` builds the dictionary literal at line 55 THEN the system silently drops one value because the key literal `6` is repeated, losing the intended entry (F601).

1.4 WHEN any in-scope file contains lines longer than 100 characters, imports placed after other statements, unused local variables, ambiguous single-character variable names, or trailing whitespace on blank lines THEN the system reports E501, E402, F841, E741, and W293 violations respectively, contributing to the non-zero exit.

### Expected Behavior (Correct)

2.1 WHEN the CI "Lint Python (ruff)" step runs `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` THEN the system SHALL report 0 violations and exit 0, passing the gate.

2.2 WHEN `test_module_closing_question_ownership.py` is collected THEN the system SHALL retain two distinct, non-shadowing test functions for the inline-questions check and the wait-instructions check so that both originally-intended test bodies execute (F811 resolved).

2.3 WHEN `test_validate_module.py` builds the dictionary literal at line 55 THEN the system SHALL define each key exactly once so that no intended value is dropped (F601 resolved).

2.4 WHEN any in-scope file is linted THEN the system SHALL report no E501, E402, F841, E741, or W293 violations — remediating them via `ruff check --fix` where safe, manual line reflow for E501, and, where E402 is legitimately required (e.g., `sys.path` manipulation before imports in test/script files), targeted `# noqa: E402` or per-file ignores in `pyproject.toml` rather than restructuring imports.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the full test suite runs (`pytest senzing-bootcamp/tests/ tests/`) THEN the system SHALL CONTINUE TO report 4,830 passed and 0 failed (with the previously-shadowed tests now also executing and passing, and the restored dict entry intact).

3.2 WHEN every other CI gate runs (validate_power, measure_steering --check, validate_commonmark, validate_dependencies, compose_hook_prompts --verify, sync_hook_registry --verify, lint_steering, validate_prerequisites, validate_progress_ci, validate_mandatory_gates, validate_governance_rules, validate_yaml_schemas, eval_conversations) THEN the system SHALL CONTINUE TO pass with no regressions.

3.3 WHEN any script under `senzing-bootcamp/scripts/` is executed THEN the system SHALL CONTINUE TO produce identical runtime behavior and output, since only formatting and correctness changes are applied — not logic changes.

3.4 WHEN scripts are inspected for dependencies THEN the system SHALL CONTINUE TO be Python 3.11+ stdlib-only (except `validate_dependencies.py`, which uses PyYAML), introducing no new third-party imports as part of the fix.

## Bug Condition and Properties

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type FileSet  // files under the ruff scope:
                            // senzing-bootcamp/scripts/, senzing-bootcamp/tests/, tests/
  OUTPUT: boolean

  // True when running ruff over the scoped files yields any violations
  RETURN ruffViolationCount(X) > 0
END FUNCTION
```

### Property: Fix Checking

```pascal
// Property: Ruff gate passes for the scoped file set
FOR ALL X WHERE isBugCondition(X) DO
  result ← ruffCheck'(X)   // F' = repository after the fix
  ASSERT ruffViolationCount(result) = 0 AND exitCode(result) = 0
END FOR
```

The three correctness defects additionally require:

```pascal
// Previously-shadowed tests now execute
ASSERT executes(test_module_07_no_inline_questions)
ASSERT executes(test_module_07_no_wait_instructions)

// Dropped dict entry restored
ASSERT dictEntryForKey(test_validate_module, 6) is preserved
```

### Property: Preservation Checking

```pascal
// Property: Behavior preserved for everything not triggering the bug
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)   // identical runtime behavior of scripts
END FOR

// Concretely:
ASSERT pytest(F') = "4830 passed, 86 skipped, 0 failed"
ASSERT allOtherCiGates(F') = PASS
```

**Definitions:**
- **F**: the repository as it exists before the fix (ruff gate fails with 438 violations).
- **F'**: the repository after the fix (ruff gate passes; correctness defects resolved; all tests and gates preserved).
- **Counterexample**: running `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` today returns 438 violations and a non-zero exit code.
