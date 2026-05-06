# Requirements Document

## Introduction

Consolidate the senzing-bootcamp power's hook infrastructure to reduce visible hook executions per conversation turn. Currently, four hooks fire visibly per turn (two `agentStop` hooks after agent output, two `promptSubmit` hooks after bootcamper input), creating visual noise. This feature merges overlapping hooks into fewer, unified hooks while preserving all existing behavior.

## Glossary

- **Hook**: A JSON file (`.kiro.hook`) that maps an IDE event to an agent action. Each hook fires visibly in the conversation when triggered.
- **Agent_Stop_Hook**: A hook with `when.type` = `agentStop` that fires after the agent finishes a response.
- **Prompt_Submit_Hook**: A hook with `when.type` = `promptSubmit` that fires after the bootcamper submits a message.
- **Hook_Registry**: The steering file `hook-registry.md` that documents all hooks with their id, name, description, and prompt.
- **Consolidated_Agent_Stop_Hook**: The single merged `agentStop` hook replacing `ask-bootcamper` and `feedback-submission-reminder`.
- **Consolidated_Prompt_Submit_Hook**: The single merged `promptSubmit` hook replacing `capture-feedback` and `review-bootcamper-input`.
- **Silent_Processing**: A prompt pattern instructing the agent to produce zero output when conditions are not met.
- **Feedback_Trigger_Phrase**: One of the case-insensitive phrases that initiate the feedback workflow: "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue".
- **CI_Pipeline**: The GitHub Actions workflow that runs `sync_hook_registry.py --verify` and pytest to validate hook consistency.

## Requirements

### Requirement 1: Merge agentStop Hooks into a Single Hook

**User Story:** As a bootcamper, I want only one hook to fire after the agent stops, so that the conversation is not cluttered with multiple visible hook executions.

#### Acceptance Criteria

1. THE Consolidated_Agent_Stop_Hook SHALL combine the closing-question logic from `ask-bootcamper` and the feedback-submission-reminder logic from `feedback-submission-reminder` into a single hook file.
2. WHEN the agent stops, THE Consolidated_Agent_Stop_Hook SHALL check all silence conditions (no question pending, no existing 👉, no trailing question) before producing any recap or closing question.
3. WHEN the bootcamper has completed their chosen track AND the 📋 marker has not appeared in the session AND saved feedback exists, THE Consolidated_Agent_Stop_Hook SHALL append the feedback submission reminder after the closing question output.
4. WHEN the silence conditions are not met, THE Consolidated_Agent_Stop_Hook SHALL produce zero output regardless of track completion state.
5. THE Consolidated_Agent_Stop_Hook SHALL use the filename `ask-bootcamper.kiro.hook` to preserve the existing hook id for CI compatibility.
6. WHEN the feedback-submission-reminder conditions are met but the closing-question conditions are not, THE Consolidated_Agent_Stop_Hook SHALL still produce the feedback submission reminder as standalone output.

### Requirement 2: Merge promptSubmit Hooks into a Single Hook

**User Story:** As a bootcamper, I want only one hook to fire after I submit a message, so that the conversation flow is not interrupted by redundant hook executions.

#### Acceptance Criteria

1. THE Consolidated_Prompt_Submit_Hook SHALL combine the feedback trigger detection from `capture-feedback` and `review-bootcamper-input` into a single hook file.
2. WHEN the bootcamper's message contains a Feedback_Trigger_Phrase, THE Consolidated_Prompt_Submit_Hook SHALL initiate the feedback workflow with automatic context capture.
3. WHEN the bootcamper's message does not contain a Feedback_Trigger_Phrase, THE Consolidated_Prompt_Submit_Hook SHALL produce zero output using Silent_Processing.
4. THE Consolidated_Prompt_Submit_Hook SHALL use the filename `review-bootcamper-input.kiro.hook` to preserve the existing hook id for CI compatibility.
5. THE Consolidated_Prompt_Submit_Hook SHALL read `config/bootcamp_progress.json` for current module context, note recent conversation activity, and identify open editor files when a trigger phrase is detected.

### Requirement 3: Remove Redundant Hook Files

**User Story:** As a power maintainer, I want obsolete hook files removed, so that the hook directory accurately reflects the active hook set.

