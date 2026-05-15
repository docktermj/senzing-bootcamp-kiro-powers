# Implementation Tasks: forward-moving-questions

## Task 1: Update commonmark-validation hook to include forward-moving question instruction

- [x] Update the `then.prompt` field in `senzing-bootcamp/hooks/commonmark-validation.kiro.hook` to append instructions for concluding with a brief recap and a contextual 👉 forward-moving question after fixes are applied
- [x] Include instruction to check `config/bootcamp_progress.json` for current module/step context
- [x] Include instruction to output nothing and proceed silently when no issues are found
- [x] Validate the hook JSON remains well-formed (required fields: name, version, when, then)

## Task 2: Update ask-bootcamper hook no-op clause to treat file edits as substantive

- [x] Modify the Phase 1 no-op clause in `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` to remove the ambiguous "(e.g., only a hook fired)" parenthetical
- [x] Replace with explicit logic: if files were edited (even by hook-triggered action), that IS substantive work — provide a closing question unless a 👉 is already present
- [x] Validate the hook JSON remains well-formed (required fields: name, version, when, then)

## Task 3: Add Choice Formatting section to conversation-protocol.md

- [x] Insert a new "## Choice Formatting" section in `senzing-bootcamp/steering/conversation-protocol.md` after the "One Question Rule" section
- [x] Include rule: when a 👉 question presents 2+ distinct alternatives, format as a numbered list
- [x] Include WRONG example (inline prose with "or" between options)
- [x] Include CORRECT example (numbered list of options)
- [x] Include exception: simple yes/no questions remain as inline prose (with CORRECT example)

## Task 4: Run validation suite

- [x] Run `python3 senzing-bootcamp/scripts/validate_power.py` to confirm power structure is valid
- [x] Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` to confirm hook registry is consistent
- [x] Run `pytest` to confirm no regressions in existing tests
