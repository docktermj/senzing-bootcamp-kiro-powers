# Implementation Plan: Consolidate Redundant agentStop Hooks

## Overview

Merge the "Feedback Submission Reminder" agentStop hook into the "Ask Bootcamper" agentStop hook, eliminating the redundant second hook invocation visible to the bootcamper after every agent turn.

## Tasks

- [x] 1. Update ask-bootcamper hook prompt to include feedback reminder logic
  - [x] 1.1 Read the current `feedback-submission-reminder.kiro.hook` prompt to capture its exact conditional logic
  - [x] 1.2 Append a "Feedback Reminder (conditional)" section to the `ask-bootcamper.kiro.hook` prompt
    - Place it after the existing SECOND branch (recap + closing question)
    - Include the track-completion conditional: only mention feedback when the bootcamper is on the final step or has completed their track
    - Include explicit "otherwise produce nothing for this section" instruction
    - _Requirements: 1, 2, 3, 4, 5_

- [x] 2. Delete the feedback-submission-reminder hook file
  - [x] 2.1 Remove `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook`
    - _Requirements: 1_

- [x] 3. Update hook-registry.md
  - [x] 3.1 Remove the `feedback-submission-reminder` entry from `senzing-bootcamp/steering/hook-registry.md`
  - [x] 3.2 Update the `ask-bootcamper` entry description to note its dual responsibility (recap/closing question + conditional feedback reminder)
    - _Requirements: 1, 2_

- [x] 4. Update hook-categories.yaml if applicable
  - [x] 4.1 Check `senzing-bootcamp/hooks/hook-categories.yaml` for any reference to `feedback-submission-reminder` and remove it
    - _Requirements: 1_

- [x] 5. Verify consolidation
  - Confirm only one agentStop hook file exists in `senzing-bootcamp/hooks/`
  - Confirm the consolidated prompt contains both the ask-bootcamper logic and the conditional feedback reminder
  - Confirm hook-registry.md is consistent with the actual hook files
  - Run any existing hook validation scripts (e.g., `sync_hook_registry.py --verify`)

## Notes

- The Ask Bootcamper suppression behavior (zero output when 👉 question is pending) must remain unchanged
- The feedback reminder must remain silent except near track completion
- No Python code changes — only hook JSON and steering markdown edits
