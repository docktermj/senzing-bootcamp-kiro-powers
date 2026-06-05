# Implementation Plan

## Overview

This plan fixes three **independent** defects in the `senzing-bootcamp` Kiro Power. It follows the
exploratory bugfix methodology: write/run the bug-condition exploration tests FIRST (they fail on
the unfixed tree and confirm each bug), capture preservation baselines on the unfixed tree, then
apply each fix, then re-run the same tests to confirm the bug is gone and nothing regressed.

Property labels map to the design's Correctness Properties so hover status works:

| Bug | Bug-Condition property | Preservation property | Requirements |
|---|---|---|---|
| BUG 1 — onboarding-split test drift | Property 1 | Property 2 | 1.1–1.9 / 2.1–2.9 / 3.1, 3.2, 3.3, 3.6 |
| BUG 2 — token-budget aggregate | Property 3 | Property 4 | 1.10, 1.11 / 2.10, 2.11 / 3.5, 3.7 |
| BUG 3 — linter false positives | Property 5 | Property 6 | 1.12–1.14 / 2.12–2.15 / 3.8, 3.9 |

**Environment:** Python 3.11/3.12/3.13, `pytest` + Hypothesis, stdlib-only scripts (PyYAML only in
`validate_dependencies.py`). Run the suite as `python -m pytest senzing-bootcamp/tests/ tests/`.

**Cross-cutting rule (observation-first regeneration):** every regenerated snapshot/hash is
recomputed from the *current shipped* (post-split, fixed) bytes and is paired with an independent
content assertion, so a regenerated baseline can never silently lock in a regression.

## Tasks

### Phase A — Bug-condition exploration tests (run on UNFIXED code — expected to FAIL)

- [x] 1. Confirm BUG 1 (onboarding-split test drift) with a bug-condition exploration test
  - **Property 1: Bug Condition** - Onboarding-Split Tests Validate the Shipped Layout
  - **IMPORTANT**: Run/observe this BEFORE changing any test. These tests encode the expected
    post-split layout and will validate the fix once they pass after re-targeting.
  - **DO NOT attempt to fix the test or the steering content when it fails here.**
  - **GOAL**: Surface counterexamples proving 147 tests assert moved onboarding content in the
    pre-split location (`onboarding-flow.md` / old heading sequence).
  - **Scoped PBT Approach**: BUG 1 is deterministic — scope the property to the concrete failing
    cases. Run `python -m pytest senzing-bootcamp/tests/ tests/` and capture the authoritative
    failing-test list; confirm `147 failed, 4648 passed, 86 skipped`.
  - Confirm representative counterexamples from the design's impacted-files table:
    - `tests/test_bootcamp_ux_preservation.py::TestOnboardingFlowPreservation::test_welcome_banner_text`
      asserts the welcome banner in `onboarding-flow.md`
      (actual: Step 5 of `onboarding-phase1b-intro-language.md`)
    - `senzing-bootcamp/tests/test_comprehension_check.py` (27), `test_disambiguate_language_prompt.py` (12)
    - `test_missing_pointer_marker_preservation.py` (10) + `_exploration.py` (6) — pinned region/markers
    - `test_onboarding_question_ownership.py` (7) + `test_module_closing_question_ownership.py` (4)
    - `test_track_selection_gate_preservation.py` (5); `test_onboarding_ux_improvements.py` (5) + `test_onboarding_flow_restructuring.py` (5)
    - `test_system_verification_unit.py` (5) + `_properties.py` (2); `test_typescript_language_maturity.py` (3)
    - `test_wait_before_server_termination_preservation.py` (4) + `_bug.py` (2)
    - `test_self_answering_questions_preservation.py` (4) + `_bug.py` (4) + `test_self_answering_reinforcement.py` (2)
    - repo-root `tests/test_license_guidance_workflow_properties.py` (1), `tests/test_auto_load_error_recovery_properties.py` (1)
    - singletons: `test_version_unit.py`, `test_track_switcher_unit.py`, `test_entity_resolution_intro_structure.py`,
      `test_session_resume_split.py`, `test_mandatory_gate_exploration.py`, `test_cord_data_priority.py`,
      `test_no_skip_offer_mandatory_gate_bug.py`, `test_bootcamp_ux_feedback_unit.py`, `test_sdk_method_discovery_bug.py`
  - **EXPECTED OUTCOME**: 147 tests FAIL (this is correct — it proves the drift exists).
  - Document the counterexamples and persist the exact failing-test list for use in Task 7.
  - Mark complete when the suite has been run and the 147 failures are recorded.
  - _Bug_Condition: isBugCondition_1(test) — asserts welcome banner / language-selection step / comprehension checks (3,4,4b/5a,4c/5b) in pre-split layout_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_

- [x] 2. Confirm BUG 2 (token-budget aggregate mismatch) with a bug-condition exploration test
  - **Property 3: Bug Condition** - Token-Budget Aggregate Equals the Sum and Is Enforced
  - **IMPORTANT**: Run this BEFORE changing `steering-index.yaml` or `measure_steering.py`.
  - **DO NOT attempt to fix the data or script when it fails here.**
  - **GOAL**: Show the declared aggregate diverges from the per-file sum AND that `--check` is blind to it.
  - **Scoped PBT Approach**: deterministic — scope to the shipped index. Run
    `senzing-bootcamp/tests/test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_actual_steering_index_total_tokens_equals_sum`.
  - Confirm `budget.total_tokens` is declared `169633` while the sum of the 91
    `file_metadata.*.token_count` entries is `169576` (off by +57).
  - Confirm the validator blind spot: `python senzing-bootcamp/scripts/measure_steering.py --check`
    prints "within 10% tolerance" and exits `0` despite the mismatch.
  - **EXPECTED OUTCOME**: `test_actual_steering_index_total_tokens_equals_sum` FAILS; `--check` exits 0.
  - Document the counterexample: `declared=169633, sum(file_metadata)=169576`.
  - Mark complete when the failing property test and the silent `--check` are recorded.
  - _Bug_Condition: isBugCondition_2(index) — index.budget.total_tokens != SUM(file_metadata[*].token_count)_
  - _Requirements: 1.10, 1.11_

