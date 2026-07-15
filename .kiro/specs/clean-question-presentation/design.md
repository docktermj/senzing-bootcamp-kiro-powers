# Clean Question Presentation Bugfix Design

## Overview

Two related UX defects reach the bootcamper when the agent asks a 👉 question,
and both are driven entirely by the steering files — there is no application
code path. The fix keeps every behavioral guarantee the steering already
enforces (end-the-turn, wait-for-input, never-skip-a-gate, one question per
turn) while removing what leaks to the bootcamper:

- **Bug 1 — internal directives leak into user-facing output.** The `🛑 STOP`
  and `⛔ MANDATORY GATE` glyphs are currently used two ways in steering: as
  *internal agent directives* ("end here and wait") **and** as *emitted content*
  inside "CORRECT" example turns. That ambiguity taught the agent to render the
  glyphs next to the 👉 question. The fix makes both glyphs **internal-only**
  directives: they still govern agent behavior, but they are never rendered
  beside the question the bootcamper sees.

- **Bug 2 — the same question is displayed twice.** A comprehension-check
  question was first composed as a prose "or" compound, the compound-question
  self-correction regenerated it as a clean single question, and the bootcamper
  saw the question twice. The fix requires composing a clean, single,
  non-compound 👉 question on the **first** attempt and suppressing any duplicate
  re-display from an internal correction pass.

The fix strategy is: (1) add one authoritative "internal-only directive" rule to
the governing steering files; (2) rewrite every steering example that renders a
marker as emitted content so the correct output ends on the 👉 question; (3)
reinforce the compose-clean-first and no-duplicate-re-display rules; and (4)
reconcile the conversational-eval harness so a question turn is recognized as
correctly bounded from the trailing 👉 question alone — without a rendered
`🛑 STOP` line — and every shipped fixture keeps passing so CI stays at exit 0.

A guiding constraint runs through the whole fix: the harness engine
(`eval_conversations.py`) is **not** the defect and is **not** modified. Its
`ends_with_question_then_stop` predicate already treats a turn that ends on the
👉 line (nothing substantive after it) as correctly bounded, and it still treats
a `🛑 STOP` line as a boundary when one is present. That backward compatibility
is what lets us drop the rendered marker from fixtures without touching the
predicate logic.

## Glossary

- **Bug_Condition (C)**: The condition that triggers either defect when the
  agent presents a question. `C(X) = C1(X) OR C2(X)` (marker leak OR duplicate
  question).
- **C1 (Marker Leak)**: The rendered agent turn contains a 👉 question AND a
  user-facing `🛑 STOP` or `⛔ MANDATORY GATE` marker line.
- **C2 (Duplicate Question)**: The rendered agent turn presents the same
  question more than once, or composes a compound question first that forces a
  regeneration the bootcamper then sees twice.
- **Property (P)**: The desired behavior for a question presentation — a single,
  clean, non-compound 👉 question, shown exactly once, with the stop/gate
  semantics preserved but no marker rendered.
- **Preservation**: The existing turn-taking guarantees, gate enforcement, the
  One Question Rule / leading-question guarantee, the `config/.question_pending`
  mechanism, the harness engine, and all non-question output must remain
  unchanged by the fix.
- **Internal-only directive**: A `🛑 STOP` / `⛔ MANDATORY GATE` marker that
  governs agent behavior (end-the-turn, wait-for-input, never-skip) but is never
  emitted to the bootcamper.
- **Rendered turn**: The user-facing agent-turn text — exactly what the
  conversational-eval harness evaluates as an agent turn's `content`.
- **The_Harness**: `senzing-bootcamp/scripts/eval_conversations.py`, the offline,
  deterministic checker that evaluates recorded transcript fixtures against
  declarative behavioral assertions. Not modified by this fix.
- **POINTER (👉)**: The pointer marker (`\U0001f449`) prefixing every
  input-requiring prompt (Rule 4).
- **`ends_with_question_then_stop`**: The harness predicate that passes when a
  pointer prompt ends the turn with only whitespace / a hard-stop boundary after
  it. Already passes when the 👉 line is the last line.
- **`gate_not_bypassed`**: The harness predicate that passes when a mandatory
  gate turn shows execution evidence and offers no bypass. Its execution
  evidence includes non-marker signals ("checkpoint written",
  "module_3_verification", "visualization is running") in addition to a
  `🛑 STOP` boundary.

## Bug Details

### Bug Condition

