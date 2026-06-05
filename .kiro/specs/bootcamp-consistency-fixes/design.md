# Bootcamp Consistency Fixes Bugfix Design

## Overview

This design addresses three independent defects discovered during an audit of feature branch
`1-docktermj-4`. The shipped `senzing-bootcamp` Kiro Power design is coherent — every standalone
CI validator passes — but the test suite and internal data have drifted away from the shipped
steering content during an in-flight onboarding refactor. The three defects are independent and
are fixed independently; they share only the goal of making the full test suite green again
without weakening any validator.

**BUG 1 — Onboarding-split test drift.** The welcome banner, the "Programming Language Selection"
step, and comprehension-check steps (3, 4, 4b/5a, 4c/5b) were intentionally moved out of
`onboarding-flow.md` into `onboarding-phase1b-intro-language.md`. The steering files are coherent
and cross-reference each other correctly, but 147 tests (and their preservation snapshots/hashes)
still assert that content lives in the old file. The fix updates the **tests**, not the steering
files. The split is correct and MUST NOT be reverted.

**BUG 2 — `steering-index.yaml` token-budget aggregate mismatch.** `budget.total_tokens` is
declared as `169633` but the sum of the 91 `file_metadata.*.token_count` entries is `169576`
(off by 57). `measure_steering.py --check` only validates per-file ±10% tolerance and the phase
map, never the aggregate, so the inconsistency escapes the validator. The fix corrects the total
to `169576` and extends `measure_steering.py` to validate and sync the aggregate going forward,
while preserving the existing per-file and per-phase checks.

**BUG 3 — `lint_steering.py` hook-registry false positives.** Rule 6 (`check_hook_consistency`)
reads only `hook-registry-critical.md`, which documents only the 5 critical hooks. All 24
module/`any` hooks are therefore falsely reported as "not documented in the hook registry,"
contradicting `sync_hook_registry.py --verify` (which passes). The fix points the linter at the
same set of registry sources that `sync_hook_registry.py` treats as the documentation surface, so
the two scripts agree. The design also confirms exit-code behavior, addresses the legitimate
`module-03-visualization-api-reference.md` template findings, and recommends closing the CI gaps
that let these issues escape.

The general strategy for every preservation snapshot/hash is **observation-first regeneration**:
re-derive each baseline by reading the *current shipped* steering content (the post-split, fixed
state), never by hand-editing a hash to "make the test pass." Each regenerated baseline is
cross-checked against an independent signal (the matching exploration test, the validator, or a
content assertion) so regeneration cannot silently mask a real regression.

## Glossary

- **Bug_Condition (C)**: A predicate over codebase state identifying inputs that trigger a defect.
  Three independent conditions exist here: `isBugCondition_1` (a test/snapshot asserts onboarding
  content in the pre-split layout), `isBugCondition_2` (the index aggregate diverges from the
  per-file sum), and `isBugCondition_3` (the linter calls a documented hook undocumented).
- **Property (P)**: The desired behavior for inputs where the bug condition holds — the full suite
  passes against the shipped layout (Bug 1), the aggregate equals the sum and `--check` enforces it
  (Bug 2), and the linter produces no false positives and agrees with `sync_hook_registry`
  (Bug 3).
- **Preservation (¬C)**: Behaviors that must remain unchanged. The intentional onboarding split,
  the steering content, the per-file/per-phase token checks, the per-file `token_count` values,
  the hook registry contents, and all currently-passing validators and tests.
- **F / F'**: The original (unfixed) and fixed artifacts. For Bug 1, F/F' are the *test files*
  (the steering is unchanged). For Bug 2, F/F' are `steering-index.yaml` + `measure_steering.py`.
  For Bug 3, F/F' are `lint_steering.py` (+ possibly one steering file).
- **onboarding-flow.md**: The first onboarding steering file. After the split it covers setup,
  MCP health check, version display, directory/team setup, and the prerequisite gate (Steps 0–2d),
  then directs "After Step 2d, load `onboarding-phase1b-intro-language.md`."
- **onboarding-phase1b-intro-language.md**: The new phase file that now owns the entity-resolution
  intro (Step 3), Programming Language Selection (Step 4), the welcome banner / Bootcamp
  Introduction (Step 5), the verbosity preference (Step 5a), and the comprehension check (Step 5b).
- **measure_steering.py**: stdlib-only script that measures steering token counts and validates
  `steering-index.yaml` in `--check` mode (per-file `file_metadata` tolerance + per-phase
  tolerance), or rewrites `file_metadata` + `budget` in update mode.
- **lint_steering.py**: stdlib-only structural linter for steering files; Rule 6
  (`check_hook_consistency`) cross-checks hook files against a hook-registry source.
- **sync_hook_registry.py**: Generates `hook-registry.md`, `hook-registry-critical.md`, and
  `hook-registry-modules.md` from the `.kiro.hook` JSON files (the single source of truth);
  `--verify` passes today.
- **Preservation snapshot / hash**: A pinned constant in a test — a literal substring, a SHA-256 of
  a file or a YAML sub-block, or a `_BASELINE_HASHES` map — that locks down content the fix must not
  change. Regenerating one means recomputing it from the current shipped content.

## Bug Details

### Bug Condition

#### BUG 1 — Onboarding-split test drift

