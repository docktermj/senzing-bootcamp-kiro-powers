# Write Policy Gate UX Bugfix Design

## Overview

The `write-policy-gate` is a `preToolUse` hook (`toolTypes: ["write"]`) defined in
`senzing-bootcamp/hooks/write-policy-gate.kiro.hook`. It intercepts **every** write
the agent issues and runs four policy checks in one pass: (1) Senzing SQL blocking,
(2) single-question enforcement on `.question_pending`, (3) file-path policies
including the feedback append-only guard, and (4) root file-placement enforcement.

Because the hook intercepts the tool call before it executes, the IDE surfaces the
held write as a "Rejected creation of ..." message. The agent then silently
re-issues the identical write, which succeeds and surfaces as "Accepted edits
to ...". Nothing fails — this is the safety-check intercept-then-retry cycle. But
the paired "Rejected" → "Accepted" messages recur dozens of times in a session,
most visibly on routine power-managed internal files such as
`config/bootcamp_progress.json`, which the gate has no genuine policy to enforce
against. The cosmetic noise causes bootcamper anxiety and confusion.

The fix strategy has two parts, both within the power's control:

1. **Scope the gate (prompt change).** Add an explicit, top-of-prompt exclusion so
   that writes targeting routine power-managed internal files — files that would
   always pass all four checks — are passed through with zero output, the same
   silent outcome the fast path already produces for clean writes. This removes the
   bulk of the noisy paired messages.
2. **Document the behavior (onboarding change).** Add an onboarding explanation that
   the write intercept-retry cycle is expected and harmless (writes succeed on
   retry; no data is lost), so any residual messages are understood rather than
   alarming.

The design preserves all genuine policy enforcement and the `preToolUse`
held-write/re-issue semantics for every file the gate is responsible for. Softening
the IDE's "Rejected" label itself is an IDE-level concern and is explicitly out of
scope for this power-side fix.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the cosmetic defect — a write
  to a routine power-managed internal file that would pass all four gate checks but
  is still intercepted, producing a noisy "Rejected" → "Accepted" message pair.
- **Property (P)**: The desired behavior for buggy inputs — the gate excludes the
  write from intercept-retry processing so the write completes without producing a
  "Rejected" message.
- **Preservation**: All genuine policy enforcement (SQL blocking, single-question
  rule, feedback append-only, root placement, external-path redirect) and the
  `preToolUse` held-write/re-issue semantics for every governed file must remain
  byte-for-byte unchanged in outcome.
- **write-policy-gate**: The `preToolUse` hook in
  `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` whose `then.prompt` performs
  the four policy checks. The "code" being fixed is this prompt's decision logic.
- **gate (F)** / **gate' (F')**: The gate decision behavior before / after the fix.
- **Power-managed internal file**: A routine bookkeeping file written by the power
  itself rather than authored by the bootcamper — for example
  `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, member-scoped
  `config/progress_{id}.json` and `config/preferences_{id}.yaml`, and session/recap
  log files.
- **Intercept-retry cycle**: The `preToolUse` mechanism by which a write is held
  (surfaced by the IDE as "Rejected"), then re-issued by the agent and completed
  (surfaced as "Accepted edits").

## Bug Details

### Bug Condition

The bug manifests when the agent writes to a routine power-managed internal file
that would always pass every `write-policy-gate` check, yet the gate still
intercepts the write so the IDE produces a paired "Rejected creation of ..." →
"Accepted edits to ..." message. The gate is doing real interception work for a file
against which it has no genuine policy to enforce, so the only effect is cosmetic
noise.

**Formal Specification:**
```
FUNCTION isBugCondition(W)
  INPUT: W of type WriteOperation   // { path, content, tool }
  OUTPUT: boolean

  // A routine power-managed internal file the gate has no genuine policy
  // to enforce against — it would always pass all four checks.
  RETURN isPowerManagedInternalFile(W.path)
     AND NOT endsWith(W.path, ".question_pending")   // governed: single-question rule (Check 2)
     AND NOT isFeedbackFile(W.path)                   // governed: append-only guard (Check 3)
     AND NOT containsSenzingSql(W.content)            // governed: SQL blocking (Check 1)
     AND NOT isRootBlockedPlacement(W.path)           // governed: root placement (Check 4)
