# Requirements Document

## Introduction

The Senzing Bootcamp onboarding flow currently moves from the introduction and overview (Step 4, including the verbosity preference in Step 4b) directly into track selection (Step 5). The bootcamper has just seen the welcome banner, the 11-module overview table, mock data availability, licensing details, and the verbosity preference question — a significant amount of new information. There is no pause point for the bootcamper to confirm they understand the overview or to ask clarifying questions before committing to a track.

This feature adds a comprehension check sub-step (Step 4c) between the verbosity preference (Step 4b) and track selection (Step 5). The check is a warm, inviting prompt — not a quiz — that gives the bootcamper a natural moment to absorb the overview, ask questions, or signal readiness to proceed. If the bootcamper has questions, the agent answers them before moving on. If the bootcamper signals readiness, the agent proceeds to track selection without further delay.

This step is NOT a mandatory gate (⛔). The `ask-bootcamper` hook handles the closing question on `agentStop`, so Step 4c follows the standard rule: present the comprehension check prompt and stop. The hook will fire and generate the contextual closing question. If the bootcamper responds with acknowledgment or "no questions," the agent proceeds to Step 5.

## Glossary

- **Onboarding_Flow**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines the sequential steps for setting up and introducing a new bootcamper to the Senzing Bootcamp.
- **Comprehension_Check**: A non-blocking prompt presented to the bootcamper after the introduction and overview (Step 4) that invites the bootcamper to confirm understanding or ask questions before proceeding to track selection.
- **Agent**: The Kiro-powered assistant that delivers the bootcamp content, reads steering files, and generates output for the Bootcamper.
- **Bootcamper**: The user participating in the Senzing Bootcamp learning exercise.
- **Ask_Bootcamper_Hook**: The hook defined in `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` that fires on every `agentStop` event and generates a contextual 👉 closing question.
- **Mandatory_Gate**: A step marked with ⛔ where the agent MUST stop and MUST NOT proceed without real user input. The Comprehension_Check is explicitly NOT a Mandatory_Gate.
- **Acknowledgment_Response**: A bootcamper response that signals readiness to proceed, such as "looks good," "makes sense," "no questions," "let's go," "ready," or similar affirmative phrases.
- **Clarification_Response**: A bootcamper response that contains a question or request for more information about the bootcamp overview, modules, data, licensing, or any other topic covered in Step 4.

## Requirements

### Requirement 1: Comprehension Check Sub-Step Placement

**User Story:** As a bootcamper, I want a moment to absorb the bootcamp overview before choosing a track, so that I can ask questions or confirm my understanding while the information is fresh.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL define a sub-step numbered 4c titled "Comprehension Check" that appears after sub-step 4b (Verbosity Preference) and before Step 5 (Track Selection).
2. WHEN the Agent completes Step 4b, THE Agent SHALL proceed to Step 4c before proceeding to Step 5.
3. THE Onboarding_Flow SHALL NOT mark Step 4c as a Mandatory_Gate (⛔).

### Requirement 2: Comprehension Check Prompt Content

**User Story:** As a bootcamper, I want the comprehension check to feel warm and inviting rather than like a test, so that I feel comfortable asking questions or saying I need more explanation.

#### Acceptance Criteria

1. WHEN the Agent reaches Step 4c, THE Agent SHALL present a prompt that asks the bootcamper whether the introduction makes sense and whether the bootcamper has any questions before proceeding.
2. THE Comprehension_Check prompt SHALL use a warm, conversational tone that invites questions without implying the bootcamper is being tested.
3. THE Comprehension_Check prompt SHALL reference that the bootcamper is about to choose a track, providing context for why this is a good moment to pause.
4. THE Comprehension_Check prompt SHALL NOT include inline closing questions or WAIT instructions, consistent with the Onboarding_Flow note that the Ask_Bootcamper_Hook handles closing questions.

### Requirement 3: Acknowledgment Handling

**User Story:** As a bootcamper who understands the overview, I want to quickly signal that I'm ready so the agent moves on to track selection without unnecessary delay.

#### Acceptance Criteria

1. WHEN the Bootcamper provides an Acknowledgment_Response to the Comprehension_Check, THE Agent SHALL proceed to Step 5 (Track Selection).
2. THE Agent SHALL treat responses such as "looks good," "makes sense," "no questions," "let's go," "ready," "all clear," "got it," and similar affirmative phrases as Acknowledgment_Responses.
3. WHEN the Bootcamper provides an Acknowledgment_Response, THE Agent SHALL NOT ask follow-up questions about the overview before proceeding to Step 5.

### Requirement 4: Clarification Handling

**User Story:** As a bootcamper with questions about the overview, I want the agent to answer my questions thoroughly before moving on, so that I start the bootcamp with a solid understanding.

#### Acceptance Criteria

1. WHEN the Bootcamper provides a Clarification_Response to the Comprehension_Check, THE Agent SHALL answer the question before proceeding to Step 5.
2. WHEN the Agent finishes answering a Clarification_Response, THE Agent SHALL check whether the Bootcamper has additional questions before proceeding to Step 5.
3. THE Agent SHALL NOT proceed to Step 5 until the Bootcamper provides an Acknowledgment_Response or the Bootcamper's questions have been answered and no further questions remain.
4. WHEN answering a Clarification_Response, THE Agent SHALL apply the Bootcamper's current verbosity settings from the preferences file.

### Requirement 5: Steering File Update

**User Story:** As the bootcamp power author, I want the comprehension check defined in the onboarding flow steering file, so that the agent follows the updated sequence consistently.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL contain a section for Step 4c positioned between the Step 4b section and the Step 5 section.
2. THE Step 4c section SHALL include the comprehension check prompt text, instructions for handling Acknowledgment_Responses, and instructions for handling Clarification_Responses.
3. THE Step 4c section SHALL include a note reminding the agent that Step 4c is not a Mandatory_Gate and that the Ask_Bootcamper_Hook handles the closing question.
4. THE Onboarding_Flow token count in `senzing-bootcamp/steering/steering-index.yaml` SHALL be updated to reflect the added content.
