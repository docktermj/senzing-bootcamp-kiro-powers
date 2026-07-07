# Missing Bundled Scripts Bugfix Design

## Overview

The senzing-bootcamp power ships Python helper scripts under
`senzing-bootcamp/scripts/`. Hooks (notably the `session-log-events` postToolUse
hook) and bootcamp/graduation steps shell out to these scripts using fixed,
relative paths like `senzing-bootcamp/scripts/<name>.py`. Those bundled scripts
are not guaranteed to be materialized in the bootcamper's workspace. When a hook
or step invokes a script that is absent, two failure modes occur:

1. The `session-log-events` hook runs `python3` against the missing
   `log_write_event.py`, exiting with code 2 and printing
   `No such file or directory` after every write — and the session-event log
   that feeds the completion summary is silently never written.
2. Graduation Step 0b produces no `docs/bootcamp_recap.pdf` when both bundled
   recap generators are absent, even when the optional `fpdf2` library is
   installed and capable of rendering.

The shared root cause: hooks and steps depend on `senzing-bootcamp/scripts/*`
files that are neither verified nor materialized before use, and the invoking
code does not degrade gracefully when a script is missing.

The fix has three coordinated parts, all using Python 3.11+ stdlib only (with
`fpdf2` remaining an optional, lazily-imported dependency):

1. **Materialize/verify** the bundled `senzing-bootcamp/scripts/` directory
   during onboarding and run a preflight verification that warns and self-repairs
   when scripts are missing.
2. **Graceful degradation + self-repair** at every invocation site: existence
   check before shelling out, with an inline/no-op fallback that preserves the
   downstream effect (e.g. session event still appended) and exits 0 without
   file-not-found noise.
3. **Self-contained inline PDF path** that renders `docs/bootcamp_recap.pdf` from
   `docs/bootcamp_recap.md` without depending on any bundled generator file,
   using the shared `recap_pdf_render` rendering primitives.

When the scripts are already present, all existing behavior is preserved exactly.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a hook or step
  references a bundled script at `senzing-bootcamp/scripts/<name>.py` that does
  not exist in the workspace (`NOT fileExists(X.scriptPath)`).
- **Property (P)**: The desired behavior when C holds — the invocation must not
  fail (exit 0, no file-not-found noise) and must preserve the downstream effect
  (session event appended, recap PDF rendered when `fpdf2` is present).
- **Preservation**: Existing behavior that must remain unchanged when the
  referenced script IS present — the bundled script is invoked exactly as before
  with identical output and effects.
- **F / F'**: The original (unfixed) behavior vs. the fixed behavior.
- **`log_write_event.py`**: The script in `senzing-bootcamp/scripts/` invoked by
  the `session-log-events` hook's `runCommand` to append a write-action entry
  (`{ts, action, module}`) to `config/session_log.jsonl`.
- **`session-log-events.kiro.hook`**: The postToolUse hook (`toolTypes: ["write"]`)
  whose `then.runCommand` shells out to `log_write_event.py`.
- **Inline fallback (logger)**: A self-contained appender that writes an
  equivalent JSON session event to `config/session_log.jsonl` without importing
  or executing any bundled script.
- **Inline PDF path**: `recap_pdf_render.render_markdown_pdf`, a self-contained
  renderer that converts the recap Markdown to PDF without depending on a bundled
  generator file; `fpdf` is lazily imported inside it.
- **Preflight verification**: A `preflight.py` check (existence + self-repair via
  `--fix`) that confirms `senzing-bootcamp/scripts/` and required scripts are
  present during onboarding.
- **`current_module`**: The module number read from
  `config/bootcamp_progress.json` (clamped 0–11), recorded in each session event.

## Bug Details

### Bug Condition

The bug manifests when a hook or bootcamp/graduation step shells out to a bundled
script at the fixed path `senzing-bootcamp/scripts/<name>.py` and that file is not
present in the workspace at the path the hook/step expects. The invoking code
runs `python3 <path>` unconditionally — it neither verifies the file exists nor
provides an inline fallback — so the interpreter exits with code 2 and prints a
`No such file or directory` error, and the downstream effect (session logging,
recap-PDF deliverable) is lost.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X = invocation of a hook or step that references a bundled script
         at path P = "senzing-bootcamp/scripts/<name>.py"
  OUTPUT: boolean

  // The bug is triggered when the invoked bundled script is not present
  // in the workspace at the path the hook/step expects.
  RETURN NOT fileExists(X.scriptPath)
