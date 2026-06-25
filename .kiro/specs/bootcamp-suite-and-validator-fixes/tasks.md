# Implementation Plan

## Overview

This plan fixes the "broken or incomplete" defects in the `senzing-bootcamp` Kiro Power that the
prior `bootcamp-consistency-fixes` spec missed or deferred. The work is split into **eight
independent lanes** — `A1`, `A2`, `A3`, `A4`, `A5`, `B`, `C`, `D` — that touch disjoint files and can
be driven through their own exploration → fix → preservation cycle in parallel.

It follows the exploratory bugfix methodology, exactly as the prior `bootcamp-consistency-fixes`
`tasks.md` did:

- **Phase A — bug-condition exploration tests** are written/run FIRST on the **UNFIXED** tree. They
  FAIL (or reproduce the defect) and thereby confirm each bug exists. Do NOT fix anything in Phase A.
- **Phase B — preservation baselines** are captured on the **UNFIXED** tree. They PASS, recording the
  behavior each fix must keep byte/behavior-identical.
- **Phase C — fixes**, one independent lane per top-level task, each with verify-bug + verify-
  preservation sub-tasks that re-run the SAME tests from Phases A and B.
- **Phase D — convergence gate**, the single point where all eight lanes must hold simultaneously.

Property labels map to the design's numbered Correctness Properties (1–17) so hover status works:

| Lane | Fix side | Bug-Condition property | Preservation property | Requirements (Bug / Expected / Unchanged) |
|---|---|---|---|---|
| **A1** — boolean-like string coercion | **product code** (`scripts/preferences_utils.py`) | Property 1 | Property 2 | 1.1 / 5.1 / 9.1 |
| **A2** — degenerate "." path segment | **test** (`tests/test_assess_entry_point.py`) | Property 3 | Property 4 | 1.2 / 5.2 / 9.2 |
| **A3** — chronological ordering round-trip | **test** (`tests/test_generate_recap_pdf.py`) | Property 5 | Property 6 | 1.3 / 5.3 / 9.3 |
| **A4** — self-falsifying tolerance test | **test** (`tests/test_token_budget_optimization.py`) | Property 7 | Property 8 | 1.4 / 5.4 / 9.4 |
| **A5** — flaky Hypothesis deadline | **test** (`tests/test_track_reorganization.py`) | Property 9 | Property 10 | 1.5 / 5.5 / 9.5 |
| **B** — vacuous mandatory-gate validator | **product code + new test** (`scripts/validate_mandatory_gates.py`) | Property 11 | Property 12 | 2.1–2.3 / 6.1–6.3 / 10.1–10.3 |
| **C** — CHANGELOG out of sync | **docs** (`CHANGELOG.md`) | Property 13 | Property 14 | 3.1 / 7.1 / 11.1, 11.2 |
| **D** — spurious 3->4 keyword warning | **config** (`config/module-dependencies.yaml`) | Property 15 | Property 16 | 4.1 / 8.1 / 12.1, 12.2 |
| **Convergence** | whole suite + validators | — | Property 17 | 9.6, 13.1, 13.2, 13.3 |

**Environment:** Python 3.12.3, `pytest` 9.0.3, Hypothesis 6.152.3, stdlib-only scripts (PyYAML only
in `validate_dependencies.py`). **CI invokes `python`, but the local dev environment only has
`python3` — use `python3` in every command below.** Run the suite as
`python3 -m pytest senzing-bootcamp/tests/ tests/`.

**Cross-cutting rule (observation-first regeneration):** every "expected set", baseline, or snapshot
is produced by *observing the actual current behavior/corpus first* (run the code/parser, capture
output), then encoding that observation as the assertion — never by hand-guessing values. This
governs B's expected-gate set and any A3/A4/preservation baseline.

**Lane independence:** no two lanes edit the same file. `module-dependencies.yaml` is *read* by A5's
structural tests and *edited* (one gate string) by D, but the edit does not touch structure/keys/
module lists, so A5 and D remain independent.

## Tasks

### Phase A — Bug-condition exploration tests (run on UNFIXED tree — expected to FAIL / reproduce)

- [x] 1. Confirm A1 (boolean-like string coercion) with a bug-condition exploration test
  - **Property 1: Bug Condition** - A1 Boolean-String Round-Trip Fidelity
  - **IMPORTANT**: Write/run this property-based test BEFORE editing `scripts/preferences_utils.py`.
    It encodes the expected behavior and will validate the fix once it passes after implementation.
  - **DO NOT attempt to fix the codec or the test when it fails here.**
  - **GOAL**: Surface counterexamples proving a string whose lowercased form is `true`/`false` but
    whose casing is non-canonical (e.g. `'FalSe'`, `'TRUE'`, `'False'`) is silently coerced to a
    Python `bool` on a `write_preference` -> `load_preferences` round-trip.
  - **Scoped PBT Approach**: write a Hypothesis property `read(write(X)) == X and type(read(write(X)))
    is str` for strings drawn from boolean-looking tokens of any case; the existing
    `test_session_persistence_properties.py::TestPropertyFieldPreservation::test_writing_one_field_preserves_others`
    already fails deterministically on `pacing_overrides={'0': 'FalSe'}` — scope to that concrete case
    for reproducibility.
  - Confirm the empirically-observed root cause (HEAD `56b91b4`): `_serialize_yaml_value('FalSe') ->
    'FalSe'` (bare, unquoted) and `_parse_scalar('FalSe') -> False` (bool) — the write/read sides
    disagree.
  - Run on UNFIXED code: `python3 -m pytest senzing-bootcamp/tests/test_session_persistence_properties.py -q`
  - **EXPECTED OUTCOME**: FAILS with `Field 'pacing_overrides' was modified: expected {'0': 'FalSe'},
    got {'0': False}` (this is correct — it proves the bug exists).
  - Document the counterexample(s) (`'FalSe'` -> `False`, `'TRUE'` -> `True`, `'False'` -> `False`).
  - Mark complete when the property test is written, run, and the failure is documented.
  - _Bug_Condition: isBugCondition(X) = type(X) is str AND lower(X) in {"true","false"} AND X not in {"true","false"}_
  - _Expected_Behavior: read(write(X)) == X AND type(read(write(X))) is str_
  - _Requirements: 1.1_

