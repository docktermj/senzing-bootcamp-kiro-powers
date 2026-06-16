# Module Completion Artifacts Bugfix Design

## Overview

Every time a bootcamper finishes a module, the senzing-bootcamp power is supposed to
produce a consistent set of per-module completion artifacts:

1. A **recap section** appended to `docs/bootcamp_recap.md`
2. A **journal entry** appended to `docs/bootcamp_journal.md`
3. A **completion certificate** at `docs/progress/MODULE_N_COMPLETE.md`
4. A **real elapsed-time Duration** in the recap (per-module and cumulative `Total Duration`)

In practice these artifacts fire for only some modules. The shared root cause is the
**module-completion boundary-detection logic** (the `modules_completed`-diff check used by
the agentStop hooks `module-recap-append` and `module-completion-celebration`, and by the
`module-completion.md` completion workflow). It does not reliably trigger artifact generation
on every new entry added to `modules_completed` — most notably the **final module of a track**
(e.g., Module 7 for Core Bootcamp), because that completion often coincides with the track
celebration path rather than the per-module artifact path. Separately, the recap's **Duration**
fields are filled from LLM-derived "session context" rather than the ISO 8601 timestamps already
stored in `step_history`, so they degrade to meaningless placeholders such as `Module N session`.

The fix has two cooperating parts:

- **A deterministic, stdlib-only planner module** (`senzing-bootcamp/scripts/completion_artifacts.py`)
  that, given the progress state and the artifacts currently on disk, computes (a) which completed
  modules are missing which artifact types, (b) the real per-module Duration from `step_history`
  timestamps, and (c) the cumulative `Total Duration` — omitting any Duration that cannot be reliably
  derived rather than emitting a placeholder. This module is the unit- and property-testable core of
  the fix. It also drives **backfill** for already-completed modules.
- **Hook and steering alignment** so that boundary detection fires the full artifact set on *every*
  new `modules_completed` entry (including the final module of a track), feeds the planner's computed
  Duration values into the recap, and applies certificates uniformly across all completed modules.

The regression-prevention behaviors (byte-for-byte content preservation, non-blocking error handling,
invariant step order, `.question_pending` deferral, no spurious duplicates, an unaffected celebration
hook, and the `"Bootcamper"` default name) are preserved unchanged.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a module that is present in
  `modules_completed` but is missing one or more of its completion artifacts, or whose Duration is a
  placeholder while reliable timing is derivable from `step_history`.
- **Property (P)**: The desired behavior — for every completed module, all artifact types are present,
  applied uniformly, with Duration computed from real ISO 8601 timestamps (or omitted when unreliable).
- **Preservation**: Existing artifact content, error handling, step ordering, deferral, de-duplication,
  celebration behavior, and default-name handling that must remain unchanged by the fix.
- **Artifact set**: The four per-module outputs — recap section, journal entry, completion certificate,
  and the recap Duration value.
- **Boundary detection**: The logic that compares the current `modules_completed` array against the
  prior state to detect a newly completed module. Lives in the agentStop hooks and the
  `module-completion.md` workflow.
- **`step_history`**: The object in `config/bootcamp_progress.json` keyed by module-number strings
  (`"1"`..`"12"`), each value carrying `last_completed_step` and an ISO 8601 `updated_at` timestamp.
- **`started_at`**: The top-level ISO 8601 timestamp in `config/bootcamp_progress.json` marking when
  the bootcamp began; used as the lower bound for the first module's elapsed time.
- **completion_artifacts.py**: The new stdlib-only planner module that computes artifact coverage gaps,
  per-module Duration, and cumulative Total Duration, and produces a deterministic backfill plan.
- **Backfill**: Generating the artifacts that are missing for modules completed *before* the fix, so the
  artifact set becomes complete and consistent for all completed modules.

## Bug Details

### Bug Condition

