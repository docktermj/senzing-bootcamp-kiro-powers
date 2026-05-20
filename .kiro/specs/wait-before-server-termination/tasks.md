# Implementation Plan

## Overview

Fix the premature server termination bug by adding STOP instructions and user confirmation gates to three steering files, ensuring the bootcamper can explore the visualization before cleanup proceeds.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Missing STOP and Confirmation Gate After URL Presentation
  - **IMPORTANT**: Write this property-based test BEFORE implementing the fix
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in all three steering files
  - **Scoped PBT Approach**: Scope the property to the three concrete insertion points:
    - `visualization-guide.md` Web Service Delivery Sequence has no "wait for user" step between present and fallback
    - `module-03-phase2-visualization.md` Step 9.4 section 3 has no `🛑 STOP` directive after URL presentation
    - `module-03-system-verification.md` Step 11 has no user confirmation gate before termination
  - **Test file**: `senzing-bootcamp/tests/test_wait_before_server_termination_bug.py`
  - **Test implementation**:
    - Parse `visualization-guide.md` and extract the Web Service Delivery Sequence section
    - Assert it contains a "wait for user confirmation" step (step 4) between present (step 3) and fallback — will FAIL on unfixed code
    - Parse `module-03-phase2-visualization.md` and extract Step 9.4 section 3 ("Present to bootcamper")
    - Assert it contains a `🛑 STOP` directive after the URL presentation bullets — will FAIL on unfixed code
    - Parse `module-03-system-verification.md` and extract Step 11
    - Assert it contains a user confirmation prompt before the termination logic — will FAIL on unfixed code
    - Use Hypothesis to generate random file indices across the three files and verify the bug condition is localized to the specific insertion points
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bug exists)
  - Document counterexamples found:
    - Web Service Delivery Sequence goes directly from step 3 (present) to step 4 (fallback) with no wait step
    - Step 9.4 section 3 ends with stop instructions but no `🛑 STOP` directive
    - Step 11 begins with "Terminate the web service" with no confirmation gate
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Steering File Content Unchanged Outside Insertion Points
  - **IMPORTANT**: Follow observation-first methodology
  - **Test file**: `senzing-bootcamp/tests/test_wait_before_server_termination_preservation.py`
  - **Observation phase** (run on UNFIXED code to capture baselines):
    - Observe: `visualization-guide.md` Web Service Delivery Sequence steps 1–3 (start, verify, present) content
    - Observe: `visualization-guide.md` fallback step content (currently step 4)
    - Observe: `module-03-phase2-visualization.md` Step 9.4 items 1 and 2 (start server, verify endpoints) content
    - Observe: `module-03-phase2-visualization.md` checkpoint JSON structure at end of Step 9.4
    - Observe: `module-03-system-verification.md` Step 11 items 1–4 (terminate, artifact message, purge, retain) content
    - Observe: `module-03-system-verification.md` Step 10 content (report generation)
    - Observe: `module-03-system-verification.md` Step 12 content (module close)
    - Observe: YAML frontmatter in all three files
  - **Property-based tests** (from Preservation Requirements in design):
    - For all content in `visualization-guide.md` outside the new step 4 insertion point, content matches baseline
    - For all content in `module-03-phase2-visualization.md` outside the new STOP block in Step 9.4 section 3, content matches baseline
    - For all content in `module-03-system-verification.md` outside the new confirmation gate at the beginning of Step 11, content matches baseline
    - Steps 1–3 of the Web Service Delivery Sequence are byte-identical to baseline
    - The fallback step logic is preserved (content unchanged, only renumbered from 4 to 5)
    - Step 9.4 items 1 and 2 (start server, verify endpoints) are unchanged
    - Step 11 cleanup logic (5-second termination, force-stop, purge, retain) is unchanged after the new gate
    - Step 10 (Verification Report Generation) is unchanged
    - Step 12 (Module Close) is unchanged
    - YAML frontmatter (`inclusion: manual`) is preserved in all three files
  - Use Hypothesis to generate random section indices across the three files and verify non-insertion-point content is identical to baseline
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for missing wait-before-server-termination

  - [x] 3.1 Add "wait for user confirmation" step to Web Service Delivery Sequence in `visualization-guide.md`
    - Insert a new step 4 between current step 3 (present) and step 4 (fallback)
    - New step 4 instructs the agent to end its response with a STOP directive and wait for the bootcamper to confirm they have finished exploring
    - Renumber current step 4 (fallback) to step 5
    - Update the sequence description to reflect 5 steps total
    - _Bug_Condition: isBugCondition(input) where input.step = "post_url_presentation" AND input.webServerRunning = true AND input.bootcamperConfirmedDone = false AND input.agentProceeding = true_
    - _Expected_Behavior: Agent ends response with STOP and waits for bootcamper confirmation before proceeding_
    - _Preservation: Steps 1–3 (start, verify, present) unchanged; fallback logic unchanged (only renumbered)_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.4_

  - [x] 3.2 Add `🛑 STOP` instruction after URL presentation in Step 9.4 section 3 of `module-03-phase2-visualization.md`
    - After the bullet points presenting the URL, restart command, and stop instructions, add a `🛑 STOP` block
    - Include confirmation prompt text: "👉 Take your time exploring the visualization. Let me know when you're ready and I'll continue with cleanup."
    - The STOP forces the agent to end its response and wait for bootcamper input
    - _Bug_Condition: isBugCondition(input) where Step 9.4 section 3 has no STOP directive after URL presentation_
    - _Expected_Behavior: Agent stops after presenting URL and waits for explicit bootcamper confirmation_
    - _Preservation: Step 9.4 items 1 and 2 (start server, verify endpoints) unchanged; checkpoint JSON unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 3.4_

  - [x] 3.3 Add user confirmation gate at the beginning of Step 11 in `module-03-system-verification.md`
    - Insert a pre-cleanup instruction before item 1 ("Terminate the web service")
    - Require the agent to ask the bootcamper if they have finished exploring the visualization before proceeding with termination
    - Add skip condition: if the bootcamper skipped Step 9 (no server was started), the confirmation prompt is skipped and cleanup proceeds directly
    - Include prompt text like: "👉 Have you finished exploring the visualization? Let me know when you're ready and I'll clean up the server."
    - _Bug_Condition: isBugCondition(input) where Step 11 begins with termination without confirmation gate_
    - _Expected_Behavior: Agent asks for confirmation before terminating; skips prompt if Step 9 was skipped_
    - _Preservation: Step 11 items 1–4 (terminate, artifact message, purge, retain) unchanged after the gate_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Missing STOP and Confirmation Gate After URL Presentation
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (STOP directives and confirmation gates present)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1: `pytest senzing-bootcamp/tests/test_wait_before_server_termination_bug.py -v`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Steering File Content Unchanged Outside Insertion Points
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2: `pytest senzing-bootcamp/tests/test_wait_before_server_termination_preservation.py -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_wait_before_server_termination_bug.py senzing-bootcamp/tests/test_wait_before_server_termination_preservation.py -v`
  - Ensure all tests pass, ask the user if questions arise.


## Task Dependency Graph

```json
{
  "waves": [
    {"tasks": ["1", "2"]},
    {"tasks": ["3.1", "3.2", "3.3"]},
    {"tasks": ["3.4", "3.5"]},
    {"tasks": ["4"]}
  ]
}
```

## Notes

- This is a steering-file-only fix — no application code changes required
- Tests use structural analysis (parsing Markdown content) rather than runtime execution
- The exploration test (task 1) is expected to FAIL on unfixed code, confirming the bug exists
- The preservation test (task 2) is expected to PASS on unfixed code, capturing the baseline
- After the fix (tasks 3.1–3.3), both test suites should PASS
