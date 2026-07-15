---
inclusion: always
description: "Turn-taking, question handling, and module transition protocols for active bootcamp sessions"
---

# Conversation Protocol

## The Answer_Required_Rule

**Every 👉 question requires a Real_Answer before the flow advances past it.** This is the single normative rule governing every Question in the bootcamp. A *Question* is a 👉-prefixed prompt directed at the bootcamper that yields the turn. A *Real_Answer* is a response the bootcamper actually gives — including an explicit decline or skip ("use the default", "skip this", "no preference"). An *Assumed_Answer* is any answer you supply on the bootcamper's behalf: a fabricated choice, a silent default, or proceeding as if a response was given when none was.

- **Wait for a Real_Answer.** When you present a 👉 question, stop and wait. Do not proceed past it until the bootcamper supplies a Real_Answer. An explicit decline/skip IS a Real_Answer — record it and proceed accordingly.
- **Never supply an Assumed_Answer.** You SHALL NOT fabricate a choice, apply a silent default, or proceed as if answered when the bootcamper said nothing — under **any** circumstance, including context-budget pressure, token limits, session resume, or perceived time savings. No agent-internal reasoning justifies answering a 👉 question for the bootcamper.
- **Only two exits.** A 👉 question has exactly two exits: (1) a Real_Answer, or (2) the question stays outstanding. There is no third exit in which the agent supplies the answer. If you cannot obtain a Real_Answer (for example, the session ends), the Question SHALL remain outstanding via the `config/.question_pending` marker so a later turn re-presents it — it is never resolved by an Assumed_Answer.
- **Applies everywhere.** This rule holds in all contexts — onboarding, module steps, module transitions, feedback, and session resume.
- **Optionality is an Explicit_Default_Choice.** When a step is genuinely optional, express the optionality as an Explicit_Default_Choice the bootcamper actively selects (e.g., "standard *(recommended)*"), never as license to advance with no answer. Selecting the default is a Real_Answer; assuming it is an Assumed_Answer.

This rule generalizes the existing no-self-answering stance (see the Self-Answering examples below and the `self-answering-prevention` rules): it forbids not only fabricated answers but also silent defaults. It is referenced from `agent-behavior-rules.md` and `agent-instructions.md`.

## The Ask-Once Guarantee

**Every 👉 question is asked at most once — never re-ask a question the bootcamper has already answered, unless they explicitly request a repeat.** This is the single normative rule governing question *repetition*. It complements the Answer_Required_Rule (which governs *whether* an answer is required) by governing *how many times* the same question may be asked.

- **Every 👉 question has a stable Question_Key.** The Question_Key is derived from the owning step (e.g., `onboarding.language_selection`, `module.5.7a`, `global.hardware_target`), so the same logical question always maps to the same key.
- **Consult the ledger before asking.** Before presenting a 👉 question, consult the Question_Ledger (`config/question_ledger.jsonl`, managed by `scripts/question_ledger.py`). Never re-ask a question whose Question_Key is already recorded as answered — reuse the stored answer and proceed. A key recorded as `asked` but not `answered` MAY be re-presented, because it was never answered.
- **The ledger — not conversational memory — is authoritative.** The ledger is the source of truth for what has been asked and answered, so the guarantee holds across context compaction and session resume: a resumed or compacted session consults the ledger and skips already-answered questions.
- **Re-present only on an explicit Repeat_Request.** Re-present a question only when the bootcamper explicitly asks to see it again (a Repeat_Request, e.g., "repeat that", "ask me again"). A Repeat_Request re-presents the current pending question verbatim, creates no new ledger entry, and does not change its answered status.
- **Degrade safely — but never as license to re-ask.** If a Question_Ledger read or write fails, degrade safely: fall back to the existing checkpoint/preference state and never block the bootcamper. An unknown or unavailable ledger state is never license to re-ask a question whose answer is already present in `config/bootcamp_preferences.yaml` — the ledger is the primary mechanism, preferences are the safety net.

This section is the single home of the ask-once guarantee: the narrow "do not re-ask" notes elsewhere (e.g., the Module 8 hardware question, session-resume preference fields) are specific instances of it. It is referenced from `agent-behavior-rules.md` and `agent-instructions.md`.

## Answer Processing Priority

Processing a bootcamper's answer to a 👉 question is the **highest-priority action** in any turn. No other work — content generation, context management, hook evaluation, or status updates — may proceed until the pending answer has been fully processed.