- [x] 3. Confirm BUG 3 (linter false positives) with a bug-condition exploration test
  - **Property 5: Bug Condition** - Linter Agrees With the Registry Source of Truth
  - **IMPORTANT**: Run this BEFORE changing `lint_steering.py`.
  - **DO NOT attempt to fix the linter or the registry when it fails here.**
  - **GOAL**: Show `lint_steering.py` reports documented hooks as undocumented and disagrees with
    `sync_hook_registry.py --verify`.
  - **Scoped PBT Approach**: deterministic — scope to the real corpus. Run
    `python senzing-bootcamp/scripts/lint_steering.py` and capture output.
  - Confirm 24 `WARNING: ... 'X.kiro.hook' exists but is not documented in the hook registry`
    lines for hooks such as `verify-sdk-setup`, `security-scan-on-save`, `run-tests-after-change`,
    `gate-module3-visualization` — all present in `hook-registry.md` / `hook-registry-modules.md`.
  - Confirm the disagreement: `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    prints "All registry files are up to date." and exits `0`.
  - **Edge case (refines root cause)**: confirm the only ERROR is the
    `module-03-visualization-api-reference.md` missing first-read instruction, and confirm the
    linter currently exits `1` when that ERROR is present — refuting the audit's "exits 0 on error"
    claim and re-scoping clause 2.14 to a regression guard + classification fix (per design).
  - **EXPECTED OUTCOME**: 24 false "not documented" warnings present; linter vs `sync_hook_registry` disagree.
  - Document the counterexamples (the wrong-source root cause: Rule 6 reads only `hook-registry-critical.md`).
  - Mark complete when the false positives and the disagreement are recorded.
  - _Bug_Condition: isBugCondition_3(hook) — linter reports a hook "not documented" though it is in hook-registry.md OR hook-registry-modules.md_
  - _Requirements: 1.12, 1.13, 1.14_

### Phase B — Preservation tests (run on UNFIXED code — expected to PASS)

- [x] 4. Capture BUG 1 preservation baselines (observation-first, on UNFIXED tree)
  - **Property 2: Preservation** - Steering Content and Previously-Passing Tests Unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe shipped content, then assert it.
  - Observe on the unfixed tree and record:
    - the welcome banner, the "programming language" prompt, and comprehension steps (3, 4, 5a/5b)
      exist verbatim in `onboarding-phase1b-intro-language.md`
    - `onboarding-flow.md` still says "After Step 2d, load `onboarding-phase1b-intro-language.md`"
  - Capture byte-level baselines: SHA-256 of `onboarding-flow.md` and
    `onboarding-phase1b-intro-language.md` so the fix can prove both `.md` files stay byte-identical.
  - Write/confirm a property-based assertion that, for all moved-content markers, the marker is
    present in the phase file (post-split location) — this is the preservation companion to Property 1.
  - Record the current passing count (4648) to confirm no previously-passing test regresses.
  - **EXPECTED OUTCOME**: these preservation observations hold on the UNFIXED tree (baseline confirmed).
  - _Preservation: onboarding `.md` files byte-identical; cross-references intact; non-bug-condition tests unchanged_
  - _Requirements: 3.1, 3.2, 3.3, 3.6_

- [x] 5. Capture BUG 2 preservation baselines (observation-first, on UNFIXED tree)
  - **Property 4: Preservation** - Per-File / Per-Phase Counts and Existing Checks Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the unfixed tree:
    - every per-file `token_count` value in `file_metadata` (91 entries)
    - every phase `token_count` / `size_category` in `phases`
    - the other `budget` sub-keys (`reference_window`, `warn_threshold_pct`,
      `critical_threshold_pct`, `split_threshold_tokens`)
  - Confirm `measure_steering.py --check` per-file ±10% and per-phase tolerance checks pass on the
    unfixed tree (the additive aggregate check is not yet present).
  - Write/confirm a property-based test: for an index whose per-file values are unchanged, the
    per-file ±10% and per-phase checks behave identically regardless of the aggregate value.
  - **EXPECTED OUTCOME**: per-file/per-phase baselines hold; existing `--check` semantics confirmed.
  - _Preservation: per-file/per-phase counts unchanged; only budget.total_tokens changes (169633 -> 169576)_
  - _Requirements: 3.5, 3.7_

- [x] 6. Capture BUG 3 preservation baselines (observation-first, on UNFIXED tree)
  - **Property 6: Preservation** - Registry Contents and sync_hook_registry Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the unfixed tree:
    - SHA-256 of `hook-registry.md`, `hook-registry-critical.md`, `hook-registry-modules.md`
    - `sync_hook_registry.py --verify` passes (exit 0)
  - Confirm every linter rule OTHER than hook-consistency source selection behaves as today by
    running `test_lint_steering_unit.py`, `test_lint_steering_integration.py`, and
    `test_lint_steering_properties.py` (note: the synthetic property tests are built on
    `hook-registry-critical.md`, so the fix's union logic must remain backward-compatible).
  - Write/confirm a property-based preservation assertion: registry file digests are unchanged and
    `sync_hook_registry --verify` still passes after the linter source change.
  - **EXPECTED OUTCOME**: registry digests and `sync_hook_registry --verify` baseline confirmed on UNFIXED tree.
  - _Preservation: hook-registry*.md unchanged; sync_hook_registry --verify passes; all other linter rules identical_
  - _Requirements: 3.8, 3.9_

### Phase C — Fixes (independent; see Task Dependency Graph)

- [x] 7. Fix BUG 1 — re-target/re-baseline the 147 onboarding-split tests (tests only, NO `.md` changes)

  - [x] 7.1 Re-target file reads to the shipped layout
    - Where a test reads `onboarding-flow.md` (directly, via a path constant, or via a fixture) and
      asserts moved content, change the path to `onboarding-phase1b-intro-language.md`.
    - For genuinely cross-file assertions (e.g. "version step before welcome banner"), split: read
      the version step from `onboarding-flow.md` (Step 0c) and the banner from the phase file
      (Step 5); assert ordering via the documented load sequence, not within-file position.
    - Cover the language-prompt cluster (`test_disambiguate_language_prompt.py`) -> phase file Step 4,
      and `test_typescript_language_maturity.py` -> language-maturity content in the phase file.
    - _Bug_Condition: isBugCondition_1(test) — stale file target in assertions_
    - _Expected_Behavior: expectedBehavior — test references onboarding-phase1b-intro-language.md and passes_
    - _Preservation: no steering `.md` file is edited_
    - _Requirements: 2.1, 2.3, 2.7, 2.8_

  - [x] 7.2 Update heading/step numbers to the post-split sequence
    - Language selection is Step 4; verbosity is Step 5a; comprehension check is Step 5b in the phase file.
    - Update hardcoded step numbers and heading-order lists in `test_comprehension_check.py`,
      `test_onboarding_ux_improvements.py`, `test_onboarding_flow_restructuring.py`,
      `test_entity_resolution_intro_structure.py`, `test_version_unit.py`, `test_track_switcher_unit.py`,
      `test_session_resume_split.py`, `test_mandatory_gate_exploration.py`.
    - _Bug_Condition: isBugCondition_1(test) — stale heading-sequence expectations_
    - _Expected_Behavior: tests assert post-split heading sequence (Step 4 / 5a / 5b) and pass_
    - _Requirements: 2.2, 2.6, 2.9_

  - [x] 7.3 Re-baseline pinned snapshots/hashes from live shipped content (observation-first)
    - **BUG 1 fix — TESTS ONLY.** No steering `.md` file may be modified in any leaf below.
    - **Observation-first:** recompute every snapshot/hash by reading the CURRENT shipped
      (post-split) steering content; never hand-edit a hash to make a test pass.
    - **Split is intentional:** content moved out of `onboarding-flow.md` into
      `onboarding-phase1b-intro-language.md`. The split must NOT be reverted.
    - Pair every regenerated baseline with an independent content assertion (banner present, prompt
      uses "programming language", etc.).
    - **"Moved vs changed" guard:** if recomputed content differs in more than location, STOP and
      raise it as a possible regression rather than pinning it.
    - Leaves are grouped by related test files so each is independently verifiable; run each leaf's
      specific test file(s) and confirm they pass before marking that leaf complete.

    - [x] 7.3.1 Re-baseline pointer-marker tests
      - For substring snapshots: replace the pinned literal with the current shipped text read from
        the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
      - Apply to `senzing-bootcamp/tests/test_missing_pointer_marker_preservation.py` and
        `senzing-bootcamp/tests/test_missing_pointer_marker_exploration.py`.
      - Pair every regenerated baseline with an independent content assertion (banner present, prompt
        uses "programming language", etc.); if recomputed content differs in more than location, STOP
        and raise it as a possible regression rather than pinning it.
      - Verify: `python -m pytest senzing-bootcamp/tests/test_missing_pointer_marker_preservation.py senzing-bootcamp/tests/test_missing_pointer_marker_exploration.py` and confirm they pass.
      - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
      - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
      - _Preservation: regenerated baselines reflect content that moved unchanged_
      - _Requirements: 2.4, 2.6, 2.9_

    - [x] 7.3.2 Re-baseline track-selection gate
      - For substring snapshots: replace the pinned literal with the current shipped text read from
        the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
      - Apply to `senzing-bootcamp/tests/test_track_selection_gate_preservation.py`.
      - Pair every regenerated baseline with an independent content assertion (banner present, prompt
        uses "programming language", etc.); if recomputed content differs in more than location, STOP
        and raise it as a possible regression rather than pinning it.
      - Verify: `python -m pytest senzing-bootcamp/tests/test_track_selection_gate_preservation.py` and confirm it passes.
      - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
      - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
      - _Preservation: regenerated baselines reflect content that moved unchanged_
      - _Requirements: 2.4, 2.6, 2.9_

    - [x] 7.3.3 Re-baseline system-verification tests
      - For substring snapshots: replace the pinned literal with the current shipped text read from
        the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
      - Apply to `senzing-bootcamp/tests/test_system_verification_unit.py` and
        `senzing-bootcamp/tests/test_system_verification_properties.py`.
      - Pair every regenerated baseline with an independent content assertion (banner present, prompt
        uses "programming language", etc.); if recomputed content differs in more than location, STOP
        and raise it as a possible regression rather than pinning it.
      - Verify: `python -m pytest senzing-bootcamp/tests/test_system_verification_unit.py senzing-bootcamp/tests/test_system_verification_properties.py` and confirm they pass.
      - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
      - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
      - _Preservation: regenerated baselines reflect content that moved unchanged_
      - _Requirements: 2.4, 2.6, 2.9_

    - [x] 7.3.4 Re-baseline wait-before-server-termination tests
      - For substring snapshots: replace the pinned literal with the current shipped text read from
        the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
      - Apply to `senzing-bootcamp/tests/test_wait_before_server_termination_preservation.py` and
        `senzing-bootcamp/tests/test_wait_before_server_termination_bug.py`.
      - Pair every regenerated baseline with an independent content assertion (banner present, prompt
        uses "programming language", etc.); if recomputed content differs in more than location, STOP
        and raise it as a possible regression rather than pinning it.
      - Verify: `python -m pytest senzing-bootcamp/tests/test_wait_before_server_termination_preservation.py senzing-bootcamp/tests/test_wait_before_server_termination_bug.py` and confirm they pass.
      - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
      - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
      - _Preservation: regenerated baselines reflect content that moved unchanged_
      - _Requirements: 2.4, 2.6, 2.9_

    - [x] 7.3.5 Re-baseline self-answering tests
      - Split into one leaf per test file so each is small and independently verifiable.
      - For substring snapshots: replace the pinned literal with the current shipped text read from
        the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
      - Pair every regenerated baseline with an independent content assertion (banner present, prompt
        uses "programming language", etc.); if recomputed content differs in more than location, STOP
        and raise it as a possible regression rather than pinning it.

      - [x] 7.3.5a Re-baseline self-answering preservation test
        - For substring snapshots: replace the pinned literal with the current shipped text read from
          the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
        - Apply to `senzing-bootcamp/tests/test_self_answering_questions_preservation.py`.
        - Pair every regenerated baseline with an independent content assertion; if recomputed content
          differs in more than location, STOP and raise it as a possible regression rather than pinning it.
        - Verify: `python -m pytest senzing-bootcamp/tests/test_self_answering_questions_preservation.py` and confirm it passes.
        - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
        - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
        - _Preservation: regenerated baselines reflect content that moved unchanged_
        - _Requirements: 2.4, 2.6, 2.9_

      - [x] 7.3.5b Re-baseline self-answering bug test
        - For substring snapshots: replace the pinned literal with the current shipped text read from
          the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
        - Apply to `senzing-bootcamp/tests/test_self_answering_questions_bug.py`.
        - Pair every regenerated baseline with an independent content assertion; if recomputed content
          differs in more than location, STOP and raise it as a possible regression rather than pinning it.
        - Verify: `python -m pytest senzing-bootcamp/tests/test_self_answering_questions_bug.py` and confirm it passes.
        - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
        - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
        - _Preservation: regenerated baselines reflect content that moved unchanged_
        - _Requirements: 2.4, 2.6, 2.9_

      - [x] 7.3.5c Re-baseline self-answering reinforcement test
        - For substring snapshots: replace the pinned literal with the current shipped text read from
          the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
        - Apply to `senzing-bootcamp/tests/test_self_answering_reinforcement.py`.
        - Pair every regenerated baseline with an independent content assertion; if recomputed content
          differs in more than location, STOP and raise it as a possible regression rather than pinning it.
        - Verify: `python -m pytest senzing-bootcamp/tests/test_self_answering_reinforcement.py` and confirm it passes.
        - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
        - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
        - _Preservation: regenerated baselines reflect content that moved unchanged_
        - _Requirements: 2.4, 2.6, 2.9_

    - [x] 7.3.6 Re-baseline misc singletons
      - Split into one leaf per test file so each is small and independently verifiable.
      - For substring snapshots: replace the pinned literal with the current shipped text read from
        the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
      - Pair every regenerated baseline with an independent content assertion (banner present, prompt
        uses "programming language", etc.); if recomputed content differs in more than location, STOP
        and raise it as a possible regression rather than pinning it.

      - [x] 7.3.6a Re-baseline cord-data-priority test
        - For substring snapshots: replace the pinned literal with the current shipped text read from
          the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
        - Apply to `senzing-bootcamp/tests/test_cord_data_priority.py`.
        - Pair every regenerated baseline with an independent content assertion; if recomputed content
          differs in more than location, STOP and raise it as a possible regression rather than pinning it.
        - Verify: `python -m pytest senzing-bootcamp/tests/test_cord_data_priority.py` and confirm it passes.
        - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
        - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
        - _Preservation: regenerated baselines reflect content that moved unchanged_
        - _Requirements: 2.4, 2.6, 2.9_

      - [x] 7.3.6b Re-baseline no-skip-offer-mandatory-gate test
        - For substring snapshots: replace the pinned literal with the current shipped text read from
          the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
        - Apply to `senzing-bootcamp/tests/test_no_skip_offer_mandatory_gate_bug.py`.
        - Pair every regenerated baseline with an independent content assertion; if recomputed content
          differs in more than location, STOP and raise it as a possible regression rather than pinning it.
        - Verify: `python -m pytest senzing-bootcamp/tests/test_no_skip_offer_mandatory_gate_bug.py` and confirm it passes.
        - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
        - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
        - _Preservation: regenerated baselines reflect content that moved unchanged_
        - _Requirements: 2.4, 2.6, 2.9_

      - [x] 7.3.6c Re-baseline bootcamp-ux-feedback-unit test
        - For substring snapshots: replace the pinned literal with the current shipped text read from
          the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
        - Apply to `senzing-bootcamp/tests/test_bootcamp_ux_feedback_unit.py`.
        - Pair every regenerated baseline with an independent content assertion; if recomputed content
          differs in more than location, STOP and raise it as a possible regression rather than pinning it.
        - Verify: `python -m pytest senzing-bootcamp/tests/test_bootcamp_ux_feedback_unit.py` and confirm it passes.
        - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
        - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
        - _Preservation: regenerated baselines reflect content that moved unchanged_
        - _Requirements: 2.4, 2.6, 2.9_

      - [x] 7.3.6d Re-baseline sdk-method-discovery test
        - For substring snapshots: replace the pinned literal with the current shipped text read from
          the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
        - Apply to `senzing-bootcamp/tests/test_sdk_method_discovery_bug.py`.
        - Pair every regenerated baseline with an independent content assertion; if recomputed content
          differs in more than location, STOP and raise it as a possible regression rather than pinning it.
        - Verify: `python -m pytest senzing-bootcamp/tests/test_sdk_method_discovery_bug.py` and confirm it passes.
        - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
        - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
        - _Preservation: regenerated baselines reflect content that moved unchanged_
        - _Requirements: 2.4, 2.6, 2.9_

    - [x] 7.3.7 Re-baseline repo-root tests
      - For substring snapshots: replace the pinned literal with the current shipped text read from
        the correct file. For SHA-256 of a file/region: recompute from current shipped bytes.
      - Apply to repo-root `tests/test_bootcamp_ux_preservation.py`,
        `tests/test_license_guidance_workflow_properties.py`, and
        `tests/test_auto_load_error_recovery_properties.py`.
      - Pair every regenerated baseline with an independent content assertion (banner present, prompt
        uses "programming language", etc.); if recomputed content differs in more than location, STOP
        and raise it as a possible regression rather than pinning it.
      - Verify: `python -m pytest tests/test_bootcamp_ux_preservation.py tests/test_license_guidance_workflow_properties.py tests/test_auto_load_error_recovery_properties.py` and confirm they pass.
      - _Bug_Condition: isBugCondition_1(test) — pinned snapshots/hashes of the old region_
      - _Expected_Behavior: baselines recomputed from shipped post-split bytes; tests pass_
      - _Preservation: regenerated baselines reflect content that moved unchanged_
      - _Requirements: 2.4, 2.6, 2.9_

  - [x] 7.4 Update question-ownership maps to the new owning file
    - In `test_onboarding_question_ownership.py` and `test_module_closing_question_ownership.py`,
      move the welcome-banner / language / comprehension questions to the
      `onboarding-phase1b-intro-language.md` owner entry.
    - _Bug_Condition: isBugCondition_1(test) — question-ownership mapping outdated_
    - _Expected_Behavior: ownership asserted against the file that now owns each question; tests pass_
    - _Requirements: 2.5_

  - [x] 7.4b Re-target the remaining same-branch refactor drift failures (tests only)
    - The full-suite run for 7.5 surfaced ~12 additional failures beyond the enumerated clusters —
      same-branch refactor drift (module-03 dispatcher split, agent-instructions.md condensation,
      session-resume split) that earlier leaves only partially re-targeted (headings/steps but not
      content-relocation / token-budget / pinned-hash assertions). These are TESTS-ONLY; NO steering
      `.md` may be modified. Use observation-first re-baselining and the "moved vs changed" STOP guard.
    - agent-instructions.md condensation (content relocated to `track-switching.md` /
      `agent-context-management.md`):
      - `test_track_switcher_unit.py::TestAgentInstructions::test_contains_trigger_phrases`
        ("move to core" etc. now in `track-switching.md`)
      - `test_smart_context_budget.py::TestAgentInstructionsContextBudget::test_uses_percentage_not_absolute_in_budget_section`
        (Context Budget section condensed; detail moved to `agent-context-management.md`)
    - module-03 dispatcher split (Step 9 → phase2, Step 12 → phase3):
      - `test_mandatory_gate_exploration.py` (2: `test_step9_has_mandatory_gate_marker`,
        `test_mandatory_gate_marker_on_step9_line`)
      - `test_mandatory_gate_preservation.py::TestContextBudgetIndependence::test_module3_step9_does_not_allow_budget_skip`
      - `test_module3_visualization_no_skip_preservation.py::TestUnrelatedRegionsByteStable::test_unrelated_files_match_sha256_baseline`
      - `test_skip_reflection_questions_bug.py::...test_step12_has_no_reflection_question_instruction`
      - `test_skip_reflection_questions_preservation.py::...test_step12_preserved_instructions_intact`
    - onboarding/module-table + session-resume split:
      - `test_remove_duplicate_module_table.py::TestPreservationStep4::test_step4_contains_module_overview_instruction`
      - `test_steering_template_unit.py::TestRealModuleFirstRead::test_real_root_modules_have_first_read`
      - `test_session_resume_split.py` (2: `test_phase1_token_budget` — phase1 now 3380 tokens;
        `test_phase1_has_inclusion_manual_frontmatter`)
    - For each: re-target file reads / headings to the shipped location, recompute pinned SHA-256
      baselines from current shipped bytes, and adjust token-budget thresholds ONLY to match the
      shipped split (pair each with an independent content assertion). If a failure reflects a genuine
      content change rather than relocation, STOP and report it instead of pinning.
    - EXCLUDED (not this task — likely pre-existing independent property bugs, handle separately):
      `test_assess_entry_point.py::...test_result_is_valid_path`,
      `test_generate_recap_pdf.py::...test_sections_preserve_chronological_order`,
      `test_session_persistence_properties.py::...test_writing_one_field_preserves_others`.
    - EXCLUDED (owned by BUG 2 / task 8): `test_split_steering.py::...test_total_tokens_matches_sum`,
      `test_steering_index_token_count_sync_preservation.py` (2),
      `test_token_budget_optimization.py::...test_actual_steering_index_total_tokens_equals_sum`,
      `test_entity_resolution_intro_structure.py` (2 — driven by the 169633→169576 aggregate).
    - Verify each re-targeted file with `python -m pytest <file>` and confirm it passes.
    - _Bug_Condition: isBugCondition_1(test) — stale file target / pinned snapshot of moved region_
    - _Expected_Behavior: baselines recomputed from shipped post-split/refactor bytes; tests pass_
    - _Preservation: no steering `.md` file is edited; regenerated baselines reflect content that moved unchanged_
    - _Requirements: 2.1, 2.6, 2.9_

  - [x] 7.5 Verify the BUG 1 exploration test now passes
    - **Property 1: Expected Behavior** - Onboarding-Split Tests Validate the Shipped Layout
    - **IMPORTANT**: Re-run the SAME re-targeted tests from Task 1 — do NOT write new tests here.
    - Run the previously-failing 147 tests (and the full onboarding clusters).
    - **EXPECTED OUTCOME**: all 147 now PASS (confirms the drift is resolved).
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 7.6 Verify the BUG 1 preservation baselines still hold
    - **Property 2: Preservation** - Steering Content and Previously-Passing Tests Unchanged
    - **IMPORTANT**: Re-run the SAME preservation checks from Task 4 — do NOT write new tests.
    - Confirm `onboarding-flow.md` and `onboarding-phase1b-intro-language.md` are byte-identical to
      the Task 4 SHA-256 baselines, cross-references intact, and the passing count did not drop.
    - **EXPECTED OUTCOME**: preservation tests PASS (no steering content changed, no regressions).
    - _Requirements: 3.1, 3.2, 3.3, 3.6_

- [x] 8. Fix BUG 2 — correct the aggregate and add an additive aggregate check to `measure_steering.py`

  - [x] 8.1 Correct the declared aggregate in `steering-index.yaml`
    - Change `budget.total_tokens: 169633` -> `budget.total_tokens: 169576`. No other line changes.
    - _Bug_Condition: isBugCondition_2(index) — declared total != sum of per-file token_count_
    - _Expected_Behavior: budget.total_tokens == SUM(file_metadata[*].token_count) == 169576_
    - _Preservation: per-file/per-phase entries and other budget sub-keys untouched_
    - _Requirements: 2.10, 3.7_

  - [x] 8.2 Add the additive aggregate check to `measure_steering.py` (stdlib-only)
    - Add `parse_budget_total(content) -> int | None` using a localized regex consistent with the
      existing `re.search(r"total_tokens:\s*(\d+)")` usage in `simulate_context_load`.
    - In `main()`'s `--check` branch, AFTER the existing `check_counts` and `check_phase_counts`
      calls, compute `declared = parse_budget_total(...)` and `expected = sum(file_metadata token_count)`
      (reuse `_parse_stored_metadata` so the "sum" matches `check_counts`); report a mismatch on
      exact inequality with a clear message, e.g.
      `Budget total mismatch: declared=169633, sum(file_metadata)=169576`.
    - Exit non-zero if ANY of the three checks fail. The aggregate check is ADDITIVE — per-file ±10%
      and per-phase checks run exactly as before. Do NOT change update mode (it already writes the sum).
    - _Bug_Condition: isBugCondition_2(index) — validator blind spot (no aggregate assertion)_
    - _Expected_Behavior: --check FAILS (exit non-zero) whenever declared != sum; passes when equal_
    - _Preservation: stdlib-only; minimal-regex parsing reused; per-file/per-phase checks unchanged_
    - _Requirements: 2.11, 3.5_

  - [x] 8.3 Re-baseline the budget hash in the preservation test (observation-first)
    - Recompute `_BASELINE_HASHES["budget"]` in
      `senzing-bootcamp/tests/test_steering_index_token_count_sync_preservation.py` as the SHA-256 of
      the `budget` block AFTER `total_tokens` is corrected to 169576 (read from live content).
    - This makes `test_update_mode_preserves_non_phase_blocks` and
      `test_total_equals_file_metadata_sum_before_and_after` pass (declared == sum on the corrected index).
    - Note: `test_token_budget_optimization.py::...::test_actual_steering_index_total_tokens_equals_sum`
      needs NO edit — it computes the sum live and passes once 8.1 lands.
    - _Bug_Condition: isBugCondition_2 — stale pinned budget-block hash_
    - _Expected_Behavior: budget-block hash recomputed from corrected bytes; coupled tests pass_
    - _Preservation: non-budget blocks and per-file/per-phase hashes unchanged_
    - _Requirements: 2.10, 2.11_

  - [x] 8.4 Verify the BUG 2 exploration test now passes
    - **Property 3: Expected Behavior** - Token-Budget Aggregate Equals the Sum and Is Enforced
    - **IMPORTANT**: Re-run the SAME tests/commands from Task 2 — do NOT write new tests.
    - Run `test_actual_steering_index_total_tokens_equals_sum` (now PASS) and confirm
      `measure_steering.py --check` now FAILS on a fixture whose aggregate is perturbed off the sum.
    - **EXPECTED OUTCOME**: aggregate equals the sum and `--check` enforces it.
    - _Requirements: 2.10, 2.11_

  - [x] 8.5 Verify the BUG 2 preservation baselines still hold
    - **Property 4: Preservation** - Per-File / Per-Phase Counts and Existing Checks Unchanged
    - **IMPORTANT**: Re-run the SAME preservation checks from Task 5 — do NOT write new tests.
    - Confirm every per-file `token_count` and every phase `token_count`/`size_category` match the
      Task 5 baselines, other `budget` sub-keys unchanged, and `--check` exits 0 when declared == sum.
    - **EXPECTED OUTCOME**: preservation tests PASS (only `total_tokens` changed).
    - _Requirements: 3.5, 3.7_

- [x] 9. Fix BUG 3 — point the linter at the union registry source and reclassify reference/dispatcher files

  - [x] 9.1 Read the full registry source set in `check_hook_consistency` (stdlib-only)
    - Replace the single `registry_path = steering_path / "hook-registry-critical.md"` with the same
      set `sync_hook_registry.py` treats as the documentation surface: `hook-registry.md`,
      `hook-registry-critical.md`, `hook-registry-modules.md`.
    - Build `registry_ids` as the UNION of hook IDs across those files; build `registry_event_types`
      from the full-prompt files carrying `**hook-id** (eventType -> actionType)` headers.
    - Handle BOTH parse shapes: the markdown table rows in `hook-registry.md`
      (`| ask-bootcamper | agentStop -> askAgent | ... |`) and the
      `- id: \`hook-id\`` + `**hook-id** (eventType -> actionType)` shapes in `-critical`/`-modules`
      (extend `RE_HOOK_ID` / `RE_HOOK_EVENT_TYPE` usage or add a table-row parser).
    - The "registry file not found" ERROR should fire only if ALL sources are absent.
    - _Bug_Condition: isBugCondition_3(hook) — wrong registry source (reads only hook-registry-critical.md)_
    - _Expected_Behavior: a hook documented in ANY recognized source is "documented"; no false positives_
    - _Preservation: registry files and sync_hook_registry.py unchanged_
    - _Requirements: 2.12, 2.13_

  - [x] 9.2 Reclassify reference/dispatcher module files out of module-template checks
    - Extend `get_module_steering_files` (used by `check_module_frontmatter`,
      `check_first_read_instruction`, `check_before_after_block`, `check_checkpoint_completeness`,
      `check_success_indicator`, `check_section_order`) to skip files that are reference/dispatcher:
      - filename suffix `*-api-reference.md` (e.g. `module-03-visualization-api-reference.md`), and
      - module files declaring a `## Phase Sub-Files` section (e.g. `module-03-system-verification.md`).
    - This resolves the only current ERROR (the visualization-reference first-read instruction) and
      the two module-03 success-indicator warnings WITHOUT injecting cosmetic scaffolding into
      reference content. Do not change registry contents or `sync_hook_registry --verify`.
    - _Bug_Condition: legitimate template findings from reference/dispatcher misclassification_
    - _Expected_Behavior: reference/dispatcher files excluded from workflow-template checks; clean run_
    - _Requirements: 2.15_

  - [x] 9.3 Add the exit-code regression guard test
    - Add a test pinning "error_count > 0 ⇒ exit_code != 0" for `run_all_checks` (the logic is
      already correct on HEAD — this is a regression guard, not a present defect).
    - Record in the test docstring that the audit's "exits 0 on error" claim (clause 1.14/2.14) does
      not reproduce on HEAD; the exit-0 symptom only appears with warnings and ZERO errors.
    - _Bug_Condition: guard for isBugCondition_3 exit-code contract_
    - _Expected_Behavior: (error_count > 0) IMPLIES (exit_code != 0)_
    - _Requirements: 2.14_

  - [x] 9.4 Verify the BUG 3 exploration test now passes
    - **Property 5: Expected Behavior** - Linter Agrees With the Registry Source of Truth
    - **IMPORTANT**: Re-run the SAME checks from Task 3 — do NOT write new tests.
    - Run `python senzing-bootcamp/scripts/lint_steering.py`: confirm zero false "not documented"
      findings, that its hook-doc conclusions agree with `sync_hook_registry.py --verify`, the
      module-03 reference/dispatcher findings are gone, and it exits 0 on the corrected tree.
    - **EXPECTED OUTCOME**: linter runs clean and agrees with the source of truth.
    - _Requirements: 2.12, 2.13, 2.14, 2.15_

  - [x] 9.5 Verify the BUG 3 preservation baselines still hold
    - **Property 6: Preservation** - Registry Contents and sync_hook_registry Unchanged
    - **IMPORTANT**: Re-run the SAME preservation checks from Task 6 — do NOT write new tests.
    - Confirm `hook-registry.md`, `hook-registry-critical.md`, `hook-registry-modules.md` match the
      Task 6 SHA-256 baselines; `sync_hook_registry.py --verify` still passes; and
      `test_lint_steering_unit.py` / `_integration.py` / `_properties.py` still pass (union logic is
      backward-compatible with the synthetic `hook-registry-critical.md`-only corpora).
    - **EXPECTED OUTCOME**: registry unchanged; all other linter rules behave identically.
    - _Requirements: 3.8, 3.9_

