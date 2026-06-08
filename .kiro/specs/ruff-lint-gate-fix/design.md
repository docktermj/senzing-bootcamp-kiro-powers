# Ruff Lint Gate Fix Bugfix Design

## Overview

The CI pipeline's "Lint Python (ruff)" step runs `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` and currently reports **438 violations**, exiting non-zero and keeping the pipeline red. The gate has never been remediated since ruff was added; every other gate (validate_power, measure_steering, validate_commonmark, validate_dependencies, compose_hook_prompts, sync_hook_registry, lint_steering, validate_prerequisites, validate_progress_ci, validate_mandatory_gates, validate_governance_rules, validate_yaml_schemas, eval_conversations) and the pytest suite (4,830 passed / 86 skipped / 0 failed) are green.

Of the 438 violations, **3 are genuine correctness defects** (2× F811 redefinition, 1× F601 repeated dict key) that silently disable tests or drop data, and **435 are style violations** (E501, E402, F841, E741, W293) governed by `pyproject.toml` (`line-length = 100`, `lint.select = ["F", "E", "W", "I"]`, `target-version = py311`).

The fix strategy is **risk-ordered and phased** — correctness first (semantic changes that must be individually verified), then safe auto-fixes, then judgment-based E402 handling, then manual reflows/renames. After every phase we re-run ruff (to watch the count trend to 0) and pytest (to confirm 4,830 passed / 0 failed is preserved). The two F811 fixes are expected to *increase* the passing count as previously-shadowed tests begin running — this is a deliberate, documented delta, not a regression. Scripts under `senzing-bootcamp/scripts/` ship to users and must keep identical runtime behavior; only formatting and the 3 correctness fixes change anything semantic.

## Glossary

- **Bug_Condition (C)**: `ruffViolationCount(X) > 0` for the scoped file set `X` = `senzing-bootcamp/scripts/`, `senzing-bootcamp/tests/`, `tests/`. The bug is present whenever ruff reports any violation.
- **Property (P)**: After the fix, `ruffViolationCount = 0` and `exitCode = 0` for the scoped file set, the 3 correctness defects are resolved (shadowed tests execute, dropped dict entry restored), and all preserved behavior is intact.
- **Preservation**: All non-violation behavior that must not change — pytest at 4,830 passed / 0 failed, every other CI gate green, identical script runtime output, stdlib-only dependency posture.
- **F (original)**: The repository before the fix — ruff gate fails with 438 violations.
- **F' (fixed)**: The repository after the fix — ruff gate passes; correctness defects resolved; all tests and gates preserved.
- **Scoped file set**: The three directories ruff lints in CI: `senzing-bootcamp/scripts/`, `senzing-bootcamp/tests/`, `tests/`.
- **ruff**: The linter configured in `pyproject.toml` as the single source of truth. CI installs it fresh (`pip install ruff`) and runs `ruff check` over the scoped file set.
- **Safe auto-fix**: A `ruff check --fix` transformation ruff classifies as safe (does not change semantics). **Unsafe fix**: requires `--unsafe-fixes`; applied only after per-occurrence review.

## Bug Details

### Bug Condition

The bug manifests whenever ruff is run over the scoped file set and reports one or more violations. The CI step `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` therefore exits non-zero and blocks release. The root cause is that the ruff gate was added to CI but the existing code was never remediated against it, so 438 pre-existing violations accumulated across `senzing-bootcamp/scripts/`, `senzing-bootcamp/tests/`, and `tests/`.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X of type FileSet  // senzing-bootcamp/scripts/, senzing-bootcamp/tests/, tests/
  OUTPUT: boolean

  // True when running ruff over the scoped files yields any violation
  RETURN ruffViolationCount(X) > 0
