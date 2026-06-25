# Requirements Document

## Introduction

This feature restructures the onboarding flow of the Senzing Bootcamp Kiro Power to improve the learning sequence and accessibility. The changes reorder steps so bootcampers understand entity resolution before choosing a programming language, add a comprehension gate between the ER introduction and language selection, provide guidance on language choice for production reuse, and make the git initialization prompt more welcoming to non-developers.

## Glossary

- **Onboarding_Flow**: The steering file (`onboarding-flow.md`) that defines the sequential steps a bootcamper follows when starting a fresh bootcamp session.
- **Bootcamper**: A user progressing through the Senzing Bootcamp modules.
- **Entity_Resolution_Introduction**: The section (currently Step 4a) that explains what entity resolution is, how it works, and how Senzing handles it, loaded from `entity-resolution-intro.md`.
- **Programming_Language_Selection**: The step (currently Step 2) where the bootcamper chooses their preferred programming language for code generation throughout the bootcamp.
- **Comprehension_Gate**: A mandatory stopping point where the agent waits for the bootcamper to confirm understanding or ask follow-up questions before proceeding.
- **Git_Initialization_Prompt**: The optional step in Module 1 where the agent offers to initialize a git repository for version control.
- **Production_Reuse_Hint**: A tip presented during programming language selection informing bootcampers that bootcamp code artifacts are designed for real-world use.

## Requirements

### Requirement 1: Move Entity Resolution Introduction Before Programming Language Selection

**User Story:** As a bootcamper, I want to learn what entity resolution is before choosing a programming language, so that I understand the domain before making a tooling decision.

#### Acceptance Criteria

1. WHEN the Onboarding_Flow reaches the step immediately after the Prerequisite Check (Step 3), THE Onboarding_Flow SHALL present the Entity_Resolution_Introduction by loading the content from `entity-resolution-intro.md` via the existing `#[[file:]]` inclusion directive, before presenting the Programming_Language_Selection.
2. THE Onboarding_Flow SHALL preserve the existing content of `entity-resolution-intro.md` and its `#[[file:]]` inclusion directive without modification to the educational material or its internal structure.
3. THE Onboarding_Flow SHALL include a mandatory gate at the end of the Entity_Resolution_Introduction section that stops and waits for bootcamper input before proceeding, using the same stop-and-wait pattern as other mandatory gates in the onboarding sequence.
4. WHEN the Entity_Resolution_Introduction is relocated, THE Onboarding_Flow SHALL update all step numbers and sub-step labels within `onboarding-flow.md` to reflect the new sequential order, ensuring no duplicate or skipped step numbers exist.
5. WHEN the Entity_Resolution_Introduction is relocated before Programming_Language_Selection, THE Onboarding_Flow SHALL keep the Verbosity Preference and Comprehension Check sub-steps grouped with the Bootcamp Introduction section, not with the Entity_Resolution_Introduction.

### Requirement 2: Add Comprehension Check After Entity Resolution Introduction

**User Story:** As a bootcamper new to entity resolution, I want the opportunity to discuss ER concepts further before moving on, so that I can build a solid understanding before making technical choices.

#### Acceptance Criteria

1. WHEN the bootcamper completes the Entity_Resolution_Introduction section, THE Onboarding_Flow SHALL present a discussion offer that includes at least two example questions about entity resolution and an explicit invitation to ask any question or signal readiness to proceed.
2. WHEN the bootcamper asks a follow-up question about entity resolution, THE Onboarding_Flow SHALL answer the question using the Senzing MCP server search_docs tool and then re-present the discussion offer.
3. WHEN the bootcamper signals readiness to proceed, THE Onboarding_Flow SHALL advance to the Programming_Language_Selection step.
4. THE Comprehension_Gate SHALL treat acknowledgment phrases including at minimum "ready", "let's go", "continue", "next", "no questions", and "makes sense", as well as semantically equivalent phrases, as signals to proceed.
5. THE Comprehension_Gate SHALL treat any response that does not match an acknowledgment phrase as a follow-up question, answer it using the Senzing MCP server search_docs tool, and then re-present the discussion offer.
6. IF the Senzing MCP server search_docs tool returns no relevant results or fails when answering a follow-up question, THEN THE Onboarding_Flow SHALL inform the bootcamper that no documentation was found for their question, suggest rephrasing or asking a different question, and re-present the discussion offer.

### Requirement 3: Add Production Reuse Hint to Programming Language Selection

**User Story:** As a bootcamper, I want to know that bootcamp code artifacts are reusable in production, so that I can choose the programming language my team already uses and maximize the long-term value of my bootcamp output.

#### Acceptance Criteria

1. WHEN the Onboarding_Flow presents the Programming_Language_Selection, THE Onboarding_Flow SHALL display a Production_Reuse_Hint containing the verbatim text: "Tip: If you plan to use these bootcamp artifacts in production, consider choosing the language your team already uses — the code we generate here is designed to be your starting point for real-world use."
2. THE Production_Reuse_Hint SHALL appear after the list of available programming languages and before the mandatory gate that waits for the bootcamper's choice.
3. THE Production_Reuse_Hint SHALL be presented as a non-blocking informational element that does not require bootcamper acknowledgment or interaction before proceeding to the mandatory gate.
4. WHEN the Programming_Language_Selection is re-presented to the bootcamper (for example, after a platform warning or a request to change selection), THE Onboarding_Flow SHALL include the Production_Reuse_Hint in the same position relative to the language list and mandatory gate.

### Requirement 4: Add Accessibility Guidance to Git Initialization Prompt

**User Story:** As a non-developer bootcamper, I want clear guidance that I can skip the git initialization step without concern, so that I do not feel intimidated by unfamiliar developer terminology.

#### Acceptance Criteria

1. WHEN the Onboarding_Flow presents the git initialization option to a bootcamper whose workspace is not already a git repository, THE Onboarding_Flow SHALL include the phrase "If you don't know what 'git' is, just skip this." in the prompt text, positioned immediately before the existing optional-explanation sentence.
2. THE Onboarding_Flow SHALL retain the existing explanation sentence ("This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp.") unchanged in the prompt text.
3. THE Onboarding_Flow SHALL present the git skip guidance phrase and the existing explanation sentence as part of the same prompt message, not as a separate follow-up message.
4. WHEN the accessibility guidance phrase is added, THE Onboarding_Flow SHALL preserve the existing STOP instruction and response-handling behavior so that the agent still waits for the bootcamper's input before proceeding.
