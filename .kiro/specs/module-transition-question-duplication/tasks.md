# Implementation Plan

## Task Dependency Graph

```
1 (Bug Condition Exploration Test)
│
2 (Preservation Property Tests)
│
3 (Implement Fix)
├── 3.1 Edit module-completion-next-steps.md
├── 3.2 Edit module-completion.md
├── 3.3 Edit module-transitions.md
├── 3.4 Edit ask-bootcamper.json (Phase 1 / Phase 1.5)
├── 3.5 Re-sync composed hook prompts + registry
├── 3.6 Verify exploration test passes
└── 3.7 Verify preservation tests pass
│
4 (Checkpoint)
```

Tasks 1 and 2 run on UNFIXED code. Task 3 implements the fix and verifies both
test suites pass after.

---

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** — The module-transition question can be rendered more than once in a completion turn
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the missing "render the transition question exactly once" guidance in the unfixed steering files
  - **Scoped PBT Approach**: Parse the target steering files and assert the required "render-once" / de-duplication content patterns
  - Test file: `tests/test_module_transition_question_duplication_bug.py`
  - Test that `senzing-bootcamp/steering/module-completion-next-steps.md` states the forward "Ready to move on to Module N?" prompt and the final-message 👉 transition question are the SAME question rendered exactly once (not two separate prompts)
  - Test that `senzing-bootcamp/steering/module-completion.md` Final-Message Ordering carries an explicit "render exactly once" clause for the forward transition question
  - Test that `senzing-bootcamp/steering/module-transitions.md` states the module-transition question is presented to the bootcamper exactly once per turn
  - Test that the `senzing-bootcamp/hooks/ask-bootcamper.json` Phase 1 / Phase 1.5 guidance recognizes an already-present inline transition prompt and does not add or leave a second copy
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the render-once guidance is missing)
  - Document counterexamples found (e.g., "module-completion-next-steps.md lists the Proceed prompt and separately requires the forward 👉 question as the final message with no same-question note")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 3: Preservation** — Non-Target Steering Files and Completion Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Test file: `tests/test_module_transition_question_duplication_preservation.py`
  - Observe: the fixed set edits only `module-completion-next-steps.md`, `module-completion.md`, `module-transitions.md`, and `ask-bootcamper.json` (plus the regenerated hook-registry mirror + lockfile)
  - Write property-based test: for all non-target steering files in `senzing-bootcamp/steering/`, file content is byte-identical before and after the fix (frozen SHA-256 snapshot comparison, excluding the edited files)
  - Write structural assertions that the edited files retain their non-target anchors:
    - `module-completion.md`: the fixed completion step order, the Shared Boundary-Detection Trigger rules, the defer-when-pending / no-op rules
    - `module-completion-next-steps.md`: the next-step options set (Proceed, Iterate, Explore, Undo, Share) and the ⛔ Immediate Execution rule
    - `module-transitions.md`: the Confirmation Response Requirements table and the ascending-numeric-order sequencing rule
    - `ask-bootcamper.json`: the `Stop` trigger and `agent` action type are unchanged; Phases 0, 2, 3, 4 are unchanged
  - Write structural assertion: the `config/.question_pending` lifecycle rules (write-policy-gate validation, treat-as-answer, delete-and-process) remain referenced and unchanged
  - Verify tests pass on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3. Fix so the module-transition question renders exactly once per turn

  - [x] 3.1 Edit `senzing-bootcamp/steering/module-completion-next-steps.md` — Same-question / render-once note
    - State that the "Proceed: Ready to move on to Module [N]?" prompt and the final-message 👉 transition question are the SAME question rendered exactly once
    - When the forward question is the final message, do not also render it as a separate inline "Proceed" 👉 line; when a recap/confirmation precedes it, the transition question appears a single time as the final message
    - Add a de-duplication note: the turn contains exactly one rendered forward transition 👉 question, matching the single `config/.question_pending` marker written for it
    - _Bug_Condition: isBugCondition(input) where input.isModuleCompletionTurn AND transition_question_count > 1_
    - _Expected_Behavior: One rendered forward transition 👉 question per completion turn_
    - _Preservation: Next-step options set and ⛔ Immediate Execution unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [x] 3.2 Edit `senzing-bootcamp/steering/module-completion.md` — Render-once clause in Final-Message Ordering
    - Add an explicit "render exactly once" clause: the forward transition 👉 question appears a single time in the turn; the "re-surface after recap/confirmation" path replaces (does not duplicate) any earlier inline rendering of the same question
    - _Bug_Condition: Final-Message Ordering describes ordering but not a single rendering_
    - _Expected_Behavior: Final-Message Ordering requires exactly one rendered transition question_
    - _Preservation: Completion step order and trigger rules unchanged_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Edit `senzing-bootcamp/steering/module-transitions.md` — Single transition prompt statement
    - Add a short statement (Module Completion / Transition Integrity): at a module-completion boundary the forward transition question is presented to the bootcamper exactly once per turn
    - _Bug_Condition: No single-prompt statement at the transition boundary_
    - _Expected_Behavior: One transition prompt per turn_
    - _Preservation: Confirmation Response Requirements and sequencing rules unchanged_
    - _Requirements: 2.1, 2.5_

  - [x] 3.4 Edit `senzing-bootcamp/hooks/ask-bootcamper.json` — Recognize an already-present inline transition prompt (Phase 1 / Phase 1.5)
    - Strengthen the Phase 1 already-present-question detection so a forward transition prompt that is present but phrased inline (without a leading 👉) is recognized and NOT supplemented with a second closing 👉 transition question
    - Extend Phase 1.5 (or Phase 1) to collapse a duplicate transition prompt — an inline prose copy paired with a single 👉 line — down to exactly one 👉 transition question, reusing the existing silent self-correction pattern
    - _Bug_Condition: isBugCondition(input) where the transition question is present inline and Phase 1 adds/leaves a second copy_
    - _Expected_Behavior: Exactly one 👉 transition question after Phase 1 / Phase 1.5_
    - _Preservation: Phases 0, 2, 3, 4 and the hook trigger/action type unchanged_
    - _Requirements: 2.4_

  - [x] 3.5 Re-sync composed hook prompts and the hook registry
    - Run `python3 senzing-bootcamp/scripts/compose_hook_prompts.py --write`
    - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write`
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to refresh steering token counts for the edited steering files
    - _Preservation: Mirror docs and lockfile stay in sync (CI verifies both)_
    - _Requirements: 2.4_

  - [x] 3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** — Transition question rendered exactly once
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - Run: `pytest tests/test_module_transition_question_duplication_bug.py -v`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.7 Verify preservation tests still pass
    - **Property 3: Preservation** — Non-Target Steering Files and Completion Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run: `pytest tests/test_module_transition_question_duplication_preservation.py -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4. Checkpoint — Ensure all tests and CI gates pass
  - Run the two spec test files: `pytest tests/test_module_transition_question_duplication_bug.py tests/test_module_transition_question_duplication_preservation.py -v`
  - Run the affected CI gates: `python3 senzing-bootcamp/scripts/compose_hook_prompts.py --verify`, `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`, `python3 senzing-bootcamp/scripts/measure_steering.py --check`, `python3 senzing-bootcamp/scripts/validate_governance_rules.py`
  - Verify no other tests in the repo are broken by the steering/hook edits: `python3 -m pytest senzing-bootcamp/tests/ tests/`
  - If any preservation snapshot pins the edited files' bytes/token counts, re-baseline them observation-first with an explanatory note
  - Ensure all tests pass; ask the user if questions arise
