# Requirements: Hook Self-Test Mode

## Overview

With 26 hooks, debugging which hook is misbehaving is non-trivial. This feature adds a self-test capability that simulates each hook's trigger condition and verifies it produces expected output (or silence), helping maintainers and advanced users diagnose issues.

## Requirements

1. A new script `senzing-bootcamp/scripts/test_hooks.py` provides hook self-testing capability
2. Running `python test_hooks.py` with no arguments tests all hooks in `senzing-bootcamp/hooks/` and reports pass/fail for each
3. Running `python test_hooks.py --hook <hook-id>` tests a single hook by ID
4. For each hook, the test verifies: (a) the hook file is valid JSON, (b) required fields exist (`name`, `version`, `when.type`, `then.type`), (c) the `when.type` is a valid event type, (d) for `askAgent` hooks, the `then.prompt` is non-empty, (e) for `runCommand` hooks, the `then.command` is non-empty
5. The test also verifies hook-registry consistency: every hook file has a matching entry in `hook-registry.md`, and every registry entry has a matching hook file
6. For hooks with `when.type: fileEdited`, the test verifies that `when.patterns` contains valid glob patterns
7. For hooks with `when.type: preToolUse` or `postToolUse`, the test verifies that `when.toolTypes` contains valid categories or regex patterns
8. The script outputs a summary table: hook ID, event type, action type, status (PASS/FAIL), and failure reason if applicable
9. Exit code is 0 if all hooks pass, 1 if any hook fails
10. The `--verbose` flag shows the full prompt/command for each hook alongside the test result
11. The `--categories` flag filters tests to hooks in a specific category from `hook-categories.yaml` (e.g., `--categories critical`)
12. The script uses stdlib only (no third-party dependencies), consistent with other scripts in the power

## Non-Requirements

- This does not execute hooks against real IDE events (it's structural validation only)
- This does not test hook prompt effectiveness (that's what the existing pytest suite does)
- This does not modify hook files
- This does not replace `sync_hook_registry.py --verify` (that checks registry sync; this checks hook validity)
