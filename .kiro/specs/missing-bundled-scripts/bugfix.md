# Bugfix Requirements Document

## Introduction

The senzing-bootcamp power ships a collection of Python helper scripts under
`senzing-bootcamp/scripts/`. Hooks (e.g. the `session-log-events` postToolUse
hook running `log_write_event.py`) and bootcamp/graduation steps shell out to
these scripts using fixed paths like `senzing-bootcamp/scripts/<name>.py`.

When the power is in use, those bundled scripts are not guaranteed to be
materialized in the working directory. When a hook or step invokes a script that
does not exist, two failure modes occur:

1. **Per-write hook failures and silent data loss** — The `session-log-events`
   hook fails on every write with `python3: can't open file
   '.../senzing-bootcamp/scripts/log_write_event.py': [Errno 2] No such file or
   directory` (exit code 2). This produces error noise after every write and,
   more importantly, the session-event log that feeds the end-of-bootcamp
   completion summary is never written. Writes still succeed (non-blocking), but
   a downstream feature is silently broken.

2. **Skipped deliverables despite capable environment** — Graduation Step 0b
   generates `docs/bootcamp_recap.pdf` by preferring the bundled
   `scripts/generate_recap_pdf.py` and falling back to
   `scripts/generate_recap_pdf_inline.py`. When both bundled scripts are absent,
   no PDF is produced — even when the optional `fpdf2` rendering library is
   installed. The only blocker is the missing generator scripts, not the
   rendering capability.

The shared root cause is that hooks and steps depend on
`senzing-bootcamp/scripts/*` files that are not verified or materialized before
use, and the invoking code does not degrade gracefully when a script is missing.

The fix must materialize and/or verify the bundled scripts in the workspace,
provide graceful degradation and self-repair when a script is still missing, and
add a self-contained inline PDF path that does not depend on a bundled file —
while preserving all existing behavior when the scripts are already present.

## Bug Analysis

### Current Behavior (Defect)

What currently happens when a hook or step depends on a bundled script that is
not present in the workspace.

1.1 WHEN the `session-log-events` postToolUse hook fires and
`senzing-bootcamp/scripts/log_write_event.py` does not exist in the workspace
THEN the system runs `python3` against the missing path, which exits with code 2
and emits `No such file or directory` error noise after every write operation.

1.2 WHEN a write operation occurs and the session-logging script is missing THEN
the system fails to record the write event, so `config/session_log.jsonl` is
never written and the end-of-bootcamp completion summary that depends on it is
silently incomplete.

1.3 WHEN any bootcamp or onboarding step shells out to a
`senzing-bootcamp/scripts/<name>.py` file (e.g. `preflight.py`,
`install_hooks.py`, `completion_artifacts.py`, `status.py`, `backup_project.py`)
that is not present in the workspace THEN the system fails with a
file-not-found error instead of degrading gracefully or self-repairing.

1.4 WHEN graduation Step 0b runs and both `scripts/generate_recap_pdf.py` and
`scripts/generate_recap_pdf_inline.py` are absent from the workspace THEN the
system produces no `docs/bootcamp_recap.pdf`, even when the optional `fpdf2`
rendering library is installed.

1.5 WHEN onboarding completes THEN the system does not verify that the bundled
`senzing-bootcamp/scripts/` directory exists, so missing scripts go undetected
until a hook or step fails later.

### Expected Behavior (Correct)

What should happen instead for the same conditions.

2.1 WHEN the `session-log-events` postToolUse hook fires and
`senzing-bootcamp/scripts/log_write_event.py` does not exist THEN the system
SHALL detect the missing script, fall back to an inline logger that appends an
equivalent JSON event (`{ts, action, module}`) to `config/session_log.jsonl`,
and exit 0 without emitting file-not-found error noise.

2.2 WHEN a write operation occurs and the session-logging script is missing THEN
the system SHALL still record the write event to `config/session_log.jsonl` via
the inline fallback so the completion summary remains complete.

2.3 WHEN any bootcamp or onboarding step would shell out to a
`senzing-bootcamp/scripts/<name>.py` file that is not present THEN the system
SHALL degrade gracefully — performing an existence check and using an
inline/no-op fallback — rather than failing with a file-not-found error.

2.4 WHEN graduation Step 0b runs and the bundled recap-PDF generator scripts are
absent but the `fpdf2` library is installed THEN the system SHALL render
`docs/bootcamp_recap.pdf` directly from `docs/bootcamp_recap.md` via a
self-contained inline PDF path that does not depend on a bundled script file.

2.5 WHEN onboarding runs THEN the system SHALL materialize the bundled
`senzing-bootcamp/scripts/` directory into the workspace before any hook or step
depends on it, and SHALL run a preflight verification that warns and self-repairs
if the scripts directory or required scripts are missing.

### Unchanged Behavior (Regression Prevention)

Existing behavior that must be preserved when the scripts are already present.

3.1 WHEN `senzing-bootcamp/scripts/log_write_event.py` exists in the workspace
and the `session-log-events` hook fires THEN the system SHALL CONTINUE TO invoke
the bundled script to record the write event (timestamp + current module) to
`config/session_log.jsonl`.

3.2 WHEN a bootcamp or onboarding step shells out to a
`senzing-bootcamp/scripts/<name>.py` file that is present THEN the system SHALL
CONTINUE TO execute that bundled script with its existing behavior and output.

3.3 WHEN graduation Step 0b runs and the bundled
`scripts/generate_recap_pdf.py` (or its `scripts/generate_recap_pdf_inline.py`
fallback) is present THEN the system SHALL CONTINUE TO use the bundled generator,
preferring `generate_recap_pdf.py` first.

3.4 WHEN the optional `fpdf2` library is not installed and no recap generator can
produce a PDF THEN the system SHALL CONTINUE TO degrade gracefully by retaining
the Markdown recap output without raising an unhandled error.

3.5 WHEN scripts are materialized or verified during onboarding THEN the system
SHALL CONTINUE TO leave already-present, correct script files unchanged (no
overwrite of valid existing scripts).

## Bug Condition and Properties

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X = invocation of a hook or step that references a bundled script
         at path P = "senzing-bootcamp/scripts/<name>.py"
  OUTPUT: boolean

  // The bug is triggered when the invoked bundled script is not present
  // in the workspace at the path the hook/step expects.
  RETURN NOT fileExists(X.scriptPath)
END FUNCTION
```

### Property — Fix Checking (graceful degradation + self-repair)

```pascal
// For every invocation that references a missing bundled script,
// the fixed system must not fail and must preserve the downstream effect.
FOR ALL X WHERE isBugCondition(X) DO
  result <- F'(X)
  ASSERT result.exitCode = 0
  ASSERT NOT result.emittedFileNotFoundError
  ASSERT downstreamEffectPreserved(X)
    // e.g. session event appended to config/session_log.jsonl via inline fallback,
    //      or recap PDF rendered from docs/bootcamp_recap.md when fpdf2 present
END FOR
```

### Property — Preservation Checking (scripts present)

```pascal
// For every invocation where the referenced script is present,
// the fixed system behaves identically to the original.
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Where **F** is the original (unfixed) behavior and **F'** is the fixed behavior.
