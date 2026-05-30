# Requirements Document

## Introduction

This feature adds four agent behavior rules to the Senzing Bootcamp Power's steering files. These rules address reported issues where the agent: (1) overrode a bootcamper's explicit choice to continue, (2) failed to acknowledge answers before proceeding, (3) asked ambiguous yes/no questions, and (4) inconsistently used the 👉 pointer indicator for bootcamper-directed prompts. Each rule codifies expected agent behavior to improve conversational UX and respect bootcamper autonomy.

## Glossary

- **Agent**: The AI assistant guided by steering files that delivers the Senzing Bootcamp experience
- **Bootcamper**: The human user progressing through the bootcamp modules
- **Steering_File**: A Markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that controls agent behavior
- **Pointer_Indicator**: The 👉 emoji prefix used on all prompts that require bootcamper input
- **Explicit_Continuation_Request**: A bootcamper message that unambiguously states intent to proceed (e.g., "continue to module 3", "let's keep going", "next module")
- **Acknowledgment**: A brief echo-back of the bootcamper's response that confirms it was received and understood before the agent proceeds
- **Compound_Question**: A question where a "yes" or "no" answer could map to more than one action due to multiple alternatives joined by prose

## Requirements

### Requirement 1: Honor Explicit Continuation Requests

**User Story:** As a bootcamper, I want the agent to immediately proceed when I explicitly say I want to continue, so that my learning pace is never overridden by unsolicited suggestions to stop.

#### Acceptance Criteria

1. WHEN the bootcamper sends an Explicit_Continuation_Request (defined as any message containing phrases such as "continue", "keep going", "next", "go on", "proceed", "let's continue", or an affirmative response to a proposed next step), THE Agent SHALL respond with the requested next step in the same turn without including any recommendation, question, or statement that proposes pausing, stopping, taking a break, or deferring work to a later session.
2. WHILE the bootcamper's most recent Explicit_Continuation_Request has not been superseded by an explicit pause request from the bootcamper or by the end of the current conversation, THE Agent SHALL treat the bootcamper's stated pace preference as authoritative and produce no output that recommends reducing pace, stopping, or starting a new session.
3. IF the Agent detects that remaining context window capacity has dropped below 20 percent of the model's maximum context length, THEN THE Agent SHALL state the context-length constraint in one sentence and continue executing the bootcamper's request in the same response rather than suggesting they stop or defer.
4. THE Agent SHALL never produce output containing recommendations, questions, or statements that propose pausing, stopping, or deferring to a later session within any response where the bootcamper has issued an Explicit_Continuation_Request.
5. IF the bootcamper sends a message that does not match any Explicit_Continuation_Request phrase and does not explicitly request continuation, THEN THE Agent SHALL NOT treat the message as an Explicit_Continuation_Request and MAY offer pacing suggestions if contextually appropriate.

### Requirement 2: Acknowledge Bootcamper Responses Before Proceeding

**User Story:** As a bootcamper, I want the agent to acknowledge my answer before moving on, so that I know my input was received and understood correctly.

#### Acceptance Criteria

1. WHEN the bootcamper provides a response to a question, THE Agent SHALL produce an Acknowledgment of no more than 2 sentences and no more than 50 words that summarizes what the bootcamper said before taking any next action.
2. WHEN the bootcamper provides a response to a question, THE Agent SHALL include the Acknowledgment within the first two sentences of the response turn.
3. WHEN the Acknowledgment is produced, THE Agent SHALL reference at least one specific concept, term, or phrase from the bootcamper's response rather than using a content-free confirmation phrase such as "Got it", "Okay", "Sure", or "Thanks" alone.
4. IF the bootcamper's response contains multiple possible interpretations, incomplete information needed to proceed, or contradicts prior context in the conversation, THEN THE Agent SHALL echo back the interpreted meaning and ask a single clarifying question before proceeding.
5. IF the bootcamper's response is empty, contains only whitespace, or does not address the question asked, THEN THE Agent SHALL indicate that no relevant answer was detected and re-pose the original question.

### Requirement 3: Eliminate Ambiguous Yes/No Questions

**User Story:** As a bootcamper, I want every question the agent asks me to have an unambiguous answer, so that I never have to guess which action my "yes" or "no" will trigger.

#### Acceptance Criteria

1. THE Agent SHALL ensure that every question directed at the bootcamper has exactly one unambiguous meaning for "yes" and exactly one unambiguous meaning for "no."
2. IF a question presents two or more distinct alternatives (up to a maximum of 5), THEN THE Agent SHALL format the alternatives as a numbered choice list preceded by a single lead question that does not favor any listed alternative.
3. THE Agent SHALL never join two or more alternatives with prose conjunctions ("or", "alternatively", "or would you rather") in a single question.
4. WHEN the Agent needs both a confirmation and a correction opportunity, THE Agent SHALL ask the confirmation question alone in one turn, then ask for corrections in a subsequent turn only if the bootcamper responds with "no" or otherwise indicates the content is incorrect.
5. IF the Agent's pre-presentation validation detects that a question matches the Compound_Question definition, THEN THE Agent SHALL rewrite the question into either a single unambiguous yes/no question or a numbered choice list before presenting it to the bootcamper.

### Requirement 4: Consistent Pointer Indicator on All Bootcamper-Directed Prompts

**User Story:** As a bootcamper, I want all prompts that require my input to use the pointer indicator consistently, so that I always know when the agent is waiting for me to respond.

#### Acceptance Criteria

1. THE Agent SHALL prefix every prompt where the Agent is waiting for bootcamper input before proceeding with the Pointer_Indicator placed at the start of the line containing the prompt text, including module completion transition prompts.
2. WHEN the Agent produces a module close message that includes a call-to-action for the bootcamper (e.g., "Say 'continue the bootcamp' when you're ready"), THE Agent SHALL prefix that call-to-action with the Pointer_Indicator.
3. IF the Agent's response contains a prompt requiring bootcamper input, THEN THE Agent SHALL ensure the final presented output includes the Pointer_Indicator prefix on that prompt, treating any omission as a formatting violation that must be corrected before the response is complete.
4. THE Agent SHALL apply the Pointer_Indicator rule uniformly across all contexts: onboarding, module steps, module transitions, feedback workflow, and session resume.
5. WHEN the Agent includes more than one prompt requiring bootcamper input within a single response turn, THE Agent SHALL prefix each individual prompt with its own Pointer_Indicator.
