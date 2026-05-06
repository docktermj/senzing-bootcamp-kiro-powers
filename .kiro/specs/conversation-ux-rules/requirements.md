# Requirements Document

## Introduction

Strengthen and consolidate the conversation UX rules across the senzing-bootcamp power's steering files to eliminate five recurring violations: multi-question turns, not waiting for responses, dead-end silences after bootcamper input, missing 👉 prefix on questions, and the agent answering its own questions after session resume. The existing `conversation-protocol.md` contains the right rules but they are not reliably followed because they lack explicit enforcement mechanisms, are not reinforced in context-specific steering files, and are not re-asserted on session resume.

## Glossary

- **Turn**: A single agent response from first token to last token. The agent produces exactly one turn before yielding to the bootcamper.
- **Bootcamper_Question**: Any question directed at the bootcamper that expects a response. Identified by the 👉 prefix.
- **Question_Pending_File**: The file `config/.question_pending` that signals a 👉 question is awaiting a bootcamper response.
- **STOP_Marker**: The `🛑 STOP` directive in steering files that marks an absolute end-of-turn boundary where the agent must cease output.
- **Conversation_Protocol**: The steering file `conversation-protocol.md` with `inclusion: auto` that defines turn-taking rules.
- **Session_Resume**: The steering file `session-resume.md` loaded when `config/bootcamp_progress.json` exists at session start.
- **Feedback_Workflow**: The steering file `feedback-workflow.md` loaded when a feedback trigger phrase is detected.
- **Dead_End_Response**: An agent turn that ends with only an acknowledgment and no forward action, leaving the bootcamper with no indication of what happens next.
- **Self_Answering**: The agent providing an answer to its own 👉 question instead of waiting for the bootcamper's real input.
- **One_Question_Rule**: The constraint that each agent turn contains at most one Bootcamper_Question.
- **Agent_Instructions**: The steering file `agent-instructions.md` with `inclusion: always` that defines top-level agent behavior.

## Requirements

### Requirement 1: One Question Per Turn

**User Story:** As a bootcamper, I want the agent to ask only one question at a time, so that I can respond clearly without being forced to answer multiple things at once.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL state that each Turn contains at most one Bootcamper_Question.
2. WHEN the agent needs to collect multiple pieces of information, THE Conversation_Protocol SHALL require the agent to ask the first question, stop, wait for the response, and then ask the next question in a subsequent Turn.
3. THE Feedback_Workflow SHALL structure its multi-step gathering (Steps 2.1 through 2.6) so that each question is a separate Turn with a STOP_Marker after each.
4. IF a Turn contains text that asks two or more questions separated by conjunctions (and, or, also, but first), THEN THE Conversation_Protocol SHALL classify this as a violation of the One_Question_Rule.
5. THE Agent_Instructions SHALL reinforce the One_Question_Rule in the Communication section with an explicit prohibition against combining questions with conjunctions.

### Requirement 2: Wait for Response Before Next Question

**User Story:** As a bootcamper, I want the agent to wait for my answer before asking the next question, so that I have the opportunity to respond to every question asked.

#### Acceptance Criteria

1. WHEN the agent asks a Bootcamper_Question, THE Conversation_Protocol SHALL require the agent to end the Turn immediately after the question text.
2. THE Conversation_Protocol SHALL state that no content may follow a 👉 question within the same Turn — no transitions, no previews, no additional questions.
3. WHEN a steering file contains multiple sequential questions (such as onboarding gates), THE Conversation_Protocol SHALL require each question to be separated by a STOP_Marker that enforces a Turn boundary.
4. THE Conversation_Protocol SHALL state that the phrase "But first" followed by a question is a violation pattern — the agent must not redirect to a different question within the same Turn.

### Requirement 3: No Dead-End Silences

**User Story:** As a bootcamper, I want the agent to always respond after I answer a question, so that the conversation never appears dead or stuck.

#### Acceptance Criteria

1. WHEN the bootcamper provides input in response to a Bootcamper_Question, THE Conversation_Protocol SHALL require the agent to produce a Turn that either advances to the next step, asks a follow-up 👉 question, or summarizes what was captured and states what comes next.
2. THE Conversation_Protocol SHALL state that producing zero output after receiving bootcamper input is a violation, regardless of hook state or system context.
3. IF the agent receives bootcamper input that does not match expected options, THEN THE Conversation_Protocol SHALL require the agent to acknowledge the input and either clarify or re-ask the question.
4. THE Conversation_Protocol SHALL state that every bootcamper message must receive a visible agent response — silence is never acceptable after bootcamper input.

### Requirement 4: Mandatory 👉 Prefix on All Bootcamper-Directed Questions