**Substantive output requirement:** When the bootcamper's message is a response to a pending 👉 question, you SHALL produce substantive output that acknowledges and acts upon the answer before the turn ends. A minimal acknowledgment (e.g., ".", "OK", empty output) is never acceptable as a response to a pending answer.

**Treat-as-answer rule:** If `config/.question_pending` exists at the start of a turn, treat the bootcamper's message as an answer to that pending question regardless of message content. Do not reinterpret, redirect, or ignore the message — process it as the answer.

**No-substantive-output-while-pending rule:** While `config/.question_pending` exists, produce no substantive output other than processing the bootcamper's answer to the pending question. Do not advance the workflow, present new content, or ask new questions until the pending answer has been processed and the file deleted.

## End-of-Turn Protocol

When you complete work that does NOT end with a 👉 question:

- Briefly recap what you accomplished and which files changed
- End with a contextual 👉 closing question asking what the bootcamper wants to do next
- This is YOUR responsibility — do not rely on hooks to provide the closing question

When you DO end with a 👉 question:

- Write the file `config/.question_pending` using the structured format:
  - **Line 1:** Question type — one of: `track_selection`, `module_transition`, `step_question`, `confirmation`, `choice`
  - **Lines 2+:** Full question text (may be multi-line)
  - If you cannot determine the appropriate type, default to `step_question`
- The ask-bootcamper hook will fire but produce no output (this is correct)

When processing the bootcamper's next message:

- Delete `config/.question_pending` before doing anything else

The ask-bootcamper hook is a safety net only — do not rely on it for closing questions.

When you complete the LAST sub-step in a gap-filling sequence (all undetermined items resolved): writing the checkpoint is NOT the end of your turn. You must also present the next numbered step's 👉 question. The checkpoint marks sub-step completion; the 👉 question marks turn completion.

### Intercept-Recovery Continuity

When a turn's primary action was a write **re-issued after a `write-policy-gate` intercept**, the turn is NOT complete until you have appended exactly one 👉 leading question reflecting the next step in the guided flow AND written `config/.question_pending`. A re-issued write is work completed in the turn — it carries the same closing-question obligation as any other yielding turn.

Ending such a turn on bare tool activity or a bare acknowledgment (".", empty output) is a **protocol violation** equivalent to a dead-end response. The intercept/retry cycle never separates the completed work from the next instruction, and you must not wait for the bootcamper to prompt for the next question.

This closing question is YOUR responsibility and is not deferred to a hook. The One Question Rule and Question Stop Protocol below continue to govern the *shape* of that question.

## Question Stop Protocol

Every 👉 question and ⛔ gate is an end-of-turn boundary. End your response immediately after the question text — produce no further tokens. Do not answer, assume a response, proceed to the next step, or write checkpoints.

After asking a 👉 question, write the file `config/.question_pending` using the structured format (type on first line, question text on subsequent lines) before ending your turn.

At the start of every turn where you process bootcamper input, check for and delete `config/.question_pending` if it exists.

### Numbered Step Execution Boundary

Every numbered step containing a 👉 question is a mandatory execution boundary with the same absolute precedence as ⛔ mandatory gates. The agent SHALL:

- Execute each numbered step individually in sequential order
- Never advance `current_step` by more than 1 without writing intermediate checkpoints
- Never skip a 👉 step for any internal reason (context budget, session length, redundancy)
- Write `config/.question_pending` before ending the turn at any 👉 question

Violation of this rule is equivalent to a ⛔ mandatory gate violation.

## No Dead-End Responses

Never end a turn with only an acknowledgment (e.g., "Understood.", "Got it.", "I see."). Every turn must advance the conversation by: (a) asking a 👉 follow-up question, (b) summarizing what was captured and stating what comes next, or (c) proceeding to the next step in the module workflow.

If you acknowledge input, always append a next action in the same response.

### Sub-Step Completion Dead-End (WRONG)

> Got it — you're looking for a clean master list. ✅ Checkpoint written.

### Sub-Step Completion (CORRECT)

> Got it — you're looking for a clean master list. ✅ Checkpoint written.
>
> 👉 **Will the entity resolution results need to interface with other
> software — for example, a CRM, search engine, data warehouse, or
> downstream application?**

## Code Block Formatting