The bug manifests when a module number is present in `modules_completed` but the per-module artifact
generation governed by boundary detection did not produce the full, consistent artifact set for it —
or produced a placeholder Duration when real timing was derivable. This happens most reliably for the
**final module of a track** (boundary detection is shadowed by the track-completion celebration path)
and for **modules completed before the artifact logic existed** (no backfill mechanism). The Duration
defect is independent: the recap fills Duration from LLM session context (`Module N session`) instead of
computing it from the ISO 8601 timestamps in `step_history`.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type ProgressState
         (modules_completed: list[int],
          step_history: map[str -> {updated_at: ISO8601, last_completed_step}],
          started_at: ISO8601 | None,
          existing_artifacts: ArtifactInventory  // recap sections, journal entries, certificates on disk
          recap_durations: map[int -> str],      // per-module Duration text currently in recap
          recap_total_duration: str | None)
  OUTPUT: boolean

  // (a) Coverage gap: a completed module is missing at least one artifact type
  coverageGap := EXISTS m IN modules_completed SUCH THAT
                   NOT existing_artifacts.hasRecapSection(m)
                   OR NOT existing_artifacts.hasJournalEntry(m)
                   OR NOT existing_artifacts.hasCertificate(m)

  // (b) Non-uniform certificates: some completed modules have certificates and some do not
  certificatesNonUniform := (SOME m IN modules_completed has a certificate)
                            AND (SOME m IN modules_completed has no certificate)

  // (c) Placeholder per-module Duration while real timing is derivable
  placeholderDuration := EXISTS m IN modules_completed SUCH THAT
                           isPlaceholder(recap_durations[m])
                           AND reliableTiming(step_history, started_at, m) IS NOT None

  // (d) Placeholder Total Duration while real timing is derivable
  placeholderTotal := isPlaceholder(recap_total_duration)
                      AND reliableTotalTiming(step_history, started_at, modules_completed) IS NOT None

  RETURN coverageGap OR certificatesNonUniform OR placeholderDuration OR placeholderTotal
END FUNCTION
```

Where `isPlaceholder(text)` returns true for empty/missing values and for non-time strings such as
`"Module N session"`, `"Module 7 session"`, etc. (any value not parseable as a real elapsed duration),
and `reliableTiming(...)` returns a computed duration only when the module's bounding ISO 8601 timestamps
exist, parse successfully, and are ordered (end ≥ start); otherwise it returns `None`.

### Examples

- **Final module missing recap section** — `modules_completed: [1,2,3,4,5,6,7]`, gate `7_complete: completed`,
  but `docs/bootcamp_recap.md` has sections only for Modules 1–6. Expected: a Module 7 recap section exists.
- **Placeholder per-module Duration** — A recap Module 3 section shows `### Duration\nModule 3 session`,
  while `step_history["3"].updated_at` and the prior module timestamp are both valid ISO 8601. Expected:
  a real elapsed time (e.g., `1h 12m`) computed from those timestamps.
- **Placeholder Total Duration** — Header shows `**Total Duration:** Module N session` while reliable
  per-module times exist. Expected: a real cumulative time rolled up from per-module elapsed times.
- **Non-uniform certificates** — `docs/progress/` contains only `MODULE_6_COMPLETE.md` and
  `MODULE_7_COMPLETE.md` although Modules 1–7 are complete. Expected: a certificate for every completed
  module (or none at all), applied uniformly.
- **Missing journal entries** — `docs/bootcamp_journal.md` has entries for Modules 3, 6, 7 only.
  Expected: an entry for every completed module.
- **Edge case (unreliable timing)** — `step_history["4"]` is absent or `updated_at` is unparseable.
  Expected: the Module 4 recap omits the `### Duration` field entirely rather than emitting a placeholder.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Pre-existing content in `docs/bootcamp_recap.md` and `docs/bootcamp_journal.md` is preserved
  byte-for-byte; already-correct entries are never overwritten or reordered (Req 3.1).
- Artifact-creation steps continue to handle file-system errors and timeouts non-blockingly — log a
  warning in the established format and proceed to the next step (Req 3.2).
