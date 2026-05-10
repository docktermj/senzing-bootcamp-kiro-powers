# Tasks: Auto-Load Error Recovery Context

## Task 1: Create error-recovery-context hook file

- [x] 1.1 Create `senzing-bootcamp/hooks/error-recovery-context.kiro.hook` with valid JSON containing name "Auto-Load Error Recovery Context", version "1.0.0", description summarizing shell failure detection and pitfalls/recovery consultation, when.type "postToolUse", when.toolTypes ["shell"], then.type "askAgent", and then.prompt with full error recovery instructions
- [x] 1.2 Ensure the prompt instructs the agent to check exit code and produce no output when exit code is zero
- [x] 1.3 Ensure the prompt instructs the agent to check `config/bootcamp_progress.json` exists and produce no output if missing
- [x] 1.4 Ensure the prompt instructs the agent to extract error message, exit code, and command context from the tool result
- [x] 1.5 Ensure the prompt instructs the agent to read `senzing-bootcamp/steering/common-pitfalls.md` and `senzing-bootcamp/steering/recovery-from-mistakes.md` on non-zero exit
- [x] 1.6 Ensure the prompt instructs the agent to scope pitfall lookup to the current module section first, then fall back to General Pitfalls and Troubleshooting by Symptom
- [x] 1.7 Ensure the prompt instructs the agent to present only the matching fix with section citation and specific command/action when a known solution is found
- [x] 1.8 Ensure the prompt instructs the agent to fall back to normal troubleshooting when no known solution matches
- [x] 1.9 Ensure the prompt instructs the agent to use `explain_error_code` from the Senzing MCP server when the error contains a SENZ error code prefix
- [x] 1.10 Ensure the prompt instructs the agent to present the most specific match when multiple pitfalls could apply

## Task 2: Update hook-categories.yaml

- [x] 2.1 Add `error-recovery-context` to the `any` list under `modules` in `senzing-bootcamp/hooks/hook-categories.yaml`
- [x] 2.2 Maintain alphabetical order in the `any` list (backup-project-on-request, error-recovery-context, git-commit-reminder)
- [x] 2.3 Verify all existing entries remain unchanged (no removals or reorderings of other hooks)

## Task 3: Regenerate hook registry

- [x] 3.1 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --write` to regenerate `hook-registry.md`
- [x] 3.2 Update `EXPECTED_HOOK_COUNT` in `tests/test_hook_prompt_standards.py` from 23 to 24

## Task 4: Write example-based unit tests

- [x] 4.1 Create `tests/test_auto_load_error_recovery.py` with tests verifying the hook file parses as valid JSON with correct field values (name, version, description, when.type, when.toolTypes, then.type)
- [x] 4.2 Add tests verifying prompt contains silent-processing instructions for exit code zero and missing progress file
- [x] 4.3 Add tests verifying prompt references `config/bootcamp_progress.json`, `common-pitfalls.md`, and `recovery-from-mistakes.md`
- [x] 4.4 Add tests verifying prompt contains module-scoped lookup instructions and fallback to General Pitfalls and Troubleshooting by Symptom
- [x] 4.5 Add tests verifying prompt contains citation instructions, specific command/action guidance, and most-specific-match prioritization
- [x] 4.6 Add tests verifying prompt references `explain_error_code` and SENZ error code prefix
- [x] 4.7 Add test verifying `hook-categories.yaml` contains `error-recovery-context` in `modules.any` list
- [x] 4.8 Add test verifying total hook count is 24

## Task 5: Write property-based tests

- [x] 5.1 Create `tests/test_auto_load_error_recovery_properties.py` with Hypothesis strategies for hook file discovery and category parsing
- [x] 5.2 [PBT] Implement Property 1: Hook structural validity — *For any* .kiro.hook file, it parses as valid JSON with all required fields and valid event/action types. **Feature: auto-load-error-recovery, Property 1: Hook structural validity**
- [x] 5.3 [PBT] Implement Property 2: Category-to-file bidirectional consistency — *For any* hook ID in hook-categories.yaml, a corresponding .kiro.hook file exists. **Feature: auto-load-error-recovery, Property 2: Category-to-file bidirectional consistency**
- [x] 5.4 [PBT] Implement Property 3: ToolType validity for tool-event hooks — *For any* postToolUse/preToolUse hook, every toolTypes entry is a valid category or compilable regex. **Feature: auto-load-error-recovery, Property 3: ToolType validity for tool-event hooks**

## Task 6: Run tests and verify

- [x] 6.1 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` and confirm exit code 0
- [x] 6.2 Run `python senzing-bootcamp/scripts/test_hooks.py --hook error-recovery-context` and confirm exit code 0
- [x] 6.3 Run `pytest tests/test_auto_load_error_recovery.py tests/test_auto_load_error_recovery_properties.py -v` and confirm all tests pass
- [x] 6.4 Run `pytest tests/test_hook_prompt_standards.py -v` and confirm existing hook validation passes with new hook included
