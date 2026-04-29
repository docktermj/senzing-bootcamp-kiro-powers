# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Hook prompts lack explicit silent-processing instructions
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the four hook prompts lack explicit "produce no output" instructions for the no-action-needed case
  - **Scoped PBT Approach**: Scope the property to the concrete affected files
  - Parse each affected hook file and hook-registry.md, extract the prompt text, and assert it contains an explicit silent-processing instruction (e.g., "produce no output")
  - Affected files to check:
    - `senzing-bootcamp/hooks/capture-feedback.kiro.hook` — prompt uses "do nothing" without "produce no output"
    - `senzing-bootcamp/hooks/enforce-feedback-path.kiro.hook` — prompt uses "do nothing" without "produce no output"
    - `senzing-bootcamp/hooks/enforce-working-directory.kiro.hook` — prompt has no explicit no-action branch
    - `senzing-bootcamp/hooks/verify-senzing-facts.kiro.hook` — prompt has no explicit no-action branch
    - `senzing-bootcamp/steering/hook-registry.md` — registry prompts mirror the same ambiguous phrasing
  - Also verify `senzing-bootcamp/steering/agent-instructions.md` does NOT yet contain a silent-processing rule under the Hooks section
  - For each affected hook file, assert the prompt CONTAINS an explicit "produce no output" instruction for the pass/no-action case
  - `isBugCondition(hook)`: hook.prompt DOES NOT CONTAIN explicit silent-processing instruction AND hook.name IN affected set
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bug exists in the affected hook prompts)
  - Document counterexamples found
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Action-required branches and non-affected hooks unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **Step 1 — Observe on UNFIXED code:**
    - For each affected hook file, extract the action-required branch text (the instructions for when a problem IS found)
    - Record the full prompt text of all non-affected hooks in `senzing-bootcamp/steering/hook-registry.md` (ask-bootcamper, code-style-check, commonmark-validation, and all module hooks)
    - Record the full content of `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`
    - Record the full content of `senzing-bootcamp/steering/agent-instructions.md`
  - **Step 2 — Write property-based tests asserting observed behavior is preserved:**
    - Property: for each affected hook, the action-required branch text is preserved in the fixed version
    - Property: for `capture-feedback`, the feedback workflow initiation instructions (read progress, note context, load feedback-workflow.md) are preserved
    - Property: for `enforce-feedback-path`, the path redirection instructions (verify path is `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`, STOP and redirect) are preserved
    - Property: for `enforce-working-directory`, the path correction instructions (replace with project-relative equivalents, Do NOT proceed) are preserved
    - Property: for `verify-senzing-facts`, the MCP verification instructions (verify via MCP tools, per SENZING_INFORMATION_POLICY.md) are preserved
    - Property: all non-affected hooks in hook-registry.md are byte-identical to the observed baseline
    - Property: `ask-bootcamper.kiro.hook` content is identical to the observed baseline
    - Property: all existing content in `agent-instructions.md` is preserved (new content may be added)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Implement the fix across all affected files

  - [x] 3.1 Fix `senzing-bootcamp/hooks/capture-feedback.kiro.hook`
    - Replace "do nothing — let the conversation continue normally" with "produce no output at all — do not acknowledge, do not explain, do not print anything"
    - Keep the feedback trigger phrase list unchanged
    - Keep the feedback workflow initiation instructions (read progress, note context, load feedback-workflow.md) unchanged
    - Do NOT modify the hook name, version, description, event type, or JSON structure
    - _Requirements: 2.1, 3.1_

  - [x] 3.2 Fix `senzing-bootcamp/hooks/enforce-feedback-path.kiro.hook`
    - Replace "do nothing — let the write proceed normally" with "produce no output at all — do not acknowledge, do not explain, do not print anything"
    - Keep the feedback content detection logic unchanged
    - Keep the path redirection instructions (verify path, STOP and redirect) unchanged
    - Do NOT modify the hook name, version, description, event type, toolTypes, or JSON structure
    - _Requirements: 2.2, 3.2_

  - [x] 3.3 Fix `senzing-bootcamp/hooks/enforce-working-directory.kiro.hook`
    - Add an explicit no-action branch: "If all paths are within the working directory, produce no output at all — do not acknowledge, do not explain, do not print anything"
    - Keep the path correction instructions (replace with project-relative equivalents, Do NOT proceed) unchanged
    - Do NOT modify the hook name, version, description, event type, toolTypes, or JSON structure
    - _Requirements: 2.3, 3.3_

  - [x] 3.4 Fix `senzing-bootcamp/hooks/verify-senzing-facts.kiro.hook`
    - Add an explicit no-action branch: "If the file contains no Senzing-specific content, or all Senzing content was already verified via MCP tools, produce no output at all — do not acknowledge, do not explain, do not print anything"
    - Keep the MCP verification instructions (verify via MCP tools, per SENZING_INFORMATION_POLICY.md) unchanged
    - Do NOT modify the hook name, version, description, event type, toolTypes, or JSON structure
    - _Requirements: 2.4, 3.4_

  - [x] 3.5 Update `senzing-bootcamp/steering/hook-registry.md`
    - Mirror the updated prompt text for all four affected hooks in the registry
    - Update ONLY the `Prompt:` field for `capture-feedback`, `enforce-feedback-path`, `enforce-working-directory`, and `verify-senzing-facts`
    - Keep all hook ids, names, descriptions, event types, and toolTypes unchanged
    - Keep all non-affected hooks (ask-bootcamper, code-style-check, commonmark-validation, and all module hooks) completely unchanged
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.5, 3.6_

  - [x] 3.6 Add silent-processing rule to `senzing-bootcamp/steering/agent-instructions.md`
    - Add a new rule under the `## Hooks` section: "When a hook check passes with no action needed, produce no output. Do not acknowledge the check, do not explain your reasoning, do not print any status message. Only produce output when the hook requires corrective action."
    - Keep all existing content in agent-instructions.md unchanged
    - Do NOT modify any other section
    - _Requirements: 2.6, 3.5_

  - [x] 3.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Hook prompts contain explicit silent-processing instructions
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (all four hook prompts contain "produce no output" instructions)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 3.8 Verify preservation tests still pass
    - **Property 2: Preservation** - Action-required branches and non-affected hooks unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the full test suite (bug condition + preservation tests)
  - Ensure all tests pass, ask the user if questions arise
