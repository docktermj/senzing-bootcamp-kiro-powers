# Implementation Plan: Bootcamp Feedback Hook

## Overview

Replace the probabilistic feedback capture (agent voluntarily loading `feedback-workflow.md`) with a deterministic `promptSubmit` hook. All deliverables are JSON, Markdown, or YAML configuration files — no executable code.

## Tasks

- [ ] 1. Create the capture-feedback hook file
  - [x] 1.1 Create `senzing-bootcamp/hooks/capture-feedback.kiro.hook` with the hook JSON
    - Use `promptSubmit` event type in `when.type`
    - Use `askAgent` in `then.type`
    - Set `name` to `"Capture Bootcamp Feedback"`, `version` to `"1.0.0"`
    - Set `description` to explain the hook fires on every message and checks for trigger phrases
    - Set `then.prompt` to the exact prompt text from the design: instruct the agent to check for all six trigger phrases (case-insensitive), do nothing if none found, load `feedback-workflow.md` if found, and auto-capture context from `config/bootcamp_progress.json`, recent conversation, and open files
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2. Update the feedback-workflow steering file
  - [x] 2.1 Add Step 0 (Automatic Context Capture) to `senzing-bootcamp/steering/feedback-workflow.md`
    - Insert a new "Step 0: Automatic Context Capture" before the current Step 1
    - Include instructions to: read `config/bootcamp_progress.json` for current module, capture recent conversation context, identify open editor files
    - Include fallback: if `bootcamp_progress.json` does not exist, record module as "Unknown"
    - Instruct agent to pre-fill context fields and present to bootcamper for confirmation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.4_

  - [x] 2.2 Update the feedback entry template in `senzing-bootcamp/steering/feedback-workflow.md`
    - Add a "Context When Reported" section to the entry template with sub-fields: Current Module, What You Were Doing, Open Files
    - _Requirements: 4.3, 6.3_

  - [x] 2.3 Add return-to-activity step and renumber all steps in `senzing-bootcamp/steering/feedback-workflow.md`
    - Add a new step (after the current "Remind About Submission") that offers to return the bootcamper to their previous activity
    - Renumber all steps to accommodate Step 0 at the beginning and the new return step
    - _Requirements: 5.1, 5.2, 5.3, 6.5_

- [ ] 3. Update agent-instructions steering file
  - [x] 3.1 Replace manual feedback-workflow loading with hook reference in `senzing-bootcamp/steering/agent-instructions.md`
    - In the Communication section, replace `On "power feedback" / "bootcamp feedback": load feedback-workflow.md` with a line referencing the capture-feedback hook: `On feedback trigger phrases: the capture-feedback hook handles this automatically — do not manually load feedback-workflow.md`
    - _Requirements: 7.1, 7.2_

  - [x] 3.2 Add capture-feedback hook to the Hooks section in `senzing-bootcamp/steering/agent-instructions.md`
    - Mention `capture-feedback.kiro.hook` in the Hooks section so it is installed alongside other bootcamp hooks
    - _Requirements: 7.3_

- [x] 4. Checkpoint — Review hook and steering file changes
  - Ensure all files are valid (hook is valid JSON, steering files are well-formed Markdown)
  - Ensure the hook prompt contains all six trigger phrases
  - Ensure feedback-workflow.md has Step 0, updated template, return-to-activity step, and correct numbering
  - Ensure agent-instructions.md no longer instructs manual loading for feedback trigger phrases
  - Ask the user if questions arise

- [ ] 5. Update hooks README and steering index
  - [x] 5.1 Add entry #15 for capture-feedback hook to `senzing-bootcamp/hooks/README.md`
    - Follow the existing format: heading, trigger, action, use case description
    - Place after entry #14 (Offer Entity Graph Visualization)
    - _Requirements: 1.1_

  - [x] 5.2 Update `senzing-bootcamp/steering/steering-index.yaml` if the feedback keyword mapping needs changes
    - Verify the `feedback: feedback-workflow.md` mapping is still correct (it should be — the hook loads the same steering file)
    - _Requirements: 6.1_

- [x] 6. Validate with validate_power.py
  - Run `python senzing-bootcamp/scripts/validate_power.py` to check the power structure is still valid after changes
  - Fix any validation errors reported
  - _Requirements: 1.1, 7.3_

- [x] 7. Final checkpoint — Ensure all deliverables are complete
  - Verify all four deliverable files exist and are correctly modified
  - Ensure all tests pass, ask the user if questions arise

## Notes

- All tasks write JSON, Markdown, or YAML — no executable Python code
- The hook file follows the same schema as the 14 existing hooks in `senzing-bootcamp/hooks/`
- The steering-index.yaml `feedback` keyword already maps to `feedback-workflow.md` — this should remain unchanged since the hook loads the same file
- Each task references specific requirements for traceability
