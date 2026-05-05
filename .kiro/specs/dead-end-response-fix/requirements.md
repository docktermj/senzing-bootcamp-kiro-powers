# Bugfix Requirements Document

## Introduction

On multiple occasions during the bootcamp, the agent responds with just "Understood." (or similar brief acknowledgments) and stops — without asking a follow-up question or guiding the bootcamper to the next step. This happens when the bootcamper provides substantive input (e.g., describing their business problem, answering a question) and expects the conversation to continue. The bootcamper is left in a dead end with no guidance on what to do next.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the bootcamper provides substantive input (e.g., describes their business problem, answers a gap-filling question, provides design details) THEN the system sometimes responds with only "Understood." or a similarly brief acknowledgment and stops, without asking a follow-up question or advancing to the next step.

1.2 WHEN the agent produces a dead-end response THEN the bootcamper has no guidance on what to do next and must repeat themselves or figure out how to re-engage the agent.

1.3 WHEN the agent acknowledges input without advancing THEN the bootcamp flow is broken — the guided experience feels unresponsive and the bootcamper loses trust that the agent is actively guiding them.

### Expected Behavior (Correct)

2.1 WHEN the bootcamper provides substantive input that answers a question or advances the conversation THEN the system SHALL acknowledge the input AND follow up with either (a) a leading question that moves the conversation forward, (b) a summary of what was captured and what comes next, or (c) the next step in the module workflow.

2.2 WHEN the agent acknowledges input with "Understood" or similar THEN the system SHALL always append a next action — never leave the bootcamper without a clear next step. Examples: "Understood. Now let me ask about..." or "Got it. Based on what you've described, here's what I'm picking up..."

2.3 WHEN the bootcamper's input completes a step in the current module THEN the system SHALL advance to the next step, displaying appropriate context and the next question or action.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent asks a 👉 question and is waiting for the bootcamper's response THEN the system SHALL CONTINUE TO stop and wait — this fix does not override the question-stop protocol.

3.2 WHEN the agent completes non-interactive work (file creation, code generation) THEN the system SHALL CONTINUE TO complete that work fully before presenting the next interaction point.

3.3 WHEN the bootcamper provides input that is genuinely unclear or off-topic THEN the system MAY ask a clarifying question rather than advancing — but SHALL NOT produce a dead-end acknowledgment with no follow-up.

## Acceptance Criteria

1. The `agent-instructions.md` Communication section SHALL contain an explicit rule prohibiting dead-end acknowledgments: after acknowledging bootcamper input, the agent must always follow up with a next action, question, or step advancement
2. The `ask-bootcamper` agentStop hook prompt SHALL reinforce that every agent turn must end with either a 👉 question OR a clear indication of what comes next — never a bare acknowledgment
3. Module steering files SHALL NOT contain patterns that could lead to dead-end responses (e.g., "acknowledge the input" without "then proceed to...")
4. The fix SHALL NOT introduce unnecessary stop points in non-interactive steps

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Dead-end 'Understood.' responses don't advance the conversation"
- Module: 1 (Business Problem) | Priority: High | Category: UX
