# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property P1: Discriminating Intercept** — verify the bug exists in unfixed code
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - Test file: `senzing-bootcamp/tests/test_file_path_hook_stall.py`
  - Parse `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook` and assert:
    - The `then.prompt` field contains "policy: pass" as an explicit pass signal (will fail — current prompt says "produce no output at all")
    - The prompt contains a fast-path condition that outputs "policy: pass" for project-relative non-feedback writes (will fail — no fast path exists)
  - Parse `senzing-bootcamp/steering/agent-instructions.md` and assert:
    - Contains an explicit "retry the original tool call" mandate for preToolUse hooks (will fail — only the silence rule exists, no retry mandate)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (confirms the bug — no explicit pass signal, no fast path, no retry mandate)
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Properties P3, P4: Violation Detection Preserved** — establish baseline
  - **IMPORTANT**: Follow observation-first methodology
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Test file: `senzing-bootcamp/tests/test_file_path_hook_stall.py` (same file, separate test class)
  - Observe on UNFIXED code and write tests verifying:
    - **External path blocking**: Hook prompt contains instructions to STOP for paths outside working directory (`/tmp/`, `%TEMP%`, `~/Downloads`)
    - **Feedback path enforcement**: Hook prompt contains instructions to redirect feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
    - **Content path check**: Hook prompt contains instructions to check file content for external path references
    - **Hook event config**: `when.type` is `"preToolUse"` and `when.toolTypes` contains `"write"`
    - **JSON validity**: Hook file parses as valid JSON
  - Use Hypothesis `@given` with `st.sampled_from` for path pattern variations
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline violation-detection behavior to preserve)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for enforce-file-path-policies hook causing silent agent stalls

  - [x] 3.1 Rewrite the hook prompt with fast-path and explicit pass signal
    - Edit `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook`
    - Replace the `then.prompt` field with the new prompt from design.md §Fix Implementation
    - The new prompt must:
      - Include a QUICK CHECK with Q1 (path inside working directory?) and Q2 (misrouted feedback?)
      - Include a FAST PATH that outputs exactly "policy: pass" when Q1=YES and Q2=NO
      - Include a SLOW PATH that STOPs for external paths and redirects misrouted feedback
      - Include a CONTENT CHECK as a secondary gate for file content with external references
    - Update the `description` field to mention the fast-path behavior
    - Bump `version` to `"2.0.0"` (behavior change)
    - Do NOT change `name`, `when.type`, or `when.toolTypes`
    - _Bug_Condition: Hook fires unconditionally on every write, produces zero output for compliant writes, agent must infer retry_
    - _Expected_Behavior: Fast path outputs "policy: pass" for common case; slow path handles violations_
    - _Preservation: External path blocking, feedback redirect, content check all preserved in slow path_
    - _Requirements: 2.1, 2.2, 2.4, 3.1, 3.2, 3.3_

  - [x] 3.2 Add explicit preToolUse retry rule to agent-instructions.md
    - Edit `senzing-bootcamp/steering/agent-instructions.md`
    - In the `## Hooks` section, after the `🔇 Hook silence rule` paragraph, add:
      ```
      **🔄 preToolUse retry rule:** When a preToolUse hook produces "policy: pass" or produces no output (zero tokens), you MUST immediately retry the original tool call with exactly the same parameters. Do not emit any acknowledgment, do not explain, do not pause — retry instantly. Only when a preToolUse hook explicitly denies access or produces corrective instructions should you NOT retry.
      ```
    - Do NOT modify any other content in agent-instructions.md
    - _Bug_Condition: No explicit retry mandate exists — agent must infer retry from silence rule_
    - _Expected_Behavior: Explicit "MUST immediately retry" rule eliminates the inferential gap_
    - _Preservation: All other agent-instructions.md content unchanged_
    - _Requirements: 2.3_

  - [x] 3.3 Update hook-registry.md to reflect the new description and version
    - Edit `senzing-bootcamp/steering/hook-registry.md`
    - Update the `enforce-file-path-policies` entry:
      - Version: `2.0.0`
      - Description: mention fast-path behavior
    - Do NOT change the hook's `id` or `Prompt` section (the prompt in the registry is a summary, not the full prompt)
    - _Preservation: Registry remains in sync with hook file_
    - _Requirements: 3.4 (CI validation must pass)_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property P1: Discriminating Intercept** — re-run the SAME test from task 1
    - **IMPORTANT**: Do NOT write a new test — re-run the existing one
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed — explicit pass signal exists, fast path exists, retry mandate exists)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - **Properties P3, P4: Violation Detection Preserved** — re-run the SAME tests from task 2
    - **IMPORTANT**: Do NOT write new tests — re-run the existing ones
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — external path blocking, feedback redirect, content check, event config all preserved)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint — Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_file_path_hook_stall.py -v`
  - Verify Property P1 (Discriminating Intercept / Explicit Pass Signal) passes
  - Verify Properties P3/P4 (Violation Detection / JSON Validity) pass
  - Run CI validation: `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
  - Verify hook file is valid JSON: `python3 -c "import json; json.load(open('senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook'))"`
  - Ensure no other tests in the repository are broken by the change
  - Ask the user if questions arise
