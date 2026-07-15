# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - License Limit Ignored at Capacity Decisions
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists (hardcoded 500 used instead of effective license limit)
  - **Scoped PBT Approach**: Generate capacity-decision contexts where `customLicenseConfigured == true` and `license_record_limit` is 0 (unlimited) or > dataset size; assert that the threshold logic uses the effective limit, not 500
  - Bug Condition from design: `isBugCondition(input)` returns true when `customLicenseConfigured == true AND decisionPoint IN ['module1_step6a', 'module4_step6', 'module6_loading', 'module8_performance'] AND comparisonLimit == 500 AND NOT licenseQueried(decisionPoint)`
  - Test that `detect_license_limit.py` correctly reads `recordLimit` from license JSON and persists it to `config/bootcamp_progress.json`
  - Test that the threshold comparison logic (`evaluate_capacity_decision`) uses the persisted `license_record_limit` (not hardcoded 500) when a custom license is configured
  - Generate random `recordLimit` values (0 to 10M) and dataset totals (1 to 10M) with Hypothesis; assert `recommendSampling == (effectiveLimit > 0 AND datasetTotal > effectiveLimit)`
  - Run test on UNFIXED code (no `detect_license_limit.py` exists yet, no `license_record_limit` field exists)
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists: there is no license-aware threshold logic)
  - Document counterexamples found (e.g., "With `recordLimit: 0` (unlimited), threshold still compares against 500 and triggers sampling recommendation")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.5, 2.1, 2.2, 2.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Evaluation License and Non-License Figures Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: When no custom license is configured (no `license_record_limit` in progress), the evaluation-limit comparison fires as expected
  - Observe: Module 6 Phase A volume tier boundaries (demo: <500, small: 500-500K, medium: 500K-10M, large: 10M+) are independent of license detection
  - Observe: SQLite ≤1,000-record performance advice remains in Module 6 Phase B
  - Write property-based test with Hypothesis: for all contexts where `customLicenseConfigured == false` OR the decision point is not a license-capacity comparison, the capacity decision logic produces the same result as original behavior (compares against evaluation capacity from MCP)
  - Write property-based test: for all dataset totals, volume tier classification (non-license use of 500) is unchanged regardless of `license_record_limit` value
  - Write property-based test: for contexts where `license_record_limit` is absent/null in progress JSON, the logic falls back to evaluation-limit behavior
  - Generate random progress files (with/without `license_record_limit` field) and dataset totals with Hypothesis to verify backward compatibility
  - Verify tests pass on UNFIXED code (since preservation tests cover non-bug-condition paths, they should pass)
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.5, 3.6_

