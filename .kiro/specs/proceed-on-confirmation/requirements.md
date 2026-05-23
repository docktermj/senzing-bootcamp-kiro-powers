# Requirements Document

## Introduction

This feature strengthens the module transition protocol to ensure the agent immediately proceeds with the next module when a bootcamper confirms a transition. It addresses a reported issue where the agent outputs minimal content (e.g., just ".") after receiving an affirmative response to a "Ready for Module X?" question, leaving the bootcamper waiting with no progress. The solution combines strengthened steering language in existing files with a new detect-and-retry hook that catches minimal-output violations and forces the agent to retry with proper module start content.

## Glossary

- **Agent**: The AI assistant executing the Senzing Bootcamp power, governed by steering files and hooks
- **Bootcamper**: The developer user participating in the bootcamp session
- **Module_Transition**: The point where the bootcamper confirms readiness to move from one module to the next
- **Transition_Confirmation**: An affirmative response from the bootcamper (e.g., "yes", "sure", "ready", "let's go", "let's do it") to a module transition question
- **Minimal_Output**: Agent output consisting of only a period ("."), empty string, single word acknowledgment, or fewer than 50 characters that does not constitute meaningful module start content
- **Module_Banner**: The formatted module start display including the module number header, journey map table, and before/after framing
- **Detect_And_Retry_Hook**: An agentStop hook that inspects agent output after a transition confirmation and forces a retry when minimal output is detected
- **Conversation_Protocol**: The steering file governing turn-taking, question handling, and module transition rules
- **Agent_Instructions**: The core steering file containing agent behavioral rules
- **Module_Transitions_Steering**: The steering file governing module start banners, journey maps, and transition integrity

## Requirements

### Requirement 1: Immediate Module Start on Transition Confirmation

**User Story:** As a bootcamper, I want the agent to immediately start the next module when I confirm readiness, so that I do not experience dead-end responses or need to prompt the agent again.

#### Acceptance Criteria

1. WHEN the Bootcamper provides a Transition_Confirmation to a module transition question, THE Agent SHALL display the Module_Banner, journey map, before/after framing, and begin Step 1 of the next module within the same response turn.
2. WHEN the Bootcamper provides a Transition_Confirmation, THE Agent SHALL produce a response containing at minimum the module start banner, journey map table, and the first step's introductory content.
3. IF the Agent produces Minimal_Output after receiving a Transition_Confirmation, THEN THE Detect_And_Retry_Hook SHALL detect the violation and instruct the Agent to retry with full module start content.

### Requirement 2: Prohibition of Minimal Output After Transition Confirmation

**User Story:** As a bootcamper, I want the agent to never output just "." or a bare acknowledgment after I confirm a module transition, so that I always see meaningful progress.

#### Acceptance Criteria

1. WHILE a Transition_Confirmation has been received and the Agent is generating a response, THE Agent SHALL produce output exceeding 50 characters that includes substantive module start content.
2. THE Conversation_Protocol SHALL define that outputting only ".", empty content, or single-word acknowledgments after a Transition_Confirmation is a protocol violation.
3. THE Agent_Instructions SHALL include a Module Transition Execution rule stating that the only valid response to a Transition_Confirmation is to start the confirmed module.

### Requirement 3: Strengthened Module Transition Protocol in Steering

**User Story:** As a power maintainer, I want the module transition rules to be explicit and unambiguous across all relevant steering files, so that the agent has clear instructions that prevent minimal-output failures.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL contain a rule stating that after a Transition_Confirmation, the Agent response must include the Module_Banner, journey map, and Step 1 content.
2. THE Module_Transitions_Steering SHALL contain a Confirmation Response Requirements section specifying minimum content expectations for post-confirmation output.
3. THE Agent_Instructions SHALL contain a Module Transition Execution rule that reinforces the prohibition against minimal output and mandates immediate module start.
4. WHEN the Conversation_Protocol Module Transition Protocol section is updated, THE Conversation_Protocol SHALL retain all existing prohibition rules (no session save, no pause, commitment rule, context-limit guidance) while adding the new minimum-content requirement.

### Requirement 4: Detect-and-Retry Hook for Transition Confirmation Enforcement

**User Story:** As a power maintainer, I want a hook-based enforcement mechanism that catches minimal-output violations after module transitions, so that even if the agent's initial response is inadequate, it is automatically corrected.

#### Acceptance Criteria

1. THE Detect_And_Retry_Hook SHALL be an agentStop hook that fires after every agent response.
2. WHEN the Detect_And_Retry_Hook fires, THE Detect_And_Retry_Hook SHALL check whether the most recent bootcamper message was a Transition_Confirmation to a module transition question.
3. IF the most recent bootcamper message was a Transition_Confirmation AND the agent output is Minimal_Output, THEN THE Detect_And_Retry_Hook SHALL instruct the Agent to retry by starting the confirmed module with full Module_Banner, journey map, and Step 1 content.
4. IF the most recent bootcamper message was NOT a Transition_Confirmation, THEN THE Detect_And_Retry_Hook SHALL output only a single period character (".") to indicate no action needed.
5. IF the agent output after a Transition_Confirmation exceeds 50 characters and contains substantive content, THEN THE Detect_And_Retry_Hook SHALL output only a single period character (".") to indicate the response is acceptable.
6. THE Detect_And_Retry_Hook SHALL recognize Transition_Confirmation patterns including: "yes", "sure", "ready", "let's go", "let's do it", "yep", "yeah", "absolutely", "go ahead", "proceed", and similar affirmative phrases appearing in response to a question containing "Ready for Module" or "move on to Module" or "proceed to Module".

### Requirement 5: Hook File Compliance

**User Story:** As a power maintainer, I want the new hook to follow existing hook conventions, so that it integrates cleanly with the power's hook infrastructure.

#### Acceptance Criteria

1. THE Detect_And_Retry_Hook file SHALL be named following the pattern `{hook-id}.kiro.hook` and placed in `senzing-bootcamp/hooks/`.
2. THE Detect_And_Retry_Hook file SHALL contain valid JSON with `name`, `version`, `description`, `when`, and `then` fields.
3. THE Detect_And_Retry_Hook `name` field SHALL follow the "to {verb phrase}" naming pattern consistent with existing hooks.
4. THE Detect_And_Retry_Hook `when.type` field SHALL be set to "agentStop".
5. THE Detect_And_Retry_Hook `then.type` field SHALL be set to "askAgent".
6. THE Detect_And_Retry_Hook SHALL be registered in `senzing-bootcamp/hooks/hook-categories.yaml` under the appropriate category.