The bug manifests when a test (or a preservation snapshot/hash embedded in a test) asserts that
onboarding content — the welcome banner, the Programming Language Selection step, or the
comprehension-check steps — lives in `onboarding-flow.md` and/or in the pre-split heading sequence.
The shipped steering moved that content into `onboarding-phase1b-intro-language.md`, so the
assertion (or the pinned hash of the old file region) no longer matches reality. The defect is in
the **tests**, not the steering content.

**Formal Specification:**

```
FUNCTION isBugCondition_1(test)
  INPUT: test of type TestCase
  OUTPUT: boolean

  RETURN (test asserts welcome-banner
          OR test asserts programming-language-selection-step
          OR test asserts comprehension-checks(3, 4, 4b/5a, 4c/5b)
          OR test pins a snapshot/hash of an onboarding file region)
         AND test expects that content in onboarding-flow.md
             OR in the pre-split heading sequence/file location
END FUNCTION
```

#### BUG 2 — Token-budget aggregate mismatch

The bug manifests whenever the declared aggregate `budget.total_tokens` differs from the sum of the
per-file `token_count` entries in `file_metadata`. `measure_steering.py --check` never compares
these two numbers, so the divergence is invisible to the validator.

**Formal Specification:**

```
FUNCTION isBugCondition_2(index)
  INPUT: index of type SteeringIndexYaml
  OUTPUT: boolean

  RETURN index.budget.total_tokens != SUM(index.file_metadata[*].token_count)
END FUNCTION
```

#### BUG 3 — Linter false positives (hook documentation)

The bug manifests whenever `lint_steering.py` reports a hook file as "not documented in the hook
registry" even though that hook IS documented in the registry source set that
`sync_hook_registry.py` generates and verifies. Root cause: Rule 6 reads only
`hook-registry-critical.md` (5 critical hooks), so every module/`any` hook is a false positive.

**Formal Specification:**

```
FUNCTION isBugCondition_3(hook)
  INPUT: hook of type HookFile
  OUTPUT: boolean

  RETURN lint_steering reports hook "not documented in the hook registry"
         AND hook documented in (hook-registry.md
                                 OR hook-registry-critical.md
                                 OR hook-registry-modules.md)
END FUNCTION
```

### Examples

**BUG 1 (observed on current code):**

- `tests/test_bootcamp_ux_preservation.py::TestOnboardingFlowPreservation::test_welcome_banner_text`
  asserts the `🎓🎓🎓 WELCOME TO THE SENZING BOOTCAMP! 🎓🎓🎓` banner is in `onboarding-flow.md`.
  Actual: the banner now lives in `onboarding-phase1b-intro-language.md` (Step 5). → FAIL.
- `senzing-bootcamp/tests/test_comprehension_check.py` (27 failures) expects comprehension-check
  steps in the old file/heading sequence. → FAIL.
- `senzing-bootcamp/tests/test_disambiguate_language_prompt.py` (12 failures) expects the
  "programming language" prompt in `onboarding-flow.md`. Actual: Step 4 of the phase file. → FAIL.
- `senzing-bootcamp/tests/test_version_unit.py::TestOnboardingIntegration::test_version_step_before_welcome_banner`
  pins the version step + welcome banner ordering within a single file. Actual: version display is
  in `onboarding-flow.md` (Step 0c) while the banner moved to the phase file. → FAIL.
- Full confirmed count: **147 failed, 4648 passed, 86 skipped**.

**BUG 2 (confirmed by direct measurement):**

- `file_metadata` has 91 entries; their `token_count` values sum to **169576**.
- `budget.total_tokens` is declared **169633** (off by +57).
- `measure_steering.py --check` → `All token counts are within 10% tolerance.` exit 0 (misses it).
- `test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_actual_steering_index_total_tokens_equals_sum`
  → FAIL (it sums `file_metadata` and compares to the declared total).

**BUG 3 (confirmed by running the linter):**

- `lint_steering.py` prints 24 `WARNING: ... 'X.kiro.hook' exists but is not documented in the hook
  registry` lines for hooks such as `verify-sdk-setup`, `security-scan-on-save`,
  `run-tests-after-change`, `gate-module3-visualization` — all of which ARE present in
  `hook-registry.md` and `hook-registry-modules.md`.
- `sync_hook_registry.py --verify` → `All registry files are up to date.` exit 0 (disagrees).
- Edge case (template findings, legitimate): `module-03-visualization-api-reference.md` is flagged
  for a missing `**🚀 First:**` instruction (ERROR), a missing Before/After block (WARNING), and a
  missing success indicator (WARNING). `module-03-system-verification.md` is flagged for a missing
  success indicator (WARNING).

> **Audit discrepancy to record (not a code change):** The requirements (clauses 1.14 / 2.14)
> state the linter "exits 0 even when it reports an error." On current `HEAD` the linter exits **1**
> when an error is present (the `module-03-visualization-api-reference.md` first-read ERROR drives
> `exit_code = 1`). The exit-code logic in `run_all_checks` is already correct: `has_issues =
> any(v.level == "ERROR" ...)` → `exit_code = 1`. The exit-0 symptom only appears when there are
> warnings but **zero** errors. This design therefore (a) adds a regression test that pins the
> error⇒non-zero contract so it can never regress, and (b) resolves the only current ERROR so the
> linter reports a clean, accurate result — rather than "fixing" an exit-code path that is already
> correct. See Fix Implementation, Bug 3.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- The intentional onboarding split is preserved: the welcome banner, the "Programming Language
  Selection" step, and comprehension-check steps (3, 4, 4b/5a, 4c/5b) remain in
  `onboarding-phase1b-intro-language.md` (Requirement 3.1).