- [x] 3. Fix for hardcoded 500-record license limit assumption

  - [x] 3.1 Create `detect_license_limit.py` helper script
    - Create `senzing-bootcamp/scripts/detect_license_limit.py` (stdlib-only, Python 3.11+)
    - Add shebang, argparse CLI, and `main()` entry point per project conventions
    - Accept license JSON via stdin or file argument
    - Parse `recordLimit` from license JSON (handle missing field, malformed input)
    - Read existing `config/bootcamp_progress.json` (create if absent)
    - Write `license_record_limit` field (integer: 0 means unlimited, positive means cap, null means not detected)
    - Print detected limit to stdout for agent consumption
    - Handle edge cases: missing `recordLimit` key → report error; non-integer value → report error
    - _Bug_Condition: isBugCondition(input) where customLicenseConfigured == true AND licenseQueried == false_
    - _Expected_Behavior: Script persists actual recordLimit to progress JSON; agent uses this value for all capacity decisions_
    - _Preservation: When no license JSON provided or field missing, script exits with clear error — does not corrupt existing progress_
    - _Requirements: 2.1, 2.4_

  - [x] 3.2 Add `license_record_limit` field to `config/bootcamp_progress.json` schema
    - Add optional `license_record_limit` field (integer | null) to progress JSON
    - `null` = not yet detected; `0` = unlimited (no cap); positive integer = that many records
    - Document the field semantics in a comment block or adjacent schema doc
    - Ensure existing progress files without this field remain valid (backward compatible)
    - _Bug_Condition: No persistence contract exists for detected license limit_
    - _Expected_Behavior: Field persisted after Module 2 license detection; read by Modules 1/4/6/8_
    - _Preservation: Existing progress fields unchanged; missing field treated as null (evaluation fallback)_
    - _Requirements: 2.4, 3.1_

  - [x] 3.3 Update steering: `module-02-sdk-setup.md` — add Step 5e (Detect License Limit)
    - After Step 5d (configure LICENSEFILE), add Step 5e instructing the agent to:
      - Generate a scaffold calling `SzProduct.get_license()` via MCP tools
      - Parse `recordLimit` from the output JSON
      - Run `detect_license_limit.py` to persist the limit to `config/bootcamp_progress.json`
      - Report detected limit to the bootcamper
    - All SDK facts (`get_license()` semantics, `recordLimit` meaning) sourced from Senzing MCP server
    - _Bug_Condition: After license setup, no introspection step exists — limit never detected_
    - _Expected_Behavior: Agent detects and persists the real recordLimit immediately after license config_
    - _Preservation: Built-in evaluation license explanation in Step 5a unchanged when no custom license_
    - _Requirements: 2.1, 2.4, 3.2, 3.5_

  - [x] 3.4 Update steering: `module-02-sdk-setup.md` — Step 5a messaging guard
    - Add conditional: when a custom license has been configured, do NOT restate the 500-record figure as the authoritative limit
    - Instead, present the detected `recordLimit` from progress JSON
    - Keep evaluation-license explanation intact for sessions without a custom license
    - _Bug_Condition: Agent restates hardcoded 500 even when custom license is present_
    - _Expected_Behavior: Agent presents detected recordLimit; stops citing 500 as authoritative_
    - _Preservation: Evaluation license explanation preserved when no custom license configured_
    - _Requirements: 2.3, 3.2_

  - [x] 3.5 Update steering: `module-01-phase1-discovery.md` — Step 6a conditional threshold
    - Change threshold comparison from `exceeds 500` to license-aware logic:
      - Read `license_record_limit` from `config/bootcamp_progress.json`
      - If present and > 0: compare dataset total against that limit
      - If present and == 0: skip license guidance (no cap)
      - If absent or null: compare against evaluation capacity (confirmed via MCP)
    - _Bug_Condition: Compares against hardcoded 500 regardless of license state_
    - _Expected_Behavior: Compares against effective license limit from progress JSON_
    - _Preservation: When no custom license (field absent/null), evaluation comparison unchanged_
    - _Requirements: 1.5, 2.5, 3.1_

  - [x] 3.6 Update steering: `module-04-data-collection.md` — canonical framing update
    - Update agent instruction to read `license_record_limit` from progress JSON
    - Use effective limit for capacity decisions
    - When `license_record_limit` is 0 or >= dataset size: do not recommend sampling for license reasons
    - When `license_record_limit` is null/absent: fall back to evaluation capacity behavior
    - Sampling for non-license reasons (large file, faster iteration) remains available
    - _Bug_Condition: Defers to hardcoded 500 figure at sampling decision point_
    - _Expected_Behavior: Reads effective limit; skips license-based sampling when limit allows full dataset_
    - _Preservation: Non-license sampling options unchanged; evaluation fallback preserved_
    - _Requirements: 2.1, 2.2, 2.5, 3.3, 3.4_

  - [x] 3.7 Update steering: `module-06-phaseB-load-first-source.md` — conditional SENZ9000 warning
    - Before warning about "SENZ9000 at record 501", check `license_record_limit` from progress
    - If custom license is active (limit is 0 or > dataset size): omit the SENZ9000 warning
    - If no custom license (limit absent/null): keep existing warning behavior
    - _Bug_Condition: Warns about SENZ9000 at 501 regardless of active license_
    - _Expected_Behavior: Warning omitted when custom license permits full dataset_
    - _Preservation: Warning preserved for evaluation-only sessions; volume tier boundaries (500 in Phase A) unchanged_
    - _Requirements: 2.2, 2.3, 3.1, 3.6_

  - [x] 3.8 Update steering: `module-08-phaseB-benchmarking.md` — benchmark cap removal
    - When custom license is active (limit is 0 or > dataset size): do not cap benchmark sample sizes at 500
    - When no custom license: keep existing benchmark guidance
    - _Bug_Condition: Caps benchmarks at 500 citing "evaluation license" when production license active_
    - _Expected_Behavior: Benchmark sizes uncapped when license permits; uses effective limit_
    - _Preservation: Evaluation-license benchmark guidance unchanged for sessions without custom license_
    - _Requirements: 2.1, 2.5, 3.1_

  - [x] 3.9 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - License Limit Used at Capacity Decisions
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (effective limit used, not hardcoded 500)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.5_

  - [x] 3.10 Verify preservation tests still pass
    - **Property 2: Preservation** - Evaluation License and Non-License Figures Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation tests still pass after fix (no regressions to evaluation flow, volume tiers, or MCP-facts rule)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full pytest suite including property-based tests from tasks 1 and 2
  - Verify `detect_license_limit.py` unit tests pass (various license JSON inputs: recordLimit 0, 500, 10000, missing field, malformed)
  - Verify threshold comparison logic works for all combinations (limit 0 + any dataset = no sampling; limit > dataset = no sampling; limit < dataset = recommend sampling; limit absent = evaluation fallback)
  - Verify steering file changes are syntactically valid Markdown with YAML frontmatter
  - Ensure all tests pass, ask the user if questions arise