END FUNCTION
```

### Violation Breakdown (verified via `ruff check ... --statistics`)

| Count | Code | Description | Category | Phase |
|------:|------|-------------|----------|-------|
| 259 | E501 | line-too-long (>100 chars) | Style | D |
| 141 | E402 | module-import-not-at-top-of-file | Style | C |
| 29 | F841 | unused-variable | Style | B |
| 5 | E741 | ambiguous-variable-name | Style | D |
| 2 | F811 | redefined-while-unused | **Correctness** | A |
| 1 | F601 | multi-value-repeated-key-literal | **Correctness** | A |
| 1 | W293 | blank-line-with-whitespace | Style | B |
| **438** | | | | |

### Examples

- **F811 (correctness)** — `senzing-bootcamp/tests/test_module_closing_question_ownership.py`: `test_module_07_no_inline_questions` is defined at line 250 and again at line 270; `test_module_07_no_wait_instructions` at line 259 and again at line 279. The second definitions are byte-for-byte copies of the first (only a preceding comment `# -- Module 07: now Query and Visualize (was module-08) --` differs). Python binds the later definitions, so the first two test bodies **never execute** — silent coverage loss. *Expected:* two distinct, non-shadowing tests both run.
- **F601 (correctness)** — `senzing-bootcamp/tests/test_validate_module.py:55`: the dict key literal `6` appears twice. The first `6` maps to 2 file-writer lambdas; the second `6` maps to 3 (a superset adding `docs/loading_strategy.md`). Python keeps the **last**, silently dropping the first entry. *Expected:* each key defined once, no intended value lost.
- **E501 (style)** — 259 lines exceed the 100-char limit across scripts and tests. *Expected:* reflowed to ≤100 chars with no logic change.
- **E402 (style)** — 141 imports placed after other statements. Many are legitimate: test/script files manipulate `sys.path` before importing scripts-as-modules (the documented pattern in `python-conventions.md`). *Expected:* no E402 reported, via per-file-ignore or targeted `# noqa` for legitimate cases.
- **F841 / E741 / W293 (style)** — 29 unused locals, 5 ambiguous single-char names, 1 blank line with trailing whitespace. *Expected:* none reported.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The full pytest suite continues to report **0 failed**. The passing count remains ≥ 4,830 (see expected delta below).
- Every other CI gate (validate_power, measure_steering --check, validate_commonmark, validate_dependencies, compose_hook_prompts --verify, sync_hook_registry --verify, lint_steering, validate_prerequisites, validate_progress_ci, validate_mandatory_gates, validate_governance_rules, validate_yaml_schemas, eval_conversations) continues to pass.
- Every script under `senzing-bootcamp/scripts/` produces identical runtime output and exit codes — only formatting changes are applied to scripts, never logic.
- The dependency posture stays Python 3.11+ stdlib-only (except `validate_dependencies.py` → PyYAML); no new third-party imports are introduced.

**Expected (non-regression) delta:** The two F811 fixes cause two previously-shadowed test bodies to begin executing. If they pass, the reported passing count rises by up to 2 (e.g., 4,830 → 4,832). This is an intended consequence of resolving the defect, not a regression. The invariant that must hold is **0 failed** and **passing count ≥ 4,830**.

**Scope:** All inputs that do NOT trigger the bug condition (i.e., everything other than the lines flagged by ruff, and all script runtime behavior) must be completely unaffected. This includes:
- Script execution paths, argument parsing, and output formatting logic.
- Test assertions and fixtures other than the 3 corrected defects.
- All non-Python files and all other CI gates.

## Hypothesized Root Cause

Based on the bug analysis, the violations fall into clearly separable root-cause categories, each remediated in its own phase:

1. **Gate added without remediation (overarching cause)**: The ruff gate was wired into CI, but the pre-existing code under the three scoped directories was never cleaned up against the configured rule set. All 438 violations are pre-existing debt surfaced by the gate.

2. **Accidental copy-paste in tests (F811)**: During a module renumbering (`module-08` → `module-07`, per the stale comment), a block of two tests was duplicated and the bodies were never updated to target the new content. The duplicate is an exact copy, so it merely shadows the original rather than testing anything new.

3. **Accidental duplicate dict key during edit (F601)**: A later edit added a third lambda to the module-`6` fixture by pasting a new `6:` block instead of extending the existing one, producing two `6` keys where the second (superset) silently wins.

4. **Legitimate structural patterns flagged as style (E402)**: The test/script `sys.path` manipulation pattern documented in `python-conventions.md` legitimately requires imports after executable statements. Ruff cannot know these are intentional, so they need explicit suppression rather than restructuring.

5. **Accumulated formatting drift (E501, F841, E741, W293)**: Long lines, leftover unused locals, ambiguous names, and stray whitespace that built up without a linter enforcing the configured limits.

