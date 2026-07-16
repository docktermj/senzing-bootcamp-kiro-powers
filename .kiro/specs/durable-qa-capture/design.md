# Durable Q&A Capture Bugfix Design

## Overview

Throughout the bootcamp, every question the agent asks and every answer the
bootcamper gives is supposed to land durably in `config/session_log.jsonl` so
the graduation recap ("the trophy") reflects the real Q&A of the whole
experience. Today capture is *agent-voluntary*: the two Q&A hooks
(`ask-bootcamper` → `record-question`, `review-bootcamper-input` →
`record-answer`) are `type: agent` hooks that merely inject a prompt asking the
agent to run `log_qa_event.py`. When the agent skips that instruction, or a
session boundary / context compaction / restart intervenes, the event is never
persisted and the exchange is lost. At graduation the recap generator can only
recreate section structure via `render_backfill_section` and inserts the honest
placeholder "N/A (section backfilled at track completion; original session
content unavailable)" — silently masking the gap.

The fix has two coordinated parts, mirroring the two failure facets in the
requirements:

1. **Durable, write-through capture.** Move Q&A persistence off the agent's
   voluntary path and onto a deterministic, command-backed hook — exactly the
   pattern `session-log-events.json` already uses (`type: command` PostToolUse
   that shells out to a script). The capture command runs at the Stop /
   UserPromptSubmit Q&A cadence whether or not the agent narrates it, so the
   event is written at ask/answer time and survives boundaries. The existing
   `log_qa_event.py` helper already does the writing; the change is *who
   invokes it* — the runtime, deterministically, not the agent, voluntarily.

2. **Loud graduation validation.** Add a completeness check that runs before
   recap rendering: every module in `modules_completed` must have real captured
   `question`/`answer` events in `config/session_log.jsonl`. If any completed
   module has no real Q&A, the graduation path halts and names the offending
   module(s) instead of allowing `render_backfill_section` to emit placeholder
   text.

Both changes are surgical and preserve the existing capture semantics
(non-blocking, idempotent, paired, append-around, real-Q&A rendering,
stdlib-only).

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a Q&A cadence
  event occurs (a question is presented, or an answer is submitted) but no
  corresponding durable event is written to `config/session_log.jsonl` because
  capture depends on the agent voluntarily running the helper; and, at
  graduation, a completed module with no real Q&A is silently rendered with
  placeholder text.
- **Property (P)**: The desired behavior — the Q&A event is durably persisted at
  capture time by a deterministic (command-backed) hook, and graduation
  validates completeness and fails loudly on any gap.
- **Preservation**: Existing capture semantics that must remain unchanged —
  non-blocking behavior, idempotent question logging, answer-to-question
  pairing/self-heal, byte-for-byte append, real-Q&A rendering, and stdlib-only
  execution.
- **Q&A cadence**: The ask/answer boundary. A question is presented at the Stop
  boundary (`ask-bootcamper`); an answer arrives at the next `UserPromptSubmit`
  (`review-bootcamper-input`). Capture fires on this cadence, never per file
  write.
- **Agent-voluntary hook**: A `type: agent` hook whose `action.prompt` only
  *asks* the agent to perform work. Nothing is guaranteed to run.
- **Command-backed hook**: A `type: command` hook whose `action.command` is
  executed deterministically by the runtime (the model used by
  `session-log-events.json`).
- **`log_qa_event.py`**: The deterministic capture helper. `record-question`
  logs the pending question (reads `config/.question_pending`, dedupes via the
  `config/.qa_capture.json` sidecar); `record-answer` logs the answer from
  stdin, paired to the pending question's id. Non-blocking; always exits 0.
- **`session_logger.py`**: The event-schema library
  (`generate_question_id`, `build_completion_entry`, `append_completion_entry`).
- **`render_backfill_section`**: The `completion_artifacts.py` function that
  produces a schema-valid `## Module N:` section filled with `N/A` placeholders
  when the original session content is unavailable.
- **Real Q&A**: `question`/`answer` completion events in `session_log.jsonl`
  with genuine `data.text`, as opposed to a backfilled placeholder.

