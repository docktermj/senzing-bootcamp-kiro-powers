# Tasks: Hook Consolidation

## Task 1: Merge feedback-submission-reminder logic into ask-bootcamper hook

- [x] 1.1 Read the current `ask-bootcamper.kiro.hook` prompt and `feedback-submission-reminder.kiro.hook` prompt
- [x] 1.2 Append the feedback-submission-reminder three-condition gate and 📋 reminder output to the ask-bootcamper prompt as a separate Phase 2 section
- [x] 1.3 Update the `description` field in `ask-bootcamper.kiro.hook` to reflect dual responsibility (closing question + feedback submission reminder)
- [x] 1.4 Bump the `version` field in `ask-bootcamper.kiro.hook` (e.g., to `3.0.0`)
- [x] 1.5 Verify the merged prompt preserves: silence-first default, 📋 deduplication, near-completion nudge separate from post-completion reminder, standalone feedback reminder when closing question is suppressed

## Task 2: Delete redundant hook files

- [x] 2.1 Delete `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook`
- [x] 2.2 Delete `senzing-bootcamp/hooks/capture-feedback.kiro.hook`

## Task 3: Update hook-categories.yaml

- [x] 3.1 Remove `capture-feedback` from the `critical` list in `senzing-bootcamp/hooks/hook-categories.yaml`
- [x] 3.2 Remove `feedback-submission-reminder` from the `critical` list in `senzing-bootcamp/hooks/hook-categories.yaml`

## Task 4: Update hook registry

- [x] 4.1 Remove the `**capture-feedback**` entry block from `senzing-bootcamp/steering/hook-registry.md`
- [x] 4.2 Remove the `**feedback-submission-reminder**` entry block from `senzing-bootcamp/steering/hook-registry.md`
- [x] 4.3 Update the `**ask-bootcamper**` entry description to mention dual responsibility (closing question + feedback submission reminder on track completion)
- [x] 4.4 Update the `**review-bootcamper-input**` entry description to mention unified responsibility (feedback trigger detection + context capture + workflow initiation)
- [x] 4.5 Update the total hook count in hook-registry.md from 25 to 23

## Task 5: Update onboarding-flow.md

- [x] 5.1 Remove the `feedback-submission-reminder` row from the Critical Hooks table in `senzing-bootcamp/steering/onboarding-flow.md`
- [x] 5.2 Remove the `capture-feedback` row from the Critical Hooks table
- [x] 5.3 Update the `ask-bootcamper` failure impact message to: "Session summaries, closing questions, and post-completion feedback reminders will not be automatically generated when the agent stops."
- [x] 5.4 Update the `review-bootcamper-input` failure impact message to: "Feedback trigger phrases will not be automatically detected on message submission."

## Task 6: Update test suite

- [x] 6.1 Update `EXPECTED_HOOK_COUNT` from 25 to 23 in `tests/test_hook_prompt_standards.py`
- [x] 6.2 Delete `senzing-bootcamp/tests/test_feedback_submission_reminder_hook.py` (hook file no longer exists)
- [x] 6.3 Update `senzing-bootcamp/tests/test_ask_bootcamper_hook.py` to add assertions verifying the prompt contains feedback-submission-reminder logic (track completion detection, 📋 deduplication, feedback file existence check)
- [x] 6.4 Create `senzing-bootcamp/tests/test_hook_consolidation.py` with:
  - [x] 6.4.1 Example tests verifying deleted hook files do not exist
  - [x] 6.4.2 Example tests verifying hook-registry.md does not contain removed entries
  - [x] 6.4.3 Example tests verifying onboarding-flow.md does not contain removed entries
  - [x] 6.4.4 Example tests verifying hook-categories.yaml does not list deleted hooks
  - [x] 6.4.5 Property test (Hypothesis, 100 examples): silence-first default in ask-bootcamper prompt (Property 1)
  - [x] 6.4.6 Property test (Hypothesis, 100 examples): all six trigger phrases preserved with case-insensitive matching in review-bootcamper-input prompt (Property 2)
  - [x] 6.4.7 Property test (Hypothesis, 100 examples): all hook files are valid JSON with required keys and valid event/action types (Property 3)

## Task 7: Run validation

- [x] 7.1 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` and confirm exit code 0
- [x] 7.2 Run `pytest tests/test_hook_prompt_standards.py` and confirm all tests pass
- [x] 7.3 Run `pytest senzing-bootcamp/tests/test_hook_consolidation.py` and confirm all tests pass
- [x] 7.4 Run `pytest senzing-bootcamp/tests/test_ask_bootcamper_hook.py` and confirm all tests pass