### Phase D — CI hardening (OPTIONAL) and whole-suite gate

- [x] 10. (Optional) Close the CI gaps that hid these defects
  - Broaden triggers in `.github/workflows/validate-power.yml`: add `tests/**` and
    `.github/workflows/**` to `on.pull_request.paths` and `on.push.paths` (consider removing the
    path filter on `push: branches: [main]`) so changes outside `senzing-bootcamp/**` are covered.
  - Add `python senzing-bootcamp/scripts/lint_steering.py` as a CI step after
    `sync_hook_registry --verify`, now that it exits non-zero only on real errors.
  - Flag for the user (not a code change): CI invokes `python` (provided by `setup-python`); the
    local dev environment only has `python3`. This is an environment detail, not a defect.
  - _Requirements: supports 3.4 (keeps validators enforced in CI); design "CI recommendation"_

- [x] 11. Checkpoint — whole-suite gate and validator gate
  - Run the ENTIRE suite (not just previously-failing files): `python -m pytest senzing-bootcamp/tests/ tests/`
    and require `0 failed` with the passing count not dropping (>= 4648 pre-fix + 147 fixed).
  - Run every standalone validator and require all pass: `validate_power`, `validate_dependencies`,
    `validate_prerequisites`, `validate_mandatory_gates`, `validate_governance_rules`,
    `validate_yaml_schemas`, `compose_hook_prompts --verify`, `sync_hook_registry --verify`,
    `validate_commonmark`, `measure_steering --check`.
  - Confirm the strengthened `measure_steering.py --check` (now asserting the aggregate) and
    `lint_steering.py` (now accurate) both run clean (exit 0) on the corrected tree.
  - Confirm cross-script agreement: `lint_steering.py` and `sync_hook_registry.py --verify` reach the
    same hook-documentation conclusion on the real corpus.
  - Ensure all tests pass; ask the user if questions arise.
  - _Requirements: 2.1, 3.4, 3.6 (and all Phase C requirements via the green suite)_

