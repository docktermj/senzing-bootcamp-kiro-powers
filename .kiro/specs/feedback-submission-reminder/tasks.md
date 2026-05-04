# Implementation Plan: Feedback Submission Reminder

## Overview

This plan implements proactive, context-aware feedback submission reminders at track completion and graduation. The implementation modifies two existing steering files, creates one new hook file, and updates the hook registry, hook categories, and steering index. All changes are additive — no existing behavior is removed, only augmented with conditional feedback detection and guided sharing instructions.

## Tasks

- [x] 1. Create the feedback-submission-reminder hook file
  - [x] 1.1 Create `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook`
    - Create a JSON hook file following the established hook file schema (see `ask-bootcamper.kiro.hook` and `enforce-visualization-offers.kiro.hook` for format reference)
    - Set `name` to `"Feedback Submission Reminder"`, `version` to `"1.0.0"`
    - Set `description` to `"After track completion or graduation, checks for saved feedback and reminds the bootcamper to share it with the power author."`
    - Set `when.type` to `"agentStop"` and `then.type` to `"askAgent"`
    - The `then.prompt` must encode the full hook logic from the design: (1) scan conversation history for track completion evidence (path completion celebration or graduation completion messages), (2) if no track completion detected → produce no output, (3) if track completion detected → check if feedback reminder was already presented (look for `📋` marker in recent conversation), (4) if already presented → produce no output, (5) check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists and contains at least one `## Improvement:` heading below the `## Your Feedback` section, (6) if feedback exists → emit: `📋 Reminder: You have bootcamp feedback saved. Say 'share feedback' to send it to the power author.`, (7) if no feedback → produce no output
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 1.2 Write unit tests for the feedback-submission-reminder hook file
    - Create `senzing-bootcamp/tests/test_feedback_submission_reminder_hook.py` following the pattern in `test_ask_bootcamper_hook.py`
    - Test that the hook file is valid JSON with required keys (`name`, `version`, `description`, `when`, `then`)
    - Test that `when.type` is `"agentStop"` and `then.type` is `"askAgent"`
    - Test that the prompt contains key behavioral markers: feedback file path (`docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`), track completion detection instructions, deduplication check (`📋` marker), the `## Improvement:` heading pattern, and the no-output conditions
    - Test that the hook `name` and `description` match expected values
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. Update module-completion.md with feedback existence check and reminder
  - [x] 2.1 Add feedback submission reminder to the Path Completion Celebration section in `senzing-bootcamp/steering/module-completion.md`
    - Replace the existing passive line `- Remind: "Say 'bootcamp feedback' to share your experience"` with an active feedback existence check and conditional reminder block
    - The new block must: (1) check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists and contains at least one `## Improvement:` heading below `## Your Feedback`, (2) if feedback exists, display: `📋 You have feedback saved in docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md. Would you like to share it with the power author?`, (3) if the bootcamper accepts, present the three sharing options (email to support@senzing.com with subject "Senzing Bootcamp Power Feedback", GitHub issue on the senzing-bootcamp power repository, or copy the file path), (4) if the bootcamper declines, proceed without re-prompting about feedback, (5) if no feedback file or no entries, display the fallback: `Say 'bootcamp feedback' to share your experience`
    - Place the feedback reminder after the graduation offer sequence and before the `Load lessons-learned.md` line
    - The agent must not automatically send emails or create GitHub issues without explicit bootcamper confirmation
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 6.3_

  - [x] 2.2 Write integration tests for module-completion.md feedback reminder placement
    - Add tests to `senzing-bootcamp/tests/test_feedback_submission_reminder_hook.py` (or a new test file) that verify:
    - `module-completion.md` contains the feedback existence check instructions in the Path Completion Celebration section
    - The feedback reminder appears after the graduation offer and before the lessons-learned load
    - The sharing instructions include all three options (email, GitHub issue, copy path)
    - The non-blocking decline behavior is described
    - _Requirements: 1.4, 6.1, 6.2, 6.3_

- [x] 3. Update graduation.md with feedback reminder after graduation completion
  - [x] 3.1 Add feedback submission reminder to the Graduation Report section in `senzing-bootcamp/steering/graduation.md`
    - Insert a feedback reminder block after the `🎓 Graduation complete!` message and before the existing `Say "bootcamp feedback" if you'd like to share your experience` line
    - The new block must: (1) check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists and contains feedback entries, (2) check conversation history for `📋` marker to skip if reminder was already shown during track completion, (3) if feedback exists and no prior reminder, display the feedback submission reminder with the same sharing instructions from Requirement 3, (4) if the bootcamper declines, proceed without re-prompting
    - Retain the existing `Say "bootcamp feedback"` line as a fallback for bootcampers without saved feedback
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3_

  - [x] 3.2 Write integration tests for graduation.md feedback reminder placement
    - Verify `graduation.md` contains the feedback existence check instructions after the graduation complete message
    - Verify the graduation feedback reminder appears before the existing "Say 'bootcamp feedback'" line
    - Verify the deduplication check (skip if `📋` already in conversation) is present
    - _Requirements: 4.1, 4.2, 4.3, 7.1, 7.2, 7.3_

- [x] 4. Checkpoint — Verify steering file changes and hook file
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Register the hook and update metadata files
  - [x] 5.1 Add the feedback-submission-reminder hook to `senzing-bootcamp/steering/hook-registry.md`
    - Add a new entry under the "Critical Hooks" section following the established format
    - Entry: `**feedback-submission-reminder** (agentStop → askAgent)` with the full prompt text, id (`feedback-submission-reminder`), name (`Feedback Submission Reminder`), and description matching the hook file
    - The prompt in the registry must exactly match the `then.prompt` value in the hook JSON file
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 5.2 Add `feedback-submission-reminder` to the `critical` list in `senzing-bootcamp/hooks/hook-categories.yaml`
    - Add the entry alphabetically within the critical list
    - _Requirements: 5.1_

  - [x] 5.3 Update `senzing-bootcamp/steering/steering-index.yaml`
    - Add keyword mapping: `share feedback: feedback-workflow.md`
    - Update `module-completion.md` token count in `file_metadata` (re-measure after edits)
    - Update `graduation.md` token count in `file_metadata` (re-measure after edits)
    - Update `hook-registry.md` token count in `file_metadata` (re-measure after edits)
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get accurate token counts for the modified files
    - _Requirements: 5.1_

  - [x] 5.4 Write integration tests for hook registry consistency
    - Verify `feedback-submission-reminder` appears in `hook-registry.md` under Critical Hooks
    - Verify `feedback-submission-reminder` appears in `hook-categories.yaml` under `critical`
    - Verify the hook file exists at `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook`
    - Verify the hook's `name`, `description`, and `when.type` in the JSON file match the registry entry
    - Verify `share feedback` keyword exists in `steering-index.yaml`
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 6. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to validate token counts
  - Run `python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify` to validate hook registry consistency
  - Run `pytest senzing-bootcamp/tests/test_feedback_submission_reminder_hook.py -v` to validate all new tests pass

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- This feature has no algorithmic code — all changes are steering files (markdown), a hook file (JSON), and metadata (YAML)
- Property-based testing does not apply; tests focus on structural validation and integration verification
- The existing CI pipeline (`validate-power.yml`) will validate all new files via `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, and pytest
