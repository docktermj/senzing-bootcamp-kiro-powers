# Requirements Document

## Introduction

The session-resume flow in the senzing-bootcamp power restores progress state (module, step, data sources) but fails to reinitialize behavioral guardrails and conversation style. This causes three observable failures after session resume: (1) the agent stops following core rules like one-question-per-turn and the 👉 prefix convention, (2) the agent answers its own questions instead of waiting for bootcamper input, and (3) the conversation tone and question-asking style degrades noticeably. This feature ensures that `session-resume.md` re-asserts all behavioral rules, restores conversation style parameters, and explicitly prohibits self-answering before the first bootcamper interaction in a resumed session.

## Glossary

- **Session_Resume**: The steering file `session-resume.md` with `inclusion: manual`, loaded when `config/bootcamp_progress.json` exists at session start.
- **Conversation_Protocol**: The steering file `conversation-protocol.md` with `inclusion: auto` that defines turn-taking, question handling, and module transition protocols.
- **Behavioral_Guardrails**: The set of core rules governing agent behavior: one-question-per-turn, 👉 prefix on all bootcamper-directed questions, STOP markers as end-of-turn boundaries, no self-answering, and no dead-end responses.
- **Conversation_Style_Profile**: A persisted record of conversation style parameters (question formatting, tone, pacing, explanation depth) stored in `config/bootcamp_preferences.yaml` under the `conversation_style` key.
- **Self_Answering**: The agent generating text that answers its own 👉 question instead of waiting for the bootcamper's real input.
- **STOP_Marker**: The `🛑 STOP` directive in steering files that marks an absolute end-of-turn boundary where the agent must cease output.
- **Question_Pending_File**: The file `config/.question_pending` that signals a 👉 question is awaiting a bootcamper response.
- **Bootcamper_Question**: Any question directed at the bootcamper that expects a response, identified by the 👉 prefix.
- **Agent_Instructions**: The steering file `agent-instructions.md` with `inclusion: always` that defines top-level agent behavior.
- **Verbosity_Control**: The steering file `verbosity-control.md` with `inclusion: auto` that manages output detail levels across five categories.
- **Preferences_File**: The YAML file `config/bootcamp_preferences.yaml` that persists bootcamper choices across sessions.

## Requirements

### Requirement 1: Re-Assert Behavioral Guardrails Before First Interaction

**User Story:** As a bootcamper, I want the agent to follow all behavioral rules from the very first message in a resumed session, so that conversation quality is identical to the original session.

#### Acceptance Criteria

1. THE Session_Resume SHALL include a "Behavioral Rules Reload" section that explicitly re-states all Behavioral_Guardrails before any bootcamper-facing output is generated.
2. WHEN a new session begins and Session_Resume is loaded, THE Session_Resume SHALL instruct the agent to re-read Conversation_Protocol and confirm awareness of its rules before proceeding to Step 3 (Summarize and Confirm).
3. THE Session_Resume Behavioral Rules Reload section SHALL enumerate each rule with its enforcement mechanism: (a) one question per turn with STOP after each, (b) 👉 prefix on every Bootcamper_Question, (c) STOP_Markers as absolute end-of-turn boundaries, (d) no Self_Answering under any circumstance, (e) no dead-end responses after bootcamper input.
4. THE Session_Resume SHALL place the Behavioral Rules Reload section between Step 1 (Read All State Files) and Step 3 (Summarize and Confirm) so that rules are internalized before the first bootcamper-facing message.

### Requirement 2: Explicit Self-Answering Prohibition on Resume

**User Story:** As a bootcamper, I want the agent to never answer questions on my behalf after a session resume, so that I retain full control over my choices regardless of session boundaries.

#### Acceptance Criteria

1. THE Session_Resume SHALL include a dedicated "Self-Answering Prohibition" subsection within the Behavioral Rules Reload that states: "After asking any 👉 question, produce zero additional tokens. Do not answer the question. Do not assume the bootcamper's response. Do not generate placeholder answers like 'just me' or 'I will go with X.'"
2. THE Session_Resume Self-Answering Prohibition SHALL include concrete violation examples showing what the agent must not do after resume, paired with correct behavior examples.
3. WHEN the Session_Resume presents the "Ready to continue?" question, THE Session_Resume SHALL write the Question_Pending_File and end the turn immediately, enforcing the same wait mechanism used during active modules.
4. IF the agent has asked a Bootcamper_Question after session resume and the Question_Pending_File exists, THEN THE Session_Resume SHALL prohibit the agent from generating any response content until the bootcamper provides input.

### Requirement 3: Restore Conversation Style on Resume

**User Story:** As a bootcamper, I want the agent's conversation style to remain consistent across sessions, so that the experience does not feel like working with a different agent after a session boundary.

