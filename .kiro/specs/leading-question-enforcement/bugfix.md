# Bugfix Requirements Document

## Introduction

During Module 1, after the bootcamper answers the gap-filling question in Step 7d (desired outcome), the agent acknowledges the input but stops without asking the next question in the workflow sequence (Step 8: software integration). The conversation stalls, forcing the bootcamper to explicitly ask the agent to continue. This violates the bootcamp's guided experience principle: every response that processes bootcamper input for a workflow step must end with the leading question for the next step.

The root cause is that the steering files instruct the agent to "ask about only one undetermined item per turn" (Step 7) and mark each sub-step with a 🛑 STOP, but do not explicitly instruct the agent to advance to the next numbered step (Step 8) once all gap-filling sub-steps are complete. The agent treats the checkpoint write as the end of its work without recognizing that the workflow requires immediate progression to the next step's question.

This differs from the existing `dead-end-response-fix` (which addresses bare "Understood." responses) and `forward-moving-questions` (which addresses hook-triggered work not ending with a question). This bug is about the agent failing to chain workflow steps — specifically, not asking the next step's question after completing a multi-part gap-filling sequence.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the bootcamper answers the last gap-filling sub-step question (e.g., Step 7d) and no further undetermined items remain THEN the system acknowledges the input, writes the checkpoint, and stops without asking the next workflow step's question (Step 8).

1.2 WHEN the bootcamper provides input that completes a multi-part step sequence (Steps 7a–7d) THEN the system does not automatically advance to the next numbered step, leaving the bootcamper without direction on what comes next.

1.3 WHEN the agent processes a gap-filling answer that resolves the last undetermined item THEN the system ends its turn without a leading question, requiring the bootcamper to manually prompt the agent to continue.

### Expected Behavior (Correct)

2.1 WHEN the bootcamper answers the last gap-filling sub-step question and no further undetermined items remain THEN the system SHALL acknowledge the input, write the checkpoint, and immediately ask the next workflow step's 👉 question (e.g., Step 8's software integration question).

2.2 WHEN the bootcamper provides input that completes a multi-part step sequence THEN the system SHALL advance to the next numbered step in the same turn, presenting that step's question as the leading question to keep the bootcamp moving forward.

2.3 WHEN the agent processes a gap-filling answer that resolves the last undetermined item THEN the system SHALL end its turn with the next step's 👉 question, ensuring the conversation always flows forward without requiring bootcamper prompting.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper answers a gap-filling sub-step question but additional undetermined items remain (e.g., answering 7b when 7c and 7d are still needed) THEN the system SHALL CONTINUE TO ask only the next undetermined sub-step question and stop, following the one-question-per-turn rule.

3.2 WHEN the agent asks a 👉 question at a 🛑 STOP point within a step THEN the system SHALL CONTINUE TO stop and wait for the bootcamper's response before proceeding.

3.3 WHEN the bootcamper's input is unclear or off-topic THEN the system SHALL CONTINUE TO ask a clarifying question rather than blindly advancing to the next step.

3.4 WHEN the agent is at a mandatory gate (⛔) that requires explicit bootcamper confirmation THEN the system SHALL CONTINUE TO wait for confirmation before advancing, regardless of the leading-question rule.

3.5 WHEN the bootcamper explicitly asks to pause, save progress, or end the session THEN the system SHALL CONTINUE TO honor that request rather than forcing advancement to the next step.