## Bug Details

### Bug Condition

The bug manifests on two paths. **Capture path:** a Q&A cadence event occurs but
the durable write is skipped because it rides on the agent's voluntary execution
of `log_qa_event.py` inside a `type: agent` hook — so a skipped instruction, a
session boundary, context compaction, or a restart leaves
`config/session_log.jsonl` with no matching `question`/`answer` event.
**Graduation path:** rendering begins while a completed module has no real
captured Q&A, and the system substitutes placeholder text via
`render_backfill_section` instead of failing loudly.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type QAEvent          # a question-presented or answer-submitted event
  OUTPUT: boolean

  RETURN input.isQACadenceEvent                       # a question was asked or answered
         AND NOT persistedDeterministically(input)    # capture rides on agent-voluntary hook
         AND eventMissingFrom("config/session_log.jsonl", input)
END FUNCTION

FUNCTION isGraduationBugCondition(state)
  INPUT: state of type GraduationState  # progress + session log at graduation
  OUTPUT: boolean

  RETURN renderingBegun(state)
         AND EXISTS module IN state.modulesCompleted SUCH THAT
             NOT hasRealQA("config/session_log.jsonl", module)
         AND rendersPlaceholderInsteadOfHalting(state, module)
END FUNCTION
```

### Examples

- **Cross-session loss (reported):** Modules 1-3 were completed in an earlier
  session under the agent-voluntary hooks. `config/session_log.jsonl` has no
  `question`/`answer` events for them. Expected: those events were written at
  ask/answer time and are present. Actual: absent — the exchanges are lost.
- **Compaction mid-module:** A question is presented (`config/.question_pending`
  written), context is compacted before the agent runs `record-question`, then
  the bootcamper answers. Expected: both the question and the answer are in the
  log. Actual: neither is, because the agent never ran the helper.
- **Silent placeholder at graduation:** Module 2 has no real Q&A at graduation.
  Expected: rendering halts and reports "Module 2 has no captured Q&A." Actual:
  the recap renders `- N/A (section backfilled at track completion; original
  session content unavailable)` and graduation reports success.
- **Edge — genuinely no substantive questions:** A module legitimately posed no
  substantive questions. Expected: this is distinguishable from a capture gap
  (an explicit "no questions" marker), so validation does not false-positive.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Modules whose Q&A *was* captured continue to render real question/answer pairs
  in ascending ask order, each response paired to its own question (Req 3.1).
- The capture helper stays non-blocking: any error is swallowed and it exits 0,
  never interrupting the bootcamp flow (Req 3.2).
- Question logging stays idempotent: a question re-presented across turns or a
  session boundary is never double-logged (Req 3.3).
- Answer recording stays paired to the pending question's id, self-healing by
  logging the question first when it was not already recorded (Req 3.4).
- Existing `config/session_log.jsonl` entries and existing
  `docs/bootcamp_recap.md` sections are preserved byte-for-byte (append-around,
  no overwrite) (Req 3.5).
- All Q&A capture code stays Python 3.11+ standard library only (Req 3.6).

**Scope:**
All inputs that do NOT involve the durability or validation defect should be
completely unaffected by this fix. This includes:
- Turns that produce no Q&A cadence event (silent pass-throughs, non-yielding
  continuations).
- Non-Q&A session-log events (`action` events from `session-log-events.json`,
  `module_complete`, etc.).
- Graduation of a track where every completed module already has real Q&A.

**Note:** The desired correct behavior is defined in the Correctness Properties
section below; this section fixes what must NOT change.

## Hypothesized Root Cause

Based on the bug report, the most likely causes are:

1. **Voluntary execution surface (primary).** Capture is wired to `type: agent`
   hooks (`ask-bootcamper`, `review-bootcamper-input`) whose `action.prompt`
   only *requests* that the agent run `log_qa_event.py`. The write therefore
   depends on the agent choosing to act and on the turn completing normally.
   Session boundaries, context compaction, and restarts drop the request before
   it executes. Contrast `session-log-events.json`, a `type: command`
   PostToolUse hook whose `action.command` the runtime runs deterministically —
   that path never depends on agent narration and never gets lost.

2. **No capture guarantee at ask time.** The pending question is written to
   `config/.question_pending` deterministically, but the corresponding
   `record-question` write is not — the marker exists while the event may not,
   so the log can diverge from the actual conversation state.

3. **Silent backfill at graduation (secondary).** The graduation/recap path has
   no pre-render completeness gate. When Q&A is missing it reaches
   `render_backfill_section`, which emits placeholder `N/A` text. A missing-Q&A
   gap is masked rather than surfaced, so the loss is invisible until a human
   inspects the recap.

4. **No distinction between "gap" and "legitimately empty."** Nothing records
   that a module intentionally had zero substantive questions, so a naive
   validator could either miss real gaps or false-positive on empty modules.

## Correctness Properties

Property 1: Bug Condition - Durable Write-Through Capture

_For any_ Q&A cadence event where the bug condition holds (isBugCondition
returns true), the fixed system SHALL persist the corresponding
`question`/`answer` event to `config/session_log.jsonl` via a deterministic,
command-backed (non-agent-voluntary) hook at ask/answer time, so the event is
present regardless of session boundaries, context compaction, or restarts.

**Validates: Requirements 2.1, 2.2**

Property 2: Bug Condition - Loud Graduation Validation

_For any_ graduation state where a completed module has no real captured Q&A
(isGraduationBugCondition returns true), the fixed system SHALL halt recap
rendering and report the missing module(s) rather than substituting the
placeholder "N/A (section backfilled at track completion; ...)" text.

**Validates: Requirements 2.3, 2.4**

Property 3: Preservation - Non-Blocking Capture

_For any_ input where the bug condition does NOT hold — including inputs that
cause the capture helper to error — the fixed helper SHALL produce the same
non-blocking outcome as the original: swallow the error and exit 0, never
interrupting the bootcamp flow.

**Validates: Requirements 3.2**

Property 4: Preservation - Idempotent Question Logging

_For any_ sequence where the same pending question is presented multiple times
(across turns or a session boundary), the fixed system SHALL log that question
exactly once, producing the same de-duplicated log the original produced.

**Validates: Requirements 3.3**

Property 5: Preservation - Answer-to-Question Pairing and Self-Heal

_For any_ answer recorded against a pending question, the fixed system SHALL
pair it to that question's id — logging the question first when it was not
already recorded — producing the same `(question, answer)` pairing the original
produced.

**Validates: Requirements 3.4**

Property 6: Preservation - Byte-for-Byte Append-Around

_For any_ pre-existing `config/session_log.jsonl` content or existing
`docs/bootcamp_recap.md` sections, the fixed system SHALL preserve prior bytes
unchanged, appending new content without overwriting — identical to the original
append-around behavior.

**Validates: Requirements 3.5**

Property 7: Preservation - Real-Q&A Rendering Unchanged

_For any_ module whose Q&A events were durably captured, the fixed recap SHALL
render the same real question/answer pairs in ascending ask order, each response
paired to its own question, exactly as the original renderer produced.

**Validates: Requirements 3.1**

Property 8: Preservation - Standard Library Only

_For any_ Q&A capture or validation code path introduced or modified by this
fix, the implementation SHALL use only the Python 3.11+ standard library, adding
no third-party runtime dependency.

**Validates: Requirements 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/hooks/capture-qa-events.json` (new) — or a paired
addition to the existing Q&A hooks

