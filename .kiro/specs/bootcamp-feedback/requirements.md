# Requirements Document

## Introduction

The Senzing Bootcamp Power currently relies on a steering file (`feedback-workflow.md`) with `inclusion: manual` to capture bootcamper feedback. The agent must recognize trigger phrases (e.g., "bootcamp feedback") and voluntarily load the steering file — a probabilistic mechanism that sometimes fails, causing feedback to be silently lost.

This feature replaces the probabilistic steering-file-loading approach with a deterministic, event-driven hook mechanism. A `promptSubmit` hook fires whenever a bootcamper's message contains feedback-related phrases, guaranteeing the agent follows the feedback workflow every time. The hook also instructs the agent to automatically capture the bootcamper's current context (module, recent activity, open files) so the bootcamper does not need to re-explain what they were doing.

## Glossary

- **Hook**: A Kiro event-driven automation that fires deterministically when a specified IDE event occurs, instructing the agent to perform an action. Unlike steering files, hooks do not depend on the agent choosing to load them.
- **Feedback_Hook**: The `promptSubmit` hook file (`senzing-bootcamp/hooks/capture-feedback.kiro.hook`) that triggers when a bootcamper's message contains feedback-related phrases.
- **Feedback_File**: The file `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` in the bootcamper's project where all feedback entries are appended.
- **Feedback_Template**: The template file `senzing-bootcamp/docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md` used to initialize the Feedback_File when it does not yet exist.
- **Feedback_Workflow_Steering**: The existing steering file `senzing-bootcamp/steering/feedback-workflow.md` that provides the agent with step-by-step instructions for collecting and formatting feedback.
- **Bootcamp_Progress**: The file `config/bootcamp_progress.json` that tracks the bootcamper's current module and completed modules.
- **Agent_Instructions**: The always-included steering file `senzing-bootcamp/steering/agent-instructions.md` that defines core agent behavior rules.
- **Trigger_Phrase**: One of the predefined phrases that indicate a bootcamper wants to provide feedback: "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue".
- **Context_Capture**: The automatic collection of the bootcamper's current working state — current module from Bootcamp_Progress, recent conversation context, and open files — performed by the agent without requiring the bootcamper to re-explain.

## Requirements

### Requirement 1: Hook Creation and Trigger

**User Story:** As a bootcamp maintainer, I want a deterministic hook that fires on feedback-related phrases, so that feedback capture is guaranteed regardless of whether the agent would have voluntarily loaded the steering file.

#### Acceptance Criteria

1. THE Feedback_Hook SHALL be a valid Kiro hook file located at `senzing-bootcamp/hooks/capture-feedback.kiro.hook`.
2. THE Feedback_Hook SHALL use the `promptSubmit` event type to fire on every user message submission.
3. WHEN a bootcamper submits a message containing any Trigger_Phrase, THE Feedback_Hook SHALL instruct the agent to initiate the feedback collection workflow.
4. THE Feedback_Hook SHALL recognize the following Trigger_Phrases in a case-insensitive manner: "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue".
5. THE Feedback_Hook prompt SHALL instruct the agent to check the bootcamper's message for Trigger_Phrases before taking action, so that non-feedback messages are not intercepted.

### Requirement 2: Automatic Context Capture

**User Story:** As a bootcamper, I want the agent to automatically capture what I was working on when I provide feedback, so that I do not have to re-explain my current context.

#### Acceptance Criteria

1. WHEN the feedback workflow is initiated, THE agent SHALL read Bootcamp_Progress to determine the bootcamper's current module number and list of completed modules.
2. WHEN the feedback workflow is initiated, THE agent SHALL capture the recent conversation context to identify what the bootcamper was doing immediately before providing feedback.
3. WHEN the feedback workflow is initiated, THE agent SHALL identify which files are currently open in the editor to provide additional context about the bootcamper's activity.
4. IF Bootcamp_Progress does not exist, THEN THE agent SHALL record the current module as "Unknown" and proceed with feedback collection without failing.
5. THE agent SHALL include the captured context (current module, recent activity summary, open files) in the formatted feedback entry without requiring the bootcamper to provide this information manually.

