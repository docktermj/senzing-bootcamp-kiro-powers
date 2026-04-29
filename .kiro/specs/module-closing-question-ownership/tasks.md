# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Inline Closing Questions and WAITs in Module Steering Files
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists across all affected module steering files
  - **Scoped PBT Approach**: Scope the property to the concrete affected files
  - Parse each affected module steering file and check for inline 👉 closing questions and WAIT-for-response instructions
  - Affected files to check:
    - `senzing-bootcamp/steering/module-01-business-problem.md` — 4 WAIT instructions
    - `senzing-bootcamp/steering/module-02-sdk-setup.md` — 4 WAIT instructions
    - `senzing-bootcamp/steering/module-04-data-collection.md` — 1 WAIT instruction
    - `senzing-bootcamp/steering/module-05-data-quality-mapping.md` — 4 WAIT instructions
    - `senzing-bootcamp/steering/module-06-single-source.md` — 1 inline 👉 question, 1 WAIT instruction
    - `senzing-bootcamp/steering/module-07-multi-source.md` — 7 inline 👉 questions, 7 WAIT instructions
    - `senzing-bootcamp/steering/module-07-reference.md` — 2 inline 👉 questions, 1 WAIT instruction
    - `senzing-bootcamp/steering/module-08-query-validation.md` — 4 inline 👉 questions, 4 WAIT instructions
    - `senzing-bootcamp/steering/module-12-deployment.md` — 1 inline 👉 question, 3 WAIT instructions
    - `senzing-bootcamp/steering/module-completion.md` — 3 inline 👉 questions, 2 WAIT instructions
  - For each affected file, assert the file does NOT contain:
    - Lines matching `👉` followed by a question (inline closing questions)
    - Lines matching `WAIT for response`, `WAIT for confirmation`, `WAIT for their response`, `WAIT for response before proceeding`, `WAIT for each`, `⚠️ WAIT — Do NOT proceed`
  - Also verify unaffected files have NO matches (modules 03, 09, 10, 11)
  - `isBugCondition(file)`: file.content CONTAINS inline 👉 closing question OR file.content CONTAINS WAIT instruction AND ask-bootcamper hook IS active
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bug exists in the affected files)
  - Document counterexamples found
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Informational Content, Step Sequences, and Untouched Files
  - **IMPORTANT**: Follow observation-first methodology
  - **Step 1 — Observe on UNFIXED code:**
    - For each affected file, extract all step/section headings and record the heading sequence
    - Extract informational content from each affected file excluding inline 👉 closing questions and WAIT instructions
    - Record content of non-affected module files (module-03, module-09, module-10, module-11) in full
    - Record content of `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`
    - Record content of `senzing-bootcamp/steering/agent-instructions.md`
    - Record content of `senzing-bootcamp/steering/onboarding-flow.md` (regression check)
  - **Step 2 — Write property-based tests asserting observed behavior is preserved:**
    - Property: for each affected file, step/section headings in the fixed file match the observed heading sequence
    - Property: for each affected file, informational content (excluding inline 👉 questions and WAIT lines) is preserved in the fixed version
    - Property: for all non-affected module files (03, 09, 10, 11), content is identical between unfixed and fixed versions
    - Property: `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` content is identical to the observed baseline
    - Property: `senzing-bootcamp/steering/agent-instructions.md` content is identical to the observed baseline
    - Property: `senzing-bootcamp/steering/onboarding-flow.md` content is identical to the observed baseline
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix for inline closing questions and WAITs in module steering files

  - [x] 3.1 Fix `senzing-bootcamp/steering/module-01-business-problem.md`
    - Remove 4 WAIT instructions: `WAIT for response` (steps 1, 3, 5), `WAIT for confirmation` (step 7)
    - Keep all informational content: git repo question, design pattern gallery offer, business problem description prompt, summary confirmation
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 3.3, 3.4_

  - [x] 3.2 Fix `senzing-bootcamp/steering/module-02-sdk-setup.md`
    - Remove 4 WAIT instructions: `WAIT for response before proceeding` (platform), `WAIT for response` ×2 (license checks), `WAIT for response` (database)
    - Keep all informational content: platform question, license check logic, database question, MCP instructions
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 3.3, 3.4_

  - [x] 3.3 Fix `senzing-bootcamp/steering/module-04-data-collection.md`
    - Remove 1 WAIT instruction: `WAIT for their response`
    - Keep all informational content: data source options, CORD dataset instructions
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 3.3, 3.4_

  - [x] 3.4 Fix `senzing-bootcamp/steering/module-05-data-quality-mapping.md`
    - Remove 4 WAIT instructions: `WAIT for response before proceeding` (quality assessment), `WAIT for confirmation` ×2 (entity plan, mapping), `WAIT for response` (final quality check)
    - Keep all informational content: quality scoring logic, mapping workflow, MCP state management
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 3.3, 3.4_

  - [x] 3.5 Fix `senzing-bootcamp/steering/module-06-single-source.md`
    - Remove 1 inline 👉 question (`👉 **Ask the bootcamper:**`) and 1 WAIT instruction (`⚠️ WAIT — Do NOT proceed`)
    - Keep the mandatory visualization offer description and DO NOT SKIP instruction — rephrase to present the offer as information without an inline closing question
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 2.4, 3.3, 3.4_

  - [x] 3.6 Fix `senzing-bootcamp/steering/module-07-multi-source.md`
    - Remove 7 inline 👉 questions and 7 WAIT instructions across steps 2, 3, 4, 5, 8, 11, 14, 15
    - Keep all informational content: data source enumeration, dependency analysis, ordering heuristics, loading strategy descriptions, orchestrator testing, visualization descriptions, UAT instructions, dashboard offer
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 2.4, 3.3, 3.4_

  - [x] 3.7 Fix `senzing-bootcamp/steering/module-07-reference.md`
    - Remove 2 inline 👉 questions and 1 WAIT instruction
    - Keep ordering examples, conflict resolution guidance, error handling options, troubleshooting reference
    - Do NOT modify informational content
    - _Requirements: 2.1, 2.2, 3.3, 3.4_

  - [x] 3.8 Fix `senzing-bootcamp/steering/module-08-query-validation.md`
    - Remove 4 inline 👉 questions and 4 WAIT instructions
    - Keep mandatory visualization offer descriptions, integration pattern descriptions, MCP instructions
    - Rephrase DO NOT SKIP blocks to present offers as information without inline closing questions
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 2.4, 3.3, 3.4_

  - [x] 3.9 Fix `senzing-bootcamp/steering/module-12-deployment.md`
    - Remove 1 inline 👉 question and 3 WAIT instructions
    - Keep deployment target logic, phase gate description, DR guidance, stakeholder summary offer
    - Do NOT modify step sequence, checkpoint logic, or MCP instructions
    - _Requirements: 2.1, 2.2, 3.3, 3.4_

  - [x] 3.10 Fix `senzing-bootcamp/steering/module-completion.md`
    - Remove 3 inline 👉 questions (`👉 What's your main takeaway`, `👉 Ready to move on`, `👉 What would you like to do?`) and 2 WAIT instructions
    - Keep journal template, reflection question description (rephrased as information), next-step options list, path completion detection, graduation offer flow, celebration content
    - Rephrase the reflection question and next-step options to present as information rather than inline closing questions
    - Do NOT modify journal template, path completion table, or graduation logic
    - _Requirements: 2.1, 2.2, 3.3, 3.4_

  - [x] 3.11 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Inline Closing Questions and WAITs Removed
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (no inline 👉 questions or WAITs in any module steering file)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.12 Verify preservation tests still pass
    - **Property 2: Preservation** - Informational Content, Step Sequences, and Untouched Files
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full test suite (bug condition + preservation tests)
  - Ensure all tests pass, ask the user if questions arise