- `onboarding-flow.md` continues to direct "After Step 2d, load
  `onboarding-phase1b-intro-language.md`" and the cross-references between the two files stay intact
  (Requirement 3.2).
- The onboarding steering files keep their coherent, complete post-split structure unchanged by this
  fix (Requirement 3.3).
- Every standalone CI validator (`validate_power`, `validate_dependencies`, `validate_prerequisites`,
  `validate_mandatory_gates`, `validate_governance_rules`, `validate_yaml_schemas`,
  `compose_hook_prompts --verify`, `sync_hook_registry --verify`, `validate_commonmark`,
  `measure_steering --check`) continues to pass (Requirement 3.4).
- `measure_steering.py --check` keeps enforcing the existing per-file ±10% tolerance and the
  per-phase tolerance; the new aggregate check is additive, not a replacement (Requirement 3.5).
- All tests that pass today (outside the 147-failure set) continue to pass (Requirement 3.6).
- Per-file `token_count` entries in `steering-index.yaml` keep their existing values; only the
  aggregate `budget.total_tokens` changes, from `169633` to `169576` (Requirement 3.7).
- The 24 hooks flagged by the linter remain documented in `hook-registry.md` and
  `hook-registry-modules.md`; the fix corrects the linter's source, not the registry
  (Requirement 3.8).
- `sync_hook_registry.py --verify` continues to pass with its current behavior (Requirement 3.9).

**Scope:**

All inputs that do NOT match a bug condition must be completely unaffected by this fix. Concretely:

- For Bug 1: the steering `.md` files (content and cross-references), and every test that does not
  assert pre-split onboarding layout.
- For Bug 2: every per-file `token_count`, every phase `token_count`/`size_category`, and the
  `budget` sub-keys other than `total_tokens` (`reference_window`, `warn_threshold_pct`,
  `critical_threshold_pct`, `split_threshold_tokens`).
- For Bug 3: the registry source files, `sync_hook_registry.py`, and every linter rule other than
  the hook-consistency source selection (and, if chosen, the single template fix to the
  visualization reference file).

> The actual *expected correct behavior* for each bug condition is specified in the Correctness
> Properties section (Property 1, 3, 5). This section enumerates what must NOT change.

## Hypothesized Root Cause

### BUG 1 — Onboarding-split test drift

1. **Stale file target in assertions** — Tests open `onboarding-flow.md` (or read it via a fixture)
   and assert content that has moved to `onboarding-phase1b-intro-language.md`. This is the dominant
   cause (e.g., `test_bootcamp_ux_preservation.py` welcome banner; `test_disambiguate_language_prompt.py`).
2. **Stale heading-sequence expectations** — Tests assert a step/heading order that assumed banner,
   language selection, and comprehension checks were contiguous in one file
   (`test_onboarding_flow_restructuring.py`, `test_version_unit.py`, `test_entity_resolution_intro_structure.py`).
3. **Pinned snapshots/hashes of the old region** — Preservation tests pin a substring or a SHA-256
   of an onboarding region that no longer exists in the old file
   (`test_missing_pointer_marker_preservation.py`, `test_track_selection_gate_preservation.py`).
4. **Question-ownership mapping outdated** — `test_onboarding_question_ownership.py` /
   `test_module_closing_question_ownership.py` map each closing question to the file that "owns" it;
   the owning file changed for the moved questions.
5. **Collateral within-file assertions** — A handful of failures in files like
   `test_system_verification_unit.py`, `test_wait_before_server_termination_*`, and
   `test_self_answering_questions_*` are pinned to module-03 / step content that was also refactored
   in the same branch; these must be re-baselined against the shipped content, not reverted.

### BUG 2 — Token-budget aggregate mismatch

1. **Validator blind spot** — `measure_steering.py --check` validates `file_metadata` per-file
   tolerance (`check_counts`) and per-phase tolerance (`check_phase_counts`) but never compares
   `budget.total_tokens` to `SUM(file_metadata.token_count)`. There is no aggregate assertion.
2. **Update/edit skew** — In update mode the script recomputes `total_tokens` as the sum, so a fresh
   `measure_steering.py` run would self-correct. The stored `169633` is a stale value left by a
   manual edit (or a prior file set) that was never reconciled because `--check` never flagged it.
   The 57-token gap is consistent with content edits to one or more steering files after the last
   full `total_tokens` rewrite.

### BUG 3 — Linter false positives

1. **Wrong registry source (primary)** — `check_hook_consistency` hardcodes
   `registry_path = steering_path / "hook-registry-critical.md"` and extracts hook IDs only from
   that file. `hook-registry-critical.md` documents the 5 critical hooks only; the 24 module/`any`
   hooks are documented in `hook-registry.md` (summary table) and `hook-registry-modules.md` (full
   prompts). Every module/`any` hook is therefore a false "not documented" warning.
2. **Disagreement with the source of truth** — `sync_hook_registry.py` treats all three registry
   files as generated artifacts of the `.kiro.hook` files. The linter consults only one of the
   three, so it cannot agree with `sync_hook_registry --verify`.
3. **Event-type extraction tied to the wrong file** — The same rule builds `registry_event_types`
   from `hook-registry-critical.md`'s `**hook-id** (eventType → actionType)` headers, so event-type
   cross-checks are also limited to critical hooks.