END FUNCTION
```

### Examples

- **Per-write hook failure**: A write occurs; the `session-log-events` hook runs
  `python3 senzing-bootcamp/scripts/log_write_event.py`, which does not exist.
  - Expected: inline fallback appends `{ts, action, module}` to
    `config/session_log.jsonl`; exit 0; no error noise.
  - Actual: `python3: can't open file '.../log_write_event.py': [Errno 2] No such
    file or directory`; exit 2; no session event recorded.
- **Silent completion-summary breakage**: Many writes occur with the logger
  script absent.
  - Expected: every write event recorded via inline fallback so the end-of-bootcamp
    completion summary is complete.
  - Actual: `config/session_log.jsonl` never written; completion summary silently
    incomplete.
- **Skipped recap PDF despite capable environment**: Graduation Step 0b runs with
  both `generate_recap_pdf.py` and `generate_recap_pdf_inline.py` absent but
  `fpdf2` installed.
  - Expected: `docs/bootcamp_recap.pdf` rendered from `docs/bootcamp_recap.md` via
    the self-contained inline PDF path.
  - Actual: no PDF produced; only blocker is the missing generator scripts.
- **Edge case — `fpdf2` absent and no generator available**: Graduation Step 0b
  runs with generators absent and `fpdf2` not installed.
  - Expected: degrade gracefully, retain the Markdown recap, print a
    `pip install fpdf2` hint, no unhandled error.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When `log_write_event.py` is present, the `session-log-events` hook SHALL
  continue to invoke the bundled script to record the write event (timestamp +
  current module) to `config/session_log.jsonl`.
- When a bootcamp/onboarding step shells out to a present
  `senzing-bootcamp/scripts/<name>.py`, the system SHALL continue to execute that
  bundled script with its existing behavior and output.
- When the bundled `generate_recap_pdf.py` (or its `generate_recap_pdf_inline.py`
  fallback) is present, graduation Step 0b SHALL continue to use the bundled
  generator, preferring `generate_recap_pdf.py` first.
- When `fpdf2` is not installed and no generator can produce a PDF, the system
  SHALL continue to degrade gracefully by retaining the Markdown recap without
  raising an unhandled error.
- When scripts are materialized or verified during onboarding, already-present,
  correct script files SHALL be left unchanged (no overwrite of valid scripts).

**Scope:**
All invocations that do NOT involve a missing bundled script
(`NOT isBugCondition(X)`) should be completely unaffected by this fix. This
includes:
- Hook/step invocations where the referenced script exists in the workspace.
- Recap-PDF generation where a bundled generator is present.
- Onboarding verification where the scripts directory and required scripts are
  already present and valid.

**Note:** The expected correct behavior for the buggy inputs is defined in the
Correctness Properties section (Property 1). This section captures what must NOT
change.

## Hypothesized Root Cause

Based on the bug analysis, the most likely issues are:

1. **No existence verification before invocation**: Hooks and steps run
   `python3 senzing-bootcamp/scripts/<name>.py` unconditionally. There is no
   `fileExists` guard, so a missing file surfaces as a raw interpreter error
   (exit 2, `No such file or directory`) instead of a handled condition.

2. **Scripts not materialized during onboarding**: Onboarding does not guarantee
   the bundled `senzing-bootcamp/scripts/` directory is materialized into the
   workspace, and there is no preflight check that warns/self-repairs when it (or
   a required script) is missing. Missing scripts therefore go undetected until a
   later hook or step fails.

3. **No inline fallback for the session logger**: `log_write_event.py` already
   fails silently internally (returns 0, swallows errors), but that protection
   never runs when the file itself is absent — the failure happens in the IDE's
   `runCommand` before any Python executes. There is no inline path that records
   the event without the bundled file.

4. **Recap PDF depends on a bundled file even when capable**: Step 0b prefers
   `generate_recap_pdf.py` then falls back to `generate_recap_pdf_inline.py`.
   Both are bundled files; when both are absent there is no file-independent path,
   so a capable environment (with `fpdf2` installed) still produces no PDF. The
   shared `recap_pdf_render.render_markdown_pdf` primitive can render directly
   from Markdown but is not reachable without a bundled entry point.

## Correctness Properties

Property 1: Bug Condition - Graceful Degradation and Self-Repair for Missing Scripts

_For any_ invocation where the bug condition holds (`isBugCondition(X)` returns
true — the referenced bundled script is absent), the fixed system SHALL NOT fail:
it SHALL exit with code 0, SHALL NOT emit a file-not-found error, and SHALL
preserve the downstream effect via an inline/no-op fallback. Specifically, a
missing session logger SHALL still append an equivalent `{ts, action, module}`
event to `config/session_log.jsonl`, and a missing recap generator SHALL still
render `docs/bootcamp_recap.pdf` from `docs/bootcamp_recap.md` via the
self-contained inline PDF path when `fpdf2` is installed (or degrade gracefully,
retaining the Markdown recap, when it is not).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Bundled Scripts Present

_For any_ invocation where the bug condition does NOT hold (`isBugCondition(X)`
returns false — the referenced bundled script is present), the fixed system SHALL
produce the same result as the original system, preserving the exact invocation
of the bundled script and its output/effects: the bundled `log_write_event.py` is
run for write logging, present bundled steps execute unchanged, the recap-PDF flow
prefers `generate_recap_pdf.py` then `generate_recap_pdf_inline.py`, graceful
Markdown-only degradation is retained when `fpdf2` is absent, and already-present
valid scripts are never overwritten during materialization.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**1. Onboarding materialization + preflight verification**

**File**: `senzing-bootcamp/scripts/preflight.py` (and the onboarding flow that
invokes it)

**Specific Changes**:
1. **Scripts-directory check**: Add a preflight check that verifies
   `senzing-bootcamp/scripts/` exists and contains the required scripts
   (`log_write_event.py`, `session_logger.py`, recap generators, etc.), emitting a
   `warn` (not `fail`) `CheckResult` with a remediation `fix` message when absent.
2. **Self-repair under `--fix`**: Extend the `AutoFixer` so the scripts-directory
   check can self-repair during onboarding (materialize/restore the bundled
   scripts directory) without overwriting already-present valid files
   (idempotent, no clobber).
3. **Run during onboarding**: Ensure onboarding runs this verification before any
   hook or step depends on the scripts directory.

**2. Session-logging graceful degradation (inline fallback)**

**File**: `senzing-bootcamp/hooks/session-log-events.kiro.hook` and a
self-contained inline logging path.

**Specific Changes**:
1. **Existence guard + inline fallback**: Change the hook so the `runCommand` no
   longer blindly runs `python3 .../log_write_event.py`. Either (a) guard with an
   existence check and route to a self-contained inline appender when the bundled
   script is absent, or (b) make the bundled invocation path tolerant such that a
   missing file results in exit 0 with the event still appended via the inline
   logger — never a file-not-found error to the terminal.
2. **Equivalent event**: The inline fallback SHALL append a JSON event equivalent
   to the bundled output (`{ts, action, module}`, module read from
   `config/bootcamp_progress.json`, clamped 0–11) to `config/session_log.jsonl`.
3. **Schema validity**: Keep the hook JSON schema valid (`name`, `version`,
   `when`, `then`) and the prompt/command free of unescaped/injectable input,
   per the hook-integrity rules.

**3. Generic step degradation**

**File**: Bootcamp/onboarding steps that shell out to
`senzing-bootcamp/scripts/<name>.py` (e.g. `preflight.py`, `install_hooks.py`,
`completion_artifacts.py`, `status.py`, `backup_project.py`).

**Specific Changes**:
1. **Existence check before shell-out**: Each step performs a `fileExists` check
   before invoking a bundled script and uses an inline/no-op fallback when absent,
   rather than failing with a file-not-found error.

**4. Self-contained inline recap-PDF path**

**File**: Graduation Step 0b and `senzing-bootcamp/scripts/recap_pdf_render.py`.

**Specific Changes**:
1. **File-independent render**: When both bundled generators are absent, Step 0b
   SHALL render `docs/bootcamp_recap.pdf` from `docs/bootcamp_recap.md` via the
   self-contained `recap_pdf_render.render_markdown_pdf` path, which does not
   depend on a bundled generator file.
2. **Preserve preference order**: Keep the existing preference — bundled
   `generate_recap_pdf.py` first, then `generate_recap_pdf_inline.py`, then the
   file-independent inline path — so present-script behavior is unchanged.
3. **Lazy, optional `fpdf2`**: Import `fpdf` lazily inside the render path only;
   when absent, degrade gracefully (retain Markdown recap, print
   `pip install fpdf2` hint), never import at module top level, never hard-fail.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples
that demonstrate the bug on unfixed code (missing-script invocations failing with
exit 2 and lost downstream effects), then verify the fix works correctly for all
missing-script inputs and preserves existing behavior for all present-script
inputs. Tests use pytest + Hypothesis and follow the workspace Python conventions
(stdlib only, `sys.path` import pattern, profile-driven example counts).

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the
fix. Confirm or refute the root-cause analysis. If refuted, re-hypothesize.

**Test Plan**: Write tests that simulate hook/step invocations referencing a
bundled script at a path where the file is absent (use a temp workspace with no
`senzing-bootcamp/scripts/` directory). Assert the intended fixed behavior (exit
0, no file-not-found message, downstream effect preserved). Run on UNFIXED code to
observe the failures and characterize the root cause.

**Test Cases**:
1. **Missing session logger**: Simulate the `session-log-events` runCommand when
   `log_write_event.py` is absent; expect a `session_log.jsonl` append (will fail
   on unfixed code — no append, exit 2).
2. **Missing recap generators with `fpdf2` present**: Run Step 0b with both
   generators absent; expect `docs/bootcamp_recap.pdf` rendered (will fail on
   unfixed code — no PDF).
3. **Missing generic step script**: Invoke a step that shells out to an absent
   `senzing-bootcamp/scripts/<name>.py`; expect graceful degradation (will fail on
   unfixed code — file-not-found).
4. **Onboarding with absent scripts directory**: Run preflight with no scripts
   directory; expect a `warn` + self-repair (may fail on unfixed code — no check).
5. **Edge case — generators absent and `fpdf2` absent**: Run Step 0b; expect
   graceful Markdown-only degradation with a hint (may already pass — informs
   whether the no-PDF path is correctly handled).

**Expected Counterexamples**:
- `python3: can't open file '.../log_write_event.py': [Errno 2] No such file or
  directory`, exit code 2, and no event appended to `config/session_log.jsonl`.
- No `docs/bootcamp_recap.pdf` produced despite `fpdf2` being importable.
- Possible causes: no existence guard before shell-out, no inline fallback, no
  onboarding materialization/preflight, recap path bound to bundled files.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed
function produces the expected behavior.

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  result := F_prime(X)
  ASSERT result.exitCode = 0
  ASSERT NOT result.emittedFileNotFoundError
  ASSERT downstreamEffectPreserved(X)
    // session event appended to config/session_log.jsonl via inline fallback, OR
    // recap PDF rendered from docs/bootcamp_recap.md when fpdf2 present
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (the
referenced script is present), the fixed function produces the same result as the
original function.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F_prime(X)
END FOR
```

