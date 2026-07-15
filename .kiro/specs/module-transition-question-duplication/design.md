# Module Transition Question Duplication Bugfix Design

## Overview

At the module-completion boundary the agent shows the bootcamper the forward
module-transition question ("Ready to start Module N+1: [Name]?"). A UX feedback
item reported that at the Module 6 → 7 handoff this question was rendered **more
than once** in the same turn. The One Question Rule / Final-Message Invariant
already requires a completion turn to end with exactly one live pending 👉
question, but the steering guidance that composes the completion turn offers a
"re-surface the forward question as the final message" path that can render the
transition question a second time (once inline in the next-step options, once
re-surfaced), and it provides no explicit de-duplication between the turn's
recap/next-step/closing text and the `config/.question_pending` marker. The fix
targets agent guidance in the Markdown steering files (and the paired
`ask-bootcamper` closing-question guidance) so the module-transition question is
emitted exactly once per turn.

## Glossary

- **Bug_Condition (C)**: A module-completion turn in which the forward
  module-transition 👉 question is rendered more than once (a duplicate of the
  same transition prompt within one turn).
- **Property (P)**: The desired behavior — a module-completion turn renders the
  forward transition 👉 question exactly once, as the single final pending
  question, with `config/.question_pending` written for that one question.
- **Preservation**: All other completion behavior — the fixed completion step
  order, the defer-when-pending / no-op trigger rules, the affirmative-transition
  immediate-execution commitment, the Final-Message Invariant, and every other
  single-👉 question path (onboarding, mid-module, feedback, graduation) — must
  remain unchanged.
- **Transition_Question**: The forward "Ready to (start | move on to) Module N+1
  ([Name])?" 👉 question presented at a module-completion boundary.
- **Final-Message Invariant**: The rule (in `conversation-protocol.md`) that an
  input-expecting turn ends with exactly one live pending 👉 question as its
  final message.
- **module-completion.md**: The Module_Completion_Root at
  `senzing-bootcamp/steering/module-completion.md` — completion step ordering,
  shared boundary-detection trigger, and the Final-Message Ordering rule.
- **module-completion-next-steps.md**: The slice at
  `senzing-bootcamp/steering/module-completion-next-steps.md` — the next-step
  options list (including the "Proceed" transition prompt), the Final-Message
  Ordering rule, and the ⛔ Immediate Execution rule.
- **module-transitions.md**: The always-loaded steering file at
  `senzing-bootcamp/steering/module-transitions.md` — Module Completion,
  Transition Integrity, and Confirmation Response Requirements.
- **ask-bootcamper hook**: The Stop hook at
  `senzing-bootcamp/hooks/ask-bootcamper.json` whose Phase 1 (Closing Question)
  and Phase 1.5 (Leading-Question Count Audit) own the closing 👉 question and
  the exactly-one-👉 invariant.
- **conversation-protocol.md**: The steering file defining turn-taking, the One
  Question Rule, the Ask-Once Guarantee, and the Final-Message Invariant.

## Bug Details

### Bug Condition

When a module completes, the completion turn is composed from the recap/
confirmation, the next-step options (which include the "Proceed" prompt
"Ready to move on to Module N ([name])?"), and the forward Transition_Question
that must be the final message. The Final-Message Ordering rule in
`module-completion.md` and `module-completion-next-steps.md` permits satisfying
the invariant by *re-surfacing* the forward "Ready for Module X" question as the
final message. Nothing in the guidance states that the Transition_Question must
be rendered exactly once, so it can appear both inline (as the next-step
"Proceed" option) and again as the re-surfaced final message. Separately, the
`ask-bootcamper` Phase 1 Closing Question check keys off whether the most recent
assistant message contains a 👉 anywhere; a transition prompt phrased inline
without a leading 👉 can slip past that check and cause a second closing question
for the same transition.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentTurn
  OUTPUT: boolean

  LET is_completion_turn = input.isModuleCompletionTurn
                           AND input.expectsInput

  LET transition_question_count = COUNT rendered 👉 questions in input
                                  that ask "Ready to (start|move on to)
                                  Module N+1"

  RETURN is_completion_turn AND transition_question_count > 1
