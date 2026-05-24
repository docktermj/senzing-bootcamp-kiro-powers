# Implementation Plan

## Overview

Bugfix implementation plan for adding license guidance workflow when record count exceeds 500 in Module 1 Step 6. Uses the bug condition methodology: exploration tests confirm the bug exists, preservation tests lock down existing behavior, then the fix is applied and validated.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Missing License Guidance Workflow for Record Count > 500
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in `senzing-bootcamp/steering/module-01-business-problem.md` Step 6
  - **Scoped PBT Approach**: The bug is deterministic — scope the property to the concrete Step 6 section and the transition between Step 6 and Step 7
  - Create test file `tests/test_license_guidance_workflow_properties.py`
  - Follow existing test patterns (class-based, Path-relative, Hypothesis PBT)
  - Parse `module-01-business-problem.md`, extract Step 6 and any content between Step 6 and Step 7
  - **Test 1 — Missing Threshold Check**: Assert that Step 6 (or a sub-step between 6 and 7) contains conditional logic checking whether total record count exceeds 500 (will FAIL on unfixed code — no threshold check exists)
  - **Test 2 — Missing License Question**: Assert that a step between 6 and 7 asks "Do you already have a Senzing license?" with a 👉 marker and STOP instruction (will FAIL on unfixed code — no license question exists)
  - **Test 3 — Missing "Has License" Branch**: Assert that a step contains guidance for bootcampers who already have a license (Base64 decode instructions, `licenses/g2.lic` path, LICENSEFILE engine config) (will FAIL on unfixed code — no branch exists)
  - **Test 4 — Missing "No License" Branch**: Assert that a step contains guidance for bootcampers who need a license (contact support@senzing.com, turnaround expectations, configuration instructions once received) (will FAIL on unfixed code — no branch exists)
  - **Test 5 — Missing Deferral Option**: Assert that a step offers to defer license configuration to Module 2 (will FAIL on unfixed code — no deferral option exists)
  - **PBT Test — Bug Condition Identification**: Use Hypothesis to generate record counts (501–100000) and verify that for any count > 500, the steering file should contain license guidance logic; assert the presence of threshold-based conditional content referencing the 500-record limit
  - _Bug_Condition: `isBugCondition(input)` where `input.totalRecords > 500` AND `input.currentModule = "Module 1"` AND `input.currentStep = "Step 6"` AND `licenseGuidanceNotProvided(input) = true`_
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct — it proves the bug exists)
  - Document counterexamples found: Step 6 parses record counts but has no > 500 conditional branch, no license question exists between Steps 6 and 7, no branching guidance for existing vs. new license holders
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-License-Trigger Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Create test file `tests/test_license_guidance_workflow_properties.py` (append to same file as task 1, in a separate test class)
  - Follow existing test patterns (class-based, Path-relative, Hypothesis PBT)
  - Observe the UNFIXED `module-01-business-problem.md` structure: Step 6 five-category inference (A–F), Step 7 gap-filling sub-steps (7a–7d), YAML frontmatter, Phase 2 reference line
  - **Test 1 — Step 6 Five-Category Inference Preservation**: Parse Step 6 and assert all five inference categories (RECORD TYPES, SOURCE COUNT AND NAMES, PROBLEM CATEGORY, MATCHING CRITERIA, DESIRED OUTCOME, INTEGRATION TARGETS) are present and their content is unchanged
  - **Test 2 — Step 7 Gap-Filling Preservation**: Assert Steps 7a–7d content (one-question-per-turn pattern, STOP markers, checkpoint writes) is present and unchanged
  - **Test 3 — Steps 1–5 and 8–9 Preservation**: Assert that Steps 1–5 and Steps 8–9 content is present and unchanged after the fix
  - **Test 4 — Phase 2 Reference Preservation**: Assert the Phase 2 reference line (`**Phase 2 (Steps 10–18):** Loaded from \`module-01-phase2-document-confirm.md\``) is present and unchanged
  - **Test 5 — YAML Frontmatter Preservation**: Assert the file begins with YAML frontmatter containing `inclusion: manual`
  - **Test 6 — Module 2 Step 5 Independence**: Assert that `senzing-bootcamp/steering/module-02-sdk-setup.md` is byte-identical to its original content (license gate in Module 2 is unaffected)
  - **Test 7 — Record Count ≤ 500 No License Mention**: Assert that for record counts ≤ 500, the Step 6 inference logic does not inject any license guidance content into the workflow path
  - **PBT Test — Small Dataset Preservation**: Use Hypothesis to generate record counts from 1 to 500 and verify that for any count ≤ 500, the steering file's Step 6 output path contains no license guidance triggers (no "Do you already have a Senzing license?" question, no LICENSESTRINGBASE64 references in the ≤ 500 path)
  - Verify all tests PASS on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.3, 3.4_

