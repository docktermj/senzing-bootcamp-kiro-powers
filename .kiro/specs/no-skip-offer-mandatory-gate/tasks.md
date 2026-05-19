# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** — Agent generates a question offering to skip a ⛔ mandatory gate step
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **GOAL**: Surface counterexamples demonstrating that no steering rule or hook prevents the agent from offering to skip a ⛔ step
  - Bug Condition from design: `isBugCondition(X)` where `X.type = "question" AND X.referencesStep.hasMandatoryGate = true AND X.offersSkipOrBypass = true`
  - Test that `agent-instructions.md` Mandatory Gate Precedence section does NOT contain language prohibiting skip offers (only prohibits actual skips)
  - Test that `conversation-protocol.md` Self-Check section does NOT include a check for mandatory gate skip offers (only has 4 items)
  - Test that `module-03-system-verification.md` does NOT contain a "proceed directly" instruction before Step 9
  - Use Hypothesis to generate random question content with skip-offer patterns for mandatory vs non-mandatory steps
  - **EXPECTED OUTCOME**: Test FAILS (confirms the steering gap exists — no rule prevents skip offers)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** — Non-mandatory step questions unaffected
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Observe on UNFIXED code: questions about non-mandatory steps can offer skip options
  - Observe on UNFIXED code: questions that don't reference ⛔ steps are unaffected
  - Observe on UNFIXED code: `ask-bootcamper` hook generates closing questions normally
  - Write property-based tests with Hypothesis:
    - For all questions referencing non-⛔ steps, skip offers are permitted
    - For all questions not referencing any step, no validation fires
    - The conversation-protocol self-check passes for questions about non-mandatory steps
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - _Requirements: 3.1, 3.2, 3.4_

- [x] 3. Implement fix — prohibit skip offers for ⛔ mandatory gate steps

  - [x] 3.1 Add skip-offer prohibition to `agent-instructions.md` Mandatory Gate Precedence section
    - Add bullet: "NEVER offer to skip a ⛔ mandatory gate step. Do not ask 'would you like to continue with [step]?', 'or skip ahead?', 'or move on to the next module?' when the next step is a ⛔ mandatory gate. Instead, announce that you are proceeding to the step and execute it."
    - _Bug_Condition: No rule prevents the agent from offering to skip ⛔ steps_
    - _Expected_Behavior: Explicit prohibition prevents skip-offer questions for ⛔ steps_
    - _Preservation: Non-mandatory step questions unaffected_
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Add fifth self-check item to `conversation-protocol.md`
    - In the Self-Check section, add item 5: "Does any 👉 question offer to skip or bypass an upcoming ⛔ mandatory gate step?"
    - Update the "If any answer is yes" line to reference 5 checks
    - _Bug_Condition: Self-check does not validate question content against mandatory gates_
    - _Expected_Behavior: Agent self-checks for mandatory gate skip offers before sending_
    - _Preservation: Existing 4 self-checks unchanged; non-mandatory questions unaffected_
    - _Requirements: 2.2_

  - [x] 3.3 Add "proceed directly" instruction to `module-03-system-verification.md`
    - Before Step 9, add: "**Agent behavior:** After Step 8 completes, proceed DIRECTLY to Step 9. Do not ask whether the bootcamper wants to continue — Step 9 is mandatory and unconditional."
    - _Bug_Condition: No explicit instruction prevents the agent from asking about Step 9_
    - _Expected_Behavior: Agent proceeds to Step 9 without asking permission_
    - _Preservation: Steps 1-8 behavior unchanged; Step 9 execution unchanged_
    - _Requirements: 2.1, 2.3_

  - [x] 3.4 Verify bug condition exploration test now passes
    - Re-run the SAME test from task 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms the steering gap is closed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - Re-run the SAME tests from task 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.1, 3.2, 3.4_

- [x] 4. Update token counts and run validation suite
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to update token counts
  - Run `python3 senzing-bootcamp/scripts/validate_power.py` to confirm power structure valid
  - Run `python3 senzing-bootcamp/scripts/lint_steering.py` to confirm steering passes linting
  - Run `python3 -m pytest senzing-bootcamp/tests/ tests/ -v --tb=short` to confirm no regressions
  - Update any preservation test hashes that changed due to steering file edits
  - _Requirements: All_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 3, "tasks": ["3.4"] },
    { "id": 4, "tasks": ["3.5"] },
    { "id": 5, "tasks": ["4"] }
  ]
}
```

Task 1 (exploration test) must complete before task 2 (preservation tests). Tasks 3.1, 3.2, 3.3 can run in parallel after task 2. Task 3.4 depends on 3.1 + 3.2 + 3.3. Task 3.5 depends on 3.4. Task 4 depends on 3.5.

## Notes

- This spec complements `mandatory-visualization-gate` (which prevents agent-initiated skips) and `enforce-visualization-step` (which blocks completion without checkpoints). This spec prevents the agent from **offering** to skip.
- The fix is purely steering-based (no new hooks) because detecting "offers to skip a mandatory gate" requires semantic understanding of question content relative to module state — better handled as an internalized rule than a pattern-matching hook.
- The `ask-bootcamper` hook generates closing questions at agentStop — the new steering rule ensures those questions don't offer to skip upcoming ⛔ steps.