END FUNCTION
```

### Examples

- **Reported case (Module 6 → 7)**: Module 6 (Data Processing) completes. The
  completion turn presents the recap, the next-step options (including
  "Proceed: Ready to move on to Module 7 (Query, Visualize, and Discover)?"), and
  then re-surfaces "👉 **Ready to start Module 7: Query, Visualize, and
  Discover?**" as the final message. The bootcamper sees the transition question
  twice.
- **Phase-1 append case**: A completion turn ends with an inline prose transition
  prompt that omits the leading 👉. The `ask-bootcamper` Phase 1 check sees no 👉
  in the message and appends its own closing 👉 transition question — two copies
  of the same transition prompt.
- **Correct single-render case (no fix needed)**: A completion turn runs the
  recap/confirmation first, then ends with exactly one "👉 **Ready to move on to
  Module 7?**" as the final message, and the next-step options do not
  additionally render that same question as a separate 👉 line. The bootcamper
  sees one transition prompt.
- **Non-transition question (out of scope)**: A mid-module step 👉 question, or
  the onboarding language-selection question, is rendered once. Unaffected.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The fixed completion step order (progress update → consolidated recap append →
  transcript reconciliation → completion certificate → capture-hook safeguard →
  next-step options) is unchanged.
- The defer-when-`config/.question_pending`-exists and no-op-when-nothing-new
  trigger rules are unchanged.
- The affirmative-transition commitment (⛔ Immediate Execution: an affirmative
  answer immediately starts the next module with banner, journey map,
  before/after framing, and Step 1) is unchanged.
- The Final-Message Invariant (a completion turn ends with exactly one live
  pending 👉 question as its final message) is unchanged — this fix makes it
  render exactly once, never zero.
- The `config/.question_pending` write/delete lifecycle, the treat-as-answer and
  delete-and-process rules, and the `write-policy-gate` validation are unchanged.
- Every other single-👉 question path (onboarding, mid-module steps, feedback,
  graduation) is unchanged.
- The next-step options set (Proceed, Iterate, Explore, Undo, Share) is
  unchanged; only the *duplicate* rendering of the forward transition question is
  removed.
- The compound-question rewrite (numbered-list) rule is unchanged.

**Scope:**
All turns that are NOT input-expecting module-completion transition turns are
completely unaffected. Within a completion turn, only the number of times the
forward Transition_Question is rendered changes (from potentially two-plus to
exactly one); all other content of the turn is preserved.

## Hypothesized Root Cause

Based on the reported behavior and analysis of the steering files, the most
likely causes are:

1. **No "render exactly once" rule for the Transition_Question.** The
   Final-Message Ordering rule in `module-completion.md` and
   `module-completion-next-steps.md` describes *ordering* ("run recap before the
   forward question, or re-surface the forward question as the final message")
   but never states the Transition_Question must appear a single time. The
   "re-surface" path, combined with the inline "Proceed" next-step option that
   phrases the same question, produces two renderings.

2. **The next-step "Proceed" option and the final-message transition question
   overlap.** `module-completion-next-steps.md` lists "Proceed: Ready to move on
   to Module [N] ([name])?" among the options AND requires the forward 👉
   question to be the final message. Without an explicit instruction that these
   are the *same* question rendered once (not two separate prompts), the agent
   can emit both.

3. **`ask-bootcamper` Phase 1 does not recognize an inline transition prompt.**
   Phase 1's guard ("the most recent assistant message does NOT contain a 👉
   anywhere") detects an already-present 👉 question, but a transition prompt
   phrased as inline prose without a leading 👉 is not detected, so Phase 1 can
   append a second closing 👉 question for the same transition. Phase 1.5's
   count audit only collapses *multiple 👉 lines*; it does not detect a prose
   duplicate paired with a single 👉 line.

4. **No de-duplication between the turn's recap/next-step/closing text and the
   `config/.question_pending` marker.** The marker is written for one pending
   question, but the guidance does not tie that single marker to a single
   rendered 👉 question, so a duplicate rendering is not caught.

## Correctness Properties

Property 1: Bug Condition — Transition Question Rendered Exactly Once

_For any_ input-expecting module-completion transition turn, the fixed steering
guidance SHALL ensure the forward module-transition 👉 question is rendered
exactly once — as the single final pending question — with the
`config/.question_pending` marker corresponding to that one rendered question.

**Validates: Requirements 2.1, 2.2, 2.3, 2.5**

Property 2: Bug Condition — Closing-Question Logic Does Not Duplicate the Transition

_For any_ module-completion transition turn whose forward transition question is
already present (including one phrased inline), the fixed `ask-bootcamper`
closing-question guidance SHALL recognize it and SHALL NOT add or leave a second
copy — collapsing to exactly one 👉 leading question.

**Validates: Requirements 2.4**

Property 3: Preservation — All Other Completion and Question Behavior Unchanged

_For any_ turn that is not an input-expecting module-completion transition turn,
and for all completion behavior other than the count of the rendered transition
question, the fixed guidance SHALL produce exactly the same behavior as the
original guidance — preserving the completion step order, the defer/no-op trigger
rules, the affirmative-transition immediate execution, the Final-Message
Invariant, and every other single-👉 question path.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-completion-next-steps.md`

**Section**: Next-Step Options + Final-Message Ordering

**Specific Changes**:
1. State explicitly that the forward "Ready to move on to Module [N]?" prompt and
   the final-message 👉 transition question are the **same** question rendered
   **once**, not two separate prompts. When the forward question is the final
   message, do not also render it as a separate inline "Proceed" 👉 line; when a
   recap/confirmation precedes it, the transition question appears a single time
   as the final message.
2. Add a de-duplication note: the module-completion turn contains exactly one
   rendered forward transition 👉 question, matching the single
   `config/.question_pending` marker written for it.

---

**File**: `senzing-bootcamp/steering/module-completion.md`