**Change**: Introduce deterministic, command-backed capture on the Q&A cadence,
modeled exactly on `session-log-events.json` (`type: command`). Two hook
entries, both non-blocking with a short `timeout`:

1. **Record question (Stop cadence).** A `Stop`-triggered `type: command` hook
   whose `action.command` runs, only when `config/.question_pending` exists:
   ```
   python3 senzing-bootcamp/scripts/log_qa_event.py record-question
   ```
   This persists the outstanding question deterministically at ask time,
   independent of any agent narration.

2. **Record answer (UserPromptSubmit cadence).** A `UserPromptSubmit`-triggered
   `type: command` hook whose `action.command` pipes the bootcamper's verbatim
   message on stdin to:
   ```
   python3 senzing-bootcamp/scripts/log_qa_event.py record-answer
   ```
   This persists the answer deterministically, paired to the pending question.

   The hook JSON follows the schema used by the existing hooks in this repo:
   `{ "version": "v1", "hooks": [ { "name", "trigger", "action": { "type":
   "command", "command", "timeout" } } ] }`. (Note: the security-rule shorthand
   `name/version/when/then` maps onto this repo's concrete
   `name/version/trigger/action` fields; we match the on-disk convention.)

**File**: `senzing-bootcamp/hooks/ask-bootcamper.json`,
`senzing-bootcamp/hooks/review-bootcamper-input.json`