END FUNCTION
```

Where `isPowerManagedInternalFile(path)` is true for the routine bookkeeping files
written by the power itself. The concrete set (a design decision, see Fix
Implementation) is:

- `config/bootcamp_progress.json`
- `config/bootcamp_preferences.yaml`
- member-scoped `config/progress_{id}.json`
- member-scoped `config/preferences_{id}.yaml`
- session/recap log files written by the power (e.g., under `docs/progress/` and
  recap/journal log files the power appends to during a session)

`isFeedbackFile(path)` is true for
`docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`. `isRootBlockedPlacement(path)`
is true for a project-root file with a blocked extension (`.py`, `.md`, `.jsonl`,
`.csv`, non-whitelisted `.json`) that is not on the ROOT WHITELIST.

Note: the internal files in the set live in subdirectories (`config/`,
`docs/progress/`) and are JSON/YAML/Markdown with no Senzing SQL, so each of the
four exclusion clauses is naturally satisfied for them. The clauses are stated
explicitly so the exclusion can never shadow a genuinely governed file (for example
`config/.question_pending`, which lives in `config/` but ends with
`.question_pending` and is therefore NOT excluded).

### Examples

- **`config/bootcamp_progress.json` step checkpoint** — Expected: write completes
  silently with no IDE message. Actual: IDE shows "Rejected creation of
  bootcamp_progress.json" then "Accepted edits to bootcamp_progress.json".
- **`config/bootcamp_preferences.yaml` preference update** — Expected: silent
  completion. Actual: paired "Rejected" → "Accepted" message.
- **`config/progress_alice.json` (team colocated mode)** — Expected: silent
  completion. Actual: paired "Rejected" → "Accepted" message recurs each checkpoint.
- **Edge case — `config/.question_pending`** — This is NOT the bug condition. It is
  governed by Check 2 and MUST continue to be intercepted and validated. Expected
  behavior is unchanged by the fix.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- **Check 1 — Senzing SQL blocking**: Content containing an SQL pattern (SELECT,
  INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) targeting a
  Senzing database indicator (G2C.db, RES_ENT, OBS_ENT, SZ_, sz_dm_, etc.) SHALL
  continue to be blocked with the SDK-redirect instruction.
- **Check 2 — Single-question rule**: Writes to a `.question_pending` file with a
  compound or ambiguous question SHALL continue to be intercepted and rewritten.
- **Check 3 — Feedback append-only guard**: `fs_write` overwrites and `str_replace`
  edits of `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` after initial creation
  SHALL continue to be blocked; `fs_append` continues to pass.
- **Check 3 — External-path redirect**: Writes to paths outside the working
  directory (`/tmp/`, `%TEMP%`, `~/Downloads`) or misrouted feedback content SHALL
  continue to be redirected to project-relative equivalents.
- **Check 4 — Root file placement**: Bootcamper-authored files with blocked
  extensions written to the project root SHALL continue to be routed to the correct
  directory.
- **`preToolUse` held-write/re-issue semantics**: For every file the gate is
  responsible for (including `config/.question_pending` and bootcamper-authored
  code/config), the held-write then re-issue-of-identical-write semantics SHALL
  remain intact so policy enforcement is not weakened.
- **Clean-write fast path**: Normal project-relative writes that already passed the
  fast path SHALL continue to produce zero output.

**Scope:**
All inputs that do NOT satisfy `isBugCondition` should be completely unaffected by
this fix. This includes:
- Any write containing Senzing SQL (regardless of path)
- Any write to `.question_pending`, the feedback file, or a root-blocked placement
- Any write to a path outside the working directory
- Any bootcamper-authored source/data/config file
- Any clean ordinary write already handled silently by the existing fast path

**Note:** The expected *correct* behavior for buggy inputs is defined in the
Correctness Properties section (Property 1). This section enumerates what must NOT
change.

## Hypothesized Root Cause

Based on the bug analysis, the cause is structural rather than a logic error:

1. **Hook trigger scope is "every write"**: The hook declares
   `when.type = "preToolUse"` with `toolTypes: ["write"]`. By design it intercepts
   *all* write tool calls. Interception itself — not the check outcome — is what the
   IDE surfaces as "Rejected creation of ...". So even a write that passes the fast
   path silently has already incurred one interception, producing the paired message
   for files written frequently (the power-managed internal files).

2. **No internal-file exclusion in the prompt**: The prompt's FAST PATH GATE checks
   for SQL, `.question_pending`, root placement, and feedback overwrite, but it has
   no clause that recognizes routine power-managed internal files as a class that
   never needs interception. They flow through the normal interception path each
   time they are written.

3. **High write frequency of internal files**: Progress/preference files are written
   at every step checkpoint (`progress_utils.checkpoint`), so the cosmetic noise is
   concentrated and repetitive on exactly the files with no policy to enforce.

4. **No onboarding explanation**: Even after scoping, some legitimate interceptions
   remain (the gate must keep working). Without an onboarding note, any residual
   "Rejected" message reads as a failure.

The fix targets causes (2) and (4): add an explicit internal-file exclusion clause
near the top of the gate prompt, and document the cycle in onboarding. Cause (1) —
the IDE label wording — is out of the power's control and is not addressed here.

## Correctness Properties

Property 1: Bug Condition - Power-Managed Internal Files Bypass Intercept Noise

_For any_ write where the bug condition holds (`isBugCondition(W)` returns true — a
routine power-managed internal file that is not `.question_pending`, not the
feedback file, contains no Senzing SQL, and is not a root-blocked placement), the
fixed gate SHALL exclude the write from intercept-retry processing so that the write
completes and no "Rejected creation of ..." message is produced for it.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Governed Writes Behave Identically

_For any_ write where the bug condition does NOT hold (`isBugCondition(W)` returns
false), the fixed gate SHALL produce exactly the same outcome as the original gate,
preserving all genuine policy enforcement (Senzing SQL blocking, single-question
rule, feedback append-only guard, root file placement, external-path redirect) and
the `preToolUse` held-write/re-issue semantics for every governed file.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

Property 3: Documentation - Intercept-Retry Cycle Is Explained

_For any_ bootcamper progressing through onboarding, the onboarding materials SHALL
document that the write intercept-retry cycle is expected and harmless (writes
succeed on retry; no data is lost), so that residual "Rejected" → "Accepted"
messages are understood.

**Validates: Requirements 2.3**

## Fix Implementation

### Changes Required

Assuming the root cause analysis is correct, two artifacts change.

**Change A — Scope the gate (prompt exclusion clause)**

**File**: `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`

**Location**: `then.prompt`, inserted as an explicit clause at the very top, before
the existing `FAST PATH GATE`.

**Specific Changes**:
1. **Add an "INTERNAL-FILE PASS-THROUGH" clause**: Before any other check, instruct
   the gate that if the target path is a routine power-managed internal file (define
   the exact set), produce ZERO tokens and re-invoke the tool silently — the same
   silent outcome as the existing fast path. This makes the intent explicit and keeps
   the prompt's decision deterministic.
2. **Define the internal-file set precisely**: Enumerate the exact paths/patterns so
   the exclusion cannot over-match:
   - `config/bootcamp_progress.json`
   - `config/bootcamp_preferences.yaml`
   - `config/progress_{id}.json` (member-scoped, colocated team mode)
   - `config/preferences_{id}.yaml` (member-scoped, colocated team mode)
   - power-written session/recap log files (e.g., `docs/progress/MODULE_*_COMPLETE.md`
     and recap/journal log files the power appends to)
3. **Guard the exclusion with explicit NOT clauses**: State that the pass-through
   applies only when the path is NOT `config/.question_pending`, NOT the feedback
   file, NOT a root-blocked placement, and the content contains NO Senzing SQL. This
   guarantees the exclusion can never shadow a governed file even if an internal file
   name overlaps a governed pattern.
4. **Preserve all four existing checks verbatim**: The SQL, single-question,
   file-path, and root-placement check bodies and their corrective outputs are left
   unchanged. Only the new top-of-prompt pass-through clause is added.
5. **Keep the SILENCE RULE / OUTPUT FORMAT intact**: The pass-through reuses the
   existing "zero tokens, re-invoke silently" contract; no new output strings are
   introduced.

**Change B — Document the behavior (onboarding)**

**File**: `senzing-bootcamp/steering/onboarding-flow.md` (and/or a short note in the
relevant onboarding guide under `docs/guides/`).

**Specific Changes**:
1. **Add a short "Why you may see Rejected/Accepted messages" note**: Explain that
   the `write-policy-gate` safety check briefly holds writes for inspection; a held
   write shows as "Rejected", and the agent immediately re-issues it so it completes
   as "Accepted edits". Emphasize: writes succeed on retry, no data is lost, and the
   cycle is expected and harmless.
2. **Set expectations after scoping**: Note that routine internal bookkeeping files
   no longer trigger the message, so remaining occurrences are rare and still
   harmless.

Note: Per security steering, the `preToolUse` write hook is not removed or weakened;
only an additional silent pass-through for files that already pass every check is
added, and the hook JSON keeps its required `name`/`version`/`when`/`then` schema.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples
that demonstrate the noisy interception on the unfixed gate, then verify the fix
suppresses the noise for internal files while preserving every genuine enforcement
outcome and the documentation requirement.

Because the gate logic lives in an LLM-evaluated hook prompt, tests operate on a
decision model of the gate: a function that, given a `WriteOperation`
(`path`, `content`, `tool`), returns one of `{ PASS_SILENT, INTERCEPT_CORRECTIVE }`
plus the corrective category. Tests assert on this decision outcome (mirroring the
prompt's branch logic) and on the presence of the prompt's exclusion clause and the
onboarding documentation text.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the
fix, and confirm the root cause (no internal-file exclusion exists). If refuted,
re-hypothesize.

**Test Plan**: Build the gate decision model from the *unfixed* prompt and assert
that writes to power-managed internal files are not distinguished from ordinary
intercepted writes (i.e., there is no pass-through clause recognizing them). Assert
the unfixed onboarding docs contain no explanation of the intercept-retry cycle.

**Test Cases**:
1. **Progress file** — `config/bootcamp_progress.json` write: unfixed prompt has no
   internal-file pass-through clause (will fail the "is excluded" assertion).
2. **Preferences file** — `config/bootcamp_preferences.yaml` write: no exclusion
   (will fail).
3. **Member-scoped progress** — `config/progress_alice.json`: no exclusion
   (will fail).
4. **Edge case** — `config/.question_pending`: confirm it is NOT excluded by any
   would-be clause (must remain governed) — establishes the guard boundary.
5. **Onboarding docs** — grep onboarding materials for an intercept-retry
   explanation (will fail on unfixed docs).

**Expected Counterexamples**:
- Internal-file writes are processed through normal interception with no
  pass-through, producing the "Rejected" → "Accepted" pair.
- Onboarding contains no note explaining the cycle.
- Possible alternative causes to rule out: the noise is actually a failing check
  (refuted — checks pass), or the IDE label is power-controllable (out of scope).

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed gate
produces the expected behavior (pass-through, no corrective/"Rejected" outcome).

**Pseudocode:**
```
FOR ALL W WHERE isBugCondition(W) DO
  result := gate_fixed(W)
  ASSERT result = PASS_SILENT
     AND NOT produces_rejected_message(result)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed
gate produces the same decision outcome as the original gate.

**Pseudocode:**
```
FOR ALL W WHERE NOT isBugCondition(W) DO
  ASSERT gate_original(W) = gate_fixed(W)
END FOR
```

**Testing Approach**: Property-based testing (Hypothesis, per the project test
stack) is recommended for preservation checking because:
- It generates many `WriteOperation` cases across the input domain (paths,
  extensions, SQL/non-SQL content, tools).
- It catches edge cases manual tests miss — e.g., `config/.question_pending`,
  member-scoped names that look internal but carry a governed extension, root-blocked
  files, feedback overwrites.
- It provides strong assurance that no governed outcome silently changed.

**Test Plan**: Capture the unfixed gate's decision outcomes for governed and clean
inputs first, then assert the fixed gate yields identical outcomes for all
`NOT isBugCondition` inputs.

**Test Cases**:
1. **SQL blocking preservation**: Senzing-SQL content (any path) still
   INTERCEPT_CORRECTIVE with SDK redirect.
2. **Single-question preservation**: `config/.question_pending` with a compound
   question still intercepted and rewritten — confirms the internal-file exclusion
   does not shadow it.
3. **Feedback append-only preservation**: `fs_write`/`str_replace` on the feedback
   file still blocked; `fs_append` still passes.