#### Acceptance Criteria

1. WHEN the consolidation is complete, THE Hook_Registry SHALL no longer contain entries for `feedback-submission-reminder` or `capture-feedback` as separate hooks.
2. THE file `feedback-submission-reminder.kiro.hook` SHALL be deleted from `senzing-bootcamp/hooks/`.
3. THE file `capture-feedback.kiro.hook` SHALL be deleted from `senzing-bootcamp/hooks/`.
4. IF a CI run references a deleted hook file, THEN THE CI_Pipeline SHALL pass without errors after the registry is updated.

### Requirement 4: Update Hook Registry

**User Story:** As a power maintainer, I want the hook registry to accurately reflect the consolidated hook set, so that CI validation passes and documentation stays correct.

#### Acceptance Criteria

1. THE Hook_Registry SHALL update the `ask-bootcamper` entry description to reflect its dual responsibility (closing question + feedback submission reminder on track completion).
2. THE Hook_Registry SHALL update the `review-bootcamper-input` entry description to reflect its unified responsibility (feedback trigger detection + context capture + workflow initiation).
3. THE Hook_Registry SHALL remove the `feedback-submission-reminder` entry entirely.
4. THE Hook_Registry SHALL remove the `capture-feedback` entry entirely.
5. THE Hook_Registry SHALL update the total hook count from 25 to 23.
6. WHEN `sync_hook_registry.py --verify` is run, THE CI_Pipeline SHALL report zero synchronization errors.

### Requirement 5: Update Onboarding Flow References

**User Story:** As a power maintainer, I want the onboarding-flow steering file to reference the correct hooks, so that hook installation during onboarding succeeds.

#### Acceptance Criteria

1. THE onboarding-flow.md Critical Hooks section SHALL remove the `feedback-submission-reminder` entry and its failure impact message.
2. THE onboarding-flow.md Critical Hooks section SHALL remove the `capture-feedback` entry if it is listed separately from `review-bootcamper-input`.
3. THE onboarding-flow.md Critical Hooks section SHALL update the `ask-bootcamper` failure impact message to include feedback reminder functionality: "Session summaries, closing questions, and post-completion feedback reminders will not be automatically generated when the agent stops."
4. THE onboarding-flow.md Critical Hooks section SHALL update the `review-bootcamper-input` failure impact message to: "Feedback trigger phrases will not be automatically detected on message submission."

### Requirement 6: Update Test Suite

**User Story:** As a power maintainer, I want the test suite to validate the consolidated hooks correctly, so that CI continues to pass and regressions are caught.

#### Acceptance Criteria

1. THE test suite SHALL update `EXPECTED_HOOK_COUNT` from 25 to 23.
2. THE test suite SHALL validate that the consolidated `ask-bootcamper.kiro.hook` contains both closing-question logic and feedback-submission-reminder logic in its prompt.
3. THE test suite SHALL validate that the consolidated `review-bootcamper-input.kiro.hook` contains feedback trigger phrase detection with Silent_Processing.
4. THE test suite SHALL verify that no `.kiro.hook` file exists for `feedback-submission-reminder` or `capture-feedback`.
5. WHEN pytest is run, THE test suite SHALL pass with zero failures after consolidation.

### Requirement 7: Preserve Behavioral Equivalence

**User Story:** As a bootcamper, I want the consolidated hooks to behave identically to the original separate hooks, so that no functionality is lost.

#### Acceptance Criteria

1. THE Consolidated_Agent_Stop_Hook SHALL preserve the silence-first default (zero output unless all conditions pass).
2. THE Consolidated_Agent_Stop_Hook SHALL preserve the 📋 deduplication check for the feedback submission reminder.
3. THE Consolidated_Agent_Stop_Hook SHALL preserve the near-completion feedback nudge ("say bootcamp feedback anytime") separately from the post-completion submission reminder.
4. THE Consolidated_Prompt_Submit_Hook SHALL preserve all six Feedback_Trigger_Phrases with case-insensitive matching.
5. THE Consolidated_Prompt_Submit_Hook SHALL preserve the instruction to load `feedback-workflow.md` steering file when a trigger is detected.
6. THE Consolidated_Prompt_Submit_Hook SHALL preserve the instruction to not ask the bootcamper to re-explain context.