- The completion steps continue to execute in the fixed, invariant order: `progress_update`,
  `recap_append`, `journal_entry`, `completion_certificate`, `next_step_options` (Req 3.3).
- When `config/.question_pending` exists at completion-check time, the system continues to defer to
  `ask-bootcamper` and produces no completion-artifact output (Req 3.4).
- When `modules_completed` has not gained a new entry, no recap/journal/certificate output is produced —
  no spurious duplicate artifacts (Req 3.5).
- The `module-completion-celebration` hook continues to display its celebration and next-step guidance
  without writing files, unaffected by the artifact-generation changes (Req 3.6).
- When `config/bootcamp_preferences.yaml` is missing or lacks a `name` field, `"Bootcamper"` continues to
  be used as the default name in artifact headers (Req 3.7).

**Scope:**
All inputs where the artifact set is *already* complete and consistent and Durations are already real
(i.e., `isBugCondition` is false) must be completely unaffected by this fix. This includes:
- Progress states with no newly added `modules_completed` entry (no-op path).
- States where `.question_pending` is present (deferral path).
- The celebration hook's read-only behavior.

**Note:** The expected *correct* behavior for buggy inputs is defined in the Correctness Properties
section (Properties 1, 3, 4, 5, 6). This section focuses on what must NOT change.

## Hypothesized Root Cause

Based on the bug description and the current implementation
(`hooks/module-recap-append.kiro.hook`, `hooks/module-completion-celebration.kiro.hook`,
`steering/module-completion.md`, and `step_history` in `config/bootcamp_progress.json`):

1. **Boundary detection shadowed at track end**: For the final module of a track, the
   `module-completion-celebration` boundary detection routes into the *track-completion* celebration
   (graduation acknowledgment, export/record/analytics offers) and the per-module artifact path
   (`recap_append` / `journal_entry` / `completion_certificate`) is not invoked. Result: the final
   module's artifacts are skipped.

2. **Artifact steps not uniformly bound to the same trigger**: The recap append runs from an agentStop
   hook, but the journal entry and certificate run only when the bootcamper explicitly invokes the full
   `module-completion.md` workflow ("completion" / "journal"). When that explicit step is skipped for
   some modules, those artifacts are never produced — yielding the partial, inconsistent sets observed.

3. **Duration sourced from LLM session context, not timestamps**: Step 3 of the recap hook gathers
   "Duration: elapsed time from module start to completion" from conversational context. With no real
   timing source wired in, the agent emits placeholders (`Module N session`). The ISO 8601 timestamps in
   `step_history[*].updated_at` and the top-level `started_at` are never consulted.

4. **No backfill mechanism**: There is no routine that, given the current `modules_completed` and the
   artifacts on disk, detects and fills the gaps for modules completed before the fix.

The planner module + hook/steering alignment described below address causes 1–4 directly. The
exploratory tests in the Testing Strategy will confirm or refute each cause before implementation.

## Correctness Properties

Property 1: Bug Condition — Complete artifact coverage for every completed module

_For any_ progress state where the bug condition holds because a completed module is missing one or more
artifact types (`isBugCondition` returns true via the coverage-gap clause), the fixed planner SHALL
report that module as needing the missing artifact type(s), and the aligned boundary-detection flow SHALL
produce a recap section, a journal entry, and a completion certificate for every module in
`modules_completed` — including the final module of a track.

**Validates: Requirements 2.1, 2.5, 2.6**

Property 2: Preservation — Non-buggy inputs are unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition` returns false) — including states
with no newly added `modules_completed` entry, states with `.question_pending` present, and states whose
artifact set is already complete with real Durations — the fixed code SHALL produce exactly the same
result as the original code: no spurious artifacts, existing recap/journal content preserved byte-for-byte,
the invariant step order retained, the celebration hook writing no files, non-blocking error handling, and
`"Bootcamper"` used as the default name when none is configured.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

Property 3: Bug Condition — Real per-module Duration or omission

_For any_ completed module whose recap Duration is a placeholder while reliable timing is derivable
(`isBugCondition` true via the placeholder-duration clause), the fixed planner SHALL compute the
module's elapsed time from the ISO 8601 timestamps in `step_history` (bounded below by the prior module's
timestamp or `started_at`). _For any_ completed module whose bounding timestamps are missing, unparseable,
or out of order, the planner SHALL return `None` so the recap omits the `### Duration` field entirely
rather than emitting a placeholder.

