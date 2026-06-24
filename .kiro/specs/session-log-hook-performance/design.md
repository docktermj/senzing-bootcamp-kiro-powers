# Bugfix Design Document

## Overview

The `session-log-events` hook logs one session event after every write tool call so the
completion summary can reconstruct what happened. Today it is an `askAgent` hook: every write
triggers a full agent round-trip whose prompt then spawns a fresh Python process to append one
JSONL line. The dominant cost is the agent round-trip; a secondary cost is the per-write process
spawn. In write-heavy modules these costs compound and create visible "dead air."

The fix changes the hook's `then` action from `askAgent` to `runCommand`. The IDE runs the command
directly — no agent round-trip — invoking a new small stdlib helper script
`senzing-bootcamp/scripts/log_write_event.py` that:

1. reads the current module from `config/bootcamp_progress.json` (default `0` on any error),
2. builds a generic write action entry via `session_logger.build_completion_entry`, and
3. appends it to `config/session_log.jsonl` via `session_logger.append_completion_entry`,
4. failing silently on any error.

This preserves the existing JSONL schema and the completion-summary consumer while removing the
agent round-trip entirely. The accepted tradeoff is that the entry records a generic write action
(timestamp + module + generic `action_type`/`description`) instead of the rich agent-composed
metadata.

## Glossary

- **Log_Hook**: `senzing-bootcamp/hooks/session-log-events.kiro.hook`.
- **Log_Script**: the new helper `senzing-bootcamp/scripts/log_write_event.py`.
- **Session_Logger**: the existing `senzing-bootcamp/scripts/session_logger.py` (provides
  `build_completion_entry` / `append_completion_entry`).
- **Progress_File**: `config/bootcamp_progress.json` (source of `current_module`).
- **Session_Log**: `config/session_log.jsonl` (append target).
- **F**: the original hook (`askAgent` round-trip logging).
- **F'**: the fixed hook (`runCommand` invoking Log_Script).

## Bug Details

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  RETURN X.hook_id = "session-log-events" AND X.action_type = "askAgent"
END FUNCTION
```

### Examples

- **Write completes (BUG)**: `session-log-events` fires as `askAgent`; the agent round-trips and
  spawns Python to append one line. *Expected:* in F' the IDE runs the command directly with no
  agent round-trip.
- **Completion summary read (NOT a bug)**: the narrative formatter / PDF generator reads
  `config/session_log.jsonl`. **Preserved — schema unchanged.**
- **Other hooks (NOT a bug)**: every hook other than `session-log-events`. **Untouched.**

## Hypothesized Root Cause

The logging was implemented as an `askAgent` hook because the agent could classify the write
(action type, file path) and compose a rich description. But that classification is not worth a
full agent round-trip per write: the dominant cost is the round-trip itself, and the secondary
cost is spawning a fresh interpreter each time. Moving the append to a `runCommand` removes the
round-trip; accepting a generic action entry removes the need for agent classification.

## Expected Behavior

### Preservation Requirements

All inputs where `isBugCondition(X)` is false must be completely unaffected by this fix:

- The `session_logger.py` JSONL schema and the `config/session_log.jsonl` format remain unchanged;
  the completion-summary narrative formatter and PDF generator continue to consume the log.
- The hook keeps `name`, `version`, `when.type` (`postToolUse`), and `when.toolTypes` (`["write"]`);
  only the `then` block changes from `askAgent` to `runCommand`.
- The logging remains silent (zero user-facing output) — now inherently, since the IDE runs it.
- All hooks, scripts, steering files, and configs other than `session-log-events.kiro.hook`, the
  new `log_write_event.py`, and the regenerated registry mirror are untouched.

The only changed behavior: logging happens via `runCommand` (no agent round-trip) and records a
generic `command_run` entry. The correct behavior for the buggy input is defined in Property 1.

## Correctness Properties

### Property 1: Bug Condition — Logging uses runCommand, not an agent round-trip

_For any_ hook config where `isBugCondition(X)` holds (`session-log-events` is `askAgent`), the
fixed `Log_Hook` SHALL use `then.type` = `runCommand`, and the command SHALL append exactly one
valid single-line JSON entry to `Session_Log` containing a UTC timestamp and the current module
(default `0`), failing silently on error.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Preservation — Schema, trigger, silence, registry, unrelated files unchanged

_For any_ input where the bug condition does not hold, the fix SHALL produce identical content
(`F'(X) = F(X)`). For the edited `Log_Hook`: `when.type` = `postToolUse`, `when.toolTypes` =
`["write"]`, JSON schema validity, and zero user-facing output are preserved; the `Session_Logger`
JSONL schema and `Session_Log` format are preserved; the hook registry mirror stays byte-consistent
(CI `sync_hook_registry.py --verify` passes); and all unrelated hooks/scripts/steering/config are
untouched.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### 1. New helper script — `senzing-bootcamp/scripts/log_write_event.py`

