---
inclusion: auto
description: "Turn-taking, question handling, and module transition protocols for active bootcamp sessions"
---

# Conversation Protocol

## End-of-Turn Protocol

When you complete work that does NOT end with a 👉 question:

- Briefly recap what you accomplished and which files changed
- End with a contextual 👉 closing question asking what the bootcamper wants to do next
- This is YOUR responsibility — do not rely on hooks to provide the closing question

When you DO end with a 👉 question:

- Write the file `config/.question_pending` containing the question text
- The ask-bootcamper hook will fire but produce no output (this is correct)

When processing the bootcamper's next message:

- Delete `config/.question_pending` before doing anything else

The ask-bootcamper hook is a safety net only — do not rely on it for closing questions.

## Question Stop Protocol

Every 👉 question and ⛔ gate is an end-of-turn boundary. End your response immediately after the question text — produce no further tokens. Do not answer, assume a response, proceed to the next step, or write checkpoints.

After asking a 👉 question, write the file `config/.question_pending` with the question text before ending your turn.

At the start of every turn where you process bootcamper input, check for and delete `config/.question_pending` if it exists.

## No Dead-End Responses

Never end a turn with only an acknowledgment (e.g., "Understood.", "Got it.", "I see."). Every turn must advance the conversation by: (a) asking a 👉 follow-up question, (b) summarizing what was captured and stating what comes next, or (c) proceeding to the next step in the module workflow.

If you acknowledge input, always append a next action in the same response.

## Module Transition Protocol

When you ask 'Ready for Module X?' and the bootcamper responds affirmatively (yes, sure, let's go, ready, etc.), immediately begin that module in the same turn. Display the module banner, journey map, and start Step 1. Never acknowledge without acting at a module transition.