**Validates: Requirements 2.2**

Property 4: Bug Condition — Real cumulative Total Duration or omission

_For any_ progress state where the recap `Total Duration` is a placeholder while reliable per-module
timing exists, the fixed planner SHALL compute `Total Duration` by rolling up the real per-module elapsed
times, and the rolled-up value SHALL be monotonically non-decreasing as modules are added. IF reliable
timing cannot be derived for the roll-up, the planner SHALL return `None` so the header omits the
`Total Duration` field rather than emitting a placeholder.

**Validates: Requirements 2.3**

Property 5: Bug Condition — Uniform certificate application

_For any_ progress state where certificates are applied non-uniformly across completed modules
(`isBugCondition` true via the non-uniform clause), the fixed planner SHALL produce a backfill plan that
results in either a `docs/progress/MODULE_N_COMPLETE.md` for every completed module or none at all —
never a partial subset.

**Validates: Requirements 2.4**

Property 6: Bug Condition — Backfill completes the set without duplication

_For any_ progress state with artifacts present for only some completed modules, the fixed planner SHALL
identify exactly the missing recap sections, journal entries, and certificates (the set difference between
`modules_completed` and the artifacts already on disk) and SHALL NOT re-emit artifacts that already exist,
so that after backfill the per-module artifact set is complete and consistent with no duplicates.

**Validates: Requirements 2.6, 3.5**

## Fix Implementation

### Changes Required

Assuming the root cause analysis is correct, the fix introduces one new deterministic module and aligns
the hooks/steering to use it.

**File**: `senzing-bootcamp/scripts/completion_artifacts.py` (new, stdlib-only)

Follows the project script pattern: shebang, module docstring with usage, `from __future__ import
annotations`, dataclasses, `argparse`-based `main(argv=None)`, exit 0/1. It exposes a testable API and a
CLI used by the hooks/workflow.

**Functions / API**:

1. **`compute_module_duration(step_history, started_at, module, prior_timestamp) -> str | None`**
   - Determine the module's lower bound (the prior completed module's `updated_at`, or `started_at` for the
     first module) and upper bound (`step_history[str(module)].updated_at`).
   - Parse both with `datetime.datetime.fromisoformat` (normalizing a trailing `Z` to `+00:00`).
   - If either bound is missing, unparseable, or `end < start`, return `None` (omit Duration).
   - Otherwise format the `timedelta` as a human-readable elapsed time (e.g., `1h 12m`, `2d 3h`).

2. **`compute_total_duration(step_history, started_at, modules_completed) -> str | None`**
   - Roll up per-module elapsed times for `modules_completed` in ascending order.
   - Return `None` if no reliable per-module timing is available; otherwise format the cumulative total.
   - Guarantee monotonic non-decrease as modules are added.

3. **`detect_artifact_gaps(modules_completed, inventory) -> ArtifactGapReport`**
   - Given the completed modules and an `ArtifactInventory` (recap sections, journal entries, certificates
     discovered on disk), return, per artifact type, the sorted list of modules missing that artifact.
   - Drive the uniform-certificate rule: if any certificate exists, every completed module is required to
     have one.

4. **`plan_backfill(progress_state, inventory) -> BackfillPlan`**
   - Combine `detect_artifact_gaps` with the duration computations to produce a deterministic, idempotent
     plan describing exactly which artifacts to create for which modules (set difference only — never
     re-emitting existing artifacts).

