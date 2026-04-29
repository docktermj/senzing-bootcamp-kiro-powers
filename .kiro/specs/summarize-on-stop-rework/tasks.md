# Tasks

## Task 1: Create the new ask-bootcamper hook file
- [x] 1.1 Create `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` with name "Ask Bootcamper", description reflecting the new behavior, event type `agentStop`, action type `askAgent`, and the new structured prompt
- [x] 1.2 Delete the old `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook` file

## Task 2: Update the hook registry
- [x] 2.1 Replace the `summarize-on-stop` entry in `senzing-bootcamp/steering/hook-registry.md` with an `ask-bootcamper` entry using the new id, name, description, and prompt (prompt must match hook file exactly)
- [x] 2.2 Verify the old `summarize-on-stop` entry is fully removed from the registry

## Task 3: Update agent instructions steering file
- [x] 3.1 Update the Communication section in `senzing-bootcamp/steering/agent-instructions.md` to add the closing-question ownership rule: agent must not end turns with closing questions, `ask-bootcamper` hook owns all closing questions
- [x] 3.2 Ensure the existing 👉 prefix rule is preserved and consistent with the new closing-question ownership rule

## Task 4: Create the new test suite
- [x] 4.1 Create `senzing-bootcamp/tests/test_ask_bootcamper_hook.py` with property-based tests validating: hook metadata, prompt recap instructions, 👉 question instructions, no-op skip instructions, registry-hook prompt match, and old hook removal
- [x] 4.2 Delete the old `senzing-bootcamp/tests/test_summarize_on_stop_hook.py` file
- [x] 4.3 Run the new test suite and verify all tests pass