4. **Exit code (already correct; guard against regression)** — `run_all_checks` already returns
   `exit_code = 1` when any ERROR exists. The audit's "exits 0 on error" claim does not reproduce on
   `HEAD`; the residual risk is regression, not a present defect. (See the discrepancy note above.)
5. **Legitimate template findings on a reference file** — `module-03-visualization-api-reference.md`
   matches the module file glob (`module-NN-*.md`, non-phase) and so is subjected to the module
   template checks (first-read instruction, Before/After, success indicator). It is a
   *reference/appendix* file loaded on demand from `module-03-phase2-visualization.md`, not a
   standalone workflow module, so it legitimately lacks those workflow elements. Same situation for
   `module-03-system-verification.md` (a dispatcher/overview file whose steps live in phase
   sub-files). These are real findings about classification, not false positives about hooks.

## Correctness Properties

Property 1: Bug Condition — Onboarding-Split Tests Validate the Shipped Layout

_For any_ test where the bug condition holds (`isBugCondition_1` returns true — it asserts the
welcome banner, the Programming Language Selection step, or comprehension-check steps 3/4/4b/4c, or
pins a snapshot/hash of an onboarding region, against the pre-split layout), the fixed test SHALL
reference `onboarding-phase1b-intro-language.md` (and the post-split heading sequence) and SHALL
pass, while leaving the steering content unchanged.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9**

Property 2: Preservation — Steering Content and Previously-Passing Tests Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition_1` returns false), the fixed
code SHALL produce the same result as the original: the onboarding steering files
(`onboarding-flow.md`, `onboarding-phase1b-intro-language.md`) remain byte-identical, the
cross-references are intact, and every test outside the 147-failure set still passes, preserving the
intentional onboarding split.

**Validates: Requirements 3.1, 3.2, 3.3, 3.6**

Property 3: Bug Condition — Token-Budget Aggregate Equals the Sum and Is Enforced

_For any_ steering index where the bug condition holds (`isBugCondition_2` returns true — the
declared `budget.total_tokens` differs from the sum of `file_metadata.token_count`), the fixed
artifacts SHALL set `budget.total_tokens` equal to that sum (169576), and `measure_steering.py
--check` SHALL fail (exit non-zero) whenever the aggregate diverges from the sum.

**Validates: Requirements 2.10, 2.11**

Property 4: Preservation — Per-File / Per-Phase Counts and Existing Checks Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition_2` returns false), the fixed
`measure_steering.py` SHALL produce the same result as the original: every per-file `token_count`
value is unchanged, the per-file ±10% tolerance check and the per-phase tolerance check behave
identically, the other `budget` sub-keys are preserved, and `--check` exits 0 when the aggregate
already equals the sum.

**Validates: Requirements 3.5, 3.7**

Property 5: Bug Condition — Linter Agrees With the Registry Source of Truth

_For any_ hook where the bug condition holds (`isBugCondition_3` returns true — the linter calls a
documented hook undocumented), the fixed `lint_steering.py` SHALL NOT report it as "not documented,"
its hook-documentation conclusions SHALL agree with `sync_hook_registry.py --verify`, and when one
or more ERRORs are present the linter SHALL exit non-zero.

**Validates: Requirements 2.12, 2.13, 2.14, 2.15**