5. **`isBugCondition(progress_state, inventory, recap_durations, recap_total) -> bool`** (mirrors the
   formal spec; used by tests and the CLI `--check` mode).

6. **`main(argv=None)`** — CLI:
   - `--progress`, `--recap`, `--journal`, `--progress-dir` inputs.
   - `--check` prints the gap/placeholder report and exits 1 if `isBugCondition` is true (CI-friendly).
   - `--plan` emits the backfill plan as JSON for the workflow to consume.

**File**: `senzing-bootcamp/hooks/module-recap-append.kiro.hook` (+ mirror text in
`steering/hook-registry-modules.md`)

- Replace the LLM-derived "Duration" step with a step that obtains the per-module Duration and cumulative
  `Total Duration` from `completion_artifacts.py` (reading `step_history`/`started_at`). When the helper
  returns no value, **omit** the `### Duration` field (and the header `Total Duration`) rather than writing
  a placeholder.
- Ensure boundary detection here also fires for the **final module of a track** (do not let track
  completion suppress the per-module recap section).
- Preserve all byte-for-byte append and non-blocking error-handling constraints already present.

**File**: `senzing-bootcamp/steering/module-completion.md`

- Bind `journal_entry` and `completion_certificate` to the **same boundary-detection trigger** as
  `recap_append`, so all four artifacts fire together on every new `modules_completed` entry (including the
  final module), not only when the bootcamper explicitly invokes the full workflow.
- Add a **backfill** step: on a completion boundary, run `completion_artifacts.py --plan` and generate any
  missing artifacts for already-completed modules, applying certificates uniformly.
- Source the certificate `Time Spent` and recap Duration from `completion_artifacts.py`; omit the field when
  timing is unreliable.
- Keep the fixed step order, non-blocking error handling, `.question_pending` deferral, the no-new-entry
  no-op, and the `"Bootcamper"` default unchanged.

**File**: `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook`

- No behavioral change to the celebration itself (it must remain read-only and write no files). The only
  requirement is that its track-completion branch must not *suppress* the per-module artifact path for the
  final module — that coordination lives in the recap hook and `module-completion.md`, not here.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug
on the unfixed code/state, then verify the fix produces complete, consistent artifacts with real timing and
preserves existing behavior. The deterministic `completion_artifacts.py` planner is the primary surface for
unit and property-based tests; hook/steering alignment is covered by integration-style tests against
`validate_completion_artifacts.py`.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute
the root-cause analysis. If we refute a cause, we re-hypothesize.

**Test Plan**: Construct progress states and on-disk artifact inventories that mirror the reported defect
(`modules_completed: [1..7]`, partial recap/journal/certificate sets, placeholder Durations) and assert the
expected complete-and-consistent outcome. Run these against the unfixed flow to observe failures.

**Test Cases**:
1. **Final-module recap missing** (Cause 1): completed `[1..7]`, recap has Modules 1–6 only — assert a
   Module 7 recap section is expected (will fail on unfixed flow).
2. **Journal/certificate not bound to trigger** (Cause 2): completed `[1..7]`, journal has `[3,6,7]`,
   certificates `[6,7]` — assert entries/certificates for all 7 (will fail on unfixed flow).
3. **Placeholder per-module Duration** (Cause 3): recap Module 3 Duration is `Module 3 session` while
   `step_history` has valid timestamps — assert a real computed elapsed time (will fail on unfixed flow).
4. **Placeholder Total Duration** (Cause 3): header `Total Duration` is a placeholder while reliable timing
   exists — assert a real cumulative time (will fail on unfixed flow).
5. **No backfill mechanism** (Cause 4): partial artifact set with no trigger — assert backfill fills the gap
   (will fail on unfixed flow).
6. **Edge case — unreliable timing**: `step_history["4"]` missing/unparseable — assert the Module 4 Duration
   field is omitted, not a placeholder (may fail on unfixed flow).

