# Requirements Document

## Introduction

The feedback workflow (`senzing-bootcamp/steering/feedback-workflow.md`) collects structured feedback from bootcampers and saves it locally to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`. However, the workflow never actively reminds the bootcamper to share that feedback with the power author. The only nudge is a passive line at the end of the feedback workflow ("When you complete the bootcamp, please share your feedback file with the power author") and a brief mention in `module-completion.md` ("Say 'bootcamp feedback' to share your experience"). Neither checks whether feedback already exists, and neither offers concrete sharing instructions.

This feature adds proactive, context-aware reminders at two key moments — track completion and graduation — that detect whether saved feedback exists and, if so, guide the bootcamper through sharing it. It also adds a `feedback-submission-reminder` hook that fires on `agentStop` after track-completion events to catch cases where the inline reminder might be missed.

## Glossary

- **Feedback_File**: The file `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` that accumulates structured feedback entries written by the Feedback_Workflow.
- **Feedback_Workflow**: The agent-driven feedback collection sequence defined in `senzing-bootcamp/steering/feedback-workflow.md`.
- **Module_Completion_Workflow**: The steering file at `senzing-bootcamp/steering/module-completion.md` that handles journal entries, reflection, and path completion after each module.
- **Graduation_Workflow**: The steering file at `senzing-bootcamp/steering/graduation.md` that transitions a completed bootcamp project into a production-ready codebase.
- **Feedback_Submission_Reminder_Hook**: A hook file at `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook` that fires on `agentStop` to check for unsent feedback after track completion.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Track_Completion**: The event when a bootcamper finishes the final module of their chosen track (Path A: Module 3, Path B: Module 7, Path C: Module 7, Path D: Module 11).
- **Sharing_Instructions**: A set of concrete steps the bootcamper can follow to share their Feedback_File with the power author, including email to support@senzing.com and creating a GitHub issue on the power repository.

## Requirements

### Requirement 1: Feedback Existence Check at Track Completion

**User Story:** As a bootcamper who has been collecting feedback throughout the bootcamp, I want to be reminded at track completion that I have unsent feedback, so that I do not forget to share it with the power author.

#### Acceptance Criteria

1. WHEN a bootcamper completes the final module of their chosen track and the Module_Completion_Workflow runs the Path Completion Celebration section, THE Agent SHALL check whether `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists and contains at least one feedback entry beyond the template header.
2. WHEN the Feedback_File exists and contains feedback entries, THE Agent SHALL display a reminder: "📋 You have feedback saved in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`. Would you like to share it with the power author?"
3. WHEN the Feedback_File does not exist or contains only the template header with no entries, THE Agent SHALL skip the feedback submission reminder entirely.
4. THE feedback submission reminder SHALL appear in the Path Completion Celebration section after the export-results offer and graduation offer, and before the lessons-learned retrospective offer.

### Requirement 2: Non-Blocking Reminder Interaction

**User Story:** As a bootcamper, I want the feedback sharing reminder to be optional and non-blocking, so that I can skip it and continue with the bootcamp without friction.

#### Acceptance Criteria

1. WHEN the Agent presents the feedback submission reminder, THE Agent SHALL accept "no", "skip", "not now", or any declining response as a valid answer and proceed to the next post-completion option without further prompting about feedback.
2. WHEN the bootcamper declines the feedback submission reminder, THE Agent SHALL not ask about feedback sharing again during the same track completion sequence.
3. THE feedback submission reminder SHALL not prevent the bootcamper from accessing any other post-completion option (export results, graduation, lessons-learned, path switching).

### Requirement 3: Sharing Instructions

**User Story:** As a bootcamper who wants to share feedback, I want clear instructions on how to send it to the power author, so that I know exactly what to do.

#### Acceptance Criteria

