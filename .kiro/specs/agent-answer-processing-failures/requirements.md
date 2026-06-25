# Requirements Document

## Introduction

The agent fails to process bootcamper answers to 👉 questions, creating dead-end conversations. Three manifestations have been observed: (1) track selection answers are lost during onboarding, (2) module transition confirmations are lost between modules, and (3) the agent does not wait for the bootcamper's answer before proceeding. This spec addresses all three manifestations by broadening the existing `enforce-step-and-transition` hook's Phase 2 to detect ALL pending question answer failures, adding an "answer-processing is highest priority" directive to steering files, and providing type-specific retry instructions based on the question type recorded in `config/.question_pending`.

## Glossary

- **Hook**: A JSON file (`.kiro.hook`) that defines an automated agent action triggered by an IDE event (e.g., `agentStop`).
- **Enforce_Step_And_Transition_Hook**: The existing `enforce-step-and-transition.kiro.hook` agentStop hook that validates sequential step execution and detects module transition failures.
- **Question_Pending_File**: The file `config/.question_pending` written by the agent after asking a 👉 question, containing the question text and type metadata.
- **Minimal_Output**: Agent output that is exactly ".", empty, whitespace-only, fewer than 50 characters, or a single-word acknowledgment.
- **Answer_Processing**: The act of the agent reading, interpreting, and acting upon the bootcamper's response to a previously asked 👉 question.
- **Question_Type**: A classification of the pending question (e.g., `track_selection`, `module_transition`, `step_question`, `confirmation`, `choice`) stored in the Question_Pending_File.
- **Agent_Instructions**: The steering file `senzing-bootcamp/steering/agent-instructions.md` containing core agent behavioral rules.
- **Conversation_Protocol**: The steering file `senzing-bootcamp/steering/conversation-protocol.md` containing turn-taking and question handling rules.
- **Retry_Instructions**: Type-specific corrective instructions issued by the Enforce_Step_And_Transition_Hook when it detects that an answer was not processed.

## Requirements

### Requirement 1: Answer-Processing Priority Directive in Agent Instructions

**User Story:** As a bootcamper, I want the agent to always prioritize processing my answer to a 👉 question above all other actions, so that my responses are never lost or ignored.

#### Acceptance Criteria

1. THE Agent_Instructions SHALL contain a directive stating that processing a bootcamper's answer to a pending 👉 question takes absolute precedence over all other agent actions including hook evaluation, context management, and content generation.
2. THE Agent_Instructions SHALL state that WHEN `config/.question_pending` exists and the bootcamper has provided a response, THE agent SHALL delete the Question_Pending_File and process the answer as the first action of the turn before any other work.
3. THE Agent_Instructions SHALL state that IF the agent produces Minimal_Output after a bootcamper responds to a pending 👉 question, THEN the agent has committed a critical protocol violation equivalent to a ⛔ mandatory gate violation.

### Requirement 2: Answer-Processing Priority Directive in Conversation Protocol

**User Story:** As a bootcamper, I want the conversation protocol to enforce that my answers are always processed immediately, so that I never encounter dead-end responses.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL contain an "Answer Processing Priority" section stating that processing a bootcamper's answer to a 👉 question is the highest-priority action in any turn.
2. THE Conversation_Protocol SHALL state that WHEN the bootcamper's message is a response to a pending 👉 question, THE agent SHALL produce substantive output that acknowledges and acts upon the answer before the turn ends.
3. THE Conversation_Protocol SHALL state that IF `config/.question_pending` exists at the start of a turn, THEN the agent SHALL treat the bootcamper's message as an answer to that pending question regardless of message content.

### Requirement 3: Broadened Answer-Failure Detection in Hook Phase 2

**User Story:** As a bootcamper, I want the enforce-step-and-transition hook to detect when ANY of my answers to 👉 questions are lost (not just module transitions), so that the system can automatically recover from all answer-processing failures.

#### Acceptance Criteria

