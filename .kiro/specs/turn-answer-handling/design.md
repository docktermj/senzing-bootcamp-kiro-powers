# Turn Answer Handling Bugfix Design

## Overview

This bugfix removes two ways a yielding (input-expecting) turn can leave the bootcamper without a live, actionable prompt. Both symptoms share one invariant violation: **every input-expecting turn must end with exactly ONE live 👉 pending question as its final message, and any answer to that question — including a bare numeric or lettered token matching a presented option list — must be bound and consumed before the workflow re-prompts.**

- **Item 1 (forward question displaced).** After a module completes, a recap/confirmation emission (the per-module recap step / the `module-recap-append` agentStop hook) ends the turn with a confirmation line such as "Recap updated for Module 3". The forward transition question (👉 "Ready for Module X?") was shown earlier but is no longer the last thing the bootcamper sees, so the turn ends with zero live pending questions and the session looks stalled.

- **Item 2 (bare token not bound).** At Module 6 Step 1 the agent presents the production-volume question with a numbered option list (1–4). The bootcamper replies `3` (option 3 — medium production, 500K–10M). The reply is not bound to the numbered option; `volume_utils.parse_volume_input("3")` instead returns the literal integer `3` (classified as the demo tier), the turn resolves to a minimal acknowledgment, and the agent re-presents the same Module 6 banner and volume question, so no progress is made.

The fix has two coordinated parts:

1. **Protocol/ordering (steering).** Make the "one live pending question as the final message" rule explicit and enforced for module-completion turns: the recap/confirmation step runs **before** the forward transition question, or the forward 👉 question is **re-surfaced** as the final message after any recap/confirmation, and `config/.question_pending` is (re)written for it.

2. **Answer binding (a small, pure, stdlib-only helper + steering wiring).** Introduce a reusable option-binding helper so that when the most recent question presented a numbered/lettered option list, a bare matching token reply binds to that option's meaning *before* any free-text reinterpretation. Module 6 Step 1 consults this binding first and only falls through to `volume_utils.parse_volume_input` when the reply does **not** match a presented option token.

The strategy is deliberately minimal and preservation-first: it does not change affirmative-transition startup, the One Question Rule, the `.question_pending` lifecycle, the completion fixed-step ordering, or the existing unparseable-input clarifying path.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — an input-expecting turn ends without a live pending question as its final message, OR a bare token matching a presented numbered/lettered option list is not bound to the pending question. Formalized in `isBugCondition` below.
- **Property (P)**: The desired post-fix behavior for buggy inputs — the turn ends with exactly one live 👉 pending question and writes `config/.question_pending`; a bare matching token is bound, consumed, and the workflow advances without re-asking.
- **Preservation**: Existing behavior that must remain identical for non-buggy turns — affirmative module transitions, the One Question Rule, the `.question_pending` lifecycle, the completion fixed-step ordering, and the existing unparseable-input clarifying path.
- **handleTurn (F)**: The original (unfixed) turn/answer-handling behavior governed by the steering files and helpers.
- **handleTurn' (F')**: The fixed turn/answer-handling behavior after this change.
- **Live_Pending_Question**: A 👉 question that is the final message shown to the bootcamper in the turn AND has a corresponding `config/.question_pending` file written for it.
- **Input-expecting (yielding) turn**: A turn that hands control back to the bootcamper for input. Per the One Question Rule it must end with exactly one 👉 question.
- **Option_List question**: A 👉 question that presents two or more alternatives as a numbered (1, 2, 3…) or lettered (a, b, c…) list.
- **Option_Token (bare token)**: A reply consisting essentially of a single option identifier — a number (`3`, `3.`, `(3)`) or a letter (`b`, `B)`) — that maps to a presented option, with no additional free-text meaning.
- **answer_binding**: A new pure, stdlib-only helper module (`senzing-bootcamp/scripts/answer_binding.py`) that parses a bare Option_Token and binds it to a presented option list.
- **`config/.question_pending`**: The file written for every 👉 question (type on line 1, question text on subsequent lines). Its presence makes the next bootcamper message the answer to that question.
- **`volume_utils.parse_volume_input`**: The existing free-text volume parser used by Module 6 Step 1; unchanged by this fix and used only as the fall-through path for non-Option_Token replies.