Property 6: Preservation — Registry Contents and sync_hook_registry Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition_3` returns false), the fixed
code SHALL produce the same result as the original: `hook-registry.md`,
`hook-registry-critical.md`, and `hook-registry-modules.md` are unchanged, `sync_hook_registry.py
--verify` still passes, and every linter rule other than the hook-consistency source selection
behaves identically.

**Validates: Requirements 3.8, 3.9**

## Fix Implementation

### BUG 1 — Update tests to the shipped onboarding layout

**Files (tests only — no steering `.md` changes):** the 147-failure set, clustered as:

| Cluster | File(s) | Failing | Fix kind |
|---|---|---|---|
| Comprehension checks | `senzing-bootcamp/tests/test_comprehension_check.py` | 27 | Re-target to `onboarding-phase1b-intro-language.md`; update heading numbers (5a/5b) |
| Language prompt | `senzing-bootcamp/tests/test_disambiguate_language_prompt.py` | 12 | Re-target to phase file Step 4 |
| Pointer-marker preservation/exploration | `senzing-bootcamp/tests/test_missing_pointer_marker_preservation.py` (10), `..._exploration.py` (6) | 16 | Re-baseline file region + pinned markers |
| Question ownership | `senzing-bootcamp/tests/test_onboarding_question_ownership.py` (7), `test_module_closing_question_ownership.py` (4) | 11 | Update owning-file map |
| Track-selection gate preservation | `senzing-bootcamp/tests/test_track_selection_gate_preservation.py` | 5 | Re-baseline Step 4 content markers against shipped location |
| Onboarding UX / restructuring | `test_onboarding_ux_improvements.py` (5), `test_onboarding_flow_restructuring.py` (5) | 10 | Update heading sequence + file location |
| System verification | `test_system_verification_unit.py` (5), `test_system_verification_properties.py` (2) | 7 | Re-baseline against shipped module-03 content |
| TypeScript maturity | `test_typescript_language_maturity.py` | 3 | Re-target language-maturity content to phase file |
| Wait-before-termination | `test_wait_before_server_termination_preservation.py` (4), `..._bug.py` (2) | 6 | Re-baseline step content |
| Self-answering | `test_self_answering_questions_preservation.py` (4), `..._bug.py` (4), `test_self_answering_reinforcement.py` (2) | 10 | Re-baseline |
| Repo-root UX preservation | `tests/test_bootcamp_ux_preservation.py` (2), `tests/test_license_guidance_workflow_properties.py` (1), `tests/test_auto_load_error_recovery_properties.py` (1) | 4 | Re-target/refresh hashes |
| Remaining singletons | `test_version_unit.py`, `test_track_switcher_unit.py`, `test_entity_resolution_intro_structure.py` (2), `test_session_resume_split.py` (2), `test_mandatory_gate_exploration.py` (2), `test_cord_data_priority.py` (2), `test_no_skip_offer_mandatory_gate_bug.py` (4), `test_bootcamp_ux_feedback_unit.py` (4), `test_sdk_method_discovery_bug.py` (3), `test_steering_index_token_count_sync_preservation.py` (2 — see Bug 2), `test_token_budget_optimization.py` (1 — see Bug 2), and others | remainder | Re-target file/heading or re-baseline |

> The cluster table is derived from a full `pytest` run (`147 failed`). The "remainder" rows include
> a small number of failures that belong to Bug 2 (the two `test_steering_index_token_count_sync_preservation.py`
> failures and the one `test_token_budget_optimization.py` aggregate failure) — those are fixed by
> the Bug 2 work, not by re-targeting onboarding files. The exact, authoritative failing-test list
> is regenerated at implementation time (see Testing Strategy) so no failure is missed or
> miscategorized.

**Specific changes per fix kind:**

1. **Re-target file reads** — Where a test reads `onboarding-flow.md` (directly, via a path
   constant, or via a fixture) and asserts moved content, change the path to
   `onboarding-phase1b-intro-language.md`. Where a test legitimately spans both files (e.g.
   "version step before welcome banner"), split the assertion: read the version step from
   `onboarding-flow.md` (Step 0c) and the banner from the phase file (Step 5), and assert the
   cross-file ordering via the documented load sequence rather than within-file position.
2. **Update heading/step numbers** — The moved comprehension check is now Step 5b and verbosity is
   Step 5a in the phase file; language selection is Step 4. Update any hardcoded step numbers and
   heading-order lists to the shipped sequence.
3. **Re-baseline pinned snapshots/hashes** — For substring snapshots, replace the pinned literal
   with the current shipped text (read from the correct file). For SHA-256 hashes of a file or YAML
   sub-block, recompute the digest from the current shipped bytes. Every regenerated baseline is
   produced by reading the live file, and is paired with a content assertion (see "Safe regeneration"
   below) so the new baseline cannot lock in a regression.
4. **Update question-ownership maps** — In ownership tests, move the welcome-banner / language /
   comprehension questions to the `onboarding-phase1b-intro-language.md` owner entry.

**Constraint:** No `.md` steering file is modified for Bug 1. If implementing a fix appears to
require editing a steering file, that signals a genuine regression in the steering content (not a
Bug 1 test-drift case) and must be raised separately rather than silently changed.

### BUG 2 — Correct the aggregate and add an aggregate check to `measure_steering.py`

**File 1: `senzing-bootcamp/steering/steering-index.yaml`**

- Change `budget.total_tokens: 169633` → `budget.total_tokens: 169576`. No other line changes. This
  is the single data correction; per-file and per-phase entries are untouched (Requirement 3.7).

**File 2: `senzing-bootcamp/scripts/measure_steering.py`** (stdlib-only, preserve conventions)

1. **Add an aggregate validation in `--check` mode.** In `main()`'s `--check` branch, after the
   existing `check_counts` and `check_phase_counts` calls, compute
   `declared = parse budget.total_tokens` from the index and `expected = sum(file_metadata token_count)`
   and report a mismatch when `declared != expected`. The aggregate check is **additive**: the
   per-file and per-phase checks run exactly as before, and the exit code becomes non-zero if *any*
   of the three checks fail (Requirements 2.11, 3.5).
2. **Add a small parser helper** `parse_budget_total(content) -> int | None` that extracts
   `budget.total_tokens` via a localized regex (consistent with the existing
   `re.search(r"total_tokens:\s*(\d+)")` usage in `simulate_context_load`). Reuse the existing
   `_parse_stored_metadata` to obtain the per-file sum so the "sum" definition matches `check_counts`.
3. **Exact-equality semantics.** The aggregate check uses exact equality (`declared == sum`), not a
   ±10% tolerance — the budget total is a derived bookkeeping value and should track the sum exactly,
   which is also what update mode already writes. A clear message is printed on mismatch, e.g.
   `Budget total mismatch: declared=169633, sum(file_metadata)=169576`.
4. **No change to update mode.** Update mode already writes `total_tokens = sum(...)`, so it remains
   the mechanism that keeps the value correct going forward; the new `--check` assertion guarantees
   drift is caught in CI rather than silently persisting.

> Dependency posture: `measure_steering.py` remains stdlib-only (PyYAML is permitted only in
> `validate_dependencies.py`). The aggregate check reuses the existing minimal-regex YAML parsing.

### BUG 3 — Point the linter at the correct registry source (+ confirm exit code, resolve template findings)

**File: `senzing-bootcamp/scripts/lint_steering.py`** (stdlib-only, preserve conventions)

1. **Read the full registry source set in `check_hook_consistency`.** Replace the single
   `registry_path = steering_path / "hook-registry-critical.md"` with the same set
   `sync_hook_registry.py` treats as the documentation surface:
   `hook-registry.md`, `hook-registry-critical.md`, and `hook-registry-modules.md`. Build
   `registry_ids` as the **union** of hook IDs found across those files, and build
   `registry_event_types` from whichever of those files carries the
   `**hook-id** (eventType → actionType)` headers (the full-prompt files
   `hook-registry-critical.md` / `hook-registry-modules.md`). The "registry file not found" ERROR
   should fire only if *all* sources are absent.
   - Note: `hook-registry.md` is a markdown table (`| ask-bootcamper | agentStop → askAgent | ... |`),
     while the `-critical`/`-modules` files use `- id: \`hook-id\`` lines plus
     `**hook-id** (eventType → actionType)` headers. The ID/event extraction must handle both shapes
     (extend `RE_HOOK_ID` / `RE_HOOK_EVENT_TYPE` usage or add a table-row parser). Using the union
     means a hook documented in *any* recognized source is "documented," which is exactly the
     `sync_hook_registry` contract.
