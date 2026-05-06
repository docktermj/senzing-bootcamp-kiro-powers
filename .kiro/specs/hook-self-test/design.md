# Design: Hook Self-Test Mode

## Overview

A new `test_hooks.py` script performs structural validation of all hook files — checking JSON validity, required fields, event type validity, pattern validity, and registry consistency. It provides a quick diagnostic for maintainers without needing to trigger hooks via IDE events.

## Validation Checks Per Hook

For each `.kiro.hook` file in `senzing-bootcamp/hooks/`:

| Check | What It Validates | Failure Message |
|-------|-------------------|-----------------|
| JSON parse | File is valid JSON | "Invalid JSON: {parse error}" |
| Required fields | `name`, `version`, `when.type`, `then.type` exist | "Missing required field: {field}" |
| Event type | `when.type` is one of valid event types | "Invalid event type: {value}" |
| Action type | `then.type` is "askAgent" or "runCommand" | "Invalid action type: {value}" |
| Prompt present | If askAgent, `then.prompt` is non-empty string | "Empty prompt for askAgent hook" |
| Command present | If runCommand, `then.command` is non-empty string | "Empty command for runCommand hook" |
| File patterns | If fileEdited/Created/Deleted, `when.patterns` has valid globs | "Invalid glob pattern: {pattern}" |
| Tool types | If preToolUse/postToolUse, `when.toolTypes` has valid entries | "Invalid toolType: {value}" |

### Valid Event Types
```python
VALID_EVENT_TYPES = {
    "fileEdited", "fileCreated", "fileDeleted",
    "userTriggered", "promptSubmit", "agentStop",
    "preToolUse", "postToolUse",
    "preTaskExecution", "postTaskExecution"
}
```

### Valid Tool Type Categories
```python
VALID_TOOL_CATEGORIES = {"read", "write", "shell", "web", "spec", "*"}
# Regex patterns are also valid (validated by attempting re.compile)
```

## Registry Consistency Check

After individual hook validation:
1. Parse `senzing-bootcamp/steering/hook-registry.md` for hook IDs
2. List all `.kiro.hook` files and extract IDs from filenames
3. Report: hooks in files but not in registry, hooks in registry but no file

## Output Format

```
$ python test_hooks.py

Hook Self-Test Results
═══════════════════════════════════════════════════════════════
  ID                          Event Type      Action    Status
───────────────────────────────────────────────────────────────
  ask-bootcamper              agentStop       askAgent  PASS
  review-bootcamper-input     promptSubmit    askAgent  PASS
  code-style-check            fileEdited      askAgent  PASS
  backup-before-load          preToolUse      askAgent  PASS
  invalid-hook                fileEdited      askAgent  FAIL
    → Missing required field: when.patterns
───────────────────────────────────────────────────────────────
Registry Consistency:
  ✅ All 23 hook files have registry entries
  ✅ All registry entries have hook files

Summary: 22 passed, 1 failed
```

## CLI Interface

```
usage: test_hooks.py [-h] [--hook HOOK_ID] [--categories CATEGORY] [--verbose]

Options:
  --hook HOOK_ID       Test a single hook by ID
  --categories CAT     Filter by category from hook-categories.yaml
  --verbose            Show full prompt/command for each hook
```

## Implementation Notes

- stdlib only (json, re, pathlib, argparse, os)
- Hook ID derived from filename: `ask-bootcamper.kiro.hook` → `ask-bootcamper`
- Glob validation: check for unbalanced brackets, invalid characters
- Regex validation for toolTypes: attempt `re.compile()`, catch `re.error`

## Files Created

- `senzing-bootcamp/scripts/test_hooks.py` — new script

## Testing

- Unit test: script accepts --hook, --categories, --verbose flags
- Unit test: valid hook file passes all checks
- Unit test: hook with missing field is detected
- Unit test: hook with invalid event type is detected
- Unit test: registry consistency check detects missing entries
- Property test: any valid JSON with required fields passes structural checks
