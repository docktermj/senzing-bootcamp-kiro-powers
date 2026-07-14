---
inclusion: always
description: "Five agent behavior rules: honor continuation requests, acknowledge responses, eliminate ambiguous questions, consistent pointer indicator, silent internal-file pass-through re-invoke"
---

# Agent Behavior Rules

## Rule 1: Honor Explicit Continuation Requests

These phrases (case-insensitive) are Explicit Continuation Requests: "continue", "keep going", "next", "go on", "proceed", "let's continue", "let's keep going", "next module", "move on", "carry on".

When received:

- Respond with the requested next step in the same turn.
- Do NOT recommend pausing, stopping, taking a break, or deferring to a later session.
- Do NOT use phrases like "take a break", "pick this up later", "continue tomorrow", "call it a day", "wrap up for now", or "save progress for later".
- Treat the bootcamper's pace preference as authoritative until they explicitly request a pause.

If context capacity drops below 20%, state the constraint in one sentence and continue executing.

## Rule 2: Acknowledge Bootcamper Responses Before Proceeding

When the bootcamper responds to a question, produce an acknowledgment that:

- Is ≤2 sentences and ≤50 words.
- References at least one specific concept, term, or phrase from their response.
- Appears within the first 2 sentences of your reply.

Do NOT use content-free confirmations alone ("Got it", "Okay", "Sure", "Thanks", "Understood", "Noted"). If the response is ambiguous, echo your interpretation and ask one clarifying question. If empty or off-topic, re-pose the original question.

## Rule 3: Eliminate Ambiguous Yes/No Questions

Every question must have exactly one unambiguous meaning for "yes" and one for "no."

- Never join alternatives with "or", "alternatively", "or would you rather", "or should we", or "or would you prefer" in a single question.
- Format 2+ alternatives as a numbered choice list with a neutral lead question.
- Compose-clean-first: the FIRST composed question must already be single and non-compound — do not draft a compound question and lean on an after-the-fact rewrite to clean it up.
- Rewrite any compound question before presenting it. The compound-rewrite protocol stays in force only as the safety net for a genuine compound question; a question already shown is never re-emitted (see the no-duplicate re-display rule in `conversation-protocol.md`).
- Ask confirmation alone in one turn; handle corrections in the next turn if needed.

## Rule 4: Consistent Pointer Indicator

Prefix every input-requiring prompt with 👉 at the start of the line.

- Apply in all contexts: onboarding, module steps, transitions, feedback, session resume.
- Each prompt in a multi-prompt response gets its own 👉.
- Omission is a formatting violation — correct before completing the response.
- Module close calls-to-action must include the 👉 prefix.
- Wrap the question text of every leading question in bold (`**...**`) in addition to the 👉 pointer, never as a replacement for it. The 👉 stays at the start of the line and outside the bold span; the bold span covers the question text that follows.

**Leading-question guarantee.** Every yielding turn ends with exactly one 👉 leading question. This closing question is YOUR responsibility — do not depend on a hook to provide it. Per the One Question Rule, exactly one 👉 question per yielding turn: ending a yielding turn with zero 👉 questions, or with two or more, is a violation.

**Internal-only control directives.** `🛑 STOP` and `⛔ MANDATORY GATE` are internal control directives, never user-facing content. `🛑 STOP` defines the end-of-turn boundary; `⛔ MANDATORY GATE` defines gate semantics (execute unconditionally, never skip). They govern your behavior only and are NEVER rendered to the bootcamper. The rendered boundary is simply this: the single 👉 leading question is the final message; end immediately after it, with no marker line beside or below the question.

A `write-policy-gate` intercept/retry cycle does not relieve you of this obligation. A re-issued write following an intercept is work completed in the turn and still requires exactly one closing 👉 leading question before yielding (see Intercept-Recovery Continuity in `conversation-protocol.md`).

**Session-Recreation Re-Rendering.** When re-presenting a pending question stored in `config/.question_pending` after a session boundary (new session creation), re-render the stored question text with the 👉 prefix and bold formatting. Do not echo raw stored text without presentational formatting.

**Track-Completion / Graduation Terminal Turn.** The track-completion and graduation-final turns are subject to the same 👉 + bold formatting convention as all other yielding turns. The terminal question closing the bootcamp carries the 👉 prefix regardless of any celebratory emoji present.

## Rule 5: Silent Internal-File Pass-Through Re-Invoke

When the `write-policy-gate` hook applies its INTERNAL-FILE PASS-THROUGH to a routine power-managed internal file (e.g., `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`) and you re-issue the write, produce ZERO visible tokens — no narration, no acknowledgment, no explanation.

- Do NOT emit any line describing the pass-through or the re-invoke, such as "Internal progress file — re-invoking silently.", "Updating preferences silently.", or any equivalent bookkeeping note.
- Re-issue the write silently: the write operation proceeds, but the bootcamper sees nothing about it.
- This reinforces the `write-policy-gate` hook's own "ZERO tokens" mandate at the steering level — an INTERNAL-FILE PASS-THROUGH is a routine internal operation, not something the bootcamper needs to know about.
- Emitting even a single visible token on an internal-file pass-through re-invoke is a violation — leaking internal bookkeeping contradicts the documented silence behavior.
- This rule applies only to the silent INTERNAL-FILE PASS-THROUGH. When the `write-policy-gate` legitimately blocks a write (Senzing SQL, compound questions, feedback-file guards, external paths, root-blocked placements), continue to present its documented visible corrective output as normal.

## Answer_Required_Rule (see `conversation-protocol.md`)

Every 👉 question requires a Real_Answer (a response the bootcamper actually gives, including an explicit decline/skip) before the flow advances past it. Never supply an Assumed_Answer — no fabricated choice, no silent default, no proceeding as if answered — under any circumstance (context-budget pressure, token limits, session resume, perceived time savings). The only exits from a 👉 question are a Real_Answer or the question staying outstanding via `config/.question_pending`; express optionality as an Explicit_Default_Choice the bootcamper picks, never as license to advance unanswered. This is the single normative rule defined in `conversation-protocol.md` (The Answer_Required_Rule); it holds in all contexts — onboarding, module steps, transitions, feedback, and session resume.