- [x] 3. Fix for missing license guidance workflow when record count exceeds 500

  - [x] 3.1 Implement the fix in `senzing-bootcamp/steering/module-01-business-problem.md`
    - Add conditional logic at the end of Step 6 (after the five-category inference completes) that checks whether the total record count across all sources exceeds 500
    - Add new Step 6b — License Guidance Trigger: When total records > 500, explain the 500-record evaluation limit and ask 👉 "Do you already have a Senzing license?" with a STOP instruction
    - Add new Step 6c — "Already has license" branch: Guide through providing Base64-encoded license string, decoding to `licenses/g2.lic`, adding `LICENSEFILE` to engine config PIPELINE section, recording `license: custom` in `config/bootcamp_preferences.yaml`
    - Add new Step 6d — "Does not have license" branch: Explain where to request (support@senzing.com), what information to provide, turnaround expectations (1–2 business days, 30–90 day validity), how to configure once received, and offer deferral option
    - Add new Step 6e — Deferral handling: Record `license_guidance_deferred: true` in `config/bootcamp_preferences.yaml`, note Module 2 Step 5 will handle it, proceed to Step 7
    - Do NOT modify Step 6's five-category inference logic (A–F sections)
    - Do NOT modify Steps 1–5, Steps 7–9, the Phase 2 reference, or the YAML frontmatter
    - Do NOT modify `senzing-bootcamp/steering/module-02-sdk-setup.md`
    - _Bug_Condition: `isBugCondition(input)` where `input.totalRecords > 500` AND `input.currentModule = "Module 1"` AND `input.currentStep = "Step 6"` AND `licenseGuidanceNotProvided(input) = true`_
    - _Expected_Behavior: System asks "Do you already have a Senzing license?", branches on answer, provides step-by-step configuration guidance, offers deferral option_
    - _Preservation: Step 6 five-category inference unchanged, Steps 1–5 and 7–9 unchanged, Phase 2 reference unchanged, Module 2 Step 5 unchanged, YAML frontmatter unchanged, one-question-per-turn pattern preserved_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - License Guidance Workflow Present for Record Count > 500
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (threshold check present, license question present, branching guidance present, deferral option present)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run: `python -m pytest tests/test_license_guidance_workflow_properties.py -k "BugCondition" -v`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-License-Trigger Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run: `python -m pytest tests/test_license_guidance_workflow_properties.py -k "Preservation" -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation tests still pass after fix (Step 6 inference unchanged, Steps 1–5 and 7–9 unchanged, Phase 2 reference intact, Module 2 Step 5 unmodified, frontmatter preserved, no license guidance for ≤ 500 records)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `python -m pytest tests/test_license_guidance_workflow_properties.py -v`
  - Ensure all bug condition tests PASS (confirming the fix works)
  - Ensure all preservation tests PASS (confirming no regressions)
  - Ensure `senzing-bootcamp/steering/module-02-sdk-setup.md` was NOT modified
  - Ensure Step 6 five-category inference logic (A–F) is intact
  - Ask the user if questions arise

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1", "2"],
      "description": "Write exploration and preservation tests (independent, before fix)"
    },
    {
      "wave": 2,
      "tasks": ["3.1"],
      "description": "Implement the fix (depends on understanding from tasks 1 and 2)"
    },
    {
      "wave": 3,
      "tasks": ["3.2", "3.3"],
      "description": "Verify exploration test passes and preservation tests still pass (depend on 3.1)"
    },
    {
      "wave": 4,
      "tasks": ["4"],
      "description": "Final checkpoint - ensure all tests pass (depends on 3.2 and 3.3)"
    }
  ]
}
```

## Notes

- Tests use Hypothesis for property-based testing following existing project patterns
- The exploration test (task 1) is expected to FAIL on unfixed code — this confirms the bug exists
- The preservation test (task 2) is expected to PASS on unfixed code — this locks down existing behavior
- After the fix (task 3.1), both test suites should PASS
- Module 2 (`module-02-sdk-setup.md`) must remain completely unmodified throughout