## Correctness Properties

Property 1: Bug Condition - Ruff Gate Passes With Correctness Defects Resolved

_For any_ run where the bug condition holds (`isBugCondition` returns true, i.e. ruff reports violations over the scoped file set), the fixed repository SHALL cause `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` to report **0 violations and exit 0**, AND SHALL resolve the three correctness defects such that `test_module_07_no_inline_questions` and `test_module_07_no_wait_instructions` both execute as distinct tests, and the `test_validate_module.py` dict defines key `6` exactly once with no intended entry dropped.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Tests, Gates, and Script Runtime Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition` returns false — every behavior other than the flagged violations), the fixed repository SHALL produce the same result as the original: pytest reports **0 failed with passing count ≥ 4,830** (allowing the documented +up-to-2 delta from newly-running shadowed tests), every other CI gate continues to pass, every script under `senzing-bootcamp/scripts/` produces identical runtime behavior and output, and no new third-party dependency is introduced.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

The fix proceeds in four phases ordered by descending risk. After each phase we run the two verification commands (see Testing Strategy) so that any regression is attributed to the smallest possible change set.

### Phase A — Correctness fixes (highest priority, semantic)

These change test behavior (previously-shadowed assertions begin running; a dropped fixture entry returns), so each is applied and verified **individually**.

**File**: `senzing-bootcamp/tests/test_module_closing_question_ownership.py`

**F811 (lines 250/270 and 259/279)**: The block at lines 270–287 is an exact duplicate of lines 250–267 (confirmed by inspection — identical bodies, only a `# -- Module 07: now Query and Visualize (was module-08) --` comment precedes the second block). Determine intent during implementation:
- **If accidental copy-paste (most likely):** delete the duplicate second block (lines ~269–287 plus its stale comment). The single surviving pair of tests then runs normally. No assertion is lost because the bodies are identical.
- **If the second block was meant to test renamed content (two intended-but-misnamed tests):** rename the second pair (e.g., `test_module_07_query_no_inline_questions` / `_no_wait_instructions`) and repoint them at the correct `_AFFECTED_FILES` key so both pairs assert distinct things.

The implementer MUST inspect surrounding context and the `_AFFECTED_FILES` mapping before choosing; the default assumption is accidental copy-paste (delete), since the bodies are byte-identical.

**File**: `senzing-bootcamp/tests/test_validate_module.py`

**F601 (line 55)**: Key `6` appears twice — the first maps to `{loader.py, G2C.db}`, the second (superset) to `{loader.py, G2C.db, loading_strategy.md}`. Restore the dropped value by collapsing to a single `6:` entry containing the intended complete set. Because the second block is a superset, the correct single definition is the 3-lambda version; the first (2-lambda) block is removed. Confirm against the corresponding `validate_module.py` expectations that the module-6 fixture should include `loading_strategy.md`.

### Phase B — Safe auto-fixes (F841 ×29, W293 ×1)

Run `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/ --fix` to apply ruff's **safe** fixes for unused variables and blank-line whitespace. Use `--unsafe-fixes` only on a per-occurrence basis after reviewing the diff (e.g., where removing an unused assignment could discard a deliberately-named side-effecting call). Review the diff to confirm only F841/W293 lines changed and no script logic was altered.

### Phase C — E402 (module-import-not-at-top, ×141)

Distinguish legitimate from fixable cases:
- **Legitimate**: files using the documented `sys.path.insert(...)`-before-import pattern from `python-conventions.md` (most test files and some scripts). These cannot move imports to the top without breaking the scripts-as-modules import.
- **Fixable**: any file where an import was simply placed late and can safely move up.

For legitimate cases, choose suppression by scope:
- **Per-file-ignore (recommended where an entire file legitimately needs it):** add an entry under `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`, e.g.
  ```toml
  [tool.ruff.lint.per-file-ignores]
  "senzing-bootcamp/tests/*" = ["E402"]
  ```
  scoped as narrowly as the legitimate set allows (prefer explicit globs over a blanket repo-wide ignore).
- **Targeted `# noqa: E402`:** use per-line only when just one or two imports in an otherwise-clean file need it, keeping the suppression local and visible.

