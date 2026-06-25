# Implementation Plan

## Overview

Convert the `session-log-events` postToolUse hook from `askAgent` to `runCommand` so the IDE
appends the log line directly (no agent round-trip). Add a stdlib helper
`senzing-bootcamp/scripts/log_write_event.py` that reads the current module and appends one
generic, schema-valid action entry to `config/session_log.jsonl`, failing silently.

## Tasks

- [x] 1. Write fix-checking tests (before the change)
  - Create `senzing-bootcamp/tests/test_session_log_hook_performance.py` (pytest + Hypothesis,
    stdlib + Hypothesis only, `from __future__ import annotations`, class-based, per
    `python-conventions.md`)
  - **test_hook_uses_run_command** (Property 1): parse `session-log-events.kiro.hook`; assert
    `then.type == "runCommand"` and the command references `log_write_event.py` — authored to FAIL
    on unfixed code
  - Stub the `log_write_event` behavioral tests (appends one valid line; defaults module 0; fails
    silently; no stdout) — these will pass once the script exists
  - Run: confirm `test_hook_uses_run_command` FAILS on unfixed code
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Write preservation tests (before the change)
  - In the same suite (or a preservation module): **test_hook_schema_and_trigger_preserved**
    (`name`/`version`/`when.type==postToolUse`/`when.toolTypes==["write"]`/valid schema),
    **test_session_logger_schema_unchanged** (round-trip parse of an appended entry),
    **test_unrelated_hooks_unchanged** (SHA-256 snapshot of other hook files)
  - Run: confirm preservation tests PASS on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 3. Add the helper script `log_write_event.py`
  - Create `senzing-bootcamp/scripts/log_write_event.py` (stdlib only, `main(argv) -> int`,
    argparse CLI)
  - Import `session_logger` via the scripts-dir `sys.path` pattern from `python-conventions.md`
  - Read `current_module` from `config/bootcamp_progress.json` (default `0` on any error, clamp to
    0–11)
  - Build `build_completion_entry(event_type="action", module=<module>, data={"action_type":
    "command_run", "description": "write operation"})` and append via
    `append_completion_entry("config/session_log.jsonl", entry)`
  - Wrap all logic in try/except; return `0` on any error; print nothing to stdout
  - _Requirements: 2.2, 2.3, 2.4, 3.1_

- [x] 4. Convert the hook to runCommand
  - Edit `senzing-bootcamp/hooks/session-log-events.kiro.hook`: replace the `then` block with
    `{"type": "runCommand", "command": "python3 senzing-bootcamp/scripts/log_write_event.py"}`
  - Keep `name`, `version`, `when.type` (`postToolUse`), `when.toolTypes` (`["write"]`) unchanged;
    update `description` to state the IDE appends the log line directly; add a small `timeout` if
    supported
  - _Requirements: 2.1, 3.2, 3.3, 3.6_

- [x] 5. Regenerate the hook registry mirror
  - Run `python senzing-bootcamp/scripts/sync_hook_registry.py`, then
    `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`
  - _Requirements: 3.4_

- [x] 6. Verify fix-checking and preservation tests pass
  - Run `pytest senzing-bootcamp/tests/test_session_log_hook_performance.py` — all PASS
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.5_

- [x] 7. Checkpoint — full verification
  - Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`,
    `python senzing-bootcamp/scripts/validate_commonmark.py`, and
    `python senzing-bootcamp/scripts/measure_steering.py --check`
  - Smoke-test the completion-summary tooling against a `config/session_log.jsonl` containing the
    new generic `command_run` entries to confirm it still produces a summary
  - Confirm no MCP server URL was introduced into any edited surface
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3"] },
    { "id": 2, "tasks": ["4"] },
    { "id": 3, "tasks": ["5"] },
    { "id": 4, "tasks": ["6", "7"] }
  ]
}
```

- **Wave 0** — `[1, 2]`: author fix-checking and preservation tests against the unfixed hook
  (fix-check FAILS — still `askAgent`; preservation PASSES).
- **Wave 1** — `[3]`: add the `log_write_event.py` helper script.
- **Wave 2** — `[4]`: convert the hook `then` block to `runCommand` (depends on the script
  existing).
- **Wave 3** — `[5]`: regenerate the hook registry mirror to match the converted hook.
- **Wave 4** — `[6, 7]`: verify the new suites pass and run the full CI validators + completion
  summary smoke test.

## Notes

- Removes the dominant per-write cost (the agent round-trip) by letting the IDE run the append
  directly; the helper script keeps the append structured and cross-platform.
- Accepted tradeoff: a generic `command_run` entry per write (no agent-composed
  action_type/file_path) — `command_run` is schema-valid with no required `file_path`.
- No recursion: a hook-run command is not an agent tool call and does not re-fire the
  `postToolUse` write hook.
- stdlib-only; no MCP URL in any edited surface (security gate).