2. **Confirm and lock the exit-code contract.** No logic change is required in `run_all_checks` —
   it already sets `exit_code = 1` when any ERROR exists. Add a regression test pinning
   "error_count > 0 ⇒ exit_code != 0" (see Testing Strategy) so the contract cannot silently
   regress. Record the audit discrepancy (the "exits 0 on error" claim does not reproduce on HEAD)
   in the test docstring for traceability.
3. **Resolve the legitimate template findings (Requirement 2.15) by correct classification.** The
   real, non-hook findings are about reference/dispatcher files being run through the module-workflow
   template checks:
   - `module-03-visualization-api-reference.md` — a reference/appendix file (API schemas +
     `search_builder.py` spec) loaded on demand from `module-03-phase2-visualization.md`. It is not a
     standalone workflow module and legitimately has no first-read instruction, Before/After block,
     or success indicator.
   - `module-03-system-verification.md` — a module **dispatcher/overview** whose numbered steps live
     in phase sub-files (`module-03-phase1/2/3-*.md`); it legitimately has no per-module success
     indicator of its own.

   **Chosen approach: exclude non-workflow module files from the module-template checks** (rather
   than injecting cosmetic headings into reference content). Extend `get_module_steering_files` (used
   by `check_module_frontmatter`, `check_first_read_instruction`, `check_before_after_block`,
   `check_checkpoint_completeness`, `check_success_indicator`, `check_section_order`) to skip files
   that are reference/dispatcher in nature. Recommended, explicit signals (in priority order), to
   keep the rule narrow and self-documenting:
   - filename suffix `*-api-reference.md` (reference appendices), and
   - module files that declare a `## Phase Sub-Files` section (dispatcher/overview files whose steps
     live in phase files).

   This makes the linter's output accurate without altering the meaning of the reference content,
   and it agrees with how the existing checkpoint check already special-cases `phase` files. The
   `module-03-visualization-api-reference.md` first-read ERROR (the only current ERROR) is thereby
   resolved, and the two `module-03` success-indicator warnings disappear, leaving a clean,
   accurate run.

   > Alternative (documented, not chosen): add a `**🚀 First:**` line, a Before/After block, and a
   > `**Success indicator:**` line to `module-03-visualization-api-reference.md`. Rejected because it
   > would inject workflow scaffolding into a pure reference file, changing shipped steering content
   > and creating misleading "steps" where none exist.

**CI recommendation (addresses the escape that hid these defects):**

- **Broaden the trigger paths** in `.github/workflows/validate-power.yml` so the repo-root `tests/`
  directory is covered. Today `on.pull_request.paths` and `on.push.paths` are limited to
  `senzing-bootcamp/**`, so a change touching only `tests/**`, `.github/**`, or `.kiro/**` runs no
  CI at all even though the test step already runs `tests/`. Add `tests/**` and
  `.github/workflows/**` (and consider removing the path filter on `push: branches: [main]`).
- **Add `lint_steering.py` to CI** now that it accurately exits non-zero on real errors — run it
  after `sync_hook_registry --verify` (e.g. `python senzing-bootcamp/scripts/lint_steering.py`),
  so the two stay in agreement and future false-positive regressions fail the build.
- **Note (not part of the fix, flag for the user):** CI invokes scripts as `python` (the workflow
  uses `setup-python`, which provides `python` on the runner). The local dev environment here only
  has `python3`; this is an environment detail, not a defect in the workflow.

### Safe regeneration of preservation snapshots/hashes (cross-cutting)

The risk with any preservation test that pins a hash or substring is that "fixing" it by pasting in
the new value can mask a real regression. The design mandates the following procedure so
regeneration is provably safe:

1. **Regenerate from live content, never by trial-and-error.** Recompute each substring/hash by
   reading the current shipped file (post-split, fixed state) — e.g. for
   `_BASELINE_HASHES["budget"]` in `test_steering_index_token_count_sync_preservation.py`, recompute
   the SHA-256 of the `budget` block *after* `total_tokens` is corrected to 169576.
2. **Pair every regenerated baseline with an independent content assertion.** Each preservation test
   in this suite already has a companion exploration test (e.g.
   `test_steering_index_token_count_sync_exploration.py`) or content-level assertion. The regenerated
   hash must coexist with an assertion that the *meaning* is correct (the banner text is present, the
   language prompt uses "programming language," the aggregate equals the sum). A hash alone is never
   the only guard.