---

## Task Dependency Graph

The three bugs are INDEPENDENT and fixed in parallel waves. Each fix depends only on its own
exploration + preservation tasks (all of which run on the unfixed tree and are themselves parallel).

```json
{
  "waves": [
    {
      "wave": 0,
      "name": "Baseline on UNFIXED tree (all parallel)",
      "tasks": ["1", "2", "3", "4", "5", "6"],
      "parallel": true,
      "dependsOn": []
    },
    {
      "wave": 1,
      "name": "Fixes (three independent lanes, parallel)",
      "tasks": ["7", "8", "9"],
      "parallel": true,
      "dependsOn": {
        "7": ["1", "4"],
        "8": ["2", "5"],
        "9": ["3", "6"]
      }
    },
    {
      "wave": 2,
      "name": "Optional CI hardening",
      "tasks": ["10"],
      "parallel": false,
      "dependsOn": {
        "10": ["9"]
      }
    },
    {
      "wave": 3,
      "name": "Convergence gate",
      "tasks": ["11"],
      "parallel": false,
      "dependsOn": {
        "11": ["7", "8", "9", "10"]
      }
    }
  ]
}
```

```text
Wave 0 — baseline on UNFIXED tree (all parallel; no inter-dependencies):
  +- Task 1  BUG 1 exploration (Property 1: Bug Condition)      - expect 147 FAIL
  +- Task 2  BUG 2 exploration (Property 3: Bug Condition)      - expect 1 FAIL + silent --check
  +- Task 3  BUG 3 exploration (Property 5: Bug Condition)      - expect 24 false warnings
  +- Task 4  BUG 1 preservation (Property 2: Preservation)      - expect PASS (baseline)
  +- Task 5  BUG 2 preservation (Property 4: Preservation)      - expect PASS (baseline)
  +- Task 6  BUG 3 preservation (Property 6: Preservation)      - expect PASS (baseline)

Wave 1 — fixes (three independent lanes, parallel):
  +- Task 7  Fix BUG 1   (depends on Task 1 + Task 4)
  |     7.1 -> 7.2 -> 7.3 -> 7.4  (re-target / headings / hashes / ownership — parallelizable per cluster)
  |     7.3 parent splits into independently-verifiable leaves 7.3.1..7.3.7 (grouped by related test files)
  |     7.5 verify (Property 1: Expected Behavior),  7.6 verify (Property 2: Preservation)
  +- Task 8  Fix BUG 2   (depends on Task 2 + Task 5)
  |     8.1 -> 8.2 -> 8.3,  8.4 verify (Property 3),  8.5 verify (Property 4)
  +- Task 9  Fix BUG 3   (depends on Task 3 + Task 6)
        9.1 -> 9.2 -> 9.3,  9.4 verify (Property 5),  9.5 verify (Property 6)

Wave 2 — optional CI hardening:
  +- Task 10  (depends on Task 9 — linter is accurate before adding it to CI)

Wave 3 — convergence gate (depends on Task 7, 8, 9; and Task 10 if adopted):
  +- Task 11  Whole-suite + validator + cross-script-agreement gate
```

