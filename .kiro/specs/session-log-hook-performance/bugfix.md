# Bugfix Requirements Document

## Introduction

The `session-log-events` postToolUse hook
(`senzing-bootcamp/hooks/session-log-events.kiro.hook`) is an `askAgent` hook that fires after
every write tool call (`fs_write` / `fs_append` / `str_replace`). Its prompt asks the agent to
classify the write, read `config/bootcamp_progress.json` for the current module, import
`build_completion_entry` / `append_completion_entry` from `scripts/session_logger.py`, build a
completion entry, and append one JSONL line to `config/session_log.jsonl`.

This means every file write triggers a full **agent round-trip** PLUS a fresh **Python interpreter
start + module import**, just to append a single log line. In write-heavy modules (e.g., Module 5
mapping produced dozens of writes), the cost compounds: each write becomes write → pre-write gate
hook → write → post-write log hook → agent round-trip → spawn a new Python process. The agent
round-trip and repeated process spawn dominate wall-clock time and make the session feel slow and
"stalled," even though the append itself is trivial (~0.02 ms; the function call) and the snippet
overall is ~20–40 ms of interpreter start + import.

The fix converts the hook from `askAgent` to `runCommand` so the IDE performs the logging itself
with **no agent round-trip**. The command invokes a new small stdlib-only helper script that reads
the current module from `config/bootcamp_progress.json` and appends one structured action entry to
`config/session_log.jsonl` using the existing `session_logger.py` functions. This removes the
dominant cost (the agent round-trip) and keeps logging structured and cross-platform.

**Accepted tradeoff (from feedback):** because the IDE — not the agent — runs the command, the
logged entry records a generic write action (timestamp + module + a generic action/description)
rather than the rich agent-composed `action_type` / `file_path` / `description`. The completion
summary continues to function on these entries; if detailed per-write metadata is later required,
the agent-composed entries can be batched once per turn instead (out of scope for this fix).

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN any write tool call (`fs_write` / `fs_append` / `str_replace`) completes, THE
`session-log-events` hook fires as an `askAgent` hook, consuming a full agent round-trip before
the next user-facing action.

1.2 WHEN the `askAgent` logging prompt runs, THE agent spawns a fresh Python interpreter and
imports `session_logger.py` solely to append one JSONL line, repeating this process spawn on every
write.

1.3 WHEN a module performs many writes in sequence (e.g., Module 5 mapping), THE compounded
agent round-trips and process spawns dominate wall-clock time and produce visible "dead air"
between user-facing steps.

### Expected Behavior (Correct)

2.1 WHEN any write tool call completes, THE `session-log-events` hook SHALL perform logging via a
`runCommand` action executed by the IDE, with NO agent round-trip and no agent-composed prompt.

2.2 WHEN the `runCommand` logging fires, THE command SHALL append exactly one structured JSONL
entry to `config/session_log.jsonl` containing at least a UTC timestamp and the current module
number read from `config/bootcamp_progress.json` (defaulting to module 0 when the progress file is
missing or unreadable).

2.3 WHEN the logging command runs, THE appended entry SHALL be valid JSON on a single line,
parseable by the existing completion-summary tooling that consumes `config/session_log.jsonl`.

2.4 WHEN the logging command encounters an error (missing progress file, unwritable log,
unexpected input), THE command SHALL fail silently (non-blocking) and SHALL NOT interrupt or block
the bootcamp flow.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the completion summary is generated, THE existing `session_logger.py` schema and
`config/session_log.jsonl` format SHALL CONTINUE TO be honored — entries remain compact
single-line JSON consumable by the narrative formatter and PDF generator.

3.2 WHEN the hook fires, THE hook JSON SHALL CONTINUE TO be schema-valid (`name`, `version`,
`when`, `then`) with `when.type` = `postToolUse` and `when.toolTypes` = `["write"]`; only the
`then` block changes from `askAgent` to `runCommand`.

3.3 WHEN logging completes, THE hook SHALL CONTINUE TO produce zero user-facing output (the
silent-logging behavior is preserved — now inherently, since the IDE runs the command).

3.4 WHEN the hook registry mirror (`steering/hook-registry-*.md`) is verified by CI, THE registry
SHALL CONTINUE TO match the hook file (regenerate via `sync_hook_registry.py` so
`--verify` passes).

3.5 WHEN any hook, script, steering file, or config unrelated to `session-log-events` is
considered, THE content SHALL CONTINUE TO be untouched.

3.6 WHEN the logging command writes to `config/session_log.jsonl`, THE write SHALL NOT re-trigger
the `session-log-events` hook (no infinite recursion) — a hook-run command is not an agent tool
call and does not fire `postToolUse`.

---

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type HookConfig (hook_id, action_type)
  OUTPUT: boolean

  // Returns true when the session-logging hook still uses an agent round-trip
  RETURN X.hook_id = "session-log-events"
         AND X.action_type = "askAgent"
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — session logging no longer uses an agent round-trip
FOR ALL X WHERE isBugCondition(X) DO
  config' ← applyFix(X)
  ASSERT config'.action_type = "runCommand"
  ASSERT appendsOneValidJsonlLine(config'.command)   // timestamp + module
  ASSERT failsSilently(config'.command)
END FOR
```

### Preservation Property

```pascal
// Property: Preservation — schema, trigger, silence, registry, and unrelated files unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT applyFix(X) = X
END FOR
// And for the edited hook: when.type/postToolUse, when.toolTypes/["write"],
// schema validity, zero user-facing output, and session_logger.py JSONL schema preserved.
```

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "per-write session-logging scriptlet adds latency to every file operation" and "replace per-write askAgent logging with a direct runCommand append"
- Module: 5 (Data Quality & Mapping) | Priority: Medium | Category: Performance
