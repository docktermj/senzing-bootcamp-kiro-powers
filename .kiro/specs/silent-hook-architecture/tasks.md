# Tasks: Silent Hook Architecture Fix

## Task 1: Update ask-bootcamper hook prompt

- [x] 1.1 Read the current `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` prompt
- [x] 1.2 Replace the opening "PRODUCE NO OUTPUT. YOUR OUTPUT IS EMPTY. ZERO TOKENS. DO NOT GENERATE ANY TEXT." block with: "DEFAULT OUTPUT: .\nIf BOTH phases below produce no output, your COMPLETE response is a single period character: .\nDo NOT explain your reasoning. Do NOT describe condition checks. Just output: ."
- [x] 1.3 Replace the Phase 1 failure instruction "PRODUCE NO PHASE 1 OUTPUT" with "Phase 1 output: none (continue to Phase 2)"
- [x] 1.4 Replace the Phase 2 failure instruction "produce no Phase 2 output. STOP." with "Phase 2 output: none"
- [x] 1.5 Verify the hook file remains valid JSON after modification

## Task 2: Update hook registry

- [x] 2.1 Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write` to regenerate hook-registry.md from the updated hook file
- [x] 2.2 Verify `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` passes

## Task 3: Write tests

- [x] 3.1 Create or update `senzing-bootcamp/tests/test_silent_hook_architecture.py`
- [x] 3.2 Unit test: ask-bootcamper hook prompt contains "DEFAULT OUTPUT: ." instruction
- [x] 3.3 Unit test: ask-bootcamper hook prompt does NOT contain "PRODUCE NO OUTPUT" or "ZERO TOKENS"
- [x] 3.4 Unit test: hook file is valid JSON with all required fields
- [x] 3.5 Unit test: hook-registry.md entry for ask-bootcamper matches the hook file prompt

## Task 4: Validate

- [x] 4.1 Run `python3 senzing-bootcamp/scripts/test_hooks.py --hook ask-bootcamper` to verify structural validity
- [x] 4.2 Run `pytest senzing-bootcamp/tests/test_silent_hook_architecture.py -v`
- [x] 4.3 Run `pytest senzing-bootcamp/tests/test_ask_bootcamper_hook.py -v` to confirm no regressions