**Change**: The agent-voluntary Q&A logging instructions become a redundant
best-effort backstop, not the primary path. Because the command-backed hook now
guarantees the write, the `type: agent` prompt no longer carries the durability
burden. Keep the agent prompts' non-Q&A behavior (phase logic, feedback/status
triggers) untouched; only the Q&A durability guarantee moves to the command
hook. `preToolUse`/write-backed hook removal safeguards do not apply here (we are
adding a hook, not removing a write hook).

**File**: `senzing-bootcamp/scripts/log_qa_event.py`

**Change**: No behavior change required — it is already deterministic,
idempotent, paired, non-blocking, and stdlib-only. It simply now runs from a
command hook instead of an agent prompt. (Optional hardening: ensure
`record-answer` reads stdin robustly when invoked by the command hook.)

**File**: `senzing-bootcamp/scripts/validate_qa_capture.py` (new)

**Change**: A stdlib-only validator that, given `config/bootcamp_progress.json`
and `config/session_log.jsonl`, checks that every module in `modules_completed`
has at least one real `question` event (and, where a question was answered, a
paired `answer`). It distinguishes a genuine gap from a legitimately
question-free module via an explicit marker (e.g., a "no substantive questions"
sentinel event) so it does not false-positive. CLI: exits non-zero and names the
missing module(s) on failure; `--json` for machine consumption; `--check` for
verify-only. It reuses `generate_transcript.read_events` /
`reconcile_transcript.count_logged_questions` for counting rather than
re-parsing.

**File**: `senzing-bootcamp/scripts/ensure_graduation_artifacts.py` (and/or the
graduation hook path)

**Change**: Invoke `validate_qa_capture.py` *before* any recap rendering /
backfill. If validation fails, halt graduation and surface the missing module(s)
to the bootcamper. `render_backfill_section`'s placeholder path is only reachable
for modules that legitimately have no Q&A (empty marker present), never as a
silent mask for a real gap.

## Testing Strategy

### Validation Approach

The strategy is two-phase: first surface counterexamples that demonstrate the
bug on the unfixed code, then verify the fix works and preserves existing
behavior. Property-based tests (pytest + Hypothesis) drive both the fix-checking
and preservation-checking so we cover the input domain broadly, using the
repo's Hypothesis profiles (`fast` locally, `thorough` in CI) rather than
hand-set `max_examples`.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing
the fix. Confirm or refute the root-cause analysis. If we refute, we
re-hypothesize.

**Test Plan**: Simulate the Q&A cadence *without* the agent running the helper
(the boundary/compaction/restart case), then inspect the log and the graduation
render. Run against the UNFIXED wiring to observe the loss and the silent
placeholder.

**Test Cases**:
1. **Agent-skip capture**: Present a question, submit an answer, but never call
   `log_qa_event.py` (simulating a skipped voluntary hook); assert
   `session_log.jsonl` has no matching events (will fail to persist on unfixed
   wiring).
2. **Cross-session loss**: Reproduce Modules 1-3 completed with no Q&A events;
   assert the events are absent (demonstrates 1.1/1.2).
3. **Silent placeholder at graduation**: Given a completed module with no real
   Q&A, run the graduation render; assert the recap contains the "backfilled at
   track completion" placeholder and graduation reports success (demonstrates
   1.3/1.4 — the behavior we will make fail loudly).