The bug manifests when the agent presents a 👉 question to the bootcamper and
either (C1) a `🛑 STOP` / `⛔ MANDATORY GATE` internal directive is rendered on a
user-facing line beside that question, or (C2) the same question reaches the
bootcamper more than once (because it was composed as a compound question first
and then regenerated, or an internal correction pass re-emitted it).

**Formal Specification:**

```
FUNCTION isBugCondition(X)
  INPUT:  X — a rendered agent turn that presents a 👉 question
  OUTPUT: boolean

  // --- Bug 1: internal directive leaks into user-facing output ---
  hasQuestion := count_pointers(X.content) >= 1
  leaksMarker := containsMarker(X.content, "🛑")
                 OR containsMarker(X.content, "⛔")
                 OR containsMarker(X.content, "MANDATORY GATE")
  C1 := hasQuestion AND leaksMarker

  // --- Bug 2: the same question is displayed twice ---
  duplicated := count_pointers(X.content) > 1
                AND sameQuestionRenderedTwice(X.content)
  composedCompoundFirst := firstComposedQuestion(X) is compound
                           AND regeneratedQuestionAlreadyShown(X)
  C2 := duplicated OR composedCompoundFirst

  RETURN C1 OR C2
END FUNCTION
```

```
FUNCTION expectedBehavior(result)
  INPUT:  result — the rendered agent turn produced by the fixed steering
  OUTPUT: boolean

  RETURN count_pointers(result) == 1                       // exactly one 👉
         AND endsWithQuestionThenStop(result)              // ends on the question
         AND NOT hasCompoundQuestion(result)               // single, non-compound
         AND NOT selfAnswers(result)                       // no self-answer
         AND NOT containsMarker(result, "🛑")              // no leaked stop marker
         AND NOT containsMarker(result, "⛔")              // no leaked gate marker
         AND questionShownExactlyOnce(result)              // no duplicate
END FUNCTION
```

### Examples

- **Language selection (Bug 1).** Expected: `👉 **Which programming language
  would you like to use for the bootcamp?**` as the final line. Actual: the
  question is followed by a rendered `🛑 STOP — Wait for the bootcamper's ...`
  line (see `onboarding-phase1b-intro-language.md`) and, at the gate,
  `⛔ **MANDATORY GATE** — ...`.
- **Confirmation question (Bug 1).** Expected: the turn ends on
  `👉 **Does that capture your situation accurately?**`. Actual: the shipped
  fixture `confirmation_question_disambiguation.json` renders a trailing
  `🛑 STOP — End your response here ...` line.
