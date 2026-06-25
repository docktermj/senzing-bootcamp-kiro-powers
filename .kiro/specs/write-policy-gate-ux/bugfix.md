# Bugfix Requirements Document

## Introduction

Throughout the bootcamp the IDE frequently shows paired messages such as
"Rejected creation of bootcamp_progress.json" immediately followed by
"Accepted edits to bootcamp_progress.json", along with other "Rejected
creation of ..." messages on config files and scripts. These appear because the
`write-policy-gate` `preToolUse` hook (toolTypes: `write`) intercepts every
write for inspection. A held/intercepted write is surfaced by the IDE as
"Rejected"; the agent then re-issues the identical write and it succeeds
("Accepted edits"). Nothing actually fails — it is the safety-check
intercept-then-retry cycle.

The behavior is cosmetic: writes always succeed on retry and no data is lost.
The harm is bootcamper anxiety and confusion. The "Rejected" wording implies a
failure or denial, and over a long session there are dozens of these paired
messages — especially on routine power-managed internal files like
`config/bootcamp_progress.json` that the gate has no genuine policy to enforce
against. There is also no onboarding explanation telling bootcampers the cycle
is expected and harmless.

This bugfix captures the two fixes within the power's control:

- **Scope the gate** so routine power-managed internal files (which always pass
  every gate check) are excluded from the intercept-retry cycle, eliminating
  most of the noisy paired messages.
- **Document the behavior** in onboarding so any remaining intercept-retry
  messages are understood as expected and harmless.

Note: softening the IDE label itself (from "Rejected" to "Reviewing" / "Policy
check") is an IDE-level concern and is likely outside the power's direct
control. It is recorded as a desired goal but is not a power-side requirement in
this spec.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent writes to a routine power-managed internal file (e.g.,
`config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, member
progress/preference files, session/recap log files) that would always pass every
`write-policy-gate` check, THEN the gate still intercepts the write and the IDE
surfaces a "Rejected creation of ..." message.

1.2 WHEN such an intercepted internal-file write is re-issued by the agent, THEN
the IDE shows a paired "Accepted edits to ..." message, producing a confusing
"Rejected" → "Accepted" pair that recurs dozens of times over a session.

1.3 WHEN a bootcamper progresses through onboarding, THEN the onboarding
materials provide no explanation of the write intercept-retry cycle, leaving the
"Rejected" messages unexplained and alarming.

### Expected Behavior (Correct)

2.1 WHEN the agent writes to a routine power-managed internal file that always
passes every `write-policy-gate` check, THEN the system SHALL exclude that write
from the gate's intercept-retry processing so no "Rejected creation of ..."
message is produced for it.

2.2 WHEN such an internal-file write is excluded from the gate, THEN the system
SHALL allow the write to complete without the paired "Rejected" → "Accepted"
message cycle.

2.3 WHEN a bootcamper progresses through onboarding, THEN the system SHALL
document that the write intercept-retry cycle is expected and harmless (writes
succeed on retry; no data is lost), so any remaining messages are understood.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN content contains an SQL pattern (SELECT, INSERT, UPDATE, DELETE, CREATE
TABLE, DROP TABLE, ALTER TABLE, PRAGMA) targeting a Senzing database indicator,
THEN the gate SHALL CONTINUE TO block the write and require SDK-based access.

3.2 WHEN a write targets a `.question_pending` file with a compound or ambiguous
question, THEN the gate SHALL CONTINUE TO enforce the single-question rule.

3.3 WHEN `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` is overwritten via
`fs_write` or edited via `str_replace` after initial creation, THEN the gate
SHALL CONTINUE TO enforce the append-only guard.

3.4 WHEN a bootcamper-authored file with a blocked extension (`.py`, `.md`,
`.jsonl`, `.csv`, non-whitelisted `.json`) is written to the project root, THEN
the gate SHALL CONTINUE TO enforce root file placement and route it to the
correct directory.

3.5 WHEN a write targets a path outside the working directory (e.g., `/tmp/`,
`%TEMP%`, `~/Downloads`) or misroutes feedback content, THEN the gate SHALL
CONTINUE TO redirect it to the project-relative equivalent.

3.6 WHEN the gate governs a file it is responsible for (including
`config/.question_pending` and bootcamper-authored code/config), THEN the system
SHALL CONTINUE TO honor the `preToolUse` hook semantics (held write, re-issue of
the identical write) so policy enforcement is not weakened.

## Bug Condition Derivation

**Definitions**

- **F**: The write-policy-gate behavior before the fix — intercepts every write.
- **F'**: The write-policy-gate behavior after the fix — skips routine
  power-managed internal files that always pass all checks; documentation
  explains the residual intercept-retry cycle.

**Bug Condition** — identifies writes that trigger the noisy, no-value intercept:

```pascal
FUNCTION isBugCondition(W)
  INPUT: W of type WriteOperation
  OUTPUT: boolean

  // A routine power-managed internal file that the gate has no genuine
  // policy to enforce against — it would always pass all four checks.
  RETURN isPowerManagedInternalFile(W.path)
     AND NOT endsWith(W.path, ".question_pending")   // governed: single-question rule
     AND NOT isFeedbackFile(W.path)                   // governed: append-only guard
     AND NOT containsSenzingSql(W.content)            // governed: SQL blocking
     AND NOT isRootBlockedPlacement(W.path)           // governed: root placement
END FUNCTION
```

Where `isPowerManagedInternalFile` covers routine bookkeeping files written by
the power itself — for example `config/bootcamp_progress.json`,
`config/bootcamp_preferences.yaml`, member-scoped `config/progress_{id}.json`
and `config/preferences_{id}.yaml`, and session/recap log files. The exact set
is a design concern.

**Property: Fix Checking** — for buggy inputs, no intercept-retry noise:

```pascal
FOR ALL W WHERE isBugCondition(W) DO
  result ← gate'(W)
  ASSERT NOT produces_rejected_message(result)
     AND write_completes(result)
END FOR
```

**Property: Preservation Checking** — for every other write, behavior is
identical to before the fix:

```pascal
FOR ALL W WHERE NOT isBugCondition(W) DO
  ASSERT gate(W) = gate'(W)
END FOR
```

This guarantees that all genuine policy enforcement (SQL blocking,
single-question rule, feedback append-only, root placement, external-path
redirect) and the `preToolUse` held-write/re-issue semantics remain unchanged
for every file the gate is responsible for.