**Tradeoff to document:** per-file-ignores keep individual files uncluttered and centralize the policy in `pyproject.toml`, but they suppress E402 for *all* lines in matching files (including a genuinely misplaced import added later). Per-line `# noqa` is precise and self-documenting at the point of use but adds noise and must be repeated. Recommendation: per-file-ignore for test directories that uniformly use the `sys.path` pattern; per-line `# noqa: E402` for the small number of scripts where only one import is affected. Record the chosen mapping and rationale in the implementation tasks.

### Phase D — Manual reflow / rename (E501 ×259, E741 ×5)

Not safely auto-fixable.
- **E501**: manually reflow lines >100 chars — wrap function calls/arguments, split long strings with implicit concatenation, break long comprehensions. For scripts, preserve exact runtime behavior (string values, format output) — reflow source layout only, never change emitted text.
- **E741**: rename the 5 ambiguous single-char names (`l`, `I`, `O`) to descriptive names using `semantic_rename` where the symbol is local, ensuring all references update consistently.

### Phase E — Reconcile "all CI green" documentation claims

After the gate is green, reconcile any `POWER.md` / `CHANGELOG.md` statements asserting "all CI green" that predate this fix. Record the remediation in the `[Unreleased]` section of `senzing-bootcamp/CHANGELOG.md` (the correct place for an unreleased change). This is documentation hygiene, not a code change, and must not alter script behavior.

### Files Affected

| File | Phase | Change |
|------|-------|--------|
| `senzing-bootcamp/tests/test_module_closing_question_ownership.py` | A | Remove (or rename+repoint) duplicate F811 test pair |
| `senzing-bootcamp/tests/test_validate_module.py` | A | Collapse duplicate `6` dict key to single complete entry |
| `senzing-bootcamp/scripts/*.py`, `senzing-bootcamp/tests/*.py`, `tests/*.py` | B | Safe `--fix` for F841, W293 |
| `pyproject.toml` and/or in-scope `*.py` | C | `per-file-ignores` entry and/or `# noqa: E402` |
| In-scope `*.py` (E501/E741 occurrences) | D | Manual reflow; rename ambiguous names |
| `senzing-bootcamp/CHANGELOG.md` (+ `POWER.md` if it claims all-green) | E | Record fix under `[Unreleased]`; reconcile stale claims |

## Testing Strategy

### Validation Approach

Two-phase approach: first surface the counterexample that demonstrates the bug on unfixed code, then verify the fix drives violations to zero while preserving all tests and gates. Because the fix is phased, the two verification commands are re-run **after every phase** so a regression is localized to the smallest change set. Property-based testing already exists in the suite (pytest + Hypothesis) and is exercised wholesale by the preservation run.

