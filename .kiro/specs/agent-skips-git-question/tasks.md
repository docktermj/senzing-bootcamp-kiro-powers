# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Git Question Missing 👉 Marker and Stop Instruction
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in `senzing-bootcamp/steering/module-01-business-problem.md` Step 1
  - **Scoped PBT Approach**: The bug is deterministic — scope the property to the concrete Step 1 section of the steering file
  - Create test file `senzing-bootcamp/tests/test_git_question_bug.py`
  - Follow existing test patterns from `test_track_selection_gate_bug.py` (class-based, Path-relative, Hypothesis PBT)
  - Parse `module-01-business-problem.md`, extract Step 1 ("Initialize version control") section
  - **Test 1 — Missing 👉 Marker**: Assert the git initialization question text in Step 1 contains the 👉 marker prefix (will FAIL on unfixed code — no marker exists)
  - **Test 2 — Missing Stop Instruction**: Assert Step 1 contains an explicit stop/wait instruction after the git question telling the agent to STOP and wait for the bootcamper's response (will FAIL on unfixed code — no stop instruction exists)
  - **Test 3 — Premature Checkpoint**: Assert Step 1's checkpoint is deferred until after the bootcamper responds — the checkpoint should NOT appear unconditionally right after the question/response logic (will FAIL on unfixed code — checkpoint is unconditional)
  - **PBT Test — Bug Condition Identification**: Use Hypothesis to generate step numbers (1–8) and verify that only Step 1 is the step requiring the 👉 git question marker; all other steps should not contain a git initialization question without 👉
  - _Bug_Condition: `isBugCondition(input)` where `input.currentStep = "Step 1"` AND `input.workspaceIsGitRepo = false` AND (`input.questionTextLacksPointingMarker = true` OR `input.steeringLacksStopInstruction = true`)_
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct — it proves the bug exists)
  - Document counterexamples found: Step 1 git question lacks 👉 prefix, no stop instruction after question, checkpoint is unconditional
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Git-Question Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Create test file `senzing-bootcamp/tests/test_git_question_preservation.py`
  - Follow existing test patterns from `test_track_selection_gate_preservation.py` (class-based, Path-relative, Hypothesis PBT)
  - Observe the UNFIXED `module-01-business-problem.md` structure: 8 numbered steps, YAML frontmatter, Phase 2 reference line, checkpoint patterns
  - **Test 1 — Steps 2–8 Content Preservation**: Parse Steps 2 through 8 from the unfixed file and snapshot their content; assert each step's content is present and unchanged after the fix
  - **Test 2 — Phase 2 Reference Preservation**: Assert the Phase 2 reference line (`**Phase 2 (Steps 9–16):** Loaded from \`module-01-phase2-document-confirm.md\``) is present and unchanged
  - **Test 3 — Already-a-Repo Path Preservation**: Assert Step 1 still contains the git check commands (`git rev-parse --git-dir`) and the "already a repo" skip logic that proceeds directly without prompting
  - **Test 4 — Step Count Preservation**: Assert the file contains exactly 8 numbered top-level steps (1–8) plus the Phase 2 reference
  - **Test 5 — YAML Frontmatter Preservation**: Assert the file begins with YAML frontmatter containing `inclusion: manual`
  - **Test 6 — Hook File Unchanged**: Assert `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` is byte-identical to its original content (read and snapshot the file, verify no modifications)
  - **Test 7 — Checkpoint Count Preservation**: Assert the total number of `**Checkpoint:**` lines in the file is unchanged (one per step)
  - **PBT Test — Non-Step-1 Steps Unchanged**: Use Hypothesis to generate step numbers from {2, 3, 4, 5, 6, 7, 8} and verify each step's content is identical between the observed baseline and the current file
  - Verify all tests PASS on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for agent skipping git initialization question in Module 1 Step 1

  - [x] 3.1 Implement the fix in `senzing-bootcamp/steering/module-01-business-problem.md`
    - Rewrite Step 1 ("Initialize version control") to fix the bug while preserving the "already a repo" path
    - Add the 👉 marker to the git initialization question: change from plain `ask: "Would you like me to initialize a git repository?"` to `👉 "Would you like me to initialize a git repository for version control?"`
    - Add an explicit STOP instruction after the 👉 question telling the agent to STOP and wait for the bootcamper's response before proceeding
    - Defer the Step 1 checkpoint: move `**Checkpoint:** Write step 1 to config/bootcamp_progress.json` so it only fires AFTER the bootcamper responds and the agent acts on the response
    - Restructure the conditional flow to clearly separate two paths: (a) already a repo → write checkpoint immediately, proceed to Step 2; (b) not a repo → ask 👉 question, STOP, wait for response, act on response (initialize if yes, skip if no), THEN write checkpoint and proceed
    - Do NOT modify `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` — it already correctly handles 👉 detection
    - Do NOT modify Steps 2–8, the Phase 2 reference, or the YAML frontmatter
    - _Bug_Condition: `isBugCondition(input)` where `input.currentStep = "Step 1"` AND `input.workspaceIsGitRepo = false` AND (`input.questionTextLacksPointingMarker = true` OR `input.steeringLacksStopInstruction = true`)_
    - _Expected_Behavior: Step 1 git question uses 👉 marker, agent STOPs and waits, checkpoint deferred until after response_
    - _Preservation: Steps 2–8 unchanged, Phase 2 reference unchanged, hook file unchanged, "already a repo" path preserved, YAML frontmatter unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Git Question Uses 👉 Marker and Stop Instruction
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (👉 marker present, stop instruction present, checkpoint deferred)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run: `python -m pytest senzing-bootcamp/tests/test_git_question_bug.py -v`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Git-Question Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run: `python -m pytest senzing-bootcamp/tests/test_git_question_preservation.py -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation tests still pass after fix (Steps 2–8 unchanged, Phase 2 reference intact, hook file unmodified, step count preserved, frontmatter preserved, checkpoint count preserved)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `python -m pytest senzing-bootcamp/tests/test_git_question_bug.py senzing-bootcamp/tests/test_git_question_preservation.py -v`
  - Ensure all bug condition tests PASS (confirming the fix works)
  - Ensure all preservation tests PASS (confirming no regressions)
  - Ensure the `ask-bootcamper.kiro.hook` file was NOT modified
  - Ask the user if questions arise