All JSON displayed in chat must use ` ```json ` code blocks with 2-space indentation. Never display JSON as raw text or in untagged code blocks.

### WRONG — untagged code block

````text
```
{"RECORD_ID": "1001", "NAME_FULL": "Robert Smith", "DATE_OF_BIRTH": "1982-11-02"}
```
````

### CORRECT — tagged json block with pretty-printing

````text
```json
{
  "RECORD_ID": "1001",
  "NAME_FULL": "Robert Smith",
  "DATE_OF_BIRTH": "1982-11-02"
}
```
````

## One Question Rule

⚠️ **CRITICAL — ZERO TOLERANCE** ⚠️

Every yielding turn ends with **exactly one** 👉 leading question. A turn ending with **zero** 👉 questions, or with **two or more** 👉 questions, violates this rule. This is the single most important conversation rule in the bootcamp. Violations destroy bootcamper trust.

**The rule is absolute:** One question. One question mark. One unambiguous meaning for "yes." One unambiguous meaning for "no." No exceptions. No edge cases. No "just this once."

Multi-question patterns — questions joined by conjunctions (and, or, also, but first, alternatively, or if you prefer) — are violations. When you need multiple pieces of information, ask the first question, stop, wait for the response, then ask the next question in a separate turn.

The phrase "But first" followed by a question is a violation — never redirect to a different question within the same turn.

**Enforcement:** The `write-policy-gate` hook validates every question written to `config/.question_pending`. If it detects a compound question, you MUST rewrite before proceeding. Do not attempt to bypass this check.

**Common violations to avoid:**

- "Would you like to X, or would you prefer Y?" → Use a numbered choice list instead
- "Does that look right? Anything I missed?" → Ask only the confirmation; handle corrections in the next turn
- "Ready to continue? I can also show you..." → Ask only "Ready to continue?"
- "Would you like to see examples, or should we skip ahead?" → Use a numbered choice list

## Bold Question Text

The question text of every 👉 leading question is wrapped in **bold** (CommonMark strong emphasis, `**...**`) so the actual interrogative is easy to spot inside a dense turn.

- **Bold is additive, never a replacement for 👉.** The 👉 pointer stays at the start of the line, outside the bold span, separated from the question text by a single space. The bold span opens at the first character of the question text and closes at its last character, including the terminal question mark.
- **Context stays plain.** Explanatory sentences that precede the question text are rendered in plain text — only the question text itself is bold.
- **Choice questions: bold the lead only.** In a choice question, only the neutral lead question is wrapped in bold; the numbered option lines stay in plain text.
- **Bold is presentational.** It does not alter the One Question Rule. The number of 👉 leading questions in a turn is counted solely from the 👉 occurrences and is unaffected by the presence or absence of bold markers.
- **`🛑 STOP` and `⛔ MANDATORY GATE` are internal-only directives.** They govern end-of-turn and gate behavior but are NEVER rendered to the bootcamper. Do not emit a marker line beside or below a question — the rendered boundary is the single 👉 question as the final message, ended immediately after it.

### Bold Question (CORRECT)

> 👉 **What language would you like to use?**

## Choice Formatting

When a 👉 question presents 2 or more distinct alternatives (options the bootcamper can choose between), format them as a numbered list:

### Compound Choice (WRONG)

> 👉 Would you like to proceed with Python or Java or TypeScript?

### Compound Choice (CORRECT)

> 👉 **Which language would you like to use?**
>
> 1. Python
> 2. Java
> 3. TypeScript

Simple yes/no questions or questions with a single implied action remain as inline prose:

### Simple Question (CORRECT — no list needed)

> 👉 **Ready to move on to Module 3?**

## Question Disambiguation

Every 👉 question must have exactly one unambiguous meaning for each possible short answer. A "yes" must map to one interpretation. A "no" must map to one interpretation.

**Compound Question anti-pattern:** A prompt that combines a Confirmation Question with a Follow-Up Question. Example: "Does that look right? Anything I missed?" — "yes" could mean "yes it's right" OR "yes you missed something."

**Rule:** When you need both confirmation and correction input:

1. Ask the confirmation question alone: "👉 Does that capture your situation accurately?"
2. If the bootcamper says yes → proceed to the next step.
3. If the bootcamper says no → ask "👉 What would you like me to change?" in the next turn.

Never append "or should we adjust anything?" or "Anything I missed?" to a confirmation question. Never combine "Would you like X?" with "Or would you prefer Y?" in prose — use a numbered choice list instead.

**Compose-clean-first.** Compose every 👉 question as a single, non-compound question on the FIRST attempt. Do not draft a compound "or" question and rely on a later rewrite to clean it up — for example, compose a comprehension check as `👉 **Does the overview make sense before we choose a track?**`, never as a prose "Does everything make sense so far, or is there anything you'd like me to clarify?" that then has to be regenerated. The compound-rewrite protocol (Rule 3 / the Rewrite Protocol below) remains in force only as the safety net for a genuine compound question.

**No-duplicate re-display.** An internal correction or regeneration pass MUST NOT re-emit a 👉 question that was already shown to the bootcamper. The corrected question replaces the draft before it is shown, never in addition to it. Re-display a question only when the bootcamper explicitly asks to see it again (genuine corrective content that has not yet been surfaced still follows the existing hook-output rules).

## Violation Examples

### Multi-Question (WRONG)

> 👉 What language do you want? Also, which track interests you?

### Multi-Question (CORRECT)

> 👉 **What language do you want?**

*Internal: end the turn on this question and wait. Ask "Which track interests you?" only in a separate later turn — never in this one. The stop-and-wait boundary is a directive to you, not shown to the bootcamper.*

### Not-Waiting (WRONG)

> 👉 Are you ready to continue?
> Great, let's move on to the next step.

### Not-Waiting (CORRECT)

> 👉 **Are you ready to continue?**

*Internal: end the turn on this question and wait for the bootcamper's reply before doing anything else. The boundary is a directive to you, not shown to the bootcamper.*

### Dead-End (WRONG)

> Got it.

### Dead-End (CORRECT)

> Got it. Next I'll set up your project structure.

### Missing-Prefix (WRONG)

> What language would you like to use?

### Missing-Prefix (CORRECT)

> 👉 **What language would you like to use?**

### Self-Answering (WRONG)

> 👉 Who will be working on this project?
> I'll assume it's just you for now.

### Self-Answering (CORRECT)

> 👉 **Who will be working on this project?**

*Internal: end the turn on this question and wait — never answer it yourself. The boundary is a directive to you, not shown to the bootcamper.*

### Compound Confirmation (WRONG)

> 👉 Does that summary sound right? Anything I missed or got wrong?

### Compound Confirmation (CORRECT)

> 👉 **Does that summary capture your situation accurately?**

### Compound Either/Or (WRONG)

> 👉 Would you like me to create a one-page executive summary, or would you prefer to skip that and move on to Module 2?

### Compound Either/Or (CORRECT)

> 👉 **What would you like to do next?**
>
> 1. Create a one-page executive summary
> 2. Move on to Module 2

## Rule Priority

Conversation UX rules take precedence over content generation. Never sacrifice turn-taking correctness to deliver more information in a single turn. If following a rule means splitting content across multiple turns, split it.

## Pre-Output Validation Checklist

Execute this checklist **before every turn** that contains a pointing-hand question. Stop at the first failure and rewrite before sending.

1. **Compound-question check (fail-fast):** Verify the closing question does NOT contain two or more alternatives joined by prose ("or", "Or", "alternatively", "or would you rather", "or should we"). If it does → apply the Rewrite Protocol below.
2. Verify this turn contains at most one closing question. If more than one → keep only the first; defer the rest to subsequent turns.
3. Verify every closing question has the pointing-hand prefix. If missing → add it.
4. Verify no content appears after the closing question. If content follows → move it before the question or remove it.
5. Verify you are not answering your own question. If self-answering → delete the self-answer.
6. Verify no closing question offers to skip or bypass an upcoming mandatory gate step. If it does → remove the skip option.
7. **Bold-question check:** Verify the closing 👉 question's text is wrapped in bold (`**...**`) before output. If the question text is not bold → wrap it in bold, keeping 👉 outside the span (for a choice question, bold only the lead question line).
8. **No-leaked-marker check:** Verify no `🛑 STOP` or `⛔ MANDATORY GATE` text appears in the rendered turn. If a marker is present → delete it and simply end the turn after the 👉 question (the boundary is internal, not rendered).
9. **No-duplicate check:** Verify this 👉 question was not already shown to the bootcamper — in a prior turn or an earlier draft in this same turn. If it was already surfaced → do not re-emit it, unless the bootcamper explicitly asked to see it again.

### Rewrite Protocol

When the compound-question check (item 1) fails, rewrite the question using these steps:

**Step 1 — Count the alternatives.** Identify each distinct action or option joined by prose conjunctions.

**Step 2 — Choose the format:**

- **Two or more alternatives** → numbered list preceded by a single neutral question.
- **Confirmation with appended alternative** (e.g., "Does that look right? Or would you like me to adjust it?") → keep only the confirmation; drop the appended alternative entirely.

**Step 3 — Rewrite.**

- For numbered lists: write one neutral lead question (no alternatives in it), then list each option on its own numbered line.
- For confirmations: remove everything after the first question mark.

**Step 4 — Re-validate.** Run the checklist again from item 1 on the rewritten question.

### Rewrite Examples

#### Either/Or joined by prose

##### WRONG

> 👉 Would you like me to create a one-page executive summary you can share with your team or manager? Or shall we skip that and move on to Module 3?

##### CORRECT

> 👉 **What would you like to do next?**
>
> 1. Create a one-page executive summary to share with your team
> 2. Skip ahead to Module 3

#### Appended alternative on confirmation

##### WRONG

> 👉 Does that look right? Or would you like me to adjust it?

##### CORRECT

> 👉 **Does that look right?**

#### Sentence-starter "Or"

##### WRONG

> 👉 Should I generate the loading program now? Or would you rather review the mapping first?

##### CORRECT

> 👉 **What would you like to do next?**
>
> 1. Generate the loading program now
> 2. Review the mapping first

#### Prose-joined choices (inline "or")

##### WRONG

> 👉 Would you like to proceed with Python or Java?

##### CORRECT

> 👉 **Which language would you like to use?**
>
> 1. Python
> 2. Java

## Self-Check

Before ending any turn, verify:

1. Does this turn contain more than one 👉 question?
2. Does any 👉 question lack the 👉 prefix?
3. Is there content after a 👉 question?
4. Am I answering my own question?
5. Does any 👉 question offer to skip or bypass an upcoming ⛔ mandatory gate step?
6. Does the closing 👉 question's text lack bold emphasis (`**...**`)?
7. Does the turn render a `🛑 STOP` or `⛔ MANDATORY GATE` marker beside the question?
8. Was this 👉 question already shown to the bootcamper (and not explicitly re-requested)?

If any answer is yes (across all 8 checks), revise the turn before sending.

## Mandatory question_pending

Writing `config/.question_pending` is mandatory for every 👉 question — not optional, not best-effort. If you output a 👉 question and do not write the file, you have violated the protocol. The file must use the structured format: question type on the first line (one of: `track_selection`, `module_transition`, `step_question`, `confirmation`, `choice`), full question text on subsequent lines. Default to `step_question` when the type is undetermined. The file enforces the wait: while it exists, you must not generate response content until the bootcamper provides input and the file is deleted.

## Final-Message Invariant

Every input-expecting (yielding) turn ends with exactly one **live** 👉 pending question as the **final message** shown to the bootcamper, with `config/.question_pending` written for it. The live 👉 pending question must be the final message of an input-expecting turn — nothing may appear after it.

A recap or confirmation emission must never be the final message of an input-expecting turn. If any recap/confirmation runs after the 👉 question (for example a per-module recap step), the live 👉 pending question must be re-surfaced as the final message and `config/.question_pending` (re)written for it, so the bootcamper always ends the turn looking at one actionable question.

## Module Transition Protocol

When you ask 'Ready for Module X' and the bootcamper responds affirmatively (yes, sure, let's go, ready, etc.), immediately begin that module in the same turn. Display the module banner, journey map, and start Step 1. Never acknowledge without acting at a module transition.

**📏 MINIMUM CONTENT REQUIREMENT:** After receiving a Transition_Confirmation, the agent response MUST contain:

1. The module start banner (━━━ header with module number and name)
2. The journey map table (Module | Name | Status)
3. The before/after framing
4. A brief numbered overview of the module's steps
5. Step 1's introductory content (what and why)

Outputting only ".", empty content, single-word acknowledgments, or any response under 50 characters after a Transition_Confirmation is a **protocol violation**. The detect-and-retry hook will catch and correct such violations automatically.

**⛔ PROHIBITED:** Saving progress and ending the session is PROHIBITED as a response to an affirmative answer to a module transition question. Do not save progress, do not offer to pause, do not end the session. The only valid action is to start the module.

**🔒 COMMITMENT RULE:** Once a "Ready for Module X" transition question has been asked, the only valid response to an affirmative answer is to start Module X — never to save progress, pause, or end the session. Asking the transition question is a commitment to execute the transition if confirmed.

**⚠️ CONTEXT-LIMIT GUIDANCE:** If context limits are a concern, address them BEFORE asking the transition question, not after receiving the affirmative response. If you cannot guarantee you can start the next module, do not ask the transition question — instead, transparently inform the bootcamper about the limitation and offer to save progress.