**Testing Approach**: Property-based testing (Hypothesis) is recommended for
preservation checking because:
- It generates many invocation/state combinations automatically across the input
  domain (varied module numbers, recap contents, script sets).
- It catches edge cases that manual unit tests might miss.
- It provides strong guarantees that behavior is unchanged for all present-script
  inputs.

**Test Plan**: Observe behavior on UNFIXED code first for present-script
invocations (bundled logger runs, bundled recap generator used, present steps
execute), then write property-based tests capturing that behavior and assert the
fixed code reproduces it identically.

**Test Cases**:
1. **Bundled logger preservation**: With `log_write_event.py` present, verify the
   bundled script is invoked and the recorded event matches the original
   (timestamp + current module) on both unfixed and fixed code.
2. **Bundled recap generator preservation**: With `generate_recap_pdf.py` present,
   verify Step 0b uses it first (then `generate_recap_pdf_inline.py`) unchanged.
3. **Markdown-only degradation preservation**: With generators absent and `fpdf2`
   absent, verify graceful Markdown-only degradation is unchanged (no unhandled
   error).
4. **No-overwrite preservation**: With valid scripts already present, verify
   onboarding materialization/verification leaves them byte-for-byte unchanged.

### Unit Tests

- Existence-guard branching for the session logger (present → bundled path;
  absent → inline fallback), asserting exit 0 and a `session_log.jsonl` append in
  both cases.