The two verification commands (the project's existing tooling — run as single executions, never watch mode):
- **Ruff gate (Fix Checking):** `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` — track the violation count trending toward 0; add `--statistics` to see the per-code breakdown between phases.
- **Test suite (Preservation Checking):** `python -m pytest senzing-bootcamp/tests/ tests/` — confirm 0 failed and passing count ≥ 4,830.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix, and confirm the root-cause analysis. If a hypothesis is refuted, re-hypothesize before proceeding.

**Test Plan**: Run the exact CI command on the UNFIXED code and capture the `--statistics` breakdown. Then prove the two correctness defects empirically.

**Test Cases**:
1. **Counterexample baseline** (will fail on unfixed code): `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/ --statistics` reports 438 violations and exits non-zero, with the per-code counts matching the breakdown table.
2. **F811 shadowing proof**: collect `test_module_closing_question_ownership.py` and confirm only one of each `test_module_07_no_*` pair is collected (e.g., via `pytest --collect-only -q`), demonstrating the silent coverage loss.
3. **F601 dropped-entry proof**: evaluate the `test_validate_module.py` dict and confirm key `6` resolves to the superset (3 lambdas), proving the 2-lambda block was dropped.
4. **E402 legitimacy check** (root-cause confirmation): inspect a sample of E402 sites to confirm they are the `sys.path`-before-import pattern, validating the Phase C suppression decision rather than restructuring.

**Expected Counterexamples**:
- `ruff check` returns 438 violations / non-zero exit (the documented counterexample).
- Possible causes confirmed: pre-existing debt (overarching), copy-paste duplication (F811), duplicate-key edit (F601), legitimate `sys.path` pattern (E402), formatting drift (E501/F841/E741/W293).

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed repository produces the expected behavior (zero violations, defects resolved).

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  result := ruffCheck'(X)                 // F' = repository after the fix
  ASSERT ruffViolationCount(result) = 0 AND exitCode(result) = 0
END FOR

// Correctness defects additionally:
ASSERT executes(test_module_07_no_inline_questions)
ASSERT executes(test_module_07_no_wait_instructions)
ASSERT dictEntryForKey(test_validate_module, 6) is preserved
```

**Mapping to verification steps:**
- Run `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` after the final phase → expect `All checks passed!` and exit 0. (Property 1; Req 2.1, 2.4)
- `pytest --collect-only` shows two distinct, non-duplicate `test_module_07_no_*` tests, and both pass when run. (Property 1; Req 2.2)
- The module-`6` fixture in `test_validate_module.py` contains the intended complete set and its dependent test passes. (Property 1; Req 2.3)

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed repository produces the same result as the original — no test or gate regressions, identical script runtime.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)                      // identical runtime behavior of scripts
END FOR

// Concretely:
ASSERT pytest(F') == "0 failed" AND passingCount(F') >= 4830   // allow +up-to-2 delta
ASSERT allOtherCiGates(F') == PASS
ASSERT dependencies(F') == stdlib-only (except validate_dependencies.py -> PyYAML)
```

**Testing Approach**: Property-based testing is well suited to preservation checking — the existing Hypothesis suite generates many inputs across the domain and catches edge cases manual tests miss. The preservation run simply re-executes the entire suite (including its PBT classes) after each phase, providing strong evidence that behavior is unchanged for all non-buggy inputs.

**Mapping to verification steps:**
- Run `python -m pytest senzing-bootcamp/tests/ tests/` after each phase → expect 0 failed and passing count ≥ 4,830 (≥ 4,830 + up to 2 after Phase A). (Property 2; Req 3.1)
- Re-run the other CI gate scripts (or rely on the full CI run) → all pass. (Property 2; Req 3.2)
- Diff the script changes after Phases B–D to confirm only formatting changed, not logic, and spot-run a representative script to confirm identical output. (Property 2; Req 3.3)
- Confirm no new imports were added (`pyproject.toml` and script imports unchanged in dependency terms). (Property 2; Req 3.4)

**Test Cases**:
1. **Test-suite preservation**: Observe `4830 passed, 86 skipped, 0 failed` on unfixed code; after each phase confirm 0 failed and passing ≥ 4,830 (≥ 4,832 expected after Phase A).
2. **Other-gates preservation**: Confirm the 13 other gate scripts pass before and after the fix.
3. **Script runtime preservation**: Spot-check representative scripts (e.g., `validate_power.py`, `measure_steering.py --check`) produce identical output pre/post fix.
4. **Dependency preservation**: Confirm scripts remain stdlib-only (PyYAML only in `validate_dependencies.py`); no new third-party imports introduced by reflow or suppression.

### Unit Tests

- The two restored F811 tests (`test_module_07_no_inline_questions`, `test_module_07_no_wait_instructions`) now execute and assert against the correct module-07 content.
- The corrected `test_validate_module.py` module-`6` fixture test asserts the complete intended file set.
- Edge cases: confirm `ruff check` exits 0 when run exactly as CI runs it (no extra arguments).

### Property-Based Tests

- The existing Hypothesis suite under `senzing-bootcamp/tests/` and `tests/` is re-run in full as the preservation check — its generated cases provide broad evidence that script and validation behavior is unchanged.
- No new PBT is required to remediate style violations; the property of interest (zero violations, behavior preserved) is checked directly by the ruff command and the full pytest run.

### Integration Tests

- Full CI dry-run order: execute the gate sequence from `validate-power.yml` locally (or via CI) to confirm the ruff step now exits 0 and the subsequent pytest step reports 0 failed.
- Cross-phase regression tracking: capture `ruff --statistics` after each phase to confirm the count decreases monotonically toward 0 and that earlier-phase fixes are not reintroduced.
- Documentation reconciliation: confirm the `[Unreleased]` CHANGELOG entry records the fix and that no stale "all CI green" claim remains contradicted.
