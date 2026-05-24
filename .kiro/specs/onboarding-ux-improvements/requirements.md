# Requirements Document

## Introduction

Two UX improvements to the senzing-bootcamp onboarding flow: (1) inform bootcampers about hook files that appear in the editor panel during setup, and (2) offer bootcampers an opportunity to explore Entity Resolution concepts deeper before proceeding past the introductory section.

## Glossary

- **Onboarding_Flow**: The steering file (`onboarding-flow.md`) that orchestrates the bootcamp onboarding sequence from directory creation through track selection.
- **Entity_Resolution_Intro**: The steering file (`entity-resolution-intro.md`) included via `#[[file:]]` reference during Step 4a of the Onboarding_Flow, presenting the "What is Entity Resolution?" content.
- **Hook_Files_Note**: A paragraph in Step 4 of the Onboarding_Flow that explains to the bootcamper that hook files appearing in the editor panel are automated quality checks and do not require review.
- **Mandatory_Gate**: A point in a steering file marked with ⛔ where the agent must stop and wait for explicit bootcamper input before proceeding.
- **Bootcamper**: The user progressing through the senzing-bootcamp onboarding flow.
- **Overview_Bullets**: The list of informational bullet points presented to the bootcamper in Step 4 of the Onboarding_Flow, between the welcome banner and section 4a.

## Requirements

### Requirement 1: Hook Files Note in Onboarding Overview

**User Story:** As a bootcamper, I want to understand why hook files appeared in my editor panel during setup, so that I am not confused by unexpected files and know they can be safely closed.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL include a Hook_Files_Note paragraph as the last item in the Overview_Bullets of Step 4, positioned after the "unfamiliar terms" bullet and before section 4a.
2. THE Hook_Files_Note SHALL inform the bootcamper that hook files appearing in the editor panel are automated quality checks that do not require review.
3. THE Hook_Files_Note SHALL instruct the bootcamper that hook files can be safely closed but must not be deleted.
4. WHEN the bootcamper reads the Hook_Files_Note, THE Onboarding_Flow SHALL continue to section 4a without requiring any user interaction for this note.

### Requirement 2: Entity Resolution Exploration Gate

**User Story:** As a bootcamper, I want an opportunity to ask follow-up questions about entity resolution after reading the introduction, so that I can deepen my understanding before moving on to the rest of the bootcamp.

#### Acceptance Criteria

1. THE Entity_Resolution_Intro SHALL include a Mandatory_Gate (⛔) at the end of the file, after all existing Entity Resolution content and before the Sources section comment.
2. THE Mandatory_Gate SHALL present example questions the bootcamper can ask to explore entity resolution further, including questions such as "How does Senzing match records without rules?", "What's the difference between matching and relating?", and "What kinds of data does entity resolution work with?".
3. THE Mandatory_Gate SHALL instruct the agent to stop and wait for the bootcamper to either ask follow-up questions about entity resolution or explicitly signal readiness to move on.
4. WHEN the bootcamper asks a follow-up question at the Mandatory_Gate, THE Entity_Resolution_Intro SHALL direct the agent to answer the question using MCP tools and then re-present the gate for additional questions.
5. WHEN the bootcamper signals readiness to proceed, THE Entity_Resolution_Intro SHALL allow the agent to continue to the next section of the Onboarding_Flow.
6. IF the bootcamper provides an ambiguous response at the Mandatory_Gate, THEN THE Entity_Resolution_Intro SHALL treat the response as a follow-up question and attempt to answer it before re-presenting the gate.