**Section**: Final-Message Ordering (recap vs. forward transition)

**Specific Changes**:
1. Add an explicit "render exactly once" clause to the Final-Message Ordering
   rule: the forward transition 👉 question appears a single time in the turn.
   The "re-surface after recap/confirmation" path replaces (does not duplicate)
   any earlier inline rendering of the same question.

---

**File**: `senzing-bootcamp/steering/module-transitions.md`

**Section**: Module Completion / Transition Integrity

**Specific Changes**:
1. Add a short "single transition prompt" statement: at a module-completion
   boundary, the forward transition question is presented to the bootcamper
   exactly once per turn.

---

**File**: `senzing-bootcamp/hooks/ask-bootcamper.json`

**Section**: Phase 1 (Closing Question) and/or Phase 1.5 (Leading-Question Count
Audit)

**Specific Changes**:
1. Strengthen the Phase 1 already-present-question detection so a forward
   transition prompt that is present but phrased inline (without a leading 👉) is
   recognized and NOT supplemented with a second closing 👉 transition question.
2. Extend the Phase 1.5 audit (or Phase 1 guidance) to collapse a duplicate
   transition prompt — an inline prose copy paired with a single 👉 line — down
   to exactly one 👉 transition question, reusing the existing silent
   self-correction pattern.

Note: Editing the `ask-bootcamper` hook prompt requires re-running the hook
prompt composer and registry sync (`compose_hook_prompts.py --write` then
`sync_hook_registry.py --write`) so the mirror docs and lockfile stay in sync;
CI verifies both.

## Testing Strategy

### Validation Approach

Two phases: first surface counterexamples that demonstrate the bug on unfixed
steering, then verify the fix and preservation.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the missing "render exactly
once" guidance BEFORE implementing the fix. Confirm or refute the root cause.

**Test Plan**: Parse the relevant steering files and assert the presence of the
"transition question rendered exactly once" / de-duplication guidance. Run on the
UNFIXED files to observe failures.

**Test Cases**:
1. Assert `module-completion-next-steps.md` states the forward transition prompt
   and the final-message 👉 question are the same question rendered once (fails
   on unfixed code).
2. Assert `module-completion.md` Final-Message Ordering carries a "render exactly
   once" clause for the forward transition question (fails on unfixed code).
3. Assert `module-transitions.md` states the transition question is presented
   once per turn (fails on unfixed code).
4. Assert the `ask-bootcamper` Phase 1 / Phase 1.5 guidance recognizes an
   already-present inline transition prompt and does not add a duplicate (fails
   on unfixed code).

**Expected Counterexamples**:
- `module-completion-next-steps.md` lists "Proceed: Ready to move on…" and
  separately requires the forward 👉 question as the final message, with no
  same-question / render-once note.
- `module-completion.md` Final-Message Ordering describes ordering but not a
  single rendering.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed
guidance produces the expected single-render behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := applyFixedSteering(input)
  ASSERT transitionQuestionRenderedExactlyOnce(result)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the
fixed guidance produces the same result as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalSteering(input) = fixedSteering(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation
because it generates many completion scenarios (different module numbers, tracks,
recap-before vs. re-surface orderings) and catches edge cases where a wording
change might affect a non-target path. Snapshot every non-target steering file
byte-for-byte, and assert the completion step order, defer/no-op trigger rules,
and ⛔ Immediate Execution content are preserved verbatim.

**Test Cases**:
1. Non-target steering files are byte-identical before and after the fix
   (snapshot comparison), excluding the edited files.
2. The fixed edited files retain their non-target anchors: completion step order,
   Shared Boundary-Detection Trigger rules, ⛔ Immediate Execution rule, and the
   next-step options set (Proceed, Iterate, Explore, Undo, Share).
3. The `config/.question_pending` lifecycle rules remain referenced and
   unchanged in the steering files.
4. The `ask-bootcamper` PreToolUse/Stop hook structural fields (trigger, action
   type) are unchanged; only the Phase 1 / Phase 1.5 prompt wording changes.

### Unit Tests

- Test that `module-completion-next-steps.md` states the forward transition
  prompt and the final-message 👉 question are one question rendered once.
- Test that `module-completion.md` Final-Message Ordering includes a render-once
  clause.
- Test that `module-transitions.md` states the transition question is shown once
  per turn.
- Test that the `ask-bootcamper` prompt recognizes an already-present inline
  transition prompt and does not duplicate it.

### Property-Based Tests

- Generate random module numbers / tracks and verify the guidance yields exactly
  one rendered forward transition 👉 question per completion turn.
- Generate random non-target question paths and verify no rendering-count change
  outside the module-completion transition turn.

### Integration Tests

- Simulate a module-completion turn end-to-end (Module 6 → 7) and verify exactly
  one forward transition 👉 question is present and matches the single
  `config/.question_pending` marker.
- Verify the affirmative-response path still immediately executes the next
  module's startup sequence unchanged.
- Verify the conversational-eval harness still passes (a completion turn ends
  with exactly one 👉 question).