1. WHEN `config/.question_pending` exists AND the agent produces Minimal_Output, THE Enforce_Step_And_Transition_Hook SHALL detect this as an answer-processing failure regardless of the question type.
2. THE Enforce_Step_And_Transition_Hook SHALL read the content of `config/.question_pending` to determine the Question_Type of the pending question.
3. THE Enforce_Step_And_Transition_Hook SHALL rename the existing Phase 2 from "MODULE TRANSITION RETRY" to "ANSWER PROCESSING RETRY" to reflect the broadened scope.
4. THE Enforce_Step_And_Transition_Hook SHALL remove the Transition_Confirmation detection logic as a prerequisite for Phase 2 activation, replacing it with the Question_Pending_File existence check combined with Minimal_Output detection.

### Requirement 4: Type-Specific Retry Instructions

**User Story:** As a bootcamper, I want the hook to provide recovery instructions tailored to the type of question I answered, so that the agent can correctly resume processing my specific answer.

#### Acceptance Criteria

1. WHEN the Enforce_Step_And_Transition_Hook detects an answer-processing failure for a question of type `track_selection`, THE Enforce_Step_And_Transition_Hook SHALL issue Retry_Instructions directing the agent to read the bootcamper's track choice, update `config/bootcamp_progress.json` with the selected track, save preferences to `config/bootcamp_preferences.yaml`, and begin Module 1.
2. WHEN the Enforce_Step_And_Transition_Hook detects an answer-processing failure for a question of type `module_transition`, THE Enforce_Step_And_Transition_Hook SHALL issue Retry_Instructions directing the agent to display the module start banner, journey map, before/after framing, and begin Step 1 of the confirmed module.
3. WHEN the Enforce_Step_And_Transition_Hook detects an answer-processing failure for a question of type `step_question`, THE Enforce_Step_And_Transition_Hook SHALL issue Retry_Instructions directing the agent to read the bootcamper's answer, incorporate it into the current step's workflow, update progress, and present the next action or question.
4. WHEN the Enforce_Step_And_Transition_Hook detects an answer-processing failure for a question of type `confirmation`, THE Enforce_Step_And_Transition_Hook SHALL issue Retry_Instructions directing the agent to treat the bootcamper's response as a confirmation and proceed with the confirmed action.
5. WHEN the Enforce_Step_And_Transition_Hook detects an answer-processing failure for a question of type `choice`, THE Enforce_Step_And_Transition_Hook SHALL issue Retry_Instructions directing the agent to read the bootcamper's selection from the numbered choice list, acknowledge the choice, and proceed with the selected option.
6. IF the Question_Type cannot be determined from the Question_Pending_File content, THEN THE Enforce_Step_And_Transition_Hook SHALL issue generic Retry_Instructions directing the agent to re-read the bootcamper's most recent message, treat it as an answer to the pending question, and produce a substantive response.

### Requirement 5: Question_Pending_File Content Schema

**User Story:** As a developer, I want the `.question_pending` file to contain structured content including the question type, so that the hook can provide type-specific recovery.

#### Acceptance Criteria

1. WHEN the agent writes `config/.question_pending`, THE agent SHALL include a `type` field on the first line indicating the Question_Type (one of: `track_selection`, `module_transition`, `step_question`, `confirmation`, `choice`).
2. WHEN the agent writes `config/.question_pending`, THE agent SHALL include the full question text on subsequent lines after the type field.
3. IF the agent cannot determine the appropriate Question_Type, THEN THE agent SHALL use `step_question` as the default type.

### Requirement 6: Agent Not-Waiting Prevention

**User Story:** As a bootcamper, I want the agent to never proceed past a 👉 question without my input, so that my participation is always required at decision points.

#### Acceptance Criteria

1. WHEN `config/.question_pending` exists, THE Enforce_Step_And_Transition_Hook SHALL detect if the agent produced output that advances the workflow (contains step content, module content, or new questions) without first deleting the Question_Pending_File, and flag this as a "not-waiting" violation.
2. IF a not-waiting violation is detected, THEN THE Enforce_Step_And_Transition_Hook SHALL issue instructions directing the agent to discard the premature output, acknowledge that a question is still pending, and wait for the bootcamper's response.
3. THE Conversation_Protocol SHALL state that WHILE `config/.question_pending` exists, THE agent SHALL produce no substantive output other than processing the bootcamper's answer to the pending question.
