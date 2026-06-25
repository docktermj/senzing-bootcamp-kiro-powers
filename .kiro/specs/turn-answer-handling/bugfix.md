# Bugfix Requirements Document

## Introduction

This bugfix consolidates two related High-priority UX feedback items (from `SENZING_BOOTCAMP_POWER_FEEDBACK.md`) that share a single root cause: a turn that expects input ends without a live, actionable pending question as the last thing the bootcamper sees. In both cases the bootcamp session appears stalled — the bootcamper is left with no clear prompt to respond to, or is asked something they already answered.

**Item 1 — Module-completion recap step ends the turn without a forward question.** After a module completes, the per-module recap step (part of the completion workflow) ends the turn with only a confirmation line (e.g., "Recap updated for Module 3"). The forward transition question ("Ready for Module X?") was asked in a prior message but is no longer the last thing shown, so the bootcamper has no actionable prompt. Reported context: Module 3 completed, Module 6 next; the post-completion recap ended the turn without re-surfacing the "Ready for Module 6?" question.

**Item 2 — Agent re-asked an already-answered numbered question.** At Module 6 Step 1, the agent asked "How many records do you expect to load in a production system?" with a numbered option list (1–4). The bootcamper replied "3" (option 3 — medium production, 500K–10M). The agent did not process the bare-number reply as the answer to that numbered question; the turn resolved to a minimal acknowledgment and the agent re-presented the same Module 6 banner and volume question, so no progress was made.

**Unifying bug condition.** Every turn that expects input must have exactly ONE live pending question, that pending question must be the last thing shown to the bootcamper, and answers to it (including bare numeric or lettered tokens that match a presented option list) must be consumed and bound before any re-prompt. The system must never (a) end an input-expecting turn without a live pending question as the final message, nor (b) re-ask a question the bootcamper has already answered.

The relevant artifacts are the bootcamp steering files governing module transitions, post-completion recap/hooks, and answer-handling in `senzing-bootcamp/steering/` — notably `module-completion.md`, `module-completion-next-steps.md`, `module-transitions.md`, `conversation-protocol.md`, `agent-behavior-rules.md`, and `module-06-phaseA-build-loading.md`.

## Bug Analysis

### Current Behavior (Defect)

What currently happens when the bug is triggered:

1.1 WHEN a module completes and the post-completion recap/confirmation step runs after the forward transition question THEN the system ends the turn with only a confirmation line (e.g., "Recap updated for Module 3") and the forward transition question ("Ready for Module X?") is no longer the last message shown.

1.2 WHEN a module-completion turn ends and the recap/confirmation step has consumed the final message THEN the system leaves the turn with zero live pending questions as the final output, so the bootcamper has no actionable prompt and the session appears stalled.

1.3 WHEN the most recent question presented a numbered (or lettered) option list and the bootcamper replies with a bare matching token (e.g., "3" against options 1–4) THEN the system fails to bind the bare token to the pending question and instead resolves the turn to a minimal acknowledgment.

1.4 WHEN a bare numeric/lettered answer to a numbered question is not bound THEN the system re-presents the same already-answered question (e.g., re-displays the Module 6 banner and the volume question), so no progress is made.

### Expected Behavior (Correct)

What should happen instead:

2.1 WHEN a module completes and the post-completion recap/confirmation step runs THEN the system SHALL ensure the forward transition question (👉 "Ready for Module X?") is re-surfaced as the last thing the bootcamper sees — either by appending the transition prompt after the recap/confirmation, or by running the recap/confirmation step BEFORE the transition question.

2.2 WHEN a module-completion turn that expects input ends THEN the system SHALL end the turn with exactly one live 👉 pending question as the final message, and SHALL write `config/.question_pending` for that question.

2.3 WHEN the most recent question presented a numbered (or lettered) option list and the bootcamper replies with a bare matching token (e.g., "3") THEN the system SHALL bind that reply to the pending question, consume it as the answer to that question, and advance the workflow.

2.4 WHEN a bare numeric/lettered answer to a numbered question has been bound and consumed THEN the system SHALL NOT re-ask or re-present that already-answered question, and SHALL proceed to the next step.

### Unchanged Behavior (Regression Prevention)

Existing behavior that must be preserved:

3.1 WHEN the bootcamper confirms a module transition affirmatively (yes, sure, ready, etc.) THEN the system SHALL CONTINUE TO immediately start the next module in the same turn with the module start banner, journey map, before/after framing, and Step 1 introduction.

3.2 WHEN a yielding turn ends with a 👉 question THEN the system SHALL CONTINUE TO enforce the One Question Rule (exactly one 👉 question per yielding turn) and write `config/.question_pending`.

3.3 WHEN `config/.question_pending` exists at the start of a turn THEN the system SHALL CONTINUE TO treat the bootcamper's message as the answer to that pending question and delete the pending file before processing.

3.4 WHEN the bootcamper's reply to a numbered question does NOT match any presented option token (e.g., a free-text or unparseable response) THEN the system SHALL CONTINUE TO handle it via the existing clarifying-follow-up path (e.g., `volume_utils.parse_volume_input` returning `None` triggers the numbered-list clarifying question, then defaults to the demo tier if still unparseable).

3.5 WHEN a turn completes work that does NOT end with a 👉 question THEN the system SHALL CONTINUE TO recap what was accomplished and end with a contextual 👉 closing question.

3.6 WHEN a module completes THEN the system SHALL CONTINUE TO run the fixed-order completion steps (progress_update, recap_append, journal_entry, completion_certificate, next_step_options) and produce all per-module artifacts.

## Bug Condition Derivation

### Bug Condition Function

```pascal
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

### Property Specification (Fix Checking)

```pascal
// Property: Fix Checking — One live pending question, answers bound
FOR ALL turn WHERE isBugCondition(turn) DO
  result ← handleTurn'(turn)

  // Item 1: input-expecting turns end with exactly one live 👉 pending question
  IF turn.expectsInput THEN
    ASSERT result.lastMessageIsLivePendingQuestion
    ASSERT result.livePendingQuestionCount = 1
    ASSERT result.questionPendingFileWritten
  END IF

  // Item 2: bare matching token is bound and the workflow advances without re-ask
  IF turn.priorQuestionHasOptionList
     AND isBareMatchingToken(turn.reply, turn.priorQuestion.options) THEN
    ASSERT result.replyBoundToPendingQuestion
    ASSERT NOT result.reAskedAnsweredQuestion
    ASSERT result.advanced
  END IF
END FOR
```

### Preservation Goal (Preservation Checking)

```pascal
// Property: Preservation Checking
FOR ALL turn WHERE NOT isBugCondition(turn) DO
  ASSERT handleTurn(turn) = handleTurn'(turn)
END FOR
```

**Key Definitions:**
- **F** (`handleTurn`): The original turn/answer-handling behavior before the fix.
- **F'** (`handleTurn'`): The fixed turn/answer-handling behavior after the fix.
- **isBugCondition(turn)**: True when an input-expecting turn ends without a live pending question as the final message, OR when a bare token matching a presented numbered/lettered option list is not bound to the pending question.
