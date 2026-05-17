# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Mandatory Gate Step Advancement Without Checkpoint
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the agent can advance past a ⛔ mandatory gate step without enforcement
  - **Scoped PBT Approach**: Scope the property to concrete failing cases — step advancement writes to `bootcamp_progress.json` that set `current_step` past a ⛔ mandatory gate step (e.g., Step 9) when no corresponding checkpoint exists
  - Bug Condition from design: `isBugCondition(input)` where `input.step.hasMandatoryGate = true AND input.action = "skip" AND input.initiator = "agent" AND input.bootcamperRequestedSkip = false`
  - Test that `validate_mandatory_gates.py` detects a progress state where `current_step > 9` but no `web_service` or `web_page` checkpoint exists for Step 9
  - Test that the `enforce-mandatory-gate.kiro.hook` prompt instructs blocking when step advancement skips a ⛔ gate without checkpoint evidence
  - Use Hypothesis to generate random progress states satisfying the bug condition (mandatory gate step skipped, no checkpoint, agent-initiated)
  - Run test on UNFIXED code — expect FAILURE (no enforcement hook exists yet, no validation script exists yet)
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the enforcement gap exists)
  - Document counterexamples found (e.g., "current_step=10 with no Step 9 checkpoint passes validation on unfixed code")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Mandatory Step Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Observe on UNFIXED code: bootcamper-initiated skips of non-⛔ steps proceed normally (skip recorded, consequences assessed, step advanced)
  - Observe on UNFIXED code: bootcamper-initiated skip attempts on ⛔ steps are refused with help offered
  - Observe on UNFIXED code: non-mandatory steps execute normally without interference
  - Observe on UNFIXED code: context budget management operates independently of step skip logic
  - Write property-based tests with Hypothesis:
    - For all non-mandatory steps (no ⛔ marker), the validation script reports no violation regardless of checkpoint state
    - For all steps where `current_step` advances past a non-⛔ step, no enforcement fires
    - For all bootcamper-initiated skip entries in `skipped_steps`, the validation script treats them as legitimate
    - For progress states where all ⛔ mandatory gate checkpoints exist, validation passes regardless of other state
  - Verify tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior that must not regress)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for mandatory gate enforcement — agent self-initiated skip of ⛔ steps

  - [x] 3.1 Strengthen mandatory gate language in `module-03-system-verification.md`
    - Replace current ⛔ annotation on Step 9 with explicit, unambiguous prohibition block
    - Use imperative language: "NEVER skip", "UNCONDITIONAL execution requirement"
    - Explicitly list prohibited rationalizations: session length, context budget, perceived redundancy
    - Add "NEVER" clause making the rule absolute
    - _Bug_Condition: isBugCondition(input) where input.step.hasMandatoryGate = true AND input.action = "skip" AND input.initiator = "agent"_
    - _Expected_Behavior: Agent executes ⛔ step unconditionally — result.action = "execute" AND result.stepCompleted = true_
    - _Preservation: Non-mandatory steps and bootcamper-initiated skips unaffected by language changes_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 Add mandatory gate precedence rule in `agent-instructions.md`
    - Add dedicated subsection under Agent Rules stating mandatory gates take absolute precedence over context budget, session length, and all agent-internal reasoning
    - Reference ⛔ symbol as the marker
    - Cross-reference skip-step-protocol.md constraint
    - _Bug_Condition: Agent deprioritizes ⛔ rule when reasoning about session constraints_
    - _Expected_Behavior: ⛔ rule explicitly stated as highest-priority, overriding all other considerations_
    - _Preservation: All other agent rules remain unchanged_
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Create `enforce-mandatory-gate.kiro.hook` (preToolUse hook)
    - Create new hook file at `senzing-bootcamp/hooks/enforce-mandatory-gate.kiro.hook`
    - Hook fires on write operations to `config/bootcamp_progress.json`
    - When write advances `current_step` past a ⛔ mandatory gate step, check whether corresponding checkpoint exists
    - If checkpoint missing and no `skipped_steps` entry exists for that step, block the write
    - Instruct agent to go back and execute the mandatory gate step
    - Hook JSON must have `name`, `version`, `when`, `then` fields per security rules
    - Hook prompt must not contain instructions that bypass security checks
    - _Bug_Condition: No proactive enforcement mechanism exists — agent can advance past ⛔ step without blocking_
    - _Expected_Behavior: Hook blocks step advancement past mandatory gate when checkpoint is missing_
    - _Preservation: Hook does not fire for non-mandatory steps or when checkpoints exist_
    - _Requirements: 2.1, 2.2, 2.3, 3.3_

  - [x] 3.4 Create `validate_mandatory_gates.py` validation script
    - Create new script at `senzing-bootcamp/scripts/validate_mandatory_gates.py`
    - Python 3.11+, stdlib only (no third-party deps)
    - Include `main()` entry point with argparse CLI
    - Parse steering files for ⛔ mandatory gate markers
    - Cross-reference against `config/bootcamp_progress.json` checkpoint entries
    - Report any mandatory gate steps skipped without corresponding checkpoint
    - Handle edge cases: no progress file, empty progress, partial checkpoints
    - Exit code 0 on pass, non-zero on violation (for CI integration)
    - _Bug_Condition: No validation layer exists to detect mandatory gate violations at CI time_
    - _Expected_Behavior: Script detects and reports missing checkpoints for ⛔ steps_
    - _Preservation: Script produces no false positives for non-mandatory steps or completed mandatory steps_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.5 Reinforce mandatory gate constraint in `skip-step-protocol.md`
    - Add explicit language in Constraints section: agent itself can NEVER initiate a skip of a mandatory gate step
    - Clarify that only the bootcamper can attempt it (and the protocol refuses)
    - Add cross-reference to the new `enforce-mandatory-gate.kiro.hook`
    - _Bug_Condition: Skip-step protocol lacks explicit statement that agent cannot self-initiate skips of ⛔ steps_
    - _Expected_Behavior: Protocol explicitly states agent cannot initiate mandatory gate skips_
    - _Preservation: Bootcamper-initiated skip handling for non-mandatory steps unchanged; mandatory gate refusal unchanged_
    - _Requirements: 2.2, 2.3, 3.1, 3.2_

  - [x] 3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Mandatory Gate Enforcement Active
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (validation script detects violations, hook blocks advancement)
    - When this test passes, it confirms the enforcement mechanisms work correctly
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed — enforcement now catches mandatory gate violations)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Mandatory Step Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — non-mandatory steps, bootcamper skips, context management all unaffected)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint — Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/ tests/ -v`
  - Verify bug condition exploration test passes (Property 1)
  - Verify preservation property tests pass (Property 2)
  - Verify `validate_mandatory_gates.py` integrates with CI pipeline
  - Verify `enforce-mandatory-gate.kiro.hook` JSON schema is valid
  - Ensure no regressions in existing test suite
  - Ask the user if questions arise
