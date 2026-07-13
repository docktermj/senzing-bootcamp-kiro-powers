# Bugfix Requirements Document

## Introduction

During onboarding, the `ask-bootcamper` hook fires on the agent's `Stop` trigger at the entity-resolution-intro mandatory gate (Step 3) and generates a contextual closing question. Because the hook can see upcoming steering context, it previews the *next* step — "picking your programming language" — even though the gate hasn't been cleared and the language question is never actually presented. This leaves the bootcamper confused about whether they missed a prompt or the agent stalled. The gate-to-language handoff also lacks a direct routing path, meaning the bootcamper's "move on" signal can dead-end back into the same gate rather than immediately presenting the programming-language question.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `ask-bootcamper` hook fires at the entity-resolution-intro mandatory gate (Step 3) THEN the system generates a closing question that references "picking your programming language" — a specific upcoming question that has not been asked

1.2 WHEN the bootcamper signals readiness to move on from the entity-resolution-intro gate THEN the system may re-present the same gate checkpoint instead of immediately transitioning to the programming-language question (Step 4)

1.3 WHEN the `ask-bootcamper` hook generates a contextual closing question while a mandatory gate is active THEN the system previews specific content from the next step, creating the appearance that a question was posed and dropped

### Expected Behavior (Correct)

2.1 WHEN the `ask-bootcamper` hook fires at any mandatory gate THEN the system SHALL keep any "what's next" reference generic (e.g., "we'll continue setup") and SHALL NOT name or preview a specific question from a subsequent step that has not been presented

2.2 WHEN the bootcamper signals readiness to move on from the entity-resolution-intro gate THEN the system SHALL immediately transition to the programming-language selection question (Step 4) without re-presenting the gate

2.3 WHEN the `ask-bootcamper` hook generates a contextual closing question while a mandatory gate is active THEN the system SHALL limit forward-looking references to generic phrasing that does not reveal the content of the next step's question

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the `ask-bootcamper` hook fires after a non-gate step that has been completed THEN the system SHALL CONTINUE TO generate contextual closing questions that may reference upcoming content naturally

3.2 WHEN the bootcamper asks a follow-up question at the entity-resolution-intro gate THEN the system SHALL CONTINUE TO answer it using search_docs and re-present the gate

3.3 WHEN the `ask-bootcamper` hook fires and no mandatory gate is active THEN the system SHALL CONTINUE TO produce contextual recaps and closing questions with full awareness of the session context

3.4 WHEN the bootcamper signals readiness to move on from non-gate steps THEN the system SHALL CONTINUE TO transition to the next step according to the existing steering flow

3.5 WHEN the `ask-bootcamper` hook detects a pending question (config/.question_pending exists) THEN the system SHALL CONTINUE TO suppress Phase 1 output as currently designed