#### Acceptance Criteria

1. THE Session_Resume SHALL read the Conversation_Style_Profile from the Preferences_File during Step 1 (Read All State Files) and apply it before generating any output.
2. WHEN the Conversation_Style_Profile exists in the Preferences_File, THE Session_Resume SHALL instruct the agent to match the recorded question-asking style, tone, and pacing parameters.
3. IF the Conversation_Style_Profile does not exist in the Preferences_File, THEN THE Session_Resume SHALL apply default style parameters derived from Conversation_Protocol and Verbosity_Control settings.
4. THE Session_Resume SHALL instruct the agent to maintain the same question formatting pattern used in the original session: single 👉 question, contextual framing before the question, and consistent explanation depth.

### Requirement 4: Persist Conversation Style Profile

**User Story:** As a bootcamper, I want my conversation style preferences to be saved automatically, so that they survive session boundaries without manual reconfiguration.

#### Acceptance Criteria

1. THE Agent_Instructions SHALL instruct the agent to write a Conversation_Style_Profile to the Preferences_File after the onboarding flow completes and the first module interaction establishes a baseline style.
2. THE Conversation_Style_Profile SHALL record: (a) the active verbosity preset or custom category levels, (b) the question framing pattern (contextual lead-in length), (c) the tone descriptor (concise, conversational, or detailed), and (d) the pacing preference (one concept per turn or grouped concepts).
3. WHEN the bootcamper requests a style change (via verbosity adjustment or explicit feedback), THE Verbosity_Control SHALL update the Conversation_Style_Profile in the Preferences_File to reflect the new parameters.
4. THE Conversation_Style_Profile SHALL be stored as a YAML block under the `conversation_style` key in the Preferences_File, adjacent to existing keys like `verbosity` and `detail_level`.

### Requirement 5: Reference Conversation Protocol as Authoritative

**User Story:** As a power maintainer, I want session-resume.md to explicitly reference conversation-protocol.md as the authoritative source for behavioral rules, so that there is a single source of truth and no ambiguity about which rules apply.

#### Acceptance Criteria

1. THE Session_Resume Behavioral Rules Reload section SHALL include an explicit statement: "conversation-protocol.md is the authoritative source for all turn-taking and question-handling rules. These rules apply without exception after session resume."
2. THE Session_Resume SHALL instruct the agent to treat Conversation_Protocol rules as having equal priority to Agent_Instructions rules — session resume does not reduce the authority of any behavioral rule.
3. WHEN the Session_Resume loads module steering for the resumed module, THE Session_Resume SHALL confirm that Conversation_Protocol is already loaded (via its `inclusion: auto` setting) and that its rules are active.
4. THE Session_Resume SHALL not duplicate the full text of Conversation_Protocol but SHALL summarize the five core rules and reference the file for complete definitions.

### Requirement 6: Validate Rule Compliance Before Welcome-Back Message

**User Story:** As a bootcamper, I want the agent to have fully internalized all behavioral rules before it speaks to me, so that the very first message in a resumed session is already rule-compliant.

#### Acceptance Criteria

1. THE Session_Resume SHALL structure its steps so that behavioral rule loading (Step 2) completes before the welcome-back banner and summary (Step 3) are generated.
2. WHEN the Session_Resume generates the welcome-back summary, THE summary SHALL end with exactly one 👉 question ("Ready to continue?") followed by no additional content.
3. THE Session_Resume SHALL write the Question_Pending_File after the welcome-back 👉 question, enforcing the turn boundary before the bootcamper responds.
4. IF the welcome-back summary would require asking multiple questions (such as "Ready to continue?" and "Or would you like to switch modules?"), THEN THE Session_Resume SHALL combine these into a single 👉 question with options rather than asking multiple questions.

### Requirement 7: Conversation Style Continuity Verification

**User Story:** As a power maintainer, I want a mechanism to verify that conversation style is maintained after resume, so that style drift can be detected and corrected.

#### Acceptance Criteria

1. THE Session_Resume SHALL instruct the agent to compare its first post-resume response style against the Conversation_Style_Profile and self-correct if the style diverges.
2. WHEN the Conversation_Style_Profile specifies a tone descriptor, THE Session_Resume SHALL include a brief instruction mapping each tone descriptor to observable output characteristics (e.g., "concise" means short contextual lead-ins and minimal preamble before questions).
3. THE Session_Resume SHALL instruct the agent that if no Conversation_Style_Profile exists, the agent must default to the "standard" verbosity preset behavior and the question formatting patterns defined in Conversation_Protocol.
4. WHEN the agent detects that its output style has drifted from the Conversation_Style_Profile (such as after loading a new module steering file), THE agent SHALL re-read the profile and adjust subsequent output to match.