**Expected Counterexamples**:
- Final-module and arbitrary-module artifacts absent from recap/journal/`docs/progress/`.
- Duration fields containing `Module N session` instead of computed elapsed times.
- Possible causes: track-completion shadowing boundary detection, artifact steps not bound to the shared
  trigger, Duration sourced from session context rather than `step_history`, and no backfill routine.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed planner/flow produces the
expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  plan   := plan_backfill(input.progress_state, input.inventory)
  result := apply(plan)   // recap sections, journal entries, certificates, durations
  ASSERT FOR ALL m IN input.modules_completed:
           result.hasRecapSection(m)
           AND result.hasJournalEntry(m)
           AND result.hasCertificate(m)
  ASSERT certificatesUniform(result, input.modules_completed)
  ASSERT FOR ALL m: result.duration(m) = computeOrOmit(step_history, started_at, m)
  ASSERT result.totalDuration = computeTotalOrOmit(step_history, started_at, modules_completed)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed code produces the same
result as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalFlow(input) = fixedFlow(input)
END FOR
```

**Testing Approach**: Property-based testing (Hypothesis) is recommended for preservation checking because:
- It generates many progress states / artifact inventories automatically across the input domain.
- It catches edge cases (empty `modules_completed`, missing files, `.question_pending` present, already-complete
  sets) that hand-written unit tests miss.
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: Observe behavior on the unfixed flow for non-buggy inputs (no new module, complete artifact
set, `.question_pending` present, default-name fallback), then write property-based tests capturing that
behavior and re-run against the fixed flow.

**Test Cases**:
1. **No-new-entry no-op**: `modules_completed` unchanged — assert no recap/journal/certificate output is
   produced (Req 3.5), unchanged before and after fix.
2. **Byte-for-byte preservation**: append to an existing recap/journal — assert all prior bytes are identical
   after the operation (Req 3.1).
3. **Question-pending deferral**: `config/.question_pending` present — assert no artifact output (Req 3.4).
4. **Default name**: preferences missing/`name` absent — assert `"Bootcamper"` used in headers (Req 3.7).
5. **Non-blocking errors**: simulate a write failure — assert a warning is logged and the flow continues in
   the fixed step order (Req 3.2, 3.3).
6. **Celebration read-only**: assert the celebration hook writes no files (Req 3.6).

### Unit Tests

- `compute_module_duration`: valid bounds → formatted elapsed time; missing/unparseable/out-of-order bounds
  → `None`; first module uses `started_at` as the lower bound.
- `compute_total_duration`: roll-up correctness; `None` when no reliable timing; monotonic non-decrease.
- `detect_artifact_gaps`: correct per-type missing-module lists; uniform-certificate rule.
- `plan_backfill`: idempotency (re-running on a complete set yields an empty plan); set-difference only.
- `isBugCondition`: each clause (coverage gap, non-uniform certificates, placeholder duration, placeholder
  total) toggles the result as specified.

### Property-Based Tests

- Generate random `modules_completed` subsets and artifact inventories; assert `plan_backfill` always yields
  a plan that completes the set with no duplicates (Properties 1, 6).
- Generate random valid/invalid `step_history` timestamp maps; assert `compute_module_duration` returns a
  parseable elapsed time exactly when bounds are valid/ordered, and `None` otherwise (Property 3).
- Generate increasing sequences of completed modules; assert `compute_total_duration` is monotonically
  non-decreasing and omits rather than placeholders when unreliable (Property 4).
- Generate states where `isBugCondition` is false; assert the fixed flow output equals the original
  (Property 2 — preservation).

### Integration Tests

- Full completion flow for the **final module of a track** (Module 7 Core, Module 11 Advanced): assert recap
  section, journal entry, and certificate all appear, and `validate_completion_artifacts.py` passes.
- Backfill on a project mirroring the reported state (`[1..7]` complete, partial artifacts): assert the
  artifact set is complete and consistent afterward.
- Context switching across modules then completing: assert correct per-module Durations and a monotonic
  `Total Duration`, with omission on modules lacking reliable timestamps.