## Bug Details

### Bug Condition

The bug manifests in two ways on a yielding turn. **Item 1:** a module-completion turn that expects input ends with a recap/confirmation line as its final message, so there is no live 👉 pending question last (and `config/.question_pending` does not reflect a live question the bootcamper can answer). **Item 2:** the most recent question presented a numbered/lettered option list, the bootcamper replied with a bare token matching one of those options, but the token was not bound to the pending question — it was reinterpreted (e.g., `parse_volume_input("3")` → literal `3` records → demo tier) or dropped, and the same question was re-presented.

**Formal Specification:**
```
FUNCTION isBugCondition(turn)
  INPUT: turn of type BootcampTurn
  OUTPUT: boolean

  // Item 1: an input-expecting turn ends without a live pending question
  // as the final message (recap/confirmation displaced the forward question)
  endsWithoutLivePendingQuestion ←
    turn.expectsInput AND NOT turn.lastMessageIsLivePendingQuestion

  // Item 2: the prior question presented a numbered/lettered option list and
  // the reply is a bare token matching one of those options, but it was not
  // bound to the pending question
  unboundMatchingTokenAnswer ←
    turn.priorQuestionHasOptionList
    AND isBareMatchingToken(turn.reply, turn.priorQuestion.options)
    AND NOT turn.replyBoundToPendingQuestion

  RETURN endsWithoutLivePendingQuestion OR unboundMatchingTokenAnswer
END FUNCTION
```

### Examples

