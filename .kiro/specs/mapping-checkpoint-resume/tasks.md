# Implementation Plan: Mapping Workflow Checkpoint Resume

## Overview

Enhance `session-resume.md` with explicit three-option resume offers and checkpoint validation logic, update `agent-instructions.md` with a cross-reference note, and add tests verifying the steering file content.

## Tasks

- [x] 1. Enhance session-resume.md Step 3 with resume options
  - [x] 1.1 In `senzing-bootcamp/steering/session-resume.md` Step 3, after the existing mapping checkpoint paragraph ("If mapping checkpoints exist..."), add a "Mapping resume options" subsection that presents three explicit options: (a) Resume from checkpoint, (b) Restart mapping from scratch, (c) Skip and continue with other work
  - [x] 1.2 Add instruction that for multiple checkpoints, list each data source with its state first, then ask which one(s) to resume
  - [x] 1.3 Add instruction that when option (b) restart is chosen, the checkpoint file should be deleted before starting fresh
    - _Requirements: 2, 3, 6_

- [x] 2. Enhance session-resume.md Step 4 with checkpoint validation
  - [x] 2.1 In `senzing-bootcamp/steering/session-resume.md` Step 4, within the mapping checkpoint handling block, add a "Checkpoint validation" subsection before the fast-track instruction
  - [x] 2.2 Add instruction to call `mapping_workflow` with `action='status'` and pass the full checkpoint contents as the `state` parameter to verify validity
  - [x] 2.3 Add success path: if MCP confirms state is valid, proceed with fast-tracking through `completed_steps`
  - [x] 2.4 Add failure path for invalid state: inform bootcamper the checkpoint is outdated/invalid, offer to restart the mapping
  - [x] 2.5 Add failure path for corrupted JSON: inform bootcamper the checkpoint file is corrupted and cannot be read, offer to restart
  - [x] 2.6 Add instruction to delete corrupted/invalid checkpoint files after informing the user
    - _Requirements: 4, 5, 6_

- [x] 3. Update agent-instructions.md State & Progress section
  - [x] 3.1 In `senzing-bootcamp/steering/agent-instructions.md`, modify the existing `mapping_workflow` bullet in the State & Progress section to append a cross-reference: "On session resume, `session-resume.md` detects these checkpoints and offers resume/restart/skip options with state validation via `mapping_workflow(action='status')`."
    - _Requirements: 7_

- [x] 4. Write unit tests for checkpoint resume content
  - [x] 4.1 Create `senzing-bootcamp/tests/test_mapping_checkpoint_resume.py` with imports (pathlib, re, pytest) and path constants pointing to `session-resume.md` and `agent-instructions.md`
  - [x] 4.2 Add `TestStep1CheckpointDetection` class: test that Step 1 mentions `mapping_state` file detection
  - [x] 4.3 Add `TestStep3ResumeOptions` class: test Step 3 contains mapping checkpoint display instructions, test Step 3 contains all three options (resume/restart/skip), test Step 3 mentions multiple data sources handling
  - [x] 4.4 Add `TestStep4Validation` class: test Step 4 contains `mapping_workflow` with `action='status'` reference, test Step 4 contains corrupted checkpoint handling, test Step 4 contains invalid state handling with restart offer
  - [x] 4.5 Add `TestAgentInstructionsCrossReference` class: test agent-instructions.md State & Progress section references session resume checkpoint behavior and `mapping_workflow(action='status')`
    - _Requirements: 8_

- [x] 5. Run tests and validate
  - [x] 5.1 Run `python3 -m pytest senzing-bootcamp/tests/test_mapping_checkpoint_resume.py -v` and verify all tests pass
  - [x] 5.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify modified markdown files pass CommonMark validation

## Notes

- Step 1 of `session-resume.md` already lists `config/mapping_state_*.json` as item 4 — no modification needed there
- Step 3 already has a paragraph about mapping checkpoints but lacks the explicit three-option offer
- Step 4 already has mapping checkpoint resume logic but lacks explicit MCP validation and error handling
- Tests follow the existing pattern in `test_session_resume_behavioral_rules_unit.py` — reading steering files and asserting content presence
- No new Python scripts are needed — this is purely steering file content and tests
- No Hypothesis/property-based tests needed — these are content-verification tests only
