# Requirements Document

## Introduction

This spec retroactively documents the feedback collection workflow — the guided sequence that lets Bootcampers submit structured feedback about the Senzing Bootcamp experience. The workflow lives in `senzing-bootcamp/steering/feedback-workflow.md` and stores feedback locally in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`.

## Glossary

- **Feedback_Workflow**: The agent-driven sequence (trigger → file check → gather answers → format → append → confirm) loaded when a Bootcamper requests to submit feedback.
- **Feedback_File**: The file `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` that accumulates structured feedback entries.
- **Feedback_Template**: The source template at `senzing-bootcamp/docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md` copied to create the Feedback_File on first use.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Feedback_Category**: One of seven categories: Documentation, Workflow, Tools, UX, Bug, Performance, Security.

## Requirements

### Requirement 1: Feedback Trigger and File Initialization

**User Story:** As a Bootcamper, I want to start the feedback workflow with a simple phrase and have the feedback file created automatically, so that I can submit feedback without manual setup.

#### Acceptance Criteria

1. WHEN the Bootcamper says "power feedback", "bootcamp feedback", "submit feedback", "provide feedback", "I have feedback", or "report an issue", THE Agent SHALL immediately start the Feedback_Workflow.
2. WHEN the Feedback_Workflow starts and `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` does not exist, THE Agent SHALL copy the Feedback_Template to that path and replace the date placeholder with today's date.
3. WHEN the Feedback_Workflow starts and the Feedback_File already exists, THE Agent SHALL proceed to feedback gathering without modifying existing content.

### Requirement 2: Structured Feedback Gathering and Storage

**User Story:** As a Bootcamper, I want to be guided through feedback one question at a time and have it saved as a structured markdown entry, so that my feedback is organized and actionable.

#### Acceptance Criteria

1. WHEN feedback gathering begins, THE Agent SHALL ask six questions one at a time: category (from seven Feedback_Categories), module (0-12 or General), description, impact, suggested fix, and priority (High/Medium/Low).
2. WHEN all six answers are collected, THE Agent SHALL format a structured markdown entry containing: Date, Module, Priority, Category, What Happened, Why It's a Problem, Suggested Fix, and Workaround sections.
3. WHEN the entry is formatted, THE Agent SHALL append the entry to the "Your Feedback" section of the Feedback_File, preserving all existing entries.
4. THE Agent SHALL save feedback locally to the Feedback_File only and SHALL NOT submit feedback to any MCP server unless the Bootcamper explicitly requests submission.

### Requirement 3: Confirmation, Continuation, and Reminders

**User Story:** As a Bootcamper, I want confirmation that my feedback was saved and reminders about the feedback mechanism at key milestones, so that I know my input is captured and I remember to provide it.

#### Acceptance Criteria

1. WHEN a feedback entry is saved, THE Agent SHALL confirm the save location and offer the Bootcamper a choice to add more feedback or continue with the bootcamp.
2. WHEN Module 1 starts, THE Agent SHALL inform the Bootcamper about the feedback mechanism and how to trigger it.
3. WHEN Module 12 ends, THE Agent SHALL remind the Bootcamper to share their feedback file.
