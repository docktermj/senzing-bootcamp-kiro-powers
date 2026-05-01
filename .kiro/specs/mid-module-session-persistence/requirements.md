# Requirements Document

## Introduction

The senzing-bootcamp currently tracks progress at the whole-step level: `current_step` in `config/bootcamp_progress.json` stores an integer representing the last completed numbered step in a module steering file. This works well for short steps, but long multi-part steps — particularly the mapping workflow in Module 5 — can span an entire session. If a bootcamper stops mid-step, the progress file has no record of where they were within that step, and the mapping workflow checkpoint (`config/mapping_state_[datasource].json`) is not consistently tied to the progress file's step tracking.

This feature extends `current_step` to support sub-step identifiers (e.g., `"5.3"` for Module 5 step 3, or `"7a"` for a lettered sub-step), saves mapping workflow checkpoints after each mapping step, and updates the session-resume and agent-instructions steering files to detect and resume from sub-step positions. Backward compatibility with existing progress files that use integer `current_step` values is preserved.

## Glossary

- **Progress_File**: The JSON file at `config/bootcamp_progress.json` that stores completed modules, current module, current step, step history, data sources, and database type.
- **Sub_Step_Identifier**: A string value for `current_step` that encodes both a parent step number and a position within that step. Formats include dotted notation (e.g., `"5.3"` meaning step 5, sub-step 3) and lettered notation (e.g., `"7a"` meaning step 7, sub-step a). Integer values remain valid for whole-step checkpoints.
- **Mapping_Checkpoint**: A JSON file at `config/mapping_state_[datasource].json` that captures the in-progress state of a `mapping_workflow` invocation for a specific data source, including completed mapping steps, field mapping decisions, and a timestamp.
- **Progress_Utils**: The Python module at `senzing-bootcamp/scripts/progress_utils.py` that provides `write_checkpoint`, `clear_step`, and `validate_progress_schema` functions for reading and writing the Progress_File.
- **Session_Resume**: The steering file at `senzing-bootcamp/steering/session-resume.md` that defines the workflow for resuming a bootcamp session from saved state.
- **Agent_Instructions**: The steering file at `senzing-bootcamp/steering/agent-instructions.md` that defines core agent rules including state management, checkpointing, and file placement.
- **Module_Transitions**: The steering file at `senzing-bootcamp/steering/module-transitions.md` that defines journey map display and checkpoint emission rules.
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps module numbers to steering file paths, phases, and step ranges.
- **Phase_Loading_Guide**: The steering file at `senzing-bootcamp/steering/phase-loading-guide.md` that defines how split-module phases are loaded based on `current_step`.
- **Validator**: The `validate_progress_schema` function in Progress_Utils that checks the Progress_File against the expected schema.

## Requirements

### Requirement 1: Extend current_step to Support Sub-Step Identifiers

**User Story:** As a power maintainer, I want `current_step` in the Progress_File to accept sub-step identifiers in addition to integers, so that the agent can record exactly where a bootcamper stopped within a long multi-part step.

#### Acceptance Criteria

1. THE Progress_Utils `write_checkpoint` function SHALL accept a `step` parameter of type `int`, `float`, or `str` to represent whole steps (e.g., `5`), dotted sub-steps (e.g., `"5.3"`), and lettered sub-steps (e.g., `"7a"`)
2. WHEN `write_checkpoint` is called with a Sub_Step_Identifier, THE Progress_Utils SHALL write the identifier as a string value for `current_step` in the Progress_File
3. WHEN `write_checkpoint` is called with an integer step, THE Progress_Utils SHALL write the value as an integer for `current_step` in the Progress_File to preserve backward compatibility
4. THE Progress_Utils `write_checkpoint` function SHALL update `step_history[<module>].last_completed_step` to match the `current_step` value (integer or string) and set `updated_at` to the current ISO 8601 UTC timestamp

### Requirement 2: Validate Sub-Step Identifiers in Progress Schema

**User Story:** As a power maintainer, I want the schema validator to accept sub-step identifiers in `current_step` and `step_history`, so that extended progress files pass validation without errors.

#### Acceptance Criteria

1. THE Validator SHALL accept `current_step` values of type `int`, `str`, or `null`
2. WHEN `current_step` is a string, THE Validator SHALL verify it matches one of the recognized Sub_Step_Identifier formats: dotted notation matching the pattern `<digits>.<digits>` (e.g., `"5.3"`) or lettered notation matching the pattern `<digits><letter>` (e.g., `"7a"`)
3. IF `current_step` is a string that does not match any recognized Sub_Step_Identifier format, THEN THE Validator SHALL return a descriptive error
4. THE Validator SHALL accept `step_history[<module>].last_completed_step` values of type `int` or `str`, applying the same Sub_Step_Identifier format rules as for `current_step`
5. WHEN a Progress_File contains only integer `current_step` and integer `last_completed_step` values, THE Validator SHALL report zero errors (backward compatibility)

