# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Step 5 contains a duplicate module table
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate Step 5 of `onboarding-flow.md` contains a duplicate module table
  - **Scoped PBT Approach**: Scope the property to the single affected file
  - Parse `senzing-bootcamp/steering/onboarding-flow.md` and extract the Step 5 (Track Selection) section
  - Assert Step 5 does NOT contain a markdown table with module numbers 1–12 (header row `| Module | Title` + 12 data rows)
  - Assert the introductory sentence "Display this quick-reference module table before presenting the tracks so the bootcamper can cross-reference module numbers:" does NOT appear in Step 5
  - Also count the total number of module tables (sections listing modules 1–12) in the full file and assert exactly one exists (in Step 4)
  - `isBugCondition(file)`: Step 5 section CONTAINS a markdown table with module numbers 1–12
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the duplicate table exists in Step 5)
  - Document counterexamples found
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Step 4 table, track options, and all other content unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **Step 1 — Observe on UNFIXED code:**
    - Extract Step 4 (Bootcamp Introduction) content and record the module overview bullet point "Module overview table (1-12): what each does and why it matters"
    - Extract Step 5 (Track Selection) track descriptions (A through D) and record them
    - Record the Module 2 auto-insertion note: "Module 2 inserted automatically before any module needing SDK."
    - Record the response interpretation rules: `"A"/"demo"→Module 3, "B"/"fast"→Module 5, "C"/"beginner"→Module 1, "D"/"full"→Module 1`
    - Record all other sections of the file (Steps 0–3, Switching Tracks, Changing Language, Validation Gates, Hook Registry)
  - **Step 2 — Write property-based tests asserting observed behavior is preserved:**
    - Property: Step 4 still contains the module overview instruction "Module overview table (1-12): what each does and why it matters"
    - Property: Step 5 still contains all four track options (A: Quick Demo, B: Fast Track, C: Complete Beginner, D: Full Production) with their module sequences
    - Property: Step 5 still contains the Module 2 auto-insertion note
    - Property: Step 5 still contains the response interpretation rules
    - Property: all sections outside Step 5's removed table content are identical between unfixed and fixed versions
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Remove duplicate module table from Step 5

  - [x] 3.1 Remove the quick-reference module table and its introductory sentence from Step 5
    - **File**: `senzing-bootcamp/steering/onboarding-flow.md`
    - **Section**: `## 5. Track Selection`
    - Remove the introductory sentence: "Display this quick-reference module table before presenting the tracks so the bootcamper can cross-reference module numbers:"
    - Remove the entire markdown table (header `| Module | Title ...`, separator `|--------|------...`, and all 12 data rows for modules 1–12)
    - Keep all remaining Step 5 content exactly as-is:
      - "Present tracks — not mutually exclusive, all completed modules carry forward:" and the four track options (A–D)
      - "Module 2 inserted automatically before any module needing SDK."
      - Response interpretation rules ("A"/"demo"→Module 3, etc.)
      - "Bare number→clarify letter vs module."
    - Do NOT modify any other section of the file (Steps 0–4, Switching Tracks, Changing Language, Validation Gates, Hook Registry)
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Duplicate module table removed from Step 5
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (Step 5 has no module table, file has exactly one module table in Step 4)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Step 4 table, track options, and all other content unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full test suite (bug condition + preservation tests)
  - Ensure all tests pass, ask the user if questions arise
