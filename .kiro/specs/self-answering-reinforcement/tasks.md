# Tasks: Self-Answering Reinforcement

## Task 1: Add "Human:" to forbidden patterns in agent-instructions.md

- [x] 1.1 Read the current Communication section of `senzing-bootcamp/steering/agent-instructions.md`
- [x] 1.2 Add a forbidden output patterns rule: "FORBIDDEN output patterns: never generate text beginning with 'Human:', 'User:', or any text that simulates a bootcamper response. This is a critical violation."
- [x] 1.3 Verify the addition doesn't push agent-instructions.md over 95 lines

## Task 2: Add 🛑 STOP markers to onboarding-flow.md

- [x] 2.1 Read `senzing-bootcamp/steering/onboarding-flow.md` and identify all 👉 questions
- [x] 2.2 For each 👉 question that doesn't already have a 🛑 STOP within 2 lines after it, add: "🛑 STOP — Wait for bootcamper response."
- [x] 2.3 Verify the additions don't break the existing test expectations (update test baselines if needed)

## Task 3: Add 🛑 STOP markers to module-01-business-problem.md

- [x] 3.1 Read `senzing-bootcamp/steering/module-01-business-problem.md` and identify confirmation questions (e.g., "Does that sound right?")
- [x] 3.2 Add 🛑 STOP markers after confirmation questions that lack them
- [x] 3.3 Check phase files (`module-01-phase2-document-confirm.md`) for the same pattern

## Task 4: Add anti-fabrication instruction to ask-bootcamper hook

- [x] 4.1 Add to the `ask-bootcamper.kiro.hook` prompt: "CRITICAL: NEVER generate text beginning with 'Human:' or any text that represents what the bootcamper might say."
- [x] 4.2 Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write` to update registry
- [x] 4.3 Verify hook file remains valid JSON

## Task 5: Write tests

- [x] 5.1 Create `senzing-bootcamp/tests/test_self_answering_reinforcement.py`
- [x] 5.2 Unit test: agent-instructions.md contains "Human:" in forbidden patterns
- [x] 5.3 Unit test: onboarding-flow.md has 🛑 STOP within 3 lines of every 👉 question (excluding code blocks)
- [x] 5.4 Unit test: ask-bootcamper hook contains anti-fabrication instruction mentioning "Human:"
- [x] 5.5 Property test (Hypothesis): for all steering files with 👉 questions outside code blocks, a 🛑 STOP marker exists within 3 non-blank lines

## Task 6: Validate

- [x] 6.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified files
- [x] 6.2 Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify`
- [x] 6.3 Run `python3 senzing-bootcamp/scripts/test_hooks.py`
- [x] 6.4 Run `pytest senzing-bootcamp/tests/test_self_answering_reinforcement.py -v`
- [x] 6.5 Run the full test suite to confirm no regressions