4. **Root placement preservation**: root `main.py`, `data.jsonl`, non-whitelist
   `.json` still routed.
5. **External-path preservation**: `/tmp/...`, `%TEMP%`, `~/Downloads` still
   redirected.
6. **Clean-write preservation**: ordinary `src/...` write still PASS_SILENT.

### Unit Tests

- Assert the fixed hook prompt contains the INTERNAL-FILE PASS-THROUGH clause and the
  explicit NOT-guards (`.question_pending`, feedback, root-blocked, no Senzing SQL).
- Assert the hook JSON remains schema-valid (`name`, `version`, `when`, `then`) and
  still declares `preToolUse` / `toolTypes: ["write"]`.
- Assert each internal-file path in the defined set maps to PASS_SILENT in the
  decision model.
- Assert `config/.question_pending` does NOT map to PASS_SILENT.
- Assert onboarding documentation contains the intercept-retry explanation
  (Property 3).

### Property-Based Tests

- Generate random power-managed internal-file writes (clean JSON/YAML content) and
  assert PASS_SILENT (Fix Checking — Property 1).
- Generate random non-bug-condition writes (governed paths, SQL content, root-blocked
  placements, external paths, clean ordinary writes) and assert the fixed decision
  equals the original decision (Preservation — Property 2).
- Generate paths that are near-misses to the internal-file set (e.g.,
  `config/.question_pending`, `config/notes.py`, a root `progress.json`) and assert
  they are NOT excluded.

### Integration Tests

- Simulate a step-checkpoint flow that writes `config/bootcamp_progress.json`
  repeatedly and assert no corrective output is produced across the run.
- Simulate a mixed session (internal-file writes interleaved with a Senzing-SQL
  write, a `.question_pending` write, and a feedback overwrite) and assert internal
  writes pass silently while every governed write is still intercepted.
- Verify the onboarding flow renders the intercept-retry explanation where a
  bootcamper would encounter it early in onboarding.