1. WHEN the bootcamper accepts the feedback submission reminder, THE Agent SHALL present the following sharing options: (a) email the Feedback_File contents to support@senzing.com, (b) create a GitHub issue on the senzing-bootcamp power repository with the feedback content, or (c) copy the file path for manual sharing.
2. WHEN the bootcamper chooses the email option, THE Agent SHALL display the email address and a suggested subject line ("Senzing Bootcamp Power Feedback") and offer to format the feedback content for easy copy-paste.
3. WHEN the bootcamper chooses the GitHub issue option, THE Agent SHALL provide the repository URL and offer to format the feedback as a markdown-ready issue body.
4. WHEN the bootcamper chooses the copy-path option, THE Agent SHALL display the absolute path to the Feedback_File.
5. THE Agent SHALL not automatically send emails or create GitHub issues on behalf of the bootcamper without explicit confirmation for each action.

### Requirement 4: Graduation Workflow Feedback Reminder

**User Story:** As a bootcamper completing the graduation workflow, I want a feedback sharing reminder at the end of graduation, so that I have a second opportunity to share feedback before wrapping up.

#### Acceptance Criteria

1. WHEN the Graduation_Workflow completes and generates the Graduation_Report, THE Agent SHALL check whether the Feedback_File exists and contains feedback entries.
2. WHEN the Feedback_File exists and contains entries, THE Agent SHALL display the feedback submission reminder after the graduation completion message and before the final "Say 'bootcamp feedback'" prompt.
3. WHEN the bootcamper already shared feedback during the track completion reminder in the same session, THE Agent SHALL skip the graduation feedback reminder to avoid redundancy.
4. THE graduation feedback reminder SHALL use the same Sharing_Instructions defined in Requirement 3.

### Requirement 5: Feedback Submission Reminder Hook

**User Story:** As a power maintainer, I want a hook that checks for unsent feedback after track completion events, so that the reminder fires even if the inline steering-file reminder is missed due to conversation flow.

#### Acceptance Criteria

1. THE Feedback_Submission_Reminder_Hook SHALL be defined in a hook file at `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook` with `"type": "agentStop"` as the trigger event.
2. WHEN the hook fires, THE Agent SHALL check the conversation history for evidence that a track completion just occurred (presence of path completion celebration messages or graduation completion messages).
3. WHEN track completion is detected and the Feedback_File exists with feedback entries, THE Agent SHALL include a brief reminder in the agent-stop summary: "📋 Reminder: You have bootcamp feedback saved. Say 'share feedback' to send it to the power author."
4. WHEN track completion is not detected, THE hook SHALL produce no output.
5. WHEN the feedback submission reminder was already presented during the current track completion sequence, THE hook SHALL produce no output to avoid duplicate reminders.

### Requirement 6: Module-Completion Steering Update

**User Story:** As a power maintainer, I want the feedback submission reminder integrated into the existing module-completion steering file, so that the reminder is part of the standard track completion flow.

#### Acceptance Criteria

1. THE `senzing-bootcamp/steering/module-completion.md` Path Completion Celebration section SHALL be updated to include the feedback existence check and reminder sequence defined in Requirements 1 and 2.
2. THE updated section SHALL replace the existing passive reminder ("Remind: Say 'bootcamp feedback' to share your experience") with the active feedback existence check and conditional reminder.
3. THE feedback submission reminder in `module-completion.md` SHALL appear after the graduation offer sequence and before the lessons-learned retrospective load.

### Requirement 7: Graduation Steering Update

**User Story:** As a power maintainer, I want the graduation workflow updated to include the feedback reminder at completion, so that bootcampers who graduate get a sharing prompt.

#### Acceptance Criteria

1. THE `senzing-bootcamp/steering/graduation.md` Graduation Report section SHALL be updated to include the feedback existence check and conditional reminder after the graduation completion message.
2. THE graduation feedback reminder SHALL appear after the "🎓 Graduation complete!" message and before the existing "Say 'bootcamp feedback' if you'd like to share your experience" line.
3. THE existing "Say 'bootcamp feedback'" line in `graduation.md` SHALL be retained as a fallback for bootcampers who do not have saved feedback but may want to create some.
