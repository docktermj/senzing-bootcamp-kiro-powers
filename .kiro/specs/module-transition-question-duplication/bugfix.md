# Bugfix Requirements Document

## Introduction

The bootcamp's turn-taking convention requires that a module-completion turn end
with **exactly one** live pending question — a single 👉 leading question, wrapped
in bold, written to `config/.question_pending` — as its final message (the
"One Question Rule" / Final-Message Invariant in
`senzing-bootcamp/steering/conversation-protocol.md`, reinforced by Rule 4 in
`agent-behavior-rules.md` and the Phase 1 / Phase 1.5 logic in the
`ask-bootcamper` Stop hook).

This bugfix addresses a UX defect reported from a live run (2026-07-15, Priority
Medium, Category UX): at the Module 6 → Module 7 handoff, the module-transition
question "Ready to start Module 7: Query, Visualize, and Discover?" was presented
to the bootcamper **more than once** in the same transition, rather than as a
single clean prompt. Repeated prompts are confusing — it is unclear whether an
earlier answer registered — and they add noise to the module-transition
experience. Answering once still advanced the workflow correctly, so this is a
presentation defect, not a state-machine defect.

The forward transition question is emitted at the module-completion boundary,
whose guidance lives in `senzing-bootcamp/steering/module-completion.md` and its
`module-completion-next-steps.md` slice. Both files carry a **Final-Message
Ordering** rule that offers two ways to satisfy the invariant: (a) run the
recap/confirmation *before* the forward transition question, or (b) *re-surface*
the forward "Ready for Module X" 👉 question as the final message after any
recap/confirmation. Path (b) is where the duplication arises: the transition
question is presented once inline (for example, as the "Proceed" option in the
next-step options list defined in `module-completion-next-steps.md`) and then
re-surfaced again as the final message, with no explicit rule that the transition
question must render exactly once per turn and no de-duplication between the
turn's recap/next-step/closing text and the pending-question marker.

**Relationship to existing specs.** This bugfix builds on, rather than
duplicates, the existing question-presentation work:

- `single-ask-question-guarantee` and `standardize-multi-question-steps`
  establish the one-question-per-step invariant; this bugfix closes a specific
  gap at the module-transition boundary where the *same* transition question is
  rendered twice within a single turn.
- `clean-question-presentation` (Bug 2) fixes a duplicate question caused by the
  *compound-question self-correction* regenerating a question after it was
  surfaced (an onboarding comprehension-check). This bugfix is a distinct
  mechanism: the transition question is duplicated by the module-completion
  "re-surface as final message" path overlapping with the inline next-step
  prompt — no compound-question rewrite is involved.
- `question-format-consistency` ensures pending questions keep their 👉 + bold
  formatting across session recreation and at the graduation-completion turn;
  this bugfix concerns the *count* of the transition question within a single
  in-session module-completion turn, not its formatting or a session boundary.
- `stop-hook-ux` folded the module recap append into `ask-bootcamper` Phase 0
  and documented the closing-question ownership; this bugfix targets the
  overlap between that closing text and the forward transition question.
- `module-transition-stall-fix` and `module-transition-validation-tests` govern
  that a confirmed transition actually executes; this bugfix does not change
  transition execution — only how many times the transition question is shown.

The scope of this fix is the agent guidance in the Markdown steering files (and
any paired `ask-bootcamper` hook-prompt guidance / repo-level hook-prompt test)
that governs the module-completion transition turn. Everything under
`senzing-bootcamp/` ships to bootcampers as a distributed Kiro Power.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a module completes and the agent presents the module-completion turn (recap/confirmation, next-step options, and the forward "Ready to start Module N+1?" transition question) THEN the system can render the same module-transition 👉 question more than once within that single turn.

1.2 WHEN `module-completion.md` / `module-completion-next-steps.md` satisfy the Final-Message Invariant via the "re-surface the forward 'Ready for Module X' question as the final message" path THEN the system presents the transition question inline (for example, as the "Proceed" next-step option) AND again as the re-surfaced final message, so the bootcamper sees it twice.

1.3 WHEN the module-completion turn's recap/next-step/closing text already contains the forward transition question THEN the steering guidance provides no explicit de-duplication requiring the transition question — and the `config/.question_pending` marker written for it — to correspond to exactly one rendered 👉 question in the turn.

1.4 WHEN the `ask-bootcamper` Phase 1 Closing Question logic evaluates a module-completion turn whose transition question is phrased inline without a leading 👉 (or is otherwise not detected by the "most recent assistant message does NOT contain a 👉 anywhere" check) THEN the system may append a second closing question for the same transition rather than recognizing the transition question is already present.

1.5 WHEN the bootcamper sees the module-transition question rendered more than once THEN it is unclear whether an earlier answer registered, and the duplicate prompts add noise to the module-transition experience.

### Expected Behavior (Correct)

2.1 WHEN a module completes and the agent presents the module-completion turn THEN the system SHALL render the forward module-transition 👉 question exactly once in that turn, as the single final pending question.

2.2 WHEN `module-completion.md` / `module-completion-next-steps.md` satisfy the Final-Message Invariant THEN the system SHALL ensure the forward transition question appears a single time: it is either presented once as the final message (not also repeated inline in the next-step options), or, when re-surfaced after a recap/confirmation, the inline occurrence is not additionally rendered as a separate 👉 question.

2.3 WHEN the module-completion turn's recap/next-step/closing text is composed THEN the steering guidance SHALL require de-duplication so that the transition question and the `config/.question_pending` marker written for it correspond to exactly one rendered 👉 question in the turn.

2.4 WHEN the `ask-bootcamper` Phase 1 / Phase 1.5 logic evaluates a module-completion transition turn THEN the system SHALL recognize an already-present forward transition question (including one phrased inline) and SHALL NOT add or leave a second copy of the same transition question — collapsing to exactly one 👉 leading question.

2.5 WHEN the bootcamper reaches a module transition THEN the system SHALL present one clean, unambiguous transition prompt so it is clear that a single answer advances the workflow.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper answers the module-transition question affirmatively THEN the system SHALL CONTINUE TO immediately execute the next module's startup sequence (module start banner, journey map, before/after framing, Step 1) in the same turn, per the ⛔ Immediate Execution rule in `module-completion-next-steps.md`.

3.2 WHEN a module-completion turn expects input THEN the system SHALL CONTINUE TO end with exactly one live pending 👉 question as its final message (the Final-Message Invariant), with `config/.question_pending` written for it.

3.3 WHEN a module completes THEN the system SHALL CONTINUE TO run the fixed completion step order (progress update, consolidated recap append, transcript reconciliation, completion certificate, capture-hook safeguard, next-step options) unchanged.

3.4 WHEN `config/.question_pending` exists at the completion boundary THEN the system SHALL CONTINUE TO defer (produce no completion-artifact output) to `ask-bootcamper`, and SHALL CONTINUE TO apply the treat-as-answer and delete-and-process rules when the bootcamper responds.

3.5 WHEN the agent presents any other single 👉 question outside the module-completion transition turn (onboarding, mid-module steps, feedback, graduation) THEN the system SHALL CONTINUE TO render it exactly as today, unaffected by this fix.

3.6 WHEN a genuine compound or ambiguous question is detected THEN the system SHALL CONTINUE TO apply the compound-question rewrite (numbered-list) rule; this fix does not weaken that behavior.

3.7 WHEN the next-step options are presented (Proceed, Iterate, Explore, Undo, Share) THEN the system SHALL CONTINUE TO offer the same choices; only the duplicate rendering of the forward transition question is removed.
