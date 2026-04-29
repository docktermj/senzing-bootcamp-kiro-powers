# Tasks

## Task 1: Create test module with hook file loading and registry parsing utilities

- [x] 1.1 Create `tests/test_hook_prompt_standards.py` with module-level constants (`HOOKS_DIR`, `REGISTRY_PATH`, `EXPECTED_HOOK_COUNT`, `VALID_EVENT_TYPES`, `REQUIRED_FIELDS`, `FILE_EVENT_TYPES`, `TOOL_EVENT_TYPES`, `PASS_THROUGH_EVENT_TYPES`, `EXEMPT_FROM_CLOSING_QUESTION`) and implement `get_hook_files()` that returns all `.kiro.hook` file paths from `senzing-bootcamp/hooks/`
- [x] 1.2 Implement `load_hook_files()` that parses each `.kiro.hook` file as JSON and returns a list of `(filename, parsed_dict)` tuples, and implement `parse_registry(registry_path)` that extracts `RegistryEntry(id, name, description)` objects from `hook-registry.md` using regex to match `- id:`, `- name:`, and `- description:` lines
- [x] 1.3 Implement helper functions: `validate_required_fields(hook_data)` returning missing field names using dot-notation traversal, `validate_conditional_fields(hook_data)` returning error messages for missing `when.patterns` or `when.toolTypes` based on event type, `has_silent_processing(prompt)` returning bool, and `find_closing_question(prompt)` returning the matched phrase or None

## Task 2: Implement JSON structure validation tests (Requirement 1)

- [x] 2.1 Implement `TestJsonStructure` class with parameterized tests: `test_valid_json` (each hook file parses as JSON), `test_required_fields_present` (each hook has all required fields), `test_conditional_fields_file_events` (file-event hooks have non-empty `when.patterns`), `test_conditional_fields_tool_events` (tool-event hooks have non-empty `when.toolTypes`), `test_then_type_is_ask_agent` (every hook's `then.type` is `askAgent`), and `test_prompt_minimum_length` (every hook's `then.prompt` is at least 20 characters)
  _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

## Task 3: Implement silent-processing and closing-question tests (Requirements 2, 3)

- [x] 3.1 Implement `TestSilentProcessing` class with parameterized test: `test_pass_through_hooks_have_silent_instruction` that filters hooks with `when.type` in `PASS_THROUGH_EVENT_TYPES` and verifies each prompt contains a silent-processing phrase, with failure messages identifying the hook filename
  _Requirements: 2.1, 2.2_
- [x] 3.2 Implement `TestNoInlineClosingQuestions` class with parameterized test: `test_non_exempt_hooks_no_closing_questions` that filters hooks with `when.type` not in `EXEMPT_FROM_CLOSING_QUESTION` and verifies no prompt contains a closing-question phrase, with failure messages identifying the hook filename and matched phrase
  _Requirements: 3.1, 3.2, 3.3_

## Task 4: Implement registry synchronization tests (Requirement 4)

- [x] 4.1 Implement `TestRegistrySync` class with tests: `test_registry_entry_has_hook_file` (every registry id has a corresponding `{id}.kiro.hook` file), `test_hook_file_has_registry_entry` (every hook file has a corresponding registry entry), `test_name_matches` (name field matches between file and registry for each hook), and `test_description_matches` (description field matches between file and registry for each hook)
  _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

## Task 5: Implement hook count and event type validation tests (Requirements 5, 7)

- [x] 5.1 Implement `TestHookCount` class with tests: `test_hook_file_count` (exactly 18 `.kiro.hook` files exist) and `test_registry_entry_count` (exactly 18 registry entries exist), both with failure messages showing actual vs expected count
  _Requirements: 5.1, 5.2, 5.3_
- [x] 5.2 Implement `TestEventTypeValidation` class with tests: `test_valid_event_types_constant` (VALID_EVENT_TYPES contains all 10 expected types) and `test_all_hooks_use_valid_event_types` (every hook's `when.type` is in VALID_EVENT_TYPES, with failure messages identifying the hook and invalid type)
  _Requirements: 7.1, 7.2_

## Task 6: Verify CI integration requirements (Requirement 6)

- [x] 6.1 Run `pytest tests/test_hook_prompt_standards.py` and verify: all tests pass, execution completes within 10 seconds, failure messages include hook filenames, and the exit code is 0 for passing tests
  _Requirements: 6.1, 6.2, 6.3, 6.4_

## Task 7: Property-based tests (Hypothesis)

- [x] 7.1 Create `tests/test_hook_prompt_properties.py` with Hypothesis strategies for generating random hook-like dicts (with subsets of required fields, various event types, and random prompt strings) and random registry-like entry sets
- [x] 7.2 PBT: Property 1 — Required Fields Validation: for any JSON-like dict with a random subset of required fields present, the validator reports exactly the set of missing fields with no false positives or false negatives (Req 1.2)
- [x] 7.3 PBT: Property 2 — Conditional Field Validation: for any hook dict with a valid event type, file events require non-empty `when.patterns`, tool events require non-empty `when.toolTypes`, and other event types require neither (Req 1.3, 1.4)
- [x] 7.4 PBT: Property 3 — Prompt Minimum Length Validation: for any string, the prompt validator accepts it if and only if its length is at least 20 characters (Req 1.6)
- [x] 7.5 PBT: Property 4 — Silent-Processing Detection: for any prompt string, the detector returns true if and only if the string contains at least one recognized silent-processing phrase (Req 2.1)
- [x] 7.6 PBT: Property 5 — Closing-Question Exemption by Event Type: for any (event_type, prompt) pair, the closing-question check flags a failure if and only if the prompt contains a closing question AND the event type is not in the exempt set (Req 3.1, 3.2, 3.3)
- [x] 7.7 PBT: Property 6 — Bidirectional Registry-File Synchronization: for any pair of id sets (registry_ids, file_ids), the sync checker reports every id in the symmetric difference — no missing file or missing registry entry goes unreported (Req 4.2, 4.3)
- [x] 7.8 PBT: Property 7 — Registry Field Matching: for any hook present in both registry and file with random name/description pairs, the checker reports a mismatch if and only if the fields differ (Req 4.4, 4.5)
- [x] 7.9 PBT: Property 8 — Event Type Validation: for any string, the event type validator accepts it if and only if it is a member of the valid event types set (Req 7.1, 7.2)

## Task 8: Example-based unit tests for real hook files

- [x] 8.1 Unit test: all 18 real hook files parse as valid JSON (Req 1.1)
- [x] 8.2 Unit test: hook file count is exactly 18 and registry entry count is exactly 18 (Req 5.1, 5.2)
- [x] 8.3 Unit test: VALID_EVENT_TYPES constant contains all 10 expected event type strings (Req 7.1)
- [x] 8.4 Unit test: real pass-through hooks (`capture-feedback`, `enforce-feedback-path`, `enforce-working-directory`, `verify-senzing-facts`) contain silent-processing instructions (Req 2.1)
- [x] 8.5 Unit test: real non-exempt hooks do not contain inline closing questions (Req 3.1, 3.2)
- [x] 8.6 Unit test: registry names and descriptions match file names and descriptions for all 18 hooks (Req 4.4, 4.5)