3. **Distinguish "moved" from "changed."** For Bug 1, regenerated baselines must reflect content that
   *moved files unchanged*. If the recomputed content differs from the pre-split content in more than
   location (i.e., the text itself changed), that is a regression signal to investigate, not to pin.
4. **Bug-2-specific baselines.** Three failing tests are coupled to the index aggregate:
   `test_token_budget_optimization.py::...::test_actual_steering_index_total_tokens_equals_sum`
   passes once `total_tokens` is corrected (no test edit needed — it computes the sum live). The two
   `test_steering_index_token_count_sync_preservation.py` failures
   (`test_update_mode_preserves_non_phase_blocks`, `test_total_equals_file_metadata_sum_before_and_after`)
   require recomputing `_BASELINE_HASHES["budget"]` from the corrected `budget` block; the
   `test_total_equals_file_metadata_sum_before_and_after` assertion then holds because declared ==
   sum on the corrected index.

### Keeping the full suite green

- Fix the three bugs independently, then run the **entire** suite (`senzing-bootcamp/tests/` and
  `tests/`) — not just the previously-failing files — to confirm `0 failed` and that the passing
  count does not drop (no test was made to pass by breaking another).
- Re-run every standalone validator listed in Requirement 3.4 to confirm they still pass, and run
  the newly-strengthened `measure_steering.py --check` and `lint_steering.py` to confirm they now
  pass cleanly on the corrected data.

## Testing Strategy

### Validation Approach

Two phases. First, on the **unfixed** code, run targeted tests to (a) confirm each bug condition is
real and reproduces the documented counterexamples, and (b) capture the current behavior of all
non-bug inputs so regressions are detectable. Then apply the fixes and verify the bug-condition
properties hold while the preservation properties are unchanged. Because the fixes are independent,
each bug has its own exploration → fix → preservation cycle, plus one whole-suite gate at the end.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate each bug BEFORE fixing, and confirm/refute the
root-cause hypotheses. If refuted, re-hypothesize.

**Test Plan**: Run the existing exploration tests and the documented commands on the unfixed tree;
record the exact failures.

**Test Cases**:

1. **Bug 1 — onboarding drift** (will fail on unfixed code): run the full suite and confirm
   `147 failed`, then confirm representative cases —
   `tests/test_bootcamp_ux_preservation.py::TestOnboardingFlowPreservation::test_welcome_banner_text`
   (banner asserted in `onboarding-flow.md`), `test_comprehension_check.py` (27), and
   `test_disambiguate_language_prompt.py` (12) — fail because they target the pre-split layout.
2. **Bug 2 — aggregate mismatch** (will fail on unfixed code):
   `test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_actual_steering_index_total_tokens_equals_sum`
   fails (declared 169633 ≠ sum 169576), while `measure_steering.py --check` exits 0 — demonstrating
   the validator blind spot.
3. **Bug 3 — linter false positives** (observable on unfixed code): `lint_steering.py` prints 24
   "not documented in the hook registry" warnings for hooks present in `hook-registry.md` /
   `hook-registry-modules.md`, while `sync_hook_registry.py --verify` exits 0 — demonstrating the
   disagreement and the wrong-source root cause.
4. **Edge case — exit code / template findings** (will refine root cause): confirm the only ERROR is
   the `module-03-visualization-api-reference.md` missing first-read instruction and that the linter
   currently exits 1 (refuting the audit's "exits 0 on error" claim and re-scoping that requirement
   to a regression guard + classification fix).

**Expected Counterexamples**:

- Bug 1: assertions/hashes that reference `onboarding-flow.md` or the pre-split heading order.
- Bug 2: `total_tokens` (169633) ≠ `SUM(file_metadata.token_count)` (169576); `--check` silent.
- Bug 3: documented hooks reported undocumented; linter vs `sync_hook_registry` disagree.
- Possible causes: stale test file targets / pinned snapshots (Bug 1); missing aggregate assertion
  (Bug 2); wrong registry source + reference-file misclassification (Bug 3).

### Fix Checking

**Goal**: Verify that for all inputs where a bug condition holds, the fixed artifacts produce the
expected behavior.

**Pseudocode:**