- Preflight scripts-directory check producing `warn` when absent and `pass` when
  present; `AutoFixer` self-repair is idempotent and never clobbers valid files.
- Recap-PDF path selection: bundled-first preference, then file-independent inline
  path; lazy `fpdf` import and graceful hint when `fpdf2` is absent.
- Edge cases: empty/missing `config/bootcamp_progress.json` (module defaults to 0),
  empty recap Markdown, out-of-range module values clamped to 0–11.

### Property-Based Tests

- Generate random module numbers and progress-file states; assert the inline
  fallback appends a schema-equivalent `{ts, action, module}` event for every
  missing-logger invocation (Property 1).
- Generate random sets of present/absent bundled scripts; assert present-script
  invocations behave identically to the original (Property 2) and absent-script
  invocations exit 0 with the downstream effect preserved (Property 1).
- Generate random recap Markdown bodies; assert the inline PDF path renders a
  non-empty PDF when `fpdf2` is present and degrades gracefully (Markdown retained,
  hint printed) when it is absent — for both missing and present generators.

### Integration Tests

- Full write-then-log flow: trigger the `session-log-events` hook in a workspace
  without the scripts directory and confirm `config/session_log.jsonl` is written
  with no terminal error, then with the directory present and confirm the bundled
  path is used.
- Full graduation Step 0b flow: with generators absent and `fpdf2` installed,
  confirm `docs/bootcamp_recap.pdf` is produced; with generators present, confirm
  the bundled generator is used.
- Onboarding flow: confirm materialization/preflight verification runs before
  hooks/steps depend on the scripts directory, warns and self-repairs when absent,
  and leaves present valid scripts unchanged.