Stdlib-only (per `python-conventions.md`), with `main(argv) -> int` and an argparse CLI:

```python
#!/usr/bin/env python3
"""Append one generic write event to config/session_log.jsonl (used by the
session-log-events runCommand hook). Fails silently — never blocks the bootcamp."""
from __future__ import annotations
# imports session_logger via the scripts dir; reads current_module from
# config/bootcamp_progress.json (default 0); builds an "action" completion entry
# with a generic write action; appends to config/session_log.jsonl. All errors
# are swallowed (exit 0).
```

Behavior:

- Reads `config/bootcamp_progress.json`; uses `current_module` if present and an int in 0–11,
  else `0`. Any read/parse error → module `0`.
- Builds `build_completion_entry(event_type="action", module=<module>, data={"action_type":
  "command_run", "description": "write operation"})`. **Design decision:** use
  `action_type="command_run"`, which the `session_logger` schema allows with no required
  `file_path`, so the IDE-driven generic entry stays schema-valid without fabricating a target
  path it cannot see.
- Appends via `append_completion_entry("config/session_log.jsonl", entry)`.
- Wraps everything in try/except; on any exception, returns `0` (silent, non-blocking).
- Path resolution uses the current working directory (the bootcamp workspace root), consistent
  with the existing askAgent prompt's relative paths.

> **Note on action_type:** the existing askAgent prompt classified writes into
> file_create/file_modify/file_delete/etc. The runCommand variant cannot see the target path, so
> it logs a single generic `command_run` entry per write (no required `file_path`); the
> completion-summary consumer already tolerates `command_run` entries.

### 2. Convert the hook — `senzing-bootcamp/hooks/session-log-events.kiro.hook`

Replace the `then` block:

```json
"then": {
  "type": "runCommand",
  "command": "python3 senzing-bootcamp/scripts/log_write_event.py"
}
```

Keep `name`, `version`, `when.type` (`postToolUse`), and `when.toolTypes` (`["write"]`) unchanged.
Update `description` to reflect that the IDE appends the log line directly (no agent round-trip).
Set a small `timeout` if the schema supports it (e.g., 10s) so a stuck interpreter never blocks.

> **Windows note:** invocation uses `python3` to match the existing prompt's references. If the
> target environments require it, the command may be `python` on Windows; the helper script itself
> is OS-agnostic (stdlib `pathlib`, `json`, `datetime`). Document the chosen invocation in the
> hook `description`.

### 3. Regenerate the registry mirror

Run `python senzing-bootcamp/scripts/sync_hook_registry.py` so the
`steering/hook-registry-*.md` mirror reflects the converted hook, then confirm with
`sync_hook_registry.py --verify`.

## Testing Strategy

### Validation Approach

New tests live in `senzing-bootcamp/tests/` (pytest + Hypothesis, stdlib + Hypothesis only, per
`python-conventions.md`). The fix-checking test is authored to FAIL on the unfixed hook (still
`askAgent`) and PASS after conversion; preservation tests PASS before and after.

### Fix Checking (Property 1)

- **test_hook_uses_run_command**: parse `session-log-events.kiro.hook`; assert `then.type ==
  "runCommand"` and the command references `log_write_event.py`. FAILS on unfixed code.
- **test_log_script_appends_one_valid_jsonl_line**: in a temp workspace with a sample
  `config/bootcamp_progress.json`, run `log_write_event.main([])`; assert exactly one new line was
  appended to `config/session_log.jsonl` and it parses as JSON with a `timestamp` and the expected
  `module`.
- **test_log_script_defaults_module_zero**: with no/unreadable progress file, assert the appended
  entry has `module == 0`.
- **test_log_script_fails_silently**: with an unwritable log path (simulated), assert
  `main` returns `0` and raises nothing.

### Preservation Checking (Property 2)

- **test_hook_schema_and_trigger_preserved**: assert the hook keeps `name`, `version`, `when.type
  == "postToolUse"`, `when.toolTypes == ["write"]`, and valid JSON schema.
- **test_session_logger_schema_unchanged**: assert `session_logger.build_completion_entry` /
  `append_completion_entry` still produce the existing compact single-line JSON schema (round-trip
  parse of an appended entry).
- **test_no_user_facing_output**: assert `log_write_event.main` prints nothing to stdout.
- **test_unrelated_hooks_unchanged**: SHA-256 snapshot of all other hook files is unchanged.

### Integration Tests

- Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` — mirror byte-consistent.
- Run `python senzing-bootcamp/scripts/validate_commonmark.py` — registry/docs stay valid.
- Run the completion-summary tooling against a `config/session_log.jsonl` containing the new
  generic entries to confirm it still produces a summary (smoke test).