### Requirement 3: Feedback File Initialization

**User Story:** As a bootcamper, I want the feedback file to be created automatically from the template if it does not exist, so that I can provide feedback at any point in the bootcamp without manual setup.

#### Acceptance Criteria

1. WHEN the feedback workflow is initiated and the Feedback_File does not exist at `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`, THE agent SHALL create the Feedback_File by copying the Feedback_Template.
2. WHEN the agent creates the Feedback_File from the Feedback_Template, THE agent SHALL replace the placeholder `[Date when you started using the power]` with the current date in YYYY-MM-DD format.
3. WHEN the Feedback_File already exists, THE agent SHALL use the existing file without overwriting or recreating it.
4. IF the `docs/feedback/` directory does not exist, THEN THE agent SHALL create the directory before creating the Feedback_File.

### Requirement 4: Feedback Persistence

**User Story:** As a bootcamp maintainer, I want every piece of feedback to be appended to the feedback file without exception, so that no feedback is ever lost.

#### Acceptance Criteria

1. WHEN the bootcamper provides feedback, THE agent SHALL append a formatted feedback entry to the "Your Feedback" section of the Feedback_File.
2. THE agent SHALL preserve all existing feedback entries in the Feedback_File when appending new entries.
3. THE agent SHALL format each feedback entry using the following structure: title, date, module, priority, category, "What Happened" section, "Why It's a Problem" section, "Suggested Fix" section, "Workaround Used" section, and a "Context When Reported" section containing the auto-captured context.
4. THE agent SHALL confirm to the bootcamper that feedback has been saved by displaying the file path `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`.
5. THE agent SHALL save feedback locally only and SHALL NOT submit feedback to any external service unless the bootcamper explicitly requests it.

### Requirement 5: Workflow Continuity

**User Story:** As a bootcamper, I want to return to whatever I was doing before providing feedback, so that the feedback process does not disrupt my bootcamp workflow.

#### Acceptance Criteria

1. WHEN feedback collection is complete, THE agent SHALL offer to return the bootcamper to the activity they were performing before the feedback workflow was initiated.
2. WHEN feedback collection is complete, THE agent SHALL summarize what was captured and provide the feedback file path before resuming the previous activity.
3. THE agent SHALL NOT require the bootcamper to re-navigate or re-explain their previous context after feedback collection is complete.

### Requirement 6: Steering File Update

**User Story:** As a bootcamp maintainer, I want the existing feedback-workflow.md steering file to be more prescriptive about context capture, so that when the hook loads it, the agent has clear instructions for gathering context automatically.

#### Acceptance Criteria

1. THE Feedback_Workflow_Steering SHALL include explicit instructions for the agent to read Bootcamp_Progress and capture the current module.
2. THE Feedback_Workflow_Steering SHALL include explicit instructions for the agent to capture recent conversation context and open files.
3. THE Feedback_Workflow_Steering SHALL include a "Context When Reported" section in the feedback entry template that contains: current module, what the bootcamper was doing (from conversation context), and which files were open.
4. THE Feedback_Workflow_Steering SHALL instruct the agent to pre-fill context fields automatically and present them to the bootcamper for confirmation rather than asking the bootcamper to provide context from scratch.
5. THE Feedback_Workflow_Steering SHALL instruct the agent to return the bootcamper to their previous activity after feedback collection is complete.

### Requirement 7: Agent Instructions Update

**User Story:** As a bootcamp maintainer, I want the agent-instructions.md file to reference the new hook-based feedback mechanism, so that the agent's core rules are consistent with the new approach.

#### Acceptance Criteria

1. THE Agent_Instructions SHALL reference the Feedback_Hook as the primary mechanism for feedback capture, replacing the current instruction to "load `feedback-workflow.md`" on trigger phrases.
2. THE Agent_Instructions SHALL retain the list of Trigger_Phrases for documentation purposes.
3. THE Agent_Instructions SHALL include the Feedback_Hook in the hooks installation section so that it is installed alongside other bootcamp hooks.
