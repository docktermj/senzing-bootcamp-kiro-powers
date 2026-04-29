# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Hook Prompts Lack Strong Silent-Pass Guardrails
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to the four affected hooks (ask-bootcamper, verify-senzing-facts, enforce-working-directory, enforce-feedback-path) plus hook-registry.md and agent-instructions.md
  - Extend `senzing-bootcamp/tests/test_silent_hook_processing.py` — the `TestBugCondition*` classes already exist and cover this
  - Tests parse each affected hook file's prompt and check for strong guardrail language:
    - `ask-bootcamper`: prompt must contain explicit prohibitions beyond "do nothing" (e.g., "do NOT answer", "do NOT role-play", "do NOT generate", "STOP")
    - `verify-senzing-facts`: prompt must contain a STOP/return instruction in the silent-pass branch
    - `enforce-working-directory`: prompt must contain an explicit silent-pass branch with "produce no output" AND a STOP instruction
    - `enforce-feedback-path`: prompt must contain a STOP/return instruction after "produce no output"
    - `hook-registry.md`: registry prompts must contain the same strong language as hook files
    - `agent-instructions.md`: Hooks section must contain emphatic silent-processing rule with explicit prohibitions
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., "ask-bootcamper prompt says 'do nothing' but lacks 'do NOT answer', 'do NOT role-play'")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Action-Required Branches and Non-Affected Content Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Extend `senzing-bootcamp/tests/test_silent_hook_processing.py` — the `TestPreservation*` classes already exist and cover this
  - Observe behavior on UNFIXED code for non-buggy inputs:
    - `ask-bootcamper` prompt contains recap keywords ("accomplished", "files created or modified", "👉 question", "skip the recap")
    - `verify-senzing-facts` prompt contains MCP tool names (mapping_workflow, generate_scaffold, get_sdk_reference, search_docs, explain_error_code) and SENZING_INFORMATION_POLICY
    - `enforce-working-directory` prompt contains /tmp/, %TEMP%, ~/Downloads, project-relative, "Do NOT proceed"
    - `enforce-feedback-path` prompt contains SENZING_BOOTCAMP_POWER_FEEDBACK.md and "STOP and redirect"
    - `capture-feedback` prompt contains all feedback trigger phrases and feedback-workflow.md
    - All 14 non-affected hooks in hook-registry.md match baseline sections
    - All existing content in agent-instructions.md is preserved (line-by-line check)
    - `ask-bootcamper.kiro.hook` file content matches baseline snapshot
  - Write property-based tests: for all non-buggy inputs, action-required keywords are preserved
  - Verify tests PASS on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 3. Fix hook prompt guardrails

  - [x] 3.1 Fix ask-bootcamper.kiro.hook prompt
    - Replace "do nothing" with explicit zero-output guard with prohibitions
    - Change "already ends with a 👉 question" to "already contains a 👉 character anywhere"
    - Add explicit prohibitions: "do NOT answer the question", "do NOT role-play as the bootcamper", "do NOT generate any content"
    - Add "STOP immediately and return nothing"
    - Add anti-fabrication examples: "Do not invent use-case descriptions, record counts, or system names"
    - Preserve recap branch (accomplished, files, 👉 question) and skip-recap branch (no files changed)
    - _Bug_Condition: isBugCondition(input) where input.hookId == "ask-bootcamper" AND "👉" IN input.agentOutput_
    - _Expected_Behavior: Hook produces absolutely no output when 👉 is detected_
    - _Preservation: Recap and skip-recap branches unchanged (Requirements 3.1, 3.2)_
    - _Requirements: 2.1, 2.2, 3.1, 3.2_

  - [x] 3.2 Fix verify-senzing-facts.kiro.hook prompt
    - Add STOP instruction after "produce no output at all" phrase: "STOP processing and return immediately"
    - Add redundant emphasis: "Your response must be completely empty — zero tokens, zero characters"
    - Restructure prompt to put silent-pass check FIRST (before action-required instructions)
    - Preserve MCP verification action branch (mapping_workflow, generate_scaffold, etc.)
    - _Bug_Condition: isBugCondition(input) where input.hookId == "verify-senzing-facts" AND (no Senzing content OR all verified)_
    - _Expected_Behavior: Hook produces zero tokens when no Senzing content needs verification_
    - _Preservation: MCP verification instructions unchanged (Requirement 3.3)_
    - _Requirements: 2.3, 3.3_

  - [x] 3.3 Fix enforce-working-directory.kiro.hook prompt
    - Add explicit silent-pass branch at the start: "If all paths are within the working directory, produce no output at all — do not acknowledge, do not explain, do not print anything. STOP immediately and return an empty response."
    - Add redundant emphasis: "Your response must be completely empty — zero tokens"
    - Preserve path correction action branch (/tmp/, %TEMP%, ~/Downloads, project-relative, "Do NOT proceed")
    - _Bug_Condition: isBugCondition(input) where input.hookId == "enforce-working-directory" AND allPathsWithinWorkingDirectory_
    - _Expected_Behavior: Hook produces zero tokens when all paths are valid_
    - _Preservation: Path correction instructions unchanged (Requirement 3.4)_
    - _Requirements: 2.4, 3.4_

  - [x] 3.4 Fix enforce-feedback-path.kiro.hook prompt
    - Add STOP instruction after "produce no output at all" phrase: "STOP processing and return immediately"
    - Add redundant emphasis: "Your response must be completely empty — zero tokens, zero characters"
    - Preserve feedback path redirection action branch (SENZING_BOOTCAMP_POWER_FEEDBACK.md, "STOP and redirect")
    - _Bug_Condition: isBugCondition(input) where input.hookId == "enforce-feedback-path" AND NOT isInFeedbackWorkflow_
    - _Expected_Behavior: Hook produces zero tokens when not in feedback workflow_
    - _Preservation: Feedback path redirection unchanged (Requirement 3.5)_
    - _Requirements: 2.5, 3.5_

  - [x] 3.5 Sync hook-registry.md prompts with updated hook files
    - Update ask-bootcamper prompt in hook-registry.md to match the updated hook file exactly
    - Update verify-senzing-facts prompt in hook-registry.md to match the updated hook file exactly
    - Update enforce-working-directory prompt in hook-registry.md to match the updated hook file exactly
    - Update enforce-feedback-path prompt in hook-registry.md to match the updated hook file exactly
    - Do NOT modify any non-affected hook sections
    - _Bug_Condition: Registry mirrors weak prompt language_
    - _Expected_Behavior: Registry prompts identical to hook file prompts_
    - _Preservation: All 14 non-affected hook sections unchanged (Requirement 3.8)_
    - _Requirements: 2.6, 3.8_

  - [x] 3.6 Reinforce agent-instructions.md Hooks section silent-processing rule
    - Strengthen existing silent-processing rule in ## Hooks section
    - Add explicit prohibitions: "Do not narrate your evaluation. Do not explain why no action is needed. Do not acknowledge the check. Do not print status messages. Your response must be completely empty — zero tokens."
    - Preserve all existing content in agent-instructions.md (only add/strengthen, never remove)
    - _Bug_Condition: agent-instructions.md lacks emphatic silent-processing rule_
    - _Expected_Behavior: Hooks section contains explicit zero-output enforcement_
    - _Preservation: All existing agent-instructions.md content preserved (Requirement 3.8)_
    - _Requirements: 2.7, 3.8_

  - [x] 3.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Hook Prompts Contain Strong Silent-Pass Guardrails
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1 (`pytest senzing-bootcamp/tests/test_silent_hook_processing.py -k "BugCondition"`)
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 3.8 Verify preservation tests still pass
    - **Property 2: Preservation** - Action-Required Branches and Non-Affected Content Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2 (`pytest senzing-bootcamp/tests/test_silent_hook_processing.py -k "Preservation"`)
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_silent_hook_processing.py senzing-bootcamp/tests/test_ask_bootcamper_hook.py -v`
  - Ensure all bug condition tests pass (confirming fix works)
  - Ensure all preservation tests pass (confirming no regressions)
  - Ensure ask-bootcamper hook tests pass (confirming metadata and sync)
  - Ensure all tests pass, ask the user if questions arise.