### Requirement 3: Save Mapping Workflow Checkpoints After Each Mapping Step

**User Story:** As a bootcamper, I want the mapping workflow state to be saved after each mapping step, so that if my session ends mid-mapping I can resume from the last completed mapping step instead of restarting the entire mapping workflow.

#### Acceptance Criteria

1. WHEN a `mapping_workflow` step completes for a data source, THE Agent SHALL write a Mapping_Checkpoint to `config/mapping_state_[datasource].json` containing the data source name, source file path, current mapping step number, list of completed mapping step names, field mapping decisions made so far, and an ISO 8601 UTC timestamp
2. THE Mapping_Checkpoint SHALL be written after every mapping step completion, not only at the end of the full mapping workflow
3. WHEN the full mapping workflow completes for a data source, THE Agent SHALL delete the corresponding Mapping_Checkpoint file
4. THE Agent_Instructions SHALL document the checkpoint-after-each-mapping-step rule in the "State & Progress" section

### Requirement 4: Detect and Load Mapping Checkpoints on Session Resume

**User Story:** As a bootcamper, I want the session resume workflow to detect my in-progress mapping checkpoints and continue from where I left off, so that I do not lose mapping decisions made in a previous session.

#### Acceptance Criteria

1. WHEN the Session_Resume workflow reads state files in Step 1, THE Agent SHALL scan for `config/mapping_state_*.json` files and parse each one to extract the data source name, current mapping step, and completed mapping steps
2. WHEN mapping checkpoints are found, THE Session_Resume Step 3 summary SHALL include the data source name and the list of completed mapping steps for each in-progress mapping
3. WHEN the bootcamper chooses to continue and mapping checkpoints exist, THE Agent SHALL restart `mapping_workflow` and fast-track through completed mapping steps before resuming from the first incomplete mapping step
4. IF a Mapping_Checkpoint file contains invalid JSON or missing required fields, THEN THE Agent SHALL log a warning, skip the corrupted checkpoint, and inform the bootcamper that the mapping for that data source will need to restart

### Requirement 5: Update Session Resume for Sub-Step Resumption

**User Story:** As a bootcamper, I want the session resume workflow to understand sub-step identifiers, so that I resume at the exact sub-step position rather than repeating the entire parent step.

#### Acceptance Criteria

1. WHEN `current_step` in the Progress_File is a Sub_Step_Identifier, THE Session_Resume Step 3 summary SHALL display the sub-step position (e.g., "Step 5.3 of 12" or "Step 7a of 10") instead of only the parent step number
2. WHEN `current_step` is a Sub_Step_Identifier, THE Session_Resume Step 4 SHALL instruct the agent to skip to the next sub-step after the recorded position rather than skipping to the next whole step
3. WHEN `current_step` is a Sub_Step_Identifier and the current module is a split module, THE Phase_Loading_Guide SHALL use the parent step number from the Sub_Step_Identifier to determine which phase sub-file to load
4. IF `current_step` is a Sub_Step_Identifier that references a sub-step not found in the module steering file, THEN THE Agent SHALL log a warning and fall back to resuming at the parent step number

### Requirement 6: Update Agent Instructions for Sub-Step Checkpointing

**User Story:** As a power maintainer, I want the agent instructions to document the sub-step checkpointing pattern, so that the agent knows when and how to write sub-step checkpoints during long multi-part steps.

#### Acceptance Criteria

1. THE Agent_Instructions "State & Progress" section SHALL document that `current_step` accepts both integer values (whole steps) and string Sub_Step_Identifiers (dotted or lettered notation)
2. THE Agent_Instructions SHALL instruct the agent to write a sub-step checkpoint after completing each sub-step within a multi-part step, using the Sub_Step_Identifier format defined in the module steering file
3. THE Agent_Instructions SHALL instruct the agent to write a mapping checkpoint to `config/mapping_state_[datasource].json` after each `mapping_workflow` step, not only at workflow completion
4. THE Module_Transitions checkpoint emission rule SHALL reference that sub-step checkpoints follow the same emission pattern as whole-step checkpoints

### Requirement 7: Update Module Transitions for Sub-Step Display