- **Item 1 — recap displaces the forward question.** Module 3 completes, Module 6 is next. The agent shows 👉 "Ready for Module 6?", then a recap/confirmation emission appends "Recap updated for Module 3" as the final message. *Expected:* the turn ends with 👉 "Ready for Module 6?" as the last message and `config/.question_pending` is written for it. *Actual:* the turn ends on the confirmation line with zero live pending questions.
- **Item 2 — bare numeric token not bound.** Module 6 Step 1 presents the volume question with options 1–4; the bootcamper replies `3` (meaning option 3, medium production). *Expected:* `3` binds to option 3 → medium tier; the workflow advances. *Actual:* `parse_volume_input("3")` returns literal `3` → demo tier (or a minimal ack), and the Module 6 banner + volume question are re-presented.
- **Item 2 — bare lettered token.** A question presents options a/b/c and the bootcamper replies `b`. *Expected:* `b` binds to option 2 and the workflow advances. *Actual:* the bare letter is dropped and the question is re-asked.
- **Edge case — non-matching reply (NOT a bug).** A reply of `"around ten million"` to the volume question does not match any presented option token, so it correctly falls through to `parse_volume_input` and the existing clarifying path. This input is outside the bug condition and must be preserved unchanged.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Affirmative module-transition confirmation (yes/sure/ready/let's go) still immediately starts the next module in the same turn with the start banner, journey map, before/after framing, and Step 1 introduction (Confirmation Response Requirements, ≥50 chars).
- The One Question Rule still holds: every yielding turn ends with exactly one 👉 question and writes `config/.question_pending` using the structured format.
- The `.question_pending` lifecycle is unchanged: while it exists the agent treats the next message as the answer and deletes the file before processing.
- The module-completion fixed-order steps (progress_update, recap_append, journal_entry, completion_certificate, next_step_options) still run in order and still produce every per-module artifact; the defer-when-pending and no-op-when-nothing-new trigger rules are unchanged.
- `volume_utils.parse_volume_input` behavior is byte-for-byte unchanged for every input; the existing unparseable-input clarifying follow-up (numbered list, then default to demo tier) is unchanged for replies that are not a matching Option_Token.

**Scope:**
All turns that do NOT satisfy `isBugCondition` must be completely unaffected by this fix. This includes:
- Yielding turns that already end with exactly one live 👉 pending question.
- Replies to a numbered/lettered question that are NOT a bare matching Option_Token (free text, out-of-range numbers, unparseable input).
- Any turn that does not expect input (pure work turns that recap and then close with their own contextual 👉 question).

**Note:** The expected correct behavior for buggy inputs is defined in the Correctness Properties section (Property 1). This section enumerates what must NOT change.

## Hypothesized Root Cause

Based on the bug analysis, the most likely causes are:

1. **Recap/confirmation emitted after the forward question (Item 1).** The forward 👉 "Ready for Module X?" question is produced, then a separate recap/confirmation emission (the per-module recap step or the `module-recap-append` agentStop hook) appends a confirmation line as the final message. The steering does not require the forward question to be re-surfaced last, nor does it require recap/confirmation to run before the transition question. Result: the turn ends with zero live pending questions.

2. **No explicit "live pending question must be last" invariant for completion turns (Item 1).** `conversation-protocol.md` enforces "exactly one 👉 question per yielding turn" but does not explicitly state that the 👉 question must be the **final message** even when a later recap/confirmation step runs. The ordering between recap/confirmation and the forward question is under-specified in `module-completion.md` / `module-completion-next-steps.md`.

3. **No option-token binding step before free-text parsing (Item 2).** Module 6 Step 1 routes the reply straight into `volume_utils.parse_volume_input`. A bare `3` is a valid literal record count to that parser, so it is consumed as "3 records" (demo) rather than bound to "option 3" (medium). There is no helper or steering instruction that binds a bare Option_Token to the presented numbered/lettered list first.

4. **Binding ambiguity is unresolved in favor of the wrong interpretation (Item 2).** When a numbered option list was presented, the option meaning should take precedence over a literal numeric reinterpretation. The current flow has no rule establishing that precedence, so the matching-token answer is effectively unbound and the question is re-asked.

## Correctness Properties

Property 1: Bug Condition - One Live Pending Question, Answers Bound

_For any_ turn where the bug condition holds (`isBugCondition` returns true), the fixed turn/answer handling (`handleTurn'`) SHALL: (a) for an input-expecting turn, end with exactly one live 👉 pending question as the final message and write `config/.question_pending` for it; and (b) when the most recent question presented a numbered/lettered option list and the reply is a bare token matching one of those options, bind that reply to the pending question, consume it as the answer, advance the workflow, and NOT re-ask the already-answered question.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Non-Buggy Turns Unchanged

_For any_ turn where the bug condition does NOT hold (`isBugCondition` returns false), the fixed code (`handleTurn'`) SHALL produce the same result as the original code (`handleTurn`), preserving affirmative-transition startup, the One Question Rule, the `.question_pending` lifecycle, the completion fixed-step ordering and artifacts, the unchanged `parse_volume_input` behavior, and the existing clarifying-follow-up path for non-matching replies.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming the root-cause analysis is correct, the fix has a steering/protocol part and a small pure-helper part. No third-party dependencies are introduced (stdlib-only Python).

**Part A — New answer-binding helper (Item 2 core logic)**

**File**: `senzing-bootcamp/scripts/answer_binding.py` (new, stdlib-only, follows the script conventions: shebang, `from __future__ import annotations`, module docstring, type hints, `main(argv=None)`/argparse entry point)

**Functions**:
1. **`parse_option_token(reply: str) -> str | None`**: Return the normalized bare Option_Token from a reply, or `None` if the reply is not a bare token. Recognizes a single number (`"3"`, `"3."`, `"(3)"`, `" 3 "`) or a single letter (`"b"`, `"B)"`, `"b."`). Returns `None` when the reply carries additional free-text meaning (e.g., `"3 million"`, `"around 3"`, `"option three please and ..."`) so those replies fall through to the existing path.
2. **`bind_option(reply: str, options: list[str]) -> int | None`**: Using `parse_option_token`, return the **1-based index** of the option the reply binds to within `options`, or `None` when there is no bind (not a bare token, or the token is out of range for the presented list). Letters map case-insensitively (`a`→1, `b`→2, …).
3. (Optional convenience) **`is_bare_matching_token(reply: str, options: list[str]) -> bool`**: `bind_option(...) is not None`, mirroring `isBareMatchingToken` in the bug condition.

**Part B — Module 6 Step 1 wiring (Item 2 steering)**

**File**: `senzing-bootcamp/steering/module-06-phaseA-build-loading.md`

**Function/Step**: Phase A, Step 1 — "Assess production record volume" Volume Classification agent instruction.

**Specific Changes**:
1. Add a binding-first instruction: when the volume question (or its clarifying follow-up) presented the numbered option list, FIRST attempt to bind the reply to that list with `answer_binding.bind_option`. Provide the option→tier map (1→demo, 2→small, 3→medium, 4→large) so a bound index selects the tier directly.
2. Only when `bind_option` returns `None` (the reply is not a bare matching token) fall through to the existing `volume_utils.parse_volume_input` → `classify_tier` path — preserving the current clarifying-follow-up and demo-default behavior unchanged.
3. After a successful bind, persist via the existing `volume_utils.persist_volume_selection` and advance; do NOT re-present the Module 6 banner or volume question.

**Part C — Module-completion turn ordering / re-surface forward question (Item 1 steering)**

**Files**: `senzing-bootcamp/steering/module-completion.md`, `senzing-bootcamp/steering/module-completion-next-steps.md`, and `senzing-bootcamp/steering/conversation-protocol.md`.

**Specific Changes**:
1. Make the invariant explicit in `conversation-protocol.md`: every input-expecting turn ends with exactly one **live** 👉 pending question as the **final message** shown to the bootcamper, and `config/.question_pending` is written for it. A recap/confirmation emission must never be the final message of an input-expecting turn.
2. In `module-completion.md` / `module-completion-next-steps.md`, require that the per-module recap/confirmation runs **before** the forward transition question, OR that the forward 👉 "Ready for Module X?" question is **re-surfaced as the final message** after any recap/confirmation, with `config/.question_pending` (re)written for it. Keep the fixed completion step order and the defer-when-pending / no-op trigger rules intact.
3. Reaffirm (no behavioral change) the affirmative-transition commitment so Part C does not weaken the immediate module-start requirement.

**Part D — Tests** (see Testing Strategy): exploration tests that fail on unfixed code, fix-checking tests, and preservation tests, using pytest + Hypothesis, stdlib-only.

## Testing Strategy

### Validation Approach

Two phases: first surface counterexamples that demonstrate the bug on the UNFIXED code (helper + steering), then verify the fix produces the expected behavior and preserves all non-buggy behavior. Tests live in `senzing-bootcamp/tests/` and follow the project conventions: class-based organization, `sys.path` import of `scripts/`, Hypothesis strategies prefixed `st_`, `@settings(max_examples=...)`, and docstrings naming the validated requirements.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix, and confirm or refute the root-cause analysis. If refuted, re-hypothesize.

**Test Plan**: For Item 2, drive the *intended* binding behavior against the current flow: assert that a bare token matching a presented option binds to that option's tier rather than being parsed as a literal record count. On unfixed code there is no binding helper/wiring, so these tests fail (or demonstrate `parse_volume_input("3") == 3` → demo, the wrong tier). For Item 1, parse the steering files and assert the "live pending question must be the final message" invariant and the recap-before-transition (or re-surface) ordering rule are present. On unfixed code these are absent, so the tests fail.

**Test Cases**:
1. **Bare numeric option bind (Item 2)**: `bind_option("3", four_volume_options)` returns `3` (→ medium). Will fail on unfixed code (no helper).
2. **Bare lettered option bind (Item 2)**: `bind_option("b", ["a-opt","b-opt","c-opt"])` returns `2`. Will fail on unfixed code (no helper).
3. **Volume mis-parse demonstration (Item 2)**: `parse_volume_input("3") == 3` classified as demo — documents the wrong interpretation the fix must override for an Option_List question. (May pass as a documentation assertion; paired with the binding assertion that fails on unfixed code.)
4. **Final-message invariant absent (Item 1)**: `conversation-protocol.md` lacks an explicit "live 👉 pending question must be the final message of an input-expecting turn" rule. Will fail on unfixed code.
5. **Completion ordering rule absent (Item 1)**: `module-completion.md` / `module-completion-next-steps.md` lack the recap-before-transition (or re-surface-forward-question) rule. Will fail on unfixed code.

**Expected Counterexamples**:
- A bare Option_Token is not bound to the presented option (it is parsed/dropped).
- A module-completion input-expecting turn can end with a recap/confirmation line as its final message (zero live pending questions).
- Possible causes: missing binding helper/wiring, missing final-message invariant, under-specified recap/transition ordering.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed behavior produces the expected behavior (Property 1).

**Pseudocode:**
```
FOR ALL turn WHERE isBugCondition(turn) DO
  result := handleTurn'(turn)

  IF turn.expectsInput THEN
    ASSERT result.lastMessageIsLivePendingQuestion
    ASSERT result.livePendingQuestionCount = 1
    ASSERT result.questionPendingFileWritten
  END IF

  IF turn.priorQuestionHasOptionList
     AND isBareMatchingToken(turn.reply, turn.priorQuestion.options) THEN
    ASSERT result.replyBoundToPendingQuestion
    ASSERT NOT result.reAskedAnsweredQuestion
    ASSERT result.advanced
  END IF
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed behavior equals the original behavior (Property 2).

**Pseudocode:**
```
FOR ALL turn WHERE NOT isBugCondition(turn) DO
  ASSERT handleTurn(turn) = handleTurn'(turn)
END FOR
```

**Testing Approach**: Property-based testing is well suited to preservation here because:
- It generates many replies across the input domain (numbers, words, mixed, whitespace, abbreviations) automatically.
- It catches edge cases at the boundary between "bare matching token" (bind) and "everything else" (fall through to `parse_volume_input`).
- It gives strong assurance that `parse_volume_input` and the clarifying path are untouched for non-matching replies.

**Test Plan**: Observe UNFIXED behavior for non-buggy inputs first (e.g., `parse_volume_input` outputs across a corpus, affirmative-transition steering requirements, One Question Rule statements, completion fixed-step order), then write tests that assert those outputs/statements are unchanged after the fix.

**Test Cases**:
1. **`parse_volume_input` invariance**: For any reply that is NOT a bare matching Option_Token, the Module 6 result equals the pre-fix `parse_volume_input` → `classify_tier` outcome. Verify on unfixed code, keep after fix.
2. **Clarifying-follow-up preserved**: An unparseable reply still triggers the numbered-list clarifying question and then defaults to demo if still unparseable (Req 3.4). Verify on unfixed code, keep after fix.
3. **Affirmative transition preserved**: The steering still requires immediate module start (banner, journey map, before/after, Step 1, ≥50 chars) on affirmative confirmation (Req 3.1). Verify on unfixed code, keep after fix.
4. **One Question Rule + `.question_pending` lifecycle preserved**: Exactly one 👉 per yielding turn and the write/treat-as-answer/delete lifecycle are unchanged (Req 3.2, 3.3). Verify on unfixed code, keep after fix.
5. **Completion fixed-step order + artifacts preserved**: The five-step order and per-module artifacts, plus defer-when-pending and no-op-when-nothing-new, are unchanged (Req 3.6). Verify on unfixed code, keep after fix.

### Unit Tests

- `parse_option_token`: numbers (`"3"`, `"3."`, `"(3)"`), letters (`"b"`, `"B)"`), and `None` for free-text/mixed (`"3 million"`, `"around 3"`, `""`, whitespace).
- `bind_option`: in-range numeric/lettered binds (1-based), out-of-range → `None`, non-token → `None`, case-insensitive letters.
- Module 6 option→tier mapping: bound index 1/2/3/4 → demo/small/medium/large.
- Steering presence checks: final-message invariant in `conversation-protocol.md`; recap-before-transition / re-surface rule in completion steering.

### Property-Based Tests

- For any bare numeric token `n` within the option-list length, `bind_option(str(n), options) == n` (Property 1, Item 2).
- For any bare letter within range, `bind_option` returns its 1-based position (Property 1, Item 2).
- For any reply that is NOT a bare matching token (generated free-text/number-with-units/out-of-range), `bind_option(...) is None` AND the Module 6 result equals the unchanged `parse_volume_input` outcome (Property 2 preservation boundary).
- For any volume input string, `parse_volume_input` output is identical pre- and post-fix (Property 2).

### Integration Tests

- Module 6 Step 1 end-to-end: presenting options 1–4, replying `3` binds to medium, persists via `persist_volume_selection`, advances without re-asking (Property 1).
- Module-completion turn end-to-end: a completion turn that expects input ends with the forward 👉 "Ready for Module X?" as the final message with `config/.question_pending` written, even when a recap/confirmation is emitted (Property 1, Item 1).
- Affirmative-transition flow: confirming "Ready for Module X?" still starts Module X immediately with all required start content (Property 2 preservation).
