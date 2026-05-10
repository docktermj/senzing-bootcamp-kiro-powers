# Tasks

## Task 1: Create shared helper module

- [x] 1.1 Create `tests/hook_test_helpers.py` with constants: `HOOKS_DIR`, `CATEGORIES_PATH`, `VALID_EVENT_TYPES`, `REQUIRED_FIELDS`, `FILE_EVENT_TYPES`, `TOOL_EVENT_TYPES`, `CRITICAL_HOOKS` (7 identifiers), `SEMVER_PATTERN`
- [x] 1.2 Implement `get_hook_files()`, `load_hook()`, `load_all_hooks()` functions for loading hook JSON files
- [x] 1.3 Implement `parse_categories_yaml()` — custom minimal YAML parser for hook-categories.yaml (no PyYAML dependency)
- [x] 1.4 Implement `validate_required_fields()`, `validate_conditional_fields()`, `validate_event_type()`, `validate_version()` validator functions
- [x] 1.5 Implement `has_silent_processing()` helper for detecting silent processing instructions in prompts
- [x] 1.6 Implement Hypothesis strategies: `st_valid_hook()`, `st_valid_semver()`, `st_invalid_semver()`, `st_markdown_path()`, `st_non_markdown_path()`

## Task 2: Create structural validation tests for all 25 hooks

- [x] 2.1 Create `tests/test_hook_structural_validation.py` with `TestHookJsonStructure` class — parametrized tests verifying all 25 hooks parse as valid JSON and contain required fields (Req 2.1, 2.2)
- [x] 2.2 Add `TestHookEventTypes` class — verify every hook's `when.type` is a valid Event_Type (Req 2.3)
- [x] 2.3 Add `TestHookPromptLength` class — verify every hook's `then.prompt` is non-empty with at least 20 characters (Req 2.4)
- [x] 2.4 Add `TestHookConditionalFields` class — verify file-event hooks have `when.patterns` and tool-event hooks have `when.toolTypes` (Req 2.5, 2.6)
- [x] 2.5 Add `TestHookVersionFormat` class — verify version matches semver format with no leading zeros (Req 2.7, 7.1, 7.3)
- [x] 2.6 Add `TestHookCount` class — verify exactly 25 `.kiro.hook` files exist (Req 2.8)

## Task 3: Create prompt logic tests for critical hooks

- [x] 3.1 Create `tests/test_hook_prompt_logic.py` with `TestVerifySenzingFacts` class — verify prompt references at least one MCP tool name (Req 3.1)
- [x] 3.2 Add `TestEnforceWorkingDirectory` class — verify prompt references at least one forbidden path pattern (Req 3.2)
- [x] 3.3 Add `TestReviewBootcamperInput` class — verify prompt contains at least 3 feedback trigger phrases (Req 3.3)
- [x] 3.4 Add `TestEnforceFeedbackPath` class — verify prompt contains canonical feedback file path (Req 3.4)
- [x] 3.5 Add `TestCodeStyleCheck` class — verify prompt references at least one coding standard (Req 3.5)
- [x] 3.6 Add `TestCommonmarkValidation` class — verify prompt references at least one CommonMark rule identifier (Req 3.6)
- [x] 3.7 Add `TestAskBootcamper` class — verify prompt contains `.question_pending` reference and closing question emoji (Req 3.7)
- [x] 3.8 Add `TestCriticalHookSilentProcessing` class — verify preToolUse/promptSubmit critical hooks contain silent processing instruction (Req 3.8)

## Task 4: Create hook categories synchronization tests

- [x] 4.1 Create `tests/test_hook_categories_sync.py` with `TestCategoriesFileToHookFiles` class — verify every YAML entry has a corresponding `.kiro.hook` file (Req 4.1)
- [x] 4.2 Add `TestHookFilesToCategoriesFile` class — verify every `.kiro.hook` file appears in exactly one category (Req 4.2)
- [x] 4.3 Add `TestCategoriesCounts` class — verify critical category has 7 entries and total count matches file count (Req 4.3, 4.4)
- [x] 4.4 Add `TestCategoriesUniqueness` class — verify no hook identifier appears in more than one category (Req 4.5)

## Task 5: Create property-based validator tests

- [x] 5.1 Create `tests/test_hook_validator_properties.py` with `TestValidHookAcceptance` class — Property 1: generated valid hooks pass validator with zero errors (Req 5.1)
- [x] 5.2 Add `TestMissingFieldDetection` class — Property 2: removing one required field reports exactly that field (Req 5.2)
- [x] 5.3 Add `TestInvalidEventTypeDetection` class — Property 3: invalid event type strings are rejected (Req 5.3)
- [x] 5.4 Add `TestConditionalFieldValidation` class — Property 4: missing patterns/toolTypes for conditional event types produce errors (Req 5.4, 5.5)
- [x] 5.5 Add `TestVersionFormatValidation` class — Property 5: version validator accepts valid semver and rejects invalid formats (Req 7.2)
- [x] 5.6 Add `TestMarkdownGlobMatching` class — Property 6: markdown paths match hook glob, non-markdown paths don't (Req 1.6)
- [x] 5.7 Ensure all property tests use `@settings(max_examples=100)` and include docstrings with property tag format (Req 5.6, 6.5)

## Task 6: Integration verification

- [x] 6.1 Run `pytest tests/test_hook_structural_validation.py` and verify all tests pass
- [x] 6.2 Run `pytest tests/test_hook_prompt_logic.py` and verify all tests pass
- [x] 6.3 Run `pytest tests/test_hook_categories_sync.py` and verify all tests pass
- [x] 6.4 Run `pytest tests/test_hook_validator_properties.py` and verify all property tests pass
- [x] 6.5 Run `pytest tests/` and verify the full test suite passes without errors alongside existing tests (Req 6.6)