4. **Edge — legitimately empty module**: A module with zero substantive
   questions; confirm how the current path treats it (informs the gap-vs-empty
   distinction).

**Expected Counterexamples**:
- Q&A events missing from `session_log.jsonl` after a cadence event that the
  agent did not voluntarily log.
- A recap rendering placeholder text for a completed module while graduation
  still reports success.
- Possible causes: agent-voluntary hook type, no deterministic write at ask
  time, no pre-render completeness gate.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed
system produces the expected behavior (durable capture; loud validation).

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  runCommandBackedCapture(input)                       # deterministic, not agent-voluntary
  ASSERT eventPresentIn("config/session_log.jsonl", input)
END FOR

FOR ALL state WHERE isGraduationBugCondition(state) DO
  result := runGraduationValidation(state)
  ASSERT result.halted AND result.namesMissingModules
  ASSERT NOT recapContains(state, "backfilled at track completion")
END FOR
```

Property-based framing: generate arbitrary Q&A cadence sequences and arbitrary
`modules_completed` / session-log combinations, and assert (a) every cadence
event is persisted when the deterministic command runs, and (b) any completed
module lacking real Q&A causes validation to fail loudly and name the module.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the
fixed system produces the same result as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT original_capture(input) == fixed_capture(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation
because it generates many cases across the input domain automatically, catches
edge cases manual tests miss, and gives strong guarantees that behavior is
unchanged for all non-buggy inputs.

**Test Plan**: Observe behavior on the UNFIXED code first (non-blocking exit,
idempotent question logging, answer pairing/self-heal, byte-for-byte append,
real-Q&A rendering), then write property-based tests that capture that behavior
and assert the fixed code matches it.

**Test Cases**:
1. **Non-blocking preservation**: Feed error-inducing inputs (unreadable/absent
   files, malformed sidecar); assert the helper still exits 0 and raises
   nothing (Property 3).
2. **Idempotent question preservation**: Present the same pending question N
   times (Hypothesis-generated N and text); assert exactly one `question` event
   (Property 4).
3. **Answer-pairing preservation**: Generate question/answer pairs, including
   the self-heal case where no question was logged first; assert each answer
   carries the correct `question_id` (Property 5).
4. **Append-around preservation**: Generate pre-existing log/recap content;
   assert prior bytes are byte-for-byte unchanged after capture (Property 6).
5. **Real-Q&A rendering preservation**: Generate modules with durably captured
   Q&A; assert the recap renders the same ordered pairs as the original
   (Property 7).

### Unit Tests

- `log_qa_event.py` invoked as the command hook would invoke it
  (`record-question` with/without `config/.question_pending`; `record-answer`
  from stdin with/without a sidecar).
- `validate_qa_capture.py`: completed module with real Q&A passes; completed
  module missing Q&A fails and names the module; legitimately-empty module (with
  marker) passes; exit codes and `--json` output.
- Hook JSON schema validity for the new command-backed hook (`version`,
  `hooks[].name`, `trigger`, `action.type == "command"`, `action.command`).

### Property-Based Tests

- Generate arbitrary Q&A cadence sequences; assert every event is durably
  persisted when the deterministic command runs (Property 1).
- Generate arbitrary `(modules_completed, session_log)` states; assert
  validation halts and names missing modules for every real gap, and passes
  when all completed modules have real Q&A (Property 2).
- Generate repeated/interleaved question presentations to assert idempotency and
  pairing invariants hold (Properties 4, 5).
- Generate arbitrary pre-existing content to assert append-around preservation
  (Property 6).

### Integration Tests

- Full cadence: present question → (no agent narration) → command hook writes →
  answer submitted → command hook writes → assert both events present and paired
  (end-to-end durability).
- Cross-session: write events in "session A", start "session B", complete the
  track, run graduation; assert no module ends with an unrecoverable gap.
- Graduation gate: a completed module with a real gap causes
  `ensure_graduation_artifacts.py` to halt and report before any placeholder is
  rendered; a fully-captured track graduates and renders real Q&A unchanged.