- **Module 3 visualization gate (Bug 1).** Expected: the gate turn shows
  execution evidence ("Your visualization is running", "Checkpoint written:
  module_3_verification..."), then ends on the 👉 question. Actual: a trailing
  `🛑 STOP — ...` line is rendered after the question
  (`module3_gate_not_bypassed.json`).
- **Comprehension check (Bug 2).** Expected (first attempt):
  `👉 **Does the overview make sense before we choose a track?**` shown once.
  Actual: `"Does everything make sense so far, or is there anything you'd like me
  to clarify?"` (a prose "or" compound) is composed first, the compound-question
  self-correction regenerates a clean question, and the bootcamper sees the
  question twice.
- **Edge case — bootcamper asks to see the question again.** Expected: the agent
  re-displays the question. This is NOT the bug (`C(X)` is false) — an explicit
  request to re-show is preserved behavior (see 3.5).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- The One Question Rule and leading-question guarantee: every yielding turn still
  ends with exactly one 👉 question wrapped in bold.
- The Question Stop Protocol semantics: the agent still stops and waits for real
  input at every 👉 question and ⛔ gate — no self-answering, no assuming a
  response, no proceeding.
- Mandatory gate enforcement: ⛔ gate steps still execute unconditionally and are
  never skipped, even though the `⛔ MANDATORY GATE` glyph is no longer rendered
  to the bootcamper. The `enforce-mandatory-gate` and `enforce-gate-on-stop`
  hooks and the `gate_not_bypassed` predicate keep working via non-marker
  execution evidence.
- The `config/.question_pending` write/delete mechanism and the compound-question
  rewrite protocol (Rule 3 / Pre-Output Validation Checklist) remain in force.
- The harness engine (`eval_conversations.py`) is unmodified — every predicate
  behaves identically for every input.
- Internal agent directives that instruct behavior (e.g., the "Do not answer this
  question. Wait for the bootcamper's real input." blockquotes in
  `module-01-phase1-discovery.md`, `module-08-phaseA-requirements.md`,
  `track-switching.md`) continue to govern the agent; only their user-facing
  rendering is eliminated.

**Scope:**

All inputs that do NOT involve rendering an internal directive beside a question
and do NOT involve a duplicate question should be completely unaffected by this
fix. This includes:

- Non-question turns: prose, status updates, tool calls, module transitions.
- Gate-execution turns whose "executed" evidence is non-marker (checkpoint
  written / verification recorded / visualization running).
- The harness predicates themselves and their property tests (which use a
  `🛑 STOP` boundary line as a fixture-authoring convention).
- Any turn where the bootcamper explicitly asks to see a question again.

**Note:** The actual expected correct behavior is defined in the Correctness
Properties section (Properties 1 and 2). This section focuses on what must NOT
change.

## Hypothesized Root Cause

Based on the bug analysis, the most likely issues are:

1. **Glyph overloading in steering (Bug 1 primary cause).** The `🛑 STOP` and
   `⛔ MANDATORY GATE` glyphs are used both as internal agent directives and as
   emitted content inside "CORRECT" example turns. The agent could not reliably
   distinguish "this is an instruction to me" from "this is what I should
   output," so it rendered the glyph beside the question.
   - Emitted-content occurrences: `conversation-protocol.md` (Multi-Question /
     Not-Waiting / Self-Answering CORRECT examples), `conversation-examples.md`
     (same CORRECT examples), `feedback-workflow.md` (per-step `🛑 STOP — End
     your response here.` lines), `visualization-guide.md` ("end your response
     with: > 🛑 STOP"), `onboarding-phase1b-intro-language.md` (`🛑 STOP — Wait
     ...` and `⛔ **MANDATORY GATE** — ...`).
   - Directive occurrences that are already internal-facing but ambiguous:
     `module-01-phase1-discovery.md`, `module-08-phaseA-requirements.md`,
     `track-switching.md`.

2. **A rule that presumes the marker is emitted.** `conversation-protocol.md`
   states "The 🛑 STOP marker stays plain — never wrap 🛑 STOP in bold," which
   only makes sense if the marker is part of the output. This rule (and the
   tests that assert it) encodes the buggy expectation and must be updated.

3. **Compound-first composition (Bug 2 primary cause).** No rule requires the
   *first* composed question to be non-compound; the compound-question
   self-correction is expected to clean it up. When that correction runs after
   the first question was already surfaced, the regenerated question is emitted
   again — a visible duplicate.

4. **No "no re-display" rule for internal correction passes.** Nothing instructs
   the agent to suppress re-emitting a question that was already shown (unless
   the bootcamper asks), so a correction/hook pass can duplicate it.

## Correctness Properties

Property 1: Bug Condition — Clean Question, No Leaked Internal Markers

_For any_ rendered agent turn that presents a 👉 question (the Bug_Condition C1
branch), the fixed steering SHALL produce a turn that contains exactly one 👉
question, ends on that question, is non-compound, does not self-answer, and
contains no `🛑 STOP` or `⛔ MANDATORY GATE` marker — while the stop/gate
semantics remain in force internally.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Bug Condition — Question Shown Exactly Once

_For any_ rendered agent turn that presents a 👉 question (the Bug_Condition C2
branch), the fixed steering SHALL compose a clean, single, non-compound question
on the first attempt and SHALL render that question exactly once, suppressing any
duplicate produced by an internal correction pass unless the bootcamper
explicitly asked to see it again.

**Validates: Requirements 2.4, 2.5**

Property 3: Preservation — Turn Boundary, Gate, and Harness Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition` returns
false) — non-question turns, gate-execution turns with non-marker evidence,
explicit re-display requests, and every harness-predicate input — the fixed
system SHALL produce the same result as the original system, preserving the One
Question Rule / leading-question guarantee, the stop-and-wait semantics,
unconditional gate execution, the `config/.question_pending` mechanism, the
harness engine behavior, and a shipped-fixture run that exits 0.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming the root cause analysis is correct, the fix spans steering files (the
defect), the shipped eval fixtures (the oracle that encodes expected behavior),
and the two content-assertion tests that encoded the buggy expectation. The
harness engine is intentionally untouched.

**1. Establish the internal-only directive convention (governing files)**

- **File**: `senzing-bootcamp/steering/agent-behavior-rules.md`
  - In Rule 4, add an explicit clause: `🛑 STOP` and `⛔ MANDATORY GATE` are
    internal control directives that define the end-of-turn boundary and gate
    semantics and are NEVER rendered to the bootcamper. The rendered turn
    boundary is "the single 👉 question is the final message; end immediately
    after it." Preserve the existing leading-question guarantee wording.
  - In Rule 3, reinforce that the FIRST composed question must already be single
    and non-compound (compose-clean-first), not merely rewritten after the fact.

- **File**: `senzing-bootcamp/steering/agent-instructions.md`
  - In the **Communication** section and **Question Stop Protocol** subsection,
    state that the stop/gate boundary is internal and is signaled by ending the
    turn after the 👉 question — the agent MUST NOT emit `🛑 STOP` or
    `⛔ MANDATORY GATE` text. Keep the "STOP and wait" behavioral requirement.

- **File**: `senzing-bootcamp/steering/conversation-protocol.md`
  - Replace the "The 🛑 STOP marker stays plain — never wrap 🛑 STOP in bold"
    rule with a rule that the marker is internal-only and not rendered.
  - Rewrite the CORRECT examples in **Violation Examples** (Multi-Question,
    Not-Waiting, Self-Answering) so each ends on the 👉 question with no
    rendered `🛑 STOP` line. Where the boundary must be shown, use a clearly
    non-rendered internal note (e.g., `> _(internal: end the turn here and wait —
    not shown to the bootcamper)_`).
  - Add a **no-duplicate re-display** rule to Question Disambiguation / the
    Pre-Output Validation Checklist: an internal correction/regeneration pass
    must not re-emit a question already shown unless the bootcamper explicitly
    asked; compose the clean single question the first time.

**2. Rewrite emitted-content examples (audit targets)**

| File | Occurrence | Change |
|---|---|---|
| `conversation-examples.md` | Multi-Question / Not-Waiting / Self-Answering CORRECT examples render `🛑 STOP` | End each CORRECT example on the 👉 question; drop the rendered `🛑 STOP` line |
| `feedback-workflow.md` | Per-step `🛑 STOP — End your response here.` lines + "🛑 STOP after each question" rule | Reframe as an internal directive; the emitted flow ends on each 👉 question with no rendered marker |
| `track-switching.md` | `> **🛑 STOP — End your response here.**` blockquotes after each 👉 | Keep the stop semantics as an internal directive note; ensure no rendered marker beside the question |
| `visualization-guide.md` | "end your response with: > 🛑 STOP", the delivery-mode `🛑 STOP` line, the 5-step "👉 + 🛑 STOP" example, and Static-HTML workflow `> **🛑 STOP ...**` blocks | Rewrite so the rendered offer/question ends on the 👉 line; express the wait as an internal directive |
| `module-01-phase1-discovery.md` | `> **🛑 STOP — End your response here.** Do not answer ...` after Steps 5, git, license questions | Keep as an internal directive (not rendered); confirm the emitted turn ends on the 👉 question |
| `onboarding-phase1b-intro-language.md` | `🛑 STOP — Wait ...` line and `⛔ **MANDATORY GATE** — ...` block | Convert both to internal-only directives; the rendered language prompt ends on the 👉 question |

Note: `module-08-phaseA-requirements.md` uses the same internal-directive
blockquote pattern as `module-01`; apply the same treatment (keep the directive,
ensure no rendered marker beside the question) even though it is outside the
primary named list, so the convention is consistent across the steering set.

**3. Bug 2 — compose-clean-first and no-duplicate rules**

- Strengthen `conversation-protocol.md` Question Disambiguation and Rule 3 in
  `agent-behavior-rules.md` so the initial composition of any confirmation /
  comprehension-check question is a single, non-compound question (e.g.,
  `👉 **Does the overview make sense before we choose a track?**`), removing the
  prose "or ... clarify?" compound pattern.
- Add the explicit rule that a question already surfaced is not re-displayed by
  an internal correction pass; the corrected question replaces the draft before
  it is shown, never in addition to it. Honor the existing hook-output rules for
  genuine corrective content that has not yet been surfaced (3.6).

**4. Reconcile the conversational-eval harness (fixtures + coupled tests)**

- **No change** to `senzing-bootcamp/scripts/eval_conversations.py`. Rationale:
  `ends_with_question_then_stop` already passes when the 👉 line is the last
  substantive line (empty trailing), so a turn bounded by the trailing 👉
  question alone is recognized as correct; and `_is_boundary_line` still accepts
  a `🛑 STOP` line when present, preserving the property tests that use it.
- **Fixture** `single_question_stop.json`: remove the trailing
  `🛑 STOP — End your response here ...` line from the agent turn (turn now ends
  on the 👉 question), and change the assertion `{"type": "contains_marker",
  "marker": "🛑"}` to `{"type": "absent_marker", "marker": "🛑"}` so the fixture
  now locks in the fixed behavior. Retain `exactly_one_pointer`,
  `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer`.
- **Fixture** `confirmation_question_disambiguation.json`: remove the trailing
  `🛑 STOP` line; the turn ends on the 👉 question. Existing assertions still
  pass; optionally add `absent_marker "🛑"` to guard the fix.
- **Fixture** `module3_gate_not_bypassed.json`: remove the trailing `🛑 STOP`
  line. Confirm `gate_not_bypassed` still passes because the turn retains
  non-marker execution evidence ("Your visualization is running", "Checkpoint
  written: module_3_verification.web_service = passed."). Optionally add
  `absent_marker "🛑"`.
- **New regression fixture** (e.g., `clean_question_no_marker.json`): a question
  turn that ends on the 👉 question with NO `🛑 STOP` / `⛔` line, asserting
  `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`,
  `no_self_answer`, `absent_marker "🛑"`, `absent_marker "⛔"`. This pins the
  reconciliation: a bounded question turn needs no rendered marker. Ensure it
  carries no forbidden URL/secret pattern (Property 17 in the harness tests).

**5. Update the two content-assertion tests that encode the buggy expectation**

- **File**: `senzing-bootcamp/tests/test_bold_question_steering.py`
  - `test_protocol_has_distinct_bold_rule_section`: drop the requirement that the
    bold rule contains a rendered `🛑 STOP` "stays plain" clause; assert instead
    the internal-only directive rule.
  - `test_protocol_stop_marker_is_plain` and `test_examples_stop_marker_is_plain`:
    these require a rendered `🛑 STOP` line in `conversation-protocol.md` /
    `conversation-examples.md`. Replace them with assertions that CORRECT
    question examples end on the 👉 line and render no `🛑 STOP` / `⛔` marker
    beside a question. These changes are part of the FIX (they encoded the old,
    buggy oracle), not a preservation regression.
- Any other steering test that asserts a marker is rendered *adjacent to a 👉
  question* (surfaced during implementation via the marker audit) must be
  updated the same way. Tests that assert a marker's presence as an *internal
  directive* (e.g., `test_business_case_offer_steering.py`,
  `test_licensing_guidance.py`, `test_module2_license_acquisition_info.py`) are
  preserved, because the internal directive glyphs remain.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples
that demonstrate the bug on the unfixed steering (via the conversational-eval
harness fixtures and content-assertion tests), then verify the fix works
correctly and preserves existing behavior. Because the defect lives in steering
(instructions to an LLM) rather than in a callable function, the harness fixtures
are the deterministic proxy oracle for agent behavior, and the property-based
tests run against those fixtures and the predicate engine.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing
the fix. Confirm or refute the root-cause analysis. If refuted, re-hypothesize.

**Test Plan**: Author (or adapt) fixtures whose agent turn reflects the *current*
steering behavior — a 👉 question followed by a rendered `🛑 STOP` / `⛔` line,
and a duplicate-question turn — and attach `absent_marker "🛑"`,
`absent_marker "⛔"`, and an "exactly one rendered question" assertion. Run them
on the UNFIXED oracle to observe failures. Complement with the existing
content-assertion tests to locate every rendered-marker occurrence.

**Test Cases**:
1. **Marker-leak question turn**: a 👉 question with a trailing `🛑 STOP` line
   asserted `absent_marker "🛑"` (will fail on unfixed steering).
2. **Gate-marker leak**: a gate turn rendering `⛔ MANDATORY GATE` asserted
   `absent_marker "⛔"` (will fail on unfixed steering).
3. **Duplicate comprehension-check question**: a turn where the compound "or"
   question and its regeneration both appear, asserted `exactly_one_pointer` /
   single rendered question (will fail on unfixed steering).
4. **Edge case — explicit re-display request**: bootcamper asks to see the
   question again; re-display must be allowed (should NOT be flagged).

**Expected Counterexamples**:
- A rendered `🛑 STOP` / `⛔ MANDATORY GATE` line appears beside the 👉 question.
- The same question appears twice in one rendered turn.
- Possible causes: glyph overloading in steering, a rule presuming the marker is
  emitted, compound-first composition, and no no-re-display rule.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed
steering produces the expected behavior.

**Pseudocode:**

```
FOR ALL X WHERE isBugCondition(X) DO
  result := renderedTurn_fixed(X)
  ASSERT expectedBehavior(result)
END FOR
```

Concretely: every question-presentation fixture representing fixed behavior must
satisfy `exactly_one_pointer`, `ends_with_question_then_stop`,
`no_compound_question`, `no_self_answer`, `absent_marker "🛑"`, and
`absent_marker "⛔"`, and render the question exactly once.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the
fixed system produces the same result as the original system.

**Pseudocode:**

```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT renderedTurn_original(X) = renderedTurn_fixed(X)
END FOR
```

**Testing Approach**: Property-based testing (Hypothesis) against the harness
predicates and fixtures is recommended for preservation checking because:
- It generates many inputs across the transcript-text domain automatically.
- It catches edge cases (whitespace-only trailing lines, imperative pointer
  prompts, boundary lines) that manual unit tests might miss.
- It provides strong evidence that the harness engine and the One Question Rule
  behave identically for all non-buggy inputs.

Per the repo Hypothesis-profile convention, property tests rely on the active
profile baseline for `max_examples` (no inline `@settings(max_examples=...)`
unless a specific test needs a non-baseline count).

**Test Plan**: Confirm the harness engine is unchanged and its existing property
tests still pass; confirm every non-marker gate turn and non-question turn is
unaffected; run the full shipped-fixture suite and assert exit 0.

**Test Cases**:
1. **Harness engine preserved**: `ends_with_question_then_stop` still passes for
   a turn ending on the 👉 line (empty trailing) AND for a turn ending on a
   `🛑 STOP` boundary — observed on the current engine, retained after the fix.
2. **Gate execution preserved**: `module3_gate_not_bypassed.json` with the
   rendered `🛑 STOP` line removed still passes `gate_not_bypassed` via
   non-marker evidence — observed before, verified after.
3. **One Question Rule / leading-question guarantee preserved**: every fixture
   still ends with exactly one 👉 question (`exactly_one_pointer`).
4. **Explicit re-display preserved**: a turn that re-displays a question at the
   bootcamper's explicit request is not treated as a duplicate violation.

### Unit Tests

- Steering content assertions that CORRECT question examples end on the 👉 line
  and render no `🛑 STOP` / `⛔` marker beside a question (updated
  `test_bold_question_steering.py`).
- The internal-only directive rule is present in `agent-behavior-rules.md`,
  `agent-instructions.md`, and `conversation-protocol.md`.
- The no-duplicate-re-display and compose-clean-first rules are present in the
  governing files.
- Preserved internal-directive assertions still pass
  (`test_business_case_offer_steering.py`, `test_licensing_guidance.py`,
  `test_module2_license_acquisition_info.py`).

### Property-Based Tests

- `absent_marker "🛑"` / `absent_marker "⛔"` hold across generated
  question-presentation fixtures (fix checking for Bug 1).
- `exactly_one_pointer` + single-rendered-question hold across generated
  confirmation/comprehension fixtures (fix checking for Bug 2).
- The harness predicate property tests (`ends_with_question_then_stop`,
  `no_self_answer`, `no_compound_question`, `gate_not_bypassed`) continue to pass
  unchanged (preservation of the engine), including the strategies that use a
  `🛑 STOP` boundary line.
- The shipped-fixtures oracle property (every fixture yields zero failures; full
  run exits 0) holds over the updated fixture set plus the new regression
  fixture.

### Integration Tests

- Full harness run over `senzing-bootcamp/tests/eval/` exits 0 (CI parity:
  `python senzing-bootcamp/scripts/eval_conversations.py`).
- The CI pipeline steps that gate the power (`validate_power.py`,
  `measure_steering.py --check`, `validate_commonmark.py`,
  `sync_hook_registry.py --verify`, then pytest) all pass after the steering
  rewrites, so the conversational-eval-harness CI step stays at exit code 0.
- End-to-end: a scripted onboarding-style transcript (language selection →
  comprehension check → track selection) renders one clean 👉 question per
  yielding turn, no leaked markers, and no duplicate question, while the
  `config/.question_pending` write and gate enforcement still occur internally.