- [x] 2. Confirm A2 (degenerate "." path segment) with a bug-condition exploration test
  - **Property 3: Bug Condition** - A2 Test Accepts Correct Degenerate Path Semantics
  - **IMPORTANT**: Run/observe this BEFORE changing `tests/test_assess_entry_point.py`.
  - **DO NOT attempt to fix the test or `assess_entry_point.py` when it fails here.**
  - **GOAL**: Show the test's `list(result.parts) == segments` expectation is wrong for the degenerate
    segment list `['.']`, where `_normalize_path('.')` correctly yields a `Path` whose `.parts == ()`.
  - **Scoped PBT Approach**: A2 is deterministic — scope to the concrete failing draw `segments ==
    ['.']`. Confirm `_normalize_path('.')` returns `Path('.')` with empty `.parts` (correct path
    semantics: `project_dir / Path('.') == project_dir`).
  - Run on UNFIXED code: `python3 -m pytest "senzing-bootcamp/tests/test_assess_entry_point.py::TestPathSeparatorNormalization::test_result_is_valid_path" -q`
  - **EXPECTED OUTCOME**: FAILS with `Path parts [] != segments ['.']` (this is correct — it proves
    the test's expectation, not `_normalize_path`, is wrong).
  - Document the counterexample: `segments == ['.']` -> `.parts == ()` but the test demands `['.']`.
  - Mark complete when the failure is reproduced and documented.
  - _Bug_Condition: isBugCondition(segments) = _normalize_path(join(segments)).parts == () AND segments != list(parts)_
  - _Expected_Behavior: fixed test accepts the _normalize_path result for the degenerate collapse_
  - _Requirements: 1.2_

- [x] 3. Confirm A3 (chronological ordering round-trip) with a bug-condition exploration test
  - **Property 5: Bug Condition** - A3 Strategy Emits Genuinely Sorted Timestamps
  - **IMPORTANT**: Run/observe this BEFORE changing `tests/test_generate_recap_pdf.py`.
  - **DO NOT attempt to fix the strategy or `generate_recap_pdf.py` when it fails here.**
  - **GOAL**: Show `st_sorted_timestamps`/`st_chronological_sections` emit timestamps that are NOT
    actually non-decreasing (it sorts at minute granularity then draws `second` independently after
    sorting, and clamps month/day), so the `format -> parse` round-trip — which faithfully preserves
    document order — fails the non-decreasing assertion.
  - **Scoped PBT Approach**: the failure is strategy-driven; run the property test and capture a
    one-second-apart counterexample.
  - Run on UNFIXED code: `python3 -m pytest "senzing-bootcamp/tests/test_generate_recap_pdf.py::TestModuleOrdering::test_sections_preserve_chronological_order" -q`
  - **EXPECTED OUTCOME**: FAILS on a counterexample such as `'2026-08-28T00:00:01'` appearing before
    `'2026-08-28T00:00:00'` (this is correct — it proves the strategy's claimed invariant is broken).
  - Document the counterexample (two sections whose generated seconds break monotonicity).
  - Mark complete when the failure is reproduced and documented.
  - _Bug_Condition: isBugCondition(sections) = NOT is_non_decreasing([s.timestamp for s in sections])_
  - _Expected_Behavior: timestamps non-decreasing AND parse(format(sections)) preserves input order_
  - _Requirements: 1.3_

- [x] 4. Confirm A4 (self-falsifying tolerance test) with a bug-condition exploration test
  - **Property 7: Bug Condition** - A4 Generated `stored` Within Asserted Tolerance
  - **IMPORTANT**: Run/observe this BEFORE changing `tests/test_token_budget_optimization.py`.
  - **DO NOT attempt to fix the test or `measure_steering.py` when it fails here.**
  - **GOAL**: Show the test generates `stored = round(measured * (1 + tolerance_factor))` (factor up
    to `0.09`) then asserts `deviation <= 0.10`, so for small `measured` the rounding pushes the
    absolute difference to `2` (deviation > 10%), while the small-count allowance only forgives an
    absolute difference of `1` — the test self-falsifies on a value it generated.
  - **Scoped PBT Approach**: deterministic — scope to the concrete failing draw `content_length=70`
    (`measured=18`, `tolerance_factor=0.0859`, `stored=round(18*1.0859)=20`, `deviation=2/18=11.11%`).
  - Run on UNFIXED code: `python3 -m pytest "senzing-bootcamp/tests/test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_stored_token_count_within_tolerance_of_measured" -q`
  - **EXPECTED OUTCOME**: FAILS on the self-generated `content_length=70` case (this is correct — it
    proves the test's generation/threshold logic is mutually inconsistent).
  - Document the counterexample: `measured=18, stored=20, abs=2, deviation=11.11% > 10%`.
  - Mark complete when the failure is reproduced and documented.
  - _Bug_Condition: isBugCondition(measured, factor) = measured>0 AND deviation(round(measured*(1+factor)), measured) > 0.10 AND NOT(measured<50 AND abs(stored-measured)<=1)_
  - _Expected_Behavior: generated stored satisfies abs(stored-measured)/measured <= 0.10 by construction_
  - _Requirements: 1.4_

- [x] 5. Confirm A5 (flaky Hypothesis deadline) with a bug-condition exploration observation
  - **Property 9: Bug Condition** - A5 Deterministic, No DeadlineExceeded
  - **IMPORTANT**: Run/observe this BEFORE changing `tests/test_track_reorganization.py`.
  - **DO NOT attempt to fix the test when it reproduces here.**
  - **GOAL**: Show `TestProperty1NoLegacyIdentifiersInFiles::test_no_legacy_id_in_bootcamp_files`
    runs the full-corpus `os.walk` + per-file `read_text` over five directories INSIDE the
    per-example body, so the repeated I/O exceeds Hypothesis's default 200 ms deadline (~284 ms
    observed) and raises `DeadlineExceeded` intermittently.
  - **Scoped PBT Approach**: flaky timing — reproduce by running the class repeatedly and watching for
    `DeadlineExceeded`, e.g. loop:
    `python3 -m pytest "senzing-bootcamp/tests/test_track_reorganization.py::TestProperty1NoLegacyIdentifiersInFiles" -q`
  - **EXPECTED OUTCOME**: intermittent `hypothesis.errors.DeadlineExceeded` (e.g. `Test took 284.63ms,
    which exceeds the deadline of 200.00ms`) — confirms a timing artifact, NOT a product defect.
  - Document the observed per-example wall time and the failure message.
  - Mark complete when the flaky failure mode is observed and documented.
  - _Bug_Condition: isBugCondition(run) = per_example_wall_time(run) > hypothesis_deadline (default 200 ms)_
  - _Expected_Behavior: fixed test completes without DeadlineExceeded across repeated runs_
  - _Requirements: 1.5_

- [x] 6. Confirm B (vacuous mandatory-gate validator) with a bug-condition exploration test
  - **Property 11: Bug Condition** - B Non-Vacuous Gate Parsing
  - **IMPORTANT**: Write the NEW regression test `tests/test_mandatory_gates_parser_regression.py`
    that calls the validator's OWN `parse_mandatory_gates` BEFORE editing
    `scripts/validate_mandatory_gates.py`. It encodes the expected behavior and validates the fix.
  - **DO NOT attempt to fix the validator when the new test fails here.**
  - **GOAL**: Show `validate_mandatory_gates.py` finds ZERO gates against the shipped corpus and exits
    `0` vacuously, because `_parse_gates_from_file`'s `step_pattern` matches H3 `### Step N:` only,
    while shipped gates live under H2 `## Step N:` (`module-02-sdk-setup.md` Step 5; `module-03-phase2-
    visualization.md` Step 9 with the bold-blockquote `> ⛔ **MANDATORY GATE` form whose marker sits
    in a `## ⚠️ DO NOT SKIP` preamble ABOVE the `## Step 9:` heading).
  - **Observation-first**: the new test imports the validator via `sys.path` insert and calls its own
    `parse_mandatory_gates(real_steering_dir)` against `senzing-bootcamp/steering/`, asserting
    `len(gates) >= 2` and membership of Module 2 Step 5 + Module 3 Step 9 (assert membership + len,
    NOT a brittle exact snapshot).
  - Run on UNFIXED code: `python3 -m pytest senzing-bootcamp/tests/test_mandatory_gates_parser_regression.py -q`
    and `python3 senzing-bootcamp/scripts/validate_mandatory_gates.py`
  - **EXPECTED OUTCOME**: the new test FAILS (parser returns 0 gates); the validator prints
    `No mandatory gates found in steering files.` and exits `0` (this is correct — it proves the
    vacuous pass).
  - Document the counterexample: shipped Module 2 Step 5 + Module 3 Step 9 gates are invisible today.
  - Mark complete when the new test is written, run, and its failure (and the vacuous CLI pass) recorded.
  - _Bug_Condition: isBugCondition(corpus) = EXISTS gate under H2 "## Step N:" OR "> marker **MANDATORY GATE" NOT in parse_mandatory_gates(corpus)_
  - _Expected_Behavior: parse_mandatory_gates returns non-empty set including Module 2 Step 5 + Module 3 Step 9_
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 7. Confirm C (CHANGELOG out of sync) with a bug-condition exploration check
  - **Property 13: Bug Condition** - C CHANGELOG Documents Committed + New Work
  - **IMPORTANT**: Run/observe this BEFORE editing `CHANGELOG.md`.
  - **DO NOT attempt to fix the CHANGELOG when the check fails here.**
  - **GOAL**: Show `[Unreleased]` OMITS the four consistency-fix items already committed on this branch
    (commit `56b91b4`): the `lint_steering.py` union-registry-source fix, the `measure_steering.py`
    additive aggregate check (`parse_budget_total` + "Budget total mismatch"), the `steering-index.yaml`
    `budget.total_tokens` `169633 -> 169576` correction, and the 147-test onboarding-split re-target.
  - **Scoped PBT Approach**: deterministic — write/run a check (substring scan of the `[Unreleased]`
    block) asserting all four items appear; observe it fail on the unfixed CHANGELOG.
  - Run on UNFIXED tree: grep/scan the `[Unreleased]` section of `senzing-bootcamp/CHANGELOG.md`.
  - **EXPECTED OUTCOME**: the check FAILS — none of the four committed items appear under `[Unreleased]`
    (this is correct — it proves the CHANGELOG is out of sync).
  - Document which of the four items are missing.
  - Mark complete when the omission is observed and documented.
  - _Bug_Condition: isBugCondition(changelog) = [Unreleased] OMITS any of the 4 committed consistency-fix items_
  - _Expected_Behavior: [Unreleased] documents all 4 committed items + this spec's A/B/D fixes_
  - _Requirements: 3.1_

- [x] 8. Confirm D (spurious 3->4 keyword warning) with a bug-condition exploration check
  - **Property 15: Bug Condition** - D No Spurious 3->4 Warning; Genuine Mismatches Still Caught
  - **IMPORTANT**: Run/observe this BEFORE editing `config/module-dependencies.yaml`.
  - **DO NOT attempt to fix the config or `validate_prerequisites.py` when the check fails here.**
  - **GOAL**: Show `validate_prerequisites.py` emits `WARNING: Gate '3->4': keyword 'including the
    step 9 web service + visualization (cannot be skipped)' not found in module 3 steering content`,
    because `extract_keywords` comma-splits the `3->4` requirement into a fragment absent verbatim from
    module 3 content even though the requirement is in fact satisfied.
  - **Scoped PBT Approach**: deterministic — scope to the `3->4` gate; capture the warning line.
  - Run on UNFIXED tree: `python3 senzing-bootcamp/scripts/validate_prerequisites.py` and look for the
    `3->4` warning (e.g. pipe to `grep "3->4"`).
  - **EXPECTED OUTCOME**: the spurious `3->4` keyword-mismatch WARNING is present (this is correct —
    it proves the comma-split fragment is too specific to appear verbatim).
  - Document the exact warning string and capture the FULL set of findings as the D preservation
    baseline reference (so the fix can prove only this one warning is removed).
  - Mark complete when the spurious warning is reproduced and documented.
  - _Bug_Condition: isBugCondition(gate) = gate.key=="3->4" AND a comma-split keyword fragment absent verbatim from module 3 content AND requirement is in fact satisfied_
  - _Expected_Behavior: no spurious 3->4 warning; genuinely absent keywords still warn_
  - _Requirements: 4.1_

### Phase B — Preservation baselines (capture on UNFIXED tree — expected to PASS)

- [x] 9. Capture A1 preservation baseline (observation-first, on UNFIXED tree)
  - **Property 2: Preservation** - A1 Non-Buggy Scalars Round-Trip Unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe current round-trip behavior, then
    assert it. Write this as a property-based test (the input domain is large).
  - Observe and record on the UNFIXED tree the round-trip result AND Python type for non-bug-condition
    scalars: a genuine Python `bool` (e.g. `license_guidance_deferred: true`), an `int` (e.g. `18`),
    the canonical lowercase strings `'true'`/`'false'`, a plain string (e.g. `'python'`), and `None`.
  - Write a Hypothesis property asserting, for all such non-buggy scalars, `read(write(X)) == X` with
    identical Python type — this is the preservation companion to Property 1.
  - Confirm the `validate_preferences_schema` tests are unaffected on the unfixed tree.
  - Run on UNFIXED code: `python3 -m pytest senzing-bootcamp/tests/test_session_persistence_properties.py -q`
  - **EXPECTED OUTCOME**: these preservation observations hold on the UNFIXED tree (baseline confirmed).
  - _Preservation: genuine bool, int, 'true'/'false' str, plain str, None round-trip identically in value and type_
  - _Requirements: 9.1_

- [x] 10. Capture A2 preservation baseline (observation-first, on UNFIXED tree)
  - **Property 4: Preservation** - A2 Normal Paths Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the UNFIXED tree: `_normalize_path` returns the same platform-native `Path`
    for non-degenerate segment lists (e.g. `['data','raw']`, `['data','raw','file.csv']`,
    `'data/raw/'`, `'data\\raw\\'`), and the two sibling tests
    (`test_separator_style_produces_same_result`, `test_trailing_slashes_are_stripped`) pass.
  - Capture a byte-level baseline (SHA-256) of `senzing-bootcamp/scripts/assess_entry_point.py` so the
    fix can prove the source stays byte-identical (the fix is test-only).
  - Run on UNFIXED code: `python3 -m pytest senzing-bootcamp/tests/test_assess_entry_point.py -q`
  - **EXPECTED OUTCOME**: sibling separator/trailing-slash tests PASS; `assess_entry_point.py` digest recorded.
  - _Preservation: assess_entry_point.py byte-identical; all non-degenerate segment lists still pass_
  - _Requirements: 9.2_

- [x] 11. Capture A3 preservation baseline (observation-first, on UNFIXED tree)
  - **Property 6: Preservation** - A3 Recap Round-Trip Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the UNFIXED tree: every OTHER test in `test_generate_recap_pdf.py`
    (round-trip, structural completeness, Q&A pairing, append preservation, timestamp format) passes.
  - Capture a byte-level baseline (SHA-256) of `senzing-bootcamp/scripts/generate_recap_pdf.py` so the
    fix can prove `format_recap_document`/`parse_recap_markdown` source stays byte-identical (test-only fix).
  - Run on UNFIXED code: `python3 -m pytest senzing-bootcamp/tests/test_generate_recap_pdf.py -q`
    (note the one `test_sections_preserve_chronological_order` is the Task 3 bug-condition failure).
  - **EXPECTED OUTCOME**: all OTHER recap tests PASS; `generate_recap_pdf.py` digest recorded.
  - _Preservation: generate_recap_pdf.py byte-identical; all other recap tests pass_
  - _Requirements: 9.3_

- [x] 12. Capture A4 preservation baseline (observation-first, on UNFIXED tree)
  - **Property 8: Preservation** - A4 Production ±10% Check Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the UNFIXED tree: `measure_steering.py --check` per-file ±10% tolerance and
    the additive aggregate "Budget total mismatch" check pass against the real index; the concrete
    real-index companion tests (`test_actual_steering_files_token_counts_within_tolerance`,
    `test_actual_steering_index_total_tokens_equals_sum`) pass.
  - Capture a byte-level baseline (SHA-256) of `senzing-bootcamp/scripts/measure_steering.py` so the
    fix can prove the source stays byte-identical (test-only fix; production ±10% check MUST NOT be touched).
  - Run on UNFIXED tree: `python3 senzing-bootcamp/scripts/measure_steering.py --check`
  - **EXPECTED OUTCOME**: `--check` PASSES; concrete real-index tests pass; `measure_steering.py` digest recorded.
  - _Preservation: measure_steering.py ±10% per-file check + additive aggregate check byte-identical and passing_
  - _Requirements: 9.4_

- [x] 13. Capture A5 preservation baseline (observation-first, on UNFIXED tree)
  - **Property 10: Preservation** - A5 Detection Coverage Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the UNFIXED tree the detection coverage: the scan directory set (`config/`,
    `steering/`, `docs/`, `scripts/`, `tests/`), the `_EXCLUDED_FILES` exclusions
    (`scripts/validate_dependencies.py`, `tests/test_track_reorganization.py`), and the word-boundary
    regex that fail the test on any real legacy identifier.
  - Inject a temporary file containing a legacy identifier (e.g. `fast_track`) under a scanned dir and
    confirm the test FAILS (detection works) — then remove the temporary file. This pins the coverage
    the fix must preserve.
  - Run on UNFIXED code: `python3 -m pytest senzing-bootcamp/tests/test_track_reorganization.py -q`
  - **EXPECTED OUTCOME**: the class passes on a clean tree; the injected-identifier probe fails the test (coverage confirmed).
  - _Preservation: detection_coverage(F') == detection_coverage(F); scan dirs, exclusions, word-boundary regex unchanged_
  - _Requirements: 9.5_

- [x] 14. Capture B preservation baseline (observation-first, on UNFIXED tree)
  - **Property 12: Preservation** - B Gate-Free Files and Downstream Logic Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the UNFIXED tree:
    - a steering file with genuinely NO `MANDATORY GATE` marker (e.g. `module-06-data-processing.md`)
      yields zero gates from `_parse_gates_from_file` (synthetic single-file case yields `[]`).
    - the existing `test_mandatory_gate_preservation.py` (and related suites) pass.
  - Record that the downstream logic to keep UNCHANGED is: `_get_required_checkpoints` (Module 3 Step 9
    -> `["web_service","web_page"]`), `NON_SKIPPABLE_GATES = {"3.9"}`, `validate_progress`,
    `_check_gate`, `skipped_steps`, the module-number extraction (`module-(\d+)`), and CLI/exit-code flow.
  - Run on UNFIXED code: `python3 -m pytest senzing-bootcamp/tests/test_mandatory_gate_preservation.py -q`
  - **EXPECTED OUTCOME**: gate-free file -> `[]`; preservation suite PASSES (baseline confirmed).
  - _Preservation: no-gate file -> []; cross-reference / skipped_steps / NON_SKIPPABLE_GATES / exit-code logic unchanged_
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 15. Capture C preservation baseline (observation-first, on UNFIXED tree)
  - **Property 14: Preservation** - C Prior Entries Intact, CommonMark-Clean
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the UNFIXED tree: the current `[Unreleased]`, `[0.12.0]`, and `[0.11.0]`
    section contents of `senzing-bootcamp/CHANGELOG.md` (so the fix can prove the edit is additive and
    reverts nothing); `validate_commonmark.py` passes.
  - Run on UNFIXED tree: `python3 senzing-bootcamp/scripts/validate_commonmark.py`
  - **EXPECTED OUTCOME**: prior entries recorded; `validate_commonmark.py` PASSES (baseline confirmed).
  - _Preservation: [Unreleased]/[0.12.0]/[0.11.0] prior entries intact; validate_commonmark.py passes (additive only)_
  - _Requirements: 11.1, 11.2_

- [x] 16. Capture D preservation baseline (observation-first, on UNFIXED tree)
  - **Property 16: Preservation** - D Other Gates and Config Consumers Unchanged
  - **IMPORTANT**: Follow observation-first methodology.
  - Observe and record on the UNFIXED tree the FULL set of `validate_prerequisites.py` findings (so the
    fix can prove the finding set equals the baseline MINUS the one spurious `3->4` warning, with the
    exit code unchanged).
  - Confirm `validate_dependencies.py` (the PyYAML consumer) parses `module-dependencies.yaml`, and the
    `test_track_reorganization.py` structural tests that read `module-dependencies.yaml` pass — these
    must continue to parse/pass after D's reword (which does not touch structure/keys/module lists).
  - Run on UNFIXED tree: `python3 senzing-bootcamp/scripts/validate_prerequisites.py` and
    `python3 senzing-bootcamp/scripts/validate_dependencies.py`
  - **EXPECTED OUTCOME**: baseline finding set + exit code recorded; `validate_dependencies.py` and structural tests PASS.
  - _Preservation: all other gates' findings identical; module-dependencies.yaml consumers parse/pass; only the 3->4 warning is removed_
  - _Requirements: 12.1, 12.2_
### Phase C — Fixes (one independent lane per top-level task; each with verify-bug + verify-preservation sub-tasks)

- [x] 17. Fix A1 — boolean-like string coercion (product code, `scripts/preferences_utils.py`)

  - [x] 17.1 Implement the writer + reader alignment in `preferences_utils.py`
    - In `_serialize_yaml_value`: broaden the string-quoting guard so it quotes **any** string whose
      lowercased form is a YAML bool/null literal — i.e. quote when `value.lower() in {"true",
      "false", "null"}` (in addition to the existing `("true","false","null","~","")` exact tokens).
      The genuine-`bool` branch (`isinstance(value, bool)`) precedes the `str` branch and still emits
      bare canonical `true`/`false`, so it is unaffected.
    - In `_parse_scalar`: parse **only** the exact bare lowercase tokens `true`/`false` to `bool`
      (`value == "true"` / `value == "false"`); a quoted token (`"FalSe"`, `"true"`) falls through to
      the existing quote-stripping branch and returns the inner `str`. Keep `null`/`~`/empty -> `None`
      and the `int(value)` branch unchanged.
    - Constraint: stdlib-only; no new imports. Genuine Python `bool` MUST still round-trip as `bool`.
    - The agreement to hold after editing: `read(write(x)) == x and type(read(write(x))) == type(x)`
      for every scalar `x` in {genuine bool, any str, int, None}.
    - _Bug_Condition: isBugCondition(X) = type(X) is str AND lower(X) in {"true","false"} AND X not in {"true","false"}_
    - _Expected_Behavior: read(write(X)) == X AND type(read(write(X))) is str (expectedBehavior from design A1)_
    - _Preservation: genuine bool, int, 'true'/'false' str, plain str, None round-trip unchanged in value and type_
    - _Requirements: 5.1, 9.1_

  - [x] 17.2 Verify the Task 1 bug-condition test now PASSES
    - **Property 1: Expected Behavior** - A1 Boolean-String Round-Trip Fidelity
    - **IMPORTANT**: Re-run the SAME property-based test from Task 1 — do NOT write a new test. It
      encodes the expected behavior and now validates the fix.
    - Run: `python3 -m pytest senzing-bootcamp/tests/test_session_persistence_properties.py -q`
    - **EXPECTED OUTCOME**: PASSES (the `pacing_overrides={'0': 'FalSe'}` counterexample and the
      any-case boolean-looking-string property now round-trip as `str`, confirming the bug is fixed).
    - _Expected_Behavior: read(write(X)) == X AND type(read(write(X))) is str for all boolean-looking strings of any case_
    - _Requirements: 5.1_

  - [x] 17.3 Verify the Task 9 preservation property still holds
    - **Property 2: Preservation** - A1 Non-Buggy Scalars Round-Trip Unchanged
    - **IMPORTANT**: Re-run the SAME preservation property test from Task 9 — do NOT write a new test.
    - Confirm genuine Python `bool` (e.g. `license_guidance_deferred: true`), `int`, canonical
      lowercase `'true'`/`'false'` strings, plain strings, and `None` round-trip identically in value
      and type; `validate_preferences_schema` tests still pass.
    - Run: `python3 -m pytest senzing-bootcamp/tests/test_session_persistence_properties.py -q`
    - **EXPECTED OUTCOME**: PASSES (no regressions; genuine bool still round-trips as bool).
    - _Preservation: genuine bool/int/'true'/'false' str/plain str/None round-trip unchanged in value and type_
    - _Requirements: 9.1_

- [x] 18. Fix A2 — degenerate "." path segment (test-only, `tests/test_assess_entry_point.py`)

  - [x] 18.1 Fix the test expectation in `test_result_is_valid_path`
    - In `TestPathSeparatorNormalization::test_result_is_valid_path`, compare against expected segments
      normalized the same way `_normalize_path` collapses `.`/empty — preferred:
      `expected = [s for s in segments if s not in ('.', '')]` and assert `list(result.parts) == expected`.
    - Constraint: `assess_entry_point.py` MUST stay **byte-identical** (compare against the Task 10
      SHA-256). The two sibling tests (`test_separator_style_produces_same_result`,
      `test_trailing_slashes_are_stripped`) are unchanged.
    - _Bug_Condition: isBugCondition(segments) = _normalize_path(join(segments)).parts == () AND segments != list(parts)_
    - _Expected_Behavior: fixed test accepts the _normalize_path result by normalizing expected segments (drop '.'/'')_
    - _Preservation: assess_entry_point.py byte-identical (Task 10 SHA-256); all non-degenerate segment lists still pass_
    - _Requirements: 5.2, 9.2_

  - [x] 18.2 Verify the Task 2 test PASSES
    - **Property 3: Expected Behavior** - A2 Test Accepts Correct Degenerate Path Semantics
    - **IMPORTANT**: Re-run the SAME test from Task 2 — do NOT write a new test.
    - Run: `python3 -m pytest "senzing-bootcamp/tests/test_assess_entry_point.py::TestPathSeparatorNormalization::test_result_is_valid_path" -q`
    - **EXPECTED OUTCOME**: PASSES (the `segments == ['.']` degenerate draw is now accepted because the
      expected segments are normalized the same way `_normalize_path` collapses them).
    - _Expected_Behavior: fixed test accepts the _normalize_path result for the degenerate collapse_
    - _Requirements: 5.2_

  - [x] 18.3 Verify sibling tests still pass AND `assess_entry_point.py` digest unchanged
    - **Property 4: Preservation** - A2 Normal Paths Unchanged
    - **IMPORTANT**: Re-run the SAME preservation baseline from Task 10 — do NOT write a new test.
    - Run: `python3 -m pytest senzing-bootcamp/tests/test_assess_entry_point.py -q`
    - Recompute the SHA-256 of `senzing-bootcamp/scripts/assess_entry_point.py` and confirm it equals
      the Task 10 baseline digest (empty source diff — the fix is test-only).
    - **EXPECTED OUTCOME**: sibling separator/trailing-slash tests PASS; `assess_entry_point.py` digest unchanged.
    - _Preservation: assess_entry_point.py byte-identical; all non-degenerate segment lists still pass_
    - _Requirements: 9.2_

- [x] 19. Fix A3 — chronological ordering round-trip (test-only, `tests/test_generate_recap_pdf.py`)

  - [x] 19.1 Fix the `st_sorted_timestamps`/`st_chronological_sections` strategy
    - Make the strategy emit **genuinely** non-decreasing timestamps — preferred: generate unique
      epoch-seconds, sort them, and map each to a `YYYY-MM-DDTHH:MM:SS` string with a single fixed
      timezone suffix so lexicographic order equals chronological order. Remove the independent
      post-sort `second` draw entirely. Use day range 1–28 and month 1–12 to avoid invalid dates.
    - Constraint: `generate_recap_pdf.py` MUST stay **byte-identical** (Task 11 SHA-256). Per the
      observation-first regeneration rule, do not hand-pin any expected timestamp list — let the
      corrected strategy generate them and assert monotonicity.
    - _Bug_Condition: isBugCondition(sections) = NOT is_non_decreasing([s.timestamp for s in sections])_
    - _Expected_Behavior: strategy timestamps non-decreasing AND parse(format(sections)) preserves input order_
    - _Preservation: generate_recap_pdf.py byte-identical (Task 11 SHA-256); all other recap tests pass_
    - _Requirements: 5.3, 9.3_

  - [x] 19.2 Verify the Task 3 test PASSES
    - **Property 5: Expected Behavior** - A3 Strategy Emits Genuinely Sorted Timestamps
    - **IMPORTANT**: Re-run the SAME test from Task 3 — do NOT write a new test.
    - Run: `python3 -m pytest "senzing-bootcamp/tests/test_generate_recap_pdf.py::TestModuleOrdering::test_sections_preserve_chronological_order" -q`
    - **EXPECTED OUTCOME**: PASSES (the strategy now emits genuinely non-decreasing timestamps, so the
      `format -> parse` round-trip preserves chronological order for all generated inputs).
    - _Expected_Behavior: timestamps non-decreasing AND parse(format(sections)) preserves input order_
    - _Requirements: 5.3_

  - [x] 19.3 Verify all other recap tests pass AND `generate_recap_pdf.py` digest unchanged
    - **Property 6: Preservation** - A3 Recap Round-Trip Unchanged
    - **IMPORTANT**: Re-run the SAME preservation baseline from Task 11 — do NOT write a new test.
    - Run: `python3 -m pytest senzing-bootcamp/tests/test_generate_recap_pdf.py -q`
    - Recompute the SHA-256 of `senzing-bootcamp/scripts/generate_recap_pdf.py` and confirm it equals
      the Task 11 baseline digest (`format_recap_document`/`parse_recap_markdown` source unchanged).
    - **EXPECTED OUTCOME**: all other recap tests (round-trip, structural completeness, Q&A pairing,
      append preservation, timestamp format) PASS; `generate_recap_pdf.py` digest unchanged.
    - _Preservation: generate_recap_pdf.py byte-identical; all other recap tests pass_
    - _Requirements: 9.3_

- [x] 20. Fix A4 — self-falsifying tolerance test (test-only, `tests/test_token_budget_optimization.py`)

  - [x] 20.1 Fix the test generation/assertion in `test_stored_token_count_within_tolerance_of_measured`
    - Generate `stored` provably within ±10% — preferred: draw `stored` from the closed integer
      interval `[ceil(measured * 0.90), floor(measured * 1.10)]` (non-empty for `measured >= 1` since
      `lo <= measured <= hi`), then assert `abs(stored - measured) / measured <= 0.10` with no
      special-case allowance branch needed. Generation and assertion become mutually consistent.
    - Constraint: `measure_steering.py` MUST stay **byte-identical** (Task 12 SHA-256) and its
      production ±10% per-file check MUST NOT be weakened. The concrete real-index companion tests
      (`test_actual_steering_files_token_counts_within_tolerance`,
      `test_actual_steering_index_total_tokens_equals_sum`) are NOT changed.
    - _Bug_Condition: isBugCondition(measured, factor) = measured>0 AND deviation(round(measured*(1+factor)), measured) > 0.10 AND NOT(measured<50 AND abs(stored-measured)<=1)_
    - _Expected_Behavior: stored drawn in [ceil(measured*0.90), floor(measured*1.10)] so abs(stored-measured)/measured <= 0.10 by construction_
    - _Preservation: measure_steering.py byte-identical (Task 12 SHA-256); ±10% per-file check + additive aggregate check unchanged_
    - _Requirements: 5.4, 9.4_

  - [x] 20.2 Verify the Task 4 test PASSES
    - **Property 7: Expected Behavior** - A4 Generated `stored` Within Asserted Tolerance
    - **IMPORTANT**: Re-run the SAME test from Task 4 — do NOT write a new test.
    - Run: `python3 -m pytest "senzing-bootcamp/tests/test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_stored_token_count_within_tolerance_of_measured" -q`
    - **EXPECTED OUTCOME**: PASSES (the previously self-falsifying `content_length=70` case can no
      longer be generated — `stored` is now bounded within ±10% by construction).
    - _Expected_Behavior: generated stored satisfies abs(stored-measured)/measured <= 0.10 by construction_
    - _Requirements: 5.4_

  - [x] 20.3 Verify `measure_steering.py --check` still passes AND digest unchanged
    - **Property 8: Preservation** - A4 Production ±10% Check Unchanged
    - **IMPORTANT**: Re-run the SAME preservation baseline from Task 12 — do NOT write a new test.
    - Run: `python3 senzing-bootcamp/scripts/measure_steering.py --check` and
      `python3 -m pytest senzing-bootcamp/tests/test_token_budget_optimization.py -q`.
    - Recompute the SHA-256 of `senzing-bootcamp/scripts/measure_steering.py` and confirm it equals the
      Task 12 baseline digest (production ±10% check and additive "Budget total mismatch" check untouched).
    - **EXPECTED OUTCOME**: `--check` PASSES; the concrete real-index companion tests PASS;
      `measure_steering.py` digest unchanged.
    - _Preservation: measure_steering.py ±10% per-file check + additive aggregate check byte-identical and passing_
    - _Requirements: 9.4_

- [x] 21. Fix A5 — flaky Hypothesis deadline (test-only, `tests/test_track_reorganization.py`)

  - [x] 21.1 Implement deadline relaxation + corpus-read hoist in `test_no_legacy_id_in_bootcamp_files`
    - Add `@settings(deadline=None)` to `test_no_legacy_id_in_bootcamp_files`.
    - Hoist the corpus reads (the five scan dirs `config/`, `steering/`, `docs/`, `scripts/`, `tests/`)
      to module/class scope — build a cached list of `(rel_path, content)` once — so the per-example
      body only runs the word-boundary regex (`re.compile(rf"\b{legacy_id}\b").search(content)`) over
      the cached contents instead of re-walking and re-reading the filesystem per example.
    - Constraint: keep the scan directory set, the `_EXCLUDED_FILES` exclusions
      (`scripts/validate_dependencies.py`, `tests/test_track_reorganization.py`), and the
      word-boundary regex IDENTICAL so detection coverage is unchanged.
    - _Bug_Condition: isBugCondition(run) = per_example_wall_time(run) > hypothesis_deadline (default 200 ms)_
    - _Expected_Behavior: test completes without DeadlineExceeded across repeated runs (deadline=None + hoisted reads)_
    - _Preservation: detection coverage unchanged; scan dirs, _EXCLUDED_FILES, word-boundary regex identical_
    - _Requirements: 5.5, 9.5_

  - [x] 21.2 Verify determinism — run the class ~10x with no `DeadlineExceeded`
    - **Property 9: Expected Behavior** - A5 Deterministic, No DeadlineExceeded
    - **IMPORTANT**: Re-run the SAME test from Task 5 — do NOT write a new test.
    - Run the class ~10 consecutive times:
      `python3 -m pytest "senzing-bootcamp/tests/test_track_reorganization.py::TestProperty1NoLegacyIdentifiersInFiles" -q`
    - **EXPECTED OUTCOME**: all ~10 runs PASS with no `hypothesis.errors.DeadlineExceeded` (the timing
      artifact is eliminated; the test is deterministic).
    - _Expected_Behavior: fixed test completes without DeadlineExceeded across repeated runs_
    - _Requirements: 5.5_

  - [x] 21.3 Verify the Task 13 injected-identifier probe still fails the test (coverage preserved)
    - **Property 10: Preservation** - A5 Detection Coverage Unchanged
    - **IMPORTANT**: Re-run the SAME preservation probe from Task 13 — do NOT write a new test.
    - Inject a temporary file containing a legacy identifier (e.g. `fast_track`) under a scanned dir,
      confirm the test FAILS (detection still works against the hoisted cached contents), then remove
      the temporary file.
    - Run: `python3 -m pytest senzing-bootcamp/tests/test_track_reorganization.py -q`
    - **EXPECTED OUTCOME**: clean tree PASSES; injected-identifier probe still fails the test
      (`detection_coverage(F') == detection_coverage(F)`).
    - _Preservation: detection coverage unchanged; scan dirs, exclusions, word-boundary regex identical_
    - _Requirements: 9.5_

- [x] 22. Fix B — vacuous mandatory-gate validator (product code + new test, `scripts/validate_mandatory_gates.py`)

  - [x] 22.1 Implement the parser changes in `_parse_gates_from_file`
    - (a) Broaden `step_pattern` to `re.compile(r"^#{2,3}\s+Step\s+(\d+):", re.MULTILINE)` so shipped
      H2 `## Step 5:`/`## Step 9:` headings (and any H3) are visible.
    - (b) Tolerate the bold-blockquote marker via `re.search(r"⛔\s*\**\s*MANDATORY\s*GATE", section)`
      so both `⛔ MANDATORY GATE` and `> ⛔ **MANDATORY GATE` are detected.
    - (c) **IMPORTANT** — the Module 3 `⛔` marker sits in a `## ⚠️ DO NOT SKIP` preamble ABOVE
      `## Step 9:`. Implement preamble→step association: when computing a step's `section`, extend its
      start backwards to include an immediately-preceding non-`Step`/non-`Phase` `## ` preamble block,
      so the Step 9 gate marker in the `## ⚠️ DO NOT SKIP` block is attributed to `## Step 9:`. Keep
      the existing "section ends at next Step/Phase" end logic.
    - (d) Keep UNCHANGED: `_get_required_checkpoints` (Module 3 Step 9 -> `["web_service","web_page"]`),
      `NON_SKIPPABLE_GATES = {"3.9"}`, `validate_progress`, `_check_gate`, `skipped_steps`, the
      module-number extraction (`module-(\d+)`), and the CLI/exit-code flow.
    - Constraint: stdlib-only; no new imports.
    - _Bug_Condition: isBugCondition(corpus) = EXISTS gate under H2 "## Step N:" OR "> ⛔ **MANDATORY GATE" form NOT in parse_mandatory_gates(corpus)_
    - _Expected_Behavior: parse_mandatory_gates returns non-empty set including Module 2 Step 5 + Module 3 Step 9_
    - _Preservation: no-gate file -> []; _get_required_checkpoints / NON_SKIPPABLE_GATES={"3.9"} / validate_progress / _check_gate / skipped_steps / module-number extraction / exit-code flow unchanged_
    - _Requirements: 6.1, 6.2, 6.3, 10.1, 10.2, 10.3_

  - [x] 22.2 Verify the Task 6 NEW regression test PASSES and the validator is non-vacuous
    - **Property 11: Expected Behavior** - B Non-Vacuous Gate Parsing
    - **IMPORTANT**: Re-run the SAME new test from Task 6
      (`tests/test_mandatory_gates_parser_regression.py`) — do NOT write a new test. It calls the
      validator's own `parse_mandatory_gates(real_steering_dir)`.
    - Run: `python3 -m pytest senzing-bootcamp/tests/test_mandatory_gates_parser_regression.py -q`
      and `python3 senzing-bootcamp/scripts/validate_mandatory_gates.py`.
    - **EXPECTED OUTCOME**: the regression test PASSES (`parse_mandatory_gates` returns `>= 2` gates
      including Module 2 Step 5 + Module 3 Step 9); the validator CLI no longer prints
      `No mandatory gates found` — it is now NON-VACUOUS.
    - _Expected_Behavior: parse_mandatory_gates returns non-empty set including Module 2 Step 5 + Module 3 Step 9_
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 22.3 Verify Task 14 preservation (gate-free file -> []; downstream logic unchanged)
    - **Property 12: Preservation** - B Gate-Free Files and Downstream Logic Unchanged
    - **IMPORTANT**: Re-run the SAME preservation baseline from Task 14 — do NOT write a new test.
    - Confirm a synthetic single file with NO `MANDATORY GATE` marker yields `[]`; the per-gate
      cross-reference, `skipped_steps`, `NON_SKIPPABLE_GATES`, and exit-code logic are unchanged.
    - Run: `python3 -m pytest senzing-bootcamp/tests/test_mandatory_gate_preservation.py -q` (and
      related gate suites).
    - **EXPECTED OUTCOME**: gate-free file -> `[]`; `test_mandatory_gate_preservation.py` and related
      suites still PASS (no regressions).
    - _Preservation: no-gate file -> []; cross-reference / skipped_steps / NON_SKIPPABLE_GATES / exit-code logic unchanged_
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 23. Fix C — CHANGELOG out of sync (docs, `CHANGELOG.md` `[Unreleased]`)

  - [x] 23.1 Add the `[Unreleased]` bullets (additive only)
    - Under the existing `[Unreleased]` subsections (creating `### Changed`/`### Fixed` only if needed),
      additively add bullets for the four committed consistency-fix items: (1) `lint_steering.py`
      union-registry-source fix; (2) `measure_steering.py` additive aggregate check (`parse_budget_total`
      + "Budget total mismatch"); (3) `steering-index.yaml` `budget.total_tokens` `169633 -> 169576`
      correction; (4) the 147-test onboarding-split re-target.
    - PLUS this spec's fixes: A1 boolean-string round-trip fidelity in `preferences_utils.py`; B
      non-vacuous mandatory-gate parsing (H2/H3 + blockquote + preamble) plus new regression test; D
      removal of the spurious `3->4` prerequisites keyword warning; and A2–A5 summarized as a single
      "stabilized property tests" bullet.
    - Constraint: keep the markdown CommonMark-clean; reuse the existing bullet style; do not reorder
      or remove any prior entry.
    - _Bug_Condition: isBugCondition(changelog) = [Unreleased] OMITS any of the 4 committed consistency-fix items_
    - _Expected_Behavior: [Unreleased] documents all 4 committed items + this spec's A1/B/D fixes (A2–A5 summarized)_
    - _Preservation: [Unreleased]/[0.12.0]/[0.11.0] prior entries intact; validate_commonmark.py passes (additive only)_
    - _Requirements: 7.1, 11.1, 11.2_

  - [x] 23.2 Verify the Task 7 check PASSES (all four items present)
    - **Property 13: Expected Behavior** - C CHANGELOG Documents Committed + New Work
    - **IMPORTANT**: Re-run the SAME substring-scan check from Task 7 — do NOT write a new check.
    - Re-run the `[Unreleased]` substring scan and confirm all four committed items (lint_steering
      union fix, measure_steering additive aggregate check, `total_tokens` 169633 -> 169576, 147-test
      onboarding-split re-target) AND this spec's A/B/D fixes appear.
    - **EXPECTED OUTCOME**: the check PASSES (all four committed items + this spec's fixes present).
    - _Expected_Behavior: [Unreleased] documents all 4 committed items + this spec's A/B/D fixes_
    - _Requirements: 7.1_

  - [x] 23.3 Verify Task 15 preservation (prior entries intact; CommonMark passes)
    - **Property 14: Preservation** - C Prior Entries Intact, CommonMark-Clean
    - **IMPORTANT**: Re-run the SAME preservation baseline from Task 15 — do NOT write a new check.
    - Confirm the prior `[Unreleased]`, `[0.12.0]`, and `[0.11.0]` entries are present and unchanged
      (additive diff only, no reverts).
    - Run: `python3 senzing-bootcamp/scripts/validate_commonmark.py`
    - **EXPECTED OUTCOME**: prior entries intact; `validate_commonmark.py` PASSES.
    - _Preservation: [Unreleased]/[0.12.0]/[0.11.0] prior entries intact; validate_commonmark.py passes_
    - _Requirements: 11.1, 11.2_

- [x] 24. Fix D — spurious 3->4 keyword warning (config, `config/module-dependencies.yaml`)

  - [x] 24.1 Reword the `3->4` gate requirement string
    - In `config/module-dependencies.yaml`, gate `"3->4"`, reword the `requires` string to the
      validated candidate `"System verification passed, web service + visualization, Step 9"` so each
      comma-split keyword (`system verification passed`, `web service + visualization`, `step 9`)
      appears verbatim in the concatenated module 3 steering content.
    - Constraint: do NOT touch YAML structure, keys, module lists, or the track registry — only the
      one requirement string changes.
    - _Bug_Condition: isBugCondition(gate) = gate.key=="3->4" AND a comma-split keyword fragment absent verbatim from module 3 content AND requirement is in fact satisfied_
    - _Expected_Behavior: reworded requires -> each comma-split keyword verbatim in module 3; no spurious warning; genuinely absent keyword still warns_
    - _Preservation: finding set == baseline minus the one warning; exit code unchanged; YAML structure/keys/module lists untouched; validate_dependencies.py + structural tests pass_
    - _Requirements: 8.1, 12.1, 12.2_

  - [x] 24.2 Verify the Task 8 check PASSES (no spurious 3->4 warning; bogus keyword still warns)
    - **Property 15: Expected Behavior** - D No Spurious 3->4 Warning; Genuine Mismatches Still Caught
    - **IMPORTANT**: Re-run the SAME check from Task 8 — do NOT write a new check.
    - Run: `python3 senzing-bootcamp/scripts/validate_prerequisites.py` and confirm the `3->4`
      keyword-mismatch WARNING is absent. Then inject a deliberately bogus keyword into a gate's
      `requires` and confirm a WARNING is still emitted (proving `extract_keywords` still catches
      genuine mismatches), then revert the injection.
    - **EXPECTED OUTCOME**: no spurious `3->4` warning; a deliberately bogus injected keyword still warns.
    - _Expected_Behavior: no spurious 3->4 warning; genuinely absent keywords still warn_
    - _Requirements: 8.1_

  - [x] 24.3 Verify Task 16 preservation (finding set == baseline minus the one warning)
    - **Property 16: Preservation** - D Other Gates and Config Consumers Unchanged
    - **IMPORTANT**: Re-run the SAME preservation baseline from Task 16 — do NOT write a new check.
    - Confirm the full `validate_prerequisites.py` finding set equals the Task 16 baseline MINUS the
      one spurious `3->4` warning, with the exit code unchanged.
    - Run: `python3 senzing-bootcamp/scripts/validate_dependencies.py` and
      `python3 -m pytest senzing-bootcamp/tests/test_track_reorganization.py -q` (structural tests).
    - **EXPECTED OUTCOME**: finding set == baseline minus the one warning; exit code unchanged;
      `validate_dependencies.py` and the `test_track_reorganization.py` structural tests PASS.
    - _Preservation: all other gates' findings identical; module-dependencies.yaml consumers parse/pass; only the 3->4 warning removed_
    - _Requirements: 12.1, 12.2_

### Phase D — Convergence gate

- [x] 25. Whole-suite + validator convergence gate (depends on Tasks 17–24)
  - **Property 17: Preservation** - Whole-Suite + Validator Convergence
  - **IMPORTANT**: This is the single point where all eight lanes must hold simultaneously. Run only
    after Tasks 17–24 are complete.
  - Run the full suite: `python3 -m pytest senzing-bootcamp/tests/ tests/` and require **0 failed**.
    Re-run A5's class ~10x for determinism:
    `python3 -m pytest "senzing-bootcamp/tests/test_track_reorganization.py::TestProperty1NoLegacyIdentifiersInFiles" -q`.
  - Run every standalone validator and require all pass: `validate_power.py`,
    `measure_steering.py --check`, `validate_commonmark.py`, `validate_dependencies.py`,
    `compose_hook_prompts.py --verify`, `sync_hook_registry.py --verify`, `lint_steering.py`,
    `validate_prerequisites.py`, `validate_progress_ci.py`, `validate_mandatory_gates.py` (now
    NON-VACUOUS — must find the shipped gates), `validate_governance_rules.py`,
    `validate_yaml_schemas.py`, plus `eval_conversations.py`.
  - Confirm scripts remain stdlib-only (no new third-party import; PyYAML only in
    `validate_dependencies.py`) and that no prior `bootcamp-consistency-fixes` change is reverted
    (additive only).
  - **EXPECTED OUTCOME**: `python3 -m pytest senzing-bootcamp/tests/ tests/` -> 0 failed
    (deterministic incl. A5); all validators pass; `validate_mandatory_gates.py` is non-vacuous;
    scripts stdlib-only; no prior-spec change reverted.
  - Ensure all tests pass; ask the user if questions arise.
  - _Preservation: whole-suite 0 failed (deterministic incl. A5) + all 14 standalone validators + CI set pass + stdlib-only + no prior-spec change reverted_
  - _Requirements: 9.6, 13.1, 13.2, 13.3_

---

## Task Dependency Graph

The eight lanes (A1, A2, A3, A4, A5, B, C, D) are INDEPENDENT and fixed in parallel waves. Each fix
depends only on its own exploration + preservation tasks (all of which run on the unfixed tree and are
themselves parallel). The convergence gate depends on all eight fix lanes.

```json
{
  "waves": [
    {
      "wave": 0,
      "name": "Exploration + preservation baselines on UNFIXED tree (all parallel)",
      "tasks": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16"],
      "parallel": true,
      "dependsOn": []
    },
    {
      "wave": 1,
      "name": "Fixes (eight independent lanes, parallel)",
      "tasks": ["17", "18", "19", "20", "21", "22", "23", "24"],
      "parallel": true,
      "dependsOn": {
        "17": ["1", "9"],
        "18": ["2", "10"],
        "19": ["3", "11"],
        "20": ["4", "12"],
        "21": ["5", "13"],
        "22": ["6", "14"],
        "23": ["7", "15"],
        "24": ["8", "16"]
      }
    },
    {
      "wave": 2,
      "name": "Convergence gate",
      "tasks": ["25"],
      "parallel": false,
      "dependsOn": {
        "25": ["17", "18", "19", "20", "21", "22", "23", "24"]
      }
    }
  ]
}
```

```text
Wave 0 — exploration + preservation baselines on UNFIXED tree (all parallel; no inter-dependencies):
  +- Task 1   A1 exploration  (Property 1: Bug Condition)   - expect FAIL ('FalSe' -> False)
  +- Task 2   A2 exploration  (Property 3: Bug Condition)   - expect FAIL ([] != ['.'])
  +- Task 3   A3 exploration  (Property 5: Bug Condition)   - expect FAIL (non-monotonic timestamps)
  +- Task 4   A4 exploration  (Property 7: Bug Condition)   - expect FAIL (content_length=70)
  +- Task 5   A5 exploration  (Property 9: Bug Condition)   - expect intermittent DeadlineExceeded
  +- Task 6   B  exploration  (Property 11: Bug Condition)  - expect 0 gates / vacuous pass
  +- Task 7   C  exploration  (Property 13: Bug Condition)  - expect 4 committed items missing
  +- Task 8   D  exploration  (Property 15: Bug Condition)  - expect spurious 3->4 warning
  +- Task 9   A1 preservation (Property 2: Preservation)    - expect PASS (baseline)
  +- Task 10  A2 preservation (Property 4: Preservation)    - expect PASS (+ SHA-256 baseline)
  +- Task 11  A3 preservation (Property 6: Preservation)    - expect PASS (+ SHA-256 baseline)
  +- Task 12  A4 preservation (Property 8: Preservation)    - expect PASS (+ SHA-256 baseline)
  +- Task 13  A5 preservation (Property 10: Preservation)   - expect PASS (+ injected-id probe fails)
  +- Task 14  B  preservation (Property 12: Preservation)   - expect PASS (no-gate -> [])
  +- Task 15  C  preservation (Property 14: Preservation)   - expect PASS (commonmark)
  +- Task 16  D  preservation (Property 16: Preservation)   - expect PASS (findings baseline)

Wave 1 — fixes (eight independent lanes, parallel):
  +- Task 17  Fix A1  (depends on Task 1 + Task 9)    product code: preferences_utils.py
  |     17.1 implement -> 17.2 verify (Property 1: Expected Behavior) -> 17.3 verify (Property 2: Preservation)
  +- Task 18  Fix A2  (depends on Task 2 + Task 10)   test-only: test_assess_entry_point.py
  |     18.1 -> 18.2 (Property 3: Expected Behavior) -> 18.3 (Property 4: Preservation)
  +- Task 19  Fix A3  (depends on Task 3 + Task 11)   test-only: test_generate_recap_pdf.py
  |     19.1 -> 19.2 (Property 5: Expected Behavior) -> 19.3 (Property 6: Preservation)
  +- Task 20  Fix A4  (depends on Task 4 + Task 12)   test-only: test_token_budget_optimization.py
  |     20.1 -> 20.2 (Property 7: Expected Behavior) -> 20.3 (Property 8: Preservation)
  +- Task 21  Fix A5  (depends on Task 5 + Task 13)   test-only: test_track_reorganization.py
  |     21.1 -> 21.2 (Property 9: Expected Behavior) -> 21.3 (Property 10: Preservation)
  +- Task 22  Fix B   (depends on Task 6 + Task 14)   product code + new test: validate_mandatory_gates.py
  |     22.1 -> 22.2 (Property 11: Expected Behavior) -> 22.3 (Property 12: Preservation)
  +- Task 23  Fix C   (depends on Task 7 + Task 15)   docs: CHANGELOG.md
  |     23.1 -> 23.2 (Property 13: Expected Behavior) -> 23.3 (Property 14: Preservation)
  +- Task 24  Fix D   (depends on Task 8 + Task 16)   config: module-dependencies.yaml
        24.1 -> 24.2 (Property 15: Expected Behavior) -> 24.3 (Property 16: Preservation)

Wave 2 — convergence gate (depends on Tasks 17–24):
  +- Task 25  Whole-suite + validator convergence (Property 17: Preservation)
```

## Notes

- **Lanes are independent and parallelizable.** No two lanes edit the same file. `module-dependencies.yaml`
  is *read* by A5's structural tests and *edited* (one gate string) by D, but the edit does not touch
  structure/keys/module lists, so A5 and D remain independent. Each lane runs its own
  exploration → fix → preservation cycle.
- **A1 is the only product-logic fix in Group A.** It edits `scripts/preferences_utils.py`
  (`_serialize_yaml_value` + `_parse_scalar`). Genuine Python `bool` must still round-trip as `bool`.
- **A2–A5 are test-only.** The product source under test stays byte-identical, proven by comparing the
  post-fix SHA-256 against the Task 10/11/12 baseline digests (A2 `assess_entry_point.py`, A3
  `generate_recap_pdf.py`, A4 `measure_steering.py`); A5 changes only `test_track_reorganization.py`.
- **B is product code + a new test.** It edits `scripts/validate_mandatory_gates.py` (parser only) and
  adds `tests/test_mandatory_gates_parser_regression.py`; downstream cross-reference / `skipped_steps`
  / `NON_SKIPPABLE_GATES` / exit-code logic is unchanged.
- **C is docs.** Additive `[Unreleased]` edits to `CHANGELOG.md`; prior entries stay intact and the file
  remains CommonMark-clean.
- **D is config.** One reworded `3->4` requirement string in `config/module-dependencies.yaml`; YAML
  structure/keys/module lists untouched.
- **Stdlib-only constraint.** All scripts remain stdlib-only; PyYAML stays confined to
  `validate_dependencies.py`. No new third-party import is added by any lane.
- **Use `python3`.** The local dev environment only has `python3` (no `python`); use `python3` in every
  command. CI invokes `python`, but the commands above are for local execution.
- **Observation-first regeneration.** Every baseline, expected set, or snapshot (B's expected-gate set,
  the A3/A4 baselines, the D finding set) is produced by observing the actual current behavior/corpus
  first, then encoding that observation as the assertion — never by hand-guessing values.
- **Property hover labels.** Tasks 1/2/...8 use `Property N: Bug Condition`; Tasks 9–16 and the
  `.3` verification sub-tasks use `Property N: Preservation`; the `.2` verification sub-tasks use
  `Property N: Expected Behavior`; Task 25 uses `Property 17: Preservation`. These match the design's
  Correctness Properties 1–17.