```
// Bug 1
FOR ALL test WHERE isBugCondition_1(test) DO
  result := run(test')           // test re-targeted to onboarding-phase1b-intro-language.md
  ASSERT result = PASS
END FOR

// Bug 2
FOR ALL index WHERE isBugCondition_2(index) DO
  index' := fix(index)           // budget.total_tokens := SUM(file_metadata.token_count) = 169576
  ASSERT index'.budget.total_tokens = SUM(index'.file_metadata[*].token_count)
  ASSERT measure_steering(--check) FAILS when declared != sum
END FOR

// Bug 3
FOR ALL hook WHERE isBugCondition_3(hook) DO
  ASSERT NOT lint_steering'(hook) reports "not documented"
END FOR
ASSERT lint_steering' hook-doc conclusions AGREE WITH sync_hook_registry(--verify)
ASSERT (error_count > 0) IMPLIES (exit_code != 0)
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed artifacts
produce the same result as the originals.

**Pseudocode:**

```
// Bug 1 — steering content & previously-passing tests unchanged
ASSERT onboarding-phase1b-intro-language.md content UNCHANGED   // byte-identical
ASSERT onboarding-flow.md content & cross-references UNCHANGED
FOR ALL test WHERE NOT isBugCondition_1(test) DO
  ASSERT run(test) = run(test')
END FOR

// Bug 2 — per-file/per-phase counts & existing checks unchanged
FOR ALL file IN index'.file_metadata DO ASSERT file.token_count UNCHANGED END FOR
FOR ALL phase IN index'.phases DO ASSERT phase.token_count, phase.size_category UNCHANGED END FOR
ASSERT check_counts behavior UNCHANGED                          // per-file +/-10%
ASSERT check_phase_counts behavior UNCHANGED                    // per-phase +/-10%
ASSERT measure_steering(--check) = PASS when declared == sum

// Bug 3 — registry & sync_hook_registry unchanged
ASSERT hook-registry.md, hook-registry-critical.md, hook-registry-modules.md UNCHANGED
ASSERT sync_hook_registry(--verify) = PASS
ASSERT all linter rules EXCEPT hook-source selection (and the classification skip) behave identically
```

**Testing Approach**: Property-based testing is recommended for preservation checking because it
generates many inputs across the domain, catches edge cases manual tests miss, and gives strong
guarantees that behavior is unchanged for all non-buggy inputs. The existing suite already encodes
this pattern: `test_steering_index_token_count_sync_preservation.py` pins SHA-256 baselines and
PBT-checks the per-file/per-phase tolerance; `test_lint_steering_properties.py` PBT-checks
bidirectional hook consistency and exit-code correctness on synthetic corpora.

**Test Plan**: Observe behavior on the unfixed code first (banner/language/comprehension locations,
the per-file/per-phase tolerance behavior, the registry/sync agreement), then re-baseline the
moved-content snapshots from live content and confirm the preservation tests still hold after the
fix.

**Test Cases**:

1. **Onboarding content preservation** — assert the welcome banner, language prompt, and
   comprehension steps exist verbatim in `onboarding-phase1b-intro-language.md`, and that
   `onboarding-flow.md` still says "After Step 2d, load `onboarding-phase1b-intro-language.md`."
   Verify both files are byte-identical to the shipped (pre-fix) bytes.
2. **Token per-file/per-phase preservation** — recompute `_BASELINE_HASHES` from the corrected
   `budget` block; confirm `test_steering_index_token_count_sync_preservation.py` passes and every
   per-file/per-phase value is unchanged; confirm `--check` still exits 0 when declared == sum.
3. **Registry preservation** — confirm `sync_hook_registry.py --verify` still passes and the three
   registry files are unchanged after the linter source change.
4. **Other-rules preservation** — confirm `test_lint_steering_unit.py` /
   `test_lint_steering_integration.py` / `test_lint_steering_properties.py` still pass (the
   real-corpus hook-consistency test now passes against the union source; the synthetic
   `hook-registry-critical.md`-based property tests must continue to pass — verify the union logic is
   backward-compatible with a corpus that documents hooks only in `hook-registry-critical.md`).

### Unit Tests

- **Bug 1**: per re-targeted file, assert moved content is found at the new location and old-location
  assertions are gone; assert post-split heading/step numbers (Step 4 language, 5/5a/5b).
- **Bug 2**: `measure_steering.py` unit test — `--check` fails when `total_tokens != sum` and passes
  when equal; `parse_budget_total` extracts the value; per-file/per-phase checks unchanged on a
  fixture with a deliberately wrong aggregate but correct per-file values.
- **Bug 3**: `lint_steering.py` unit test — `check_hook_consistency` against the real corpus produces
  zero "not documented" findings; a module/`any` hook documented only in `hook-registry-modules.md`
  is recognized; the classification skip removes module-03 reference/dispatcher template findings;
  `error_count > 0 ⇒ exit_code == 1`.

### Property-Based Tests

- **Bug 1**: where an existing PBT pins onboarding content (e.g. pointer-marker exploration), keep
  the generator but re-target the source file; the property (marker present / question owned) holds
  against the shipped layout.
- **Bug 2**: extend/confirm a PBT that, for a generated index whose `total_tokens` is perturbed off
  the per-file sum, `--check` reports a mismatch; and for `total_tokens == sum`, `--check` is silent —
  while per-file tolerance behavior is independent of the aggregate.
- **Bug 3**: keep `test_lint_steering_properties.py::TestProperty7HookRegistryConsistency` green —
  generate registry/disk hook-ID sets and assert every registry-only / disk-only hook is reported,
  now over the union of registry sources; keep `test_exit_code_correctness` green.

### Integration Tests

- **Whole-suite gate**: run `python -m pytest senzing-bootcamp/tests/ tests/` and require `0 failed`
  with the passing count ≥ the pre-fix passing count (4648) plus the 147 newly-fixed, minus none.
- **Validator gate**: run all Requirement 3.4 validators; require all pass. Run the strengthened
  `measure_steering.py --check` (now also asserting the aggregate) and `lint_steering.py` (now
  accurate); require exit 0 on the corrected tree.
- **CI gate (if recommendations adopted)**: confirm the broadened workflow triggers on `tests/**`
  and `.github/workflows/**`, and that `lint_steering.py` runs as a CI step and passes.
- **Cross-script agreement**: an integration test asserting `lint_steering.py` and
  `sync_hook_registry.py --verify` reach the same hook-documentation conclusion on the real corpus.