**User Story:** As a bootcamper, I want every question directed at me to use the 👉 prefix, so that I always know when it is my turn to respond.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL state that every question expecting bootcamper input must be prefixed with 👉 regardless of which steering file or workflow context generated the question.
2. WHEN a module steering file contains a question for the bootcamper (such as compliance requirements or stakeholder identification), THE question text SHALL include the 👉 prefix.
3. WHEN the Feedback_Workflow asks a question in Steps 2.1 through 2.6, THE question text SHALL include the 👉 prefix.
4. WHEN the Session_Resume presents the "Ready to continue?" question, THE question text SHALL include the 👉 prefix.
5. THE Agent_Instructions SHALL state that a question without the 👉 prefix is a formatting violation that must be corrected.
6. THE Conversation_Protocol SHALL define the 👉 prefix as the sole visual marker that signals "the agent is waiting for bootcamper input."

### Requirement 5: Never Answer Own Questions

**User Story:** As a bootcamper, I want the agent to never answer questions on my behalf, so that I retain full control over my choices and the agent does not make assumptions about my responses.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL state that after asking a Bootcamper_Question, the agent must not generate any text that could be interpreted as an answer to that question.
2. THE Session_Resume SHALL re-assert the Self_Answering prohibition in Step 3 before presenting the welcome-back summary.
3. WHEN a new session begins and the agent loads Session_Resume, THE Session_Resume SHALL include an explicit instruction: "Do not answer any 👉 question. Do not assume the bootcamper's response. Do not generate text like 'just me' or 'I'll go with X.' Wait for real input."
4. THE Conversation_Protocol SHALL state that Self_Answering is a critical violation regardless of session state, context window position, or hook execution order.
5. IF the agent has asked a Bootcamper_Question and the Question_Pending_File exists, THEN THE Conversation_Protocol SHALL prohibit the agent from generating any response content until the bootcamper provides input and the Question_Pending_File is deleted.

### Requirement 6: Session Resume Re-Asserts All Behavioral Rules

**User Story:** As a bootcamper, I want the agent to behave consistently across sessions, so that conversation quality does not degrade when I start a new session.

#### Acceptance Criteria

1. THE Session_Resume SHALL include a "Behavioral Rules Reload" section that explicitly re-states the five core conversation rules: One_Question_Rule, wait-for-response, no dead-ends, 👉 prefix requirement, and no Self_Answering.
2. THE Session_Resume behavioral rules section SHALL appear before Step 3 (Summarize and Confirm) so that rules are active before the first bootcamper interaction.
3. THE Session_Resume SHALL reference the Conversation_Protocol as the authoritative source for turn-taking rules and instruct the agent to honor it fully.
4. WHEN a new session starts, THE Session_Resume SHALL instruct the agent to write the Question_Pending_File after asking the "Ready to continue?" question, enforcing the same wait mechanism used during active modules.

### Requirement 7: Reinforce Rules in Context-Specific Steering Files

**User Story:** As a power maintainer, I want conversation UX rules reinforced in the steering files where violations have occurred, so that the rules are visible at the point of use and harder to violate.

#### Acceptance Criteria

1. THE Feedback_Workflow SHALL include a "Conversation Rules" preamble section that states: one question per turn, use 👉 prefix, stop after each question, do not combine confirmation and priority questions.
2. THE module-09-phaseA-assessment.md SHALL prefix all bootcamper-directed questions with 👉 (specifically Step 1a and Step 1b question text).
3. WHEN any module steering file contains a question directed at the bootcamper, THE question text SHALL include the 👉 prefix and be followed by a STOP_Marker.
4. THE onboarding-flow.md SHALL include the 👉 prefix on all questions within mandatory gates (⛔) and preference questions (verbosity, comprehension check).
5. THE Agent_Instructions Communication section SHALL cross-reference the Conversation_Protocol with an explicit statement: "These rules apply in ALL contexts — onboarding, feedback workflow, module steps, and session resume."

### Requirement 8: Conversation Protocol Structural Improvements

**User Story:** As a power maintainer, I want the conversation-protocol.md to be structured with clear violation examples and enforcement mechanisms, so that the rules are unambiguous and harder to misinterpret.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL include a "Violation Examples" section with concrete before/after examples for each of the five rule categories.
2. THE Conversation_Protocol SHALL include a "Rule Priority" section stating that conversation UX rules take precedence over content generation — the agent must never sacrifice turn-taking correctness to deliver more information in a single turn.
3. THE Conversation_Protocol SHALL include a "Self-Check" section listing questions the agent must verify before ending a turn: (a) Does this turn contain more than one 👉 question? (b) Does any 👉 question lack the prefix? (c) Is there content after a 👉 question? (d) Am I answering my own question?
4. THE Conversation_Protocol SHALL state that the Question_Pending_File mechanism is mandatory for every 👉 question — not optional, not best-effort.
