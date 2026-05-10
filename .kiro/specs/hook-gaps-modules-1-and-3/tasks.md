# Tasks: Hook Gaps Modules 1 and 3

## Task 1: Create validate-business-problem hook file

- [x] 1.1 Create `senzing-bootcamp/hooks/validate-business-problem.kiro.hook` with valid JSON containing name "Validate Business Problem", version "1.0.0", description, when.type "postTaskExecution", then.type "askAgent", and then.prompt with validation instructions
- [x] 1.2 Ensure the prompt instructs the agent to read `config/bootcamp_progress.json` and check `current_module` is 1 before validating
- [x] 1.3 Ensure the prompt instructs the agent to verify data sources identified, matching criteria defined, and success metrics documented when module is 1
- [x] 1.4 Ensure the prompt instructs the agent to produce no output when module is not 1
- [x] 1.5 Ensure the prompt instructs the agent to report incomplete fields and confirm readiness for Module 2

## Task 2: Create verify-demo-results hook file

- [x] 2.1 Create `senzing-bootcamp/hooks/verify-demo-results.kiro.hook` with valid JSON containing name "Verify Demo Results", version "1.0.0", description, when.type "postTaskExecution", then.type "askAgent", and then.prompt with verification instructions
- [x] 2.2 Ensure the prompt instructs the agent to read `config/bootcamp_progress.json` and check `current_module` is 3 before verifying
- [x] 2.3 Ensure the prompt instructs the agent to confirm entities were resolved and matches were found when module is 3
- [x] 2.4 Ensure the prompt instructs the agent to produce no output when module is not 3
- [x] 2.5 Ensure the prompt instructs the agent to report singleton-only results and confirm successful demo completion

## Task 3: Update hook-categories.yaml

- [x] 3.1 Add module `1` entry with `validate-business-problem` in `senzing-bootcamp/hooks/hook-categories.yaml`
- [x] 3.2 Add module `3` entry with `verify-demo-results` in `senzing-bootcamp/hooks/hook-categories.yaml`
- [x] 3.3 Verify module keys remain in ascending numeric order (1, 2, 3, 4, 5, ...)

## Task 4: Regenerate hook registry

- [x] 4.1 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --write` to regenerate `hook-registry.md`
- [x] 4.2 Update `EXPECTED_HOOK_COUNT` in `tests/test_hook_prompt_standards.py` from 23 to 25

## Task 5: Write example-based unit tests

- [x] 5.1 Create `tests/test_hook_gaps_modules_1_and_3.py` with tests verifying both hook files parse as valid JSON with correct field values
- [x] 5.2 Add tests verifying prompt content for validate-business-problem (module guard, data sources, matching criteria, success metrics, incomplete field reporting, readiness confirmation)
- [x] 5.3 Add tests verifying prompt content for verify-demo-results (module guard, entities resolved, matches found, singleton reporting, success confirmation)
- [x] 5.4 Add tests verifying hook-categories.yaml contains module 1 and module 3 entries with correct hook IDs
- [x] 5.5 Add test verifying total hook count is 25

## Task 6: Write property-based tests

- [x] 6.1 Create `tests/test_hook_gaps_modules_1_and_3_properties.py` with Property 1: For any module number 1–11, hook-categories.yaml lists at least one hook
- [x] 6.2 Add Property 2: For any hook ID in the modules section of hook-categories.yaml, a corresponding .kiro.hook file exists
- [x] 6.3 Add Property 3: For any .kiro.hook file, it parses as valid JSON with all required fields and valid event/action types

## Task 7: Run tests and verify

- [x] 7.1 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` and confirm exit code 0
- [x] 7.2 Run `pytest tests/test_hook_gaps_modules_1_and_3.py tests/test_hook_gaps_modules_1_and_3_properties.py -v` and confirm all tests pass
- [x] 7.3 Run `pytest tests/test_hook_prompt_standards.py -v` and confirm existing hook validation passes with new hooks included