**User Story:** As a bootcamper, I want the journey map to show my sub-step position within the current module, so that I can see exactly where I am in a long workflow.

#### Acceptance Criteria

1. WHEN `current_step` in the Progress_File is a Sub_Step_Identifier, THE Module_Transitions journey map SHALL display the sub-step in the status column (e.g., "🔄 Current — Step 5.3/26")
2. WHEN `current_step` is an integer, THE Module_Transitions journey map SHALL continue to display the existing format (e.g., "🔄 Current — Step 5/26")

### Requirement 8: Preserve Backward Compatibility with Existing Progress Files

**User Story:** As a power maintainer, I want existing progress files with integer `current_step` values to continue working without modification, so that in-progress bootcamps are not disrupted by this change.

#### Acceptance Criteria

1. WHEN the Progress_File contains an integer `current_step`, THE Progress_Utils, Session_Resume, Module_Transitions, and Phase_Loading_Guide SHALL handle the value identically to their current behavior
2. WHEN the Progress_File contains no `current_step` field, THE Session_Resume SHALL fall back to artifact scanning to determine the resume point, matching current behavior
3. WHEN the Progress_File contains `step_history` entries with integer `last_completed_step` values, THE Validator SHALL report zero errors
4. THE `repair_progress.py` script SHALL continue to produce integer `current_step` values when reconstructing progress from artifacts, since artifact scanning cannot determine sub-step positions

### Requirement 9: Property-Based Test for Sub-Step Identifier Validation

**User Story:** As a power maintainer, I want property-based tests that verify the schema validator correctly handles all sub-step identifier formats, so that regressions in validation logic are caught automatically.

#### Acceptance Criteria

1. THE Test_Suite SHALL use a Hypothesis strategy that generates valid Sub_Step_Identifiers in dotted notation (`<digits>.<digits>`) and lettered notation (`<digits><letter>`) alongside plain integers
2. WHEN a valid Sub_Step_Identifier is generated, THE Test_Suite SHALL verify that `validate_progress_schema` returns zero errors for a Progress_File containing that identifier as `current_step`
3. THE Test_Suite SHALL use a Hypothesis strategy that generates invalid `current_step` values (empty strings, strings with no digits, negative numbers, nested objects) and verify that `validate_progress_schema` returns at least one error for each
4. THE Test_Suite SHALL use `@settings(max_examples=100)` for each property test
5. THE Test_Suite SHALL be located at `senzing-bootcamp/tests/test_sub_step_validation_properties.py`

### Requirement 10: Property-Based Test for Sub-Step Checkpoint Round-Trip

**User Story:** As a power maintainer, I want a property-based test that verifies writing a sub-step checkpoint and reading it back produces the same value, so that no data is lost during checkpoint serialization.

#### Acceptance Criteria

1. THE Test_Suite SHALL use a Hypothesis strategy that generates random (module_number, sub_step_identifier) pairs where the sub-step identifier is an integer, dotted string, or lettered string
2. WHEN `write_checkpoint` is called with a generated pair, THE Test_Suite SHALL read the Progress_File back and verify that `current_step` equals the written sub-step identifier (type-preserving: integers remain integers, strings remain strings)
3. THE Test_Suite SHALL verify that `step_history[<module>].last_completed_step` matches the written sub-step identifier
4. THE Test_Suite SHALL verify that `step_history[<module>].updated_at` is a valid ISO 8601 datetime string
5. THE Test_Suite SHALL use `@settings(max_examples=100)` for each property test
6. THE Test_Suite SHALL be located at `senzing-bootcamp/tests/test_sub_step_checkpoint_properties.py`

### Requirement 11: Property-Based Test for Backward Compatibility

**User Story:** As a power maintainer, I want a property-based test that verifies legacy progress files (integer-only steps, no sub-step fields) continue to pass validation after the schema changes, so that existing bootcamps are not broken.

#### Acceptance Criteria

1. THE Test_Suite SHALL use a Hypothesis strategy that generates legacy Progress_File dicts containing only integer `current_step` values (or null), integer `last_completed_step` values in `step_history`, and no Sub_Step_Identifier strings
2. WHEN a legacy Progress_File dict is generated, THE Test_Suite SHALL verify that `validate_progress_schema` returns zero errors
3. THE Test_Suite SHALL verify that `write_checkpoint` called with an integer step produces a Progress_File that passes `validate_progress_schema`
4. THE Test_Suite SHALL use `@settings(max_examples=100)` for each property test
5. THE Test_Suite SHALL be located at `senzing-bootcamp/tests/test_sub_step_backward_compat_properties.py`
