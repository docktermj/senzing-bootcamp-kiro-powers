# Tasks: Hook Self-Test Mode

## Task 1: Create test_hooks.py script

- [x] 1.1 Create `senzing-bootcamp/scripts/test_hooks.py` with argparse CLI accepting `--hook`, `--categories`, and `--verbose` flags
- [x] 1.2 Implement hook file discovery: find all `.kiro.hook` files in `senzing-bootcamp/hooks/`
- [x] 1.3 Implement JSON parsing check: attempt `json.loads()` on each file, capture parse errors
- [x] 1.4 Implement required field validation: check for `name`, `version`, `when.type`, `then.type`
- [x] 1.5 Implement event type validation: verify `when.type` is in the set of valid event types
- [x] 1.6 Implement action type validation: verify `then.type` is "askAgent" or "runCommand"
- [x] 1.7 Implement prompt/command presence check: askAgent hooks need non-empty `then.prompt`, runCommand hooks need non-empty `then.command`

## Task 2: Implement pattern and toolType validation

- [x] 2.1 For file-event hooks (fileEdited, fileCreated, fileDeleted): validate that `when.patterns` exists and contains valid glob patterns
- [x] 2.2 For tool-event hooks (preToolUse, postToolUse): validate that `when.toolTypes` exists and each entry is either a valid category or a compilable regex
- [x] 2.3 Implement glob validation: check for basic structural validity (no unbalanced brackets)
- [x] 2.4 Implement regex validation: attempt `re.compile()` on non-category toolType entries

## Task 3: Implement registry consistency check

- [x] 3.1 Parse `senzing-bootcamp/steering/hook-registry.md` to extract hook IDs mentioned in the registry
- [x] 3.2 Compare hook file IDs against registry IDs
- [x] 3.3 Report hooks in files but not in registry (orphaned hooks)
- [x] 3.4 Report hooks in registry but without files (stale registry entries)

## Task 4: Implement output formatting

- [x] 4.1 Implement summary table output: ID, event type, action type, status (PASS/FAIL)
- [x] 4.2 For failed hooks, show indented failure reason below the entry
- [x] 4.3 Implement `--verbose` mode: show full prompt/command text for each hook
- [x] 4.4 Implement `--categories` filter: read `hook-categories.yaml`, filter hooks by category membership
- [x] 4.5 Implement `--hook` filter: test only the specified hook ID
- [x] 4.6 Set exit code: 0 if all pass, 1 if any fail

## Task 5: Write tests

- [x] 5.1 Create `senzing-bootcamp/tests/test_hook_self_test.py`
- [x] 5.2 Unit test: script accepts --hook, --categories, --verbose flags without error
- [x] 5.3 Unit test: valid hook file with all required fields passes all checks
- [x] 5.4 Unit test: hook with missing `when.type` field is detected as failure
- [x] 5.5 Unit test: hook with invalid event type (e.g., "invalidEvent") is detected
- [x] 5.6 Unit test: askAgent hook with empty prompt is detected
- [x] 5.7 Unit test: file-event hook without `when.patterns` is detected
- [x] 5.8 Unit test: toolType with invalid regex is detected
- [x] 5.9 Property test: any JSON object with all required fields and valid values passes structural checks
- [x] 5.10 Unit test: registry consistency detects missing entries in both directions

## Task 6: Validate

- [x] 6.1 Run `python3 senzing-bootcamp/scripts/test_hooks.py` against actual hook files and confirm all pass
- [x] 6.2 Run `pytest senzing-bootcamp/tests/test_hook_self_test.py -v`
- [x] 6.3 Verify exit code is 0 when all hooks are valid