## Notes

- **Coupling note:** the three token tests called out as "remainder" in Bug 1's table
  (`test_steering_index_token_count_sync_preservation.py` x2 and `test_token_budget_optimization.py`
  x1) are owned by **Task 8 (BUG 2)**, not Task 7. The full suite reaches `0 failed` only after all
  three fix lanes (Tasks 7, 8, 9) complete, which Task 11 verifies.
- **Bug 1 is tests-only.** No steering `.md` file is modified for BUG 1. If a fix appears to require
  editing a steering file, that signals a genuine content regression (not test drift) and must be
  raised separately rather than silently changed.
- **Exit-code re-scope (BUG 3).** The audit's "exits 0 on error" claim (clauses 1.14 / 2.14) does
  not reproduce on HEAD — `run_all_checks` already returns exit 1 when any ERROR exists. Task 9.3
  adds a regression guard pinning "error_count > 0 ⇒ exit_code != 0"; the only current ERROR is
  resolved via reclassification in Task 9.2.
- **Stdlib-only constraint.** `measure_steering.py` and `lint_steering.py` remain stdlib-only; the
  new aggregate check and union registry parsing reuse the existing minimal-regex approach. PyYAML
  stays confined to `validate_dependencies.py`.
- **Property hover labels.** Tasks 1–3 use `Property N: Bug Condition`; Tasks 4–6 and the `.6`/`.5`
  verification sub-tasks use `Property N: Preservation`; the `.5`/`.4` verification sub-tasks use
  `Property N: Expected Behavior`. These match the design's Correctness Properties 1–6.
