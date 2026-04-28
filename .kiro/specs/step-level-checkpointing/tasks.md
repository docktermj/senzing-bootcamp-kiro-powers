# Tasks

## Task 1: Extend Progress File Schema and Add Checkpoint Utility

- [x] 1.1 Create a `write_checkpoint` helper function in a new `senzing-bootcamp/scripts/progress_utils.py` module that reads `config/bootcamp_progress.json`, updates `current_step` and `step_history[<module>]` with the given step number and ISO 8601 timestamp, and writes the file back. Include a `clear_step` function that sets `current_step` to `null` and retains `step_history` (for module completion).
- [x] 1.2 Create a `validate_progress_schema` function in `progress_utils.py` that validates a progress dict against the extended schema (checks types of `current_step`, `step_history` keys/values, ISO 8601 format of `updated_at`). Return a list of validation errors (empty list if valid).
- [x] 1.3 Add unit tests for `write_checkpoint`, `clear_step`, and `validate_progress_schema` in `senzing-bootcamp/scripts/test_progress_utils.py`. Cover: normal checkpoint write, module completion clearing, schema validation of valid and invalid inputs.

## Task 2: Update status.py for Step-Level Display

- [x] 2.1 Modify `main()` in `senzing-bootcamp/scripts/status.py` to read `current_step` from the progress file and display it alongside the current module (e.g., "Current Module: Module 5, Step 3") when present. When absent, display existing module-only format.
- [x] 2.2 Modify `sync_progress_tracker()` in `senzing-bootcamp/scripts/status.py` to include step-level progress in the generated `PROGRESS_TRACKER.md` for the current module when `current_step` is present.
- [x] 2.3 Add unit tests for status.py step display in `senzing-bootcamp/scripts/test_status_steps.py`. Test with progress files that have `current_step`, without `current_step`, and with edge cases (null, missing step_history).

## Task 3: Update repair_progress.py for Step Reconstruction

- [x] 3.1 Add step-level artifact detection to `repair_progress.py` — create a `detect_steps()` function that maps module-specific artifacts to approximate step numbers (e.g., Module 5: `docs/data_source_evaluation.md` → step 7, `src/transform/` files → step 11; Module 1: `docs/business_problem.md` → step 10; Module 12: `Dockerfile` → step 5).
- [x] 3.2 Modify `main()` in `repair_progress.py` to call `detect_steps()` and include step-level info in the scan report (without `--fix`) and populate `current_step` and `step_history` when running with `--fix`. Omit `current_step` when step cannot be determined.
- [x] 3.3 Add unit tests for step detection and repair output in `senzing-bootcamp/scripts/test_repair_steps.py`.

## Task 4: Update session-resume.md Steering File

- [x] 4.1 Modify Step 1 of `senzing-bootcamp/steering/session-resume.md` to read `current_step` and `step_history` from the progress file alongside existing fields.
- [x] 4.2 Modify Step 3 of `session-resume.md` to include step number in the welcome-back summary when `current_step` is present (e.g., "Current: Module 5 — Data Quality & Mapping, Step 3 of 12").
- [x] 4.3 Modify Step 4 of `session-resume.md` to instruct the agent to skip to step `current_step + 1` when `current_step` is present. Add fallback: if `current_step` references a non-existent step, log a warning and fall back to artifact scanning.

## Task 5: Update module-transitions.md Steering File

- [x] 5.1 Modify the Journey Map section of `senzing-bootcamp/steering/module-transitions.md` to display step info in the status column when `current_step` is present (e.g., "🔄 Current — Step 3/12"). When absent, display existing "🔄 Current" status.
- [x] 5.2 Modify the Step-Level Progress section to reference the checkpoint emission pattern and link to the progress file schema.

## Task 6: Update agent-instructions.md with Checkpoint Rule

- [x] 6.1 Add a checkpoint-emission rule to the "State & Progress" section of `senzing-bootcamp/steering/agent-instructions.md` instructing the agent to write a checkpoint to `bootcamp_progress.json` after completing each numbered step in any module steering file, and to clear `current_step` on module completion.

## Task 7: Add Checkpoint Emission Instructions to Module Steering Files

- [x] 7.1 Add checkpoint emission instructions to `module-01-business-problem.md` after each numbered step (steps 1-15). Use a consistent format: "**Checkpoint:** Write step N to `config/bootcamp_progress.json`."
- [x] 7.2 Add checkpoint emission instructions to `module-02-sdk-setup.md` through `module-06-single-source.md` after each numbered step.
- [x] 7.3 Add checkpoint emission instructions to `module-07-multi-source.md` through `module-12-deployment.md` after each numbered step.

## Task 8: Property-Based Tests

- [x] 8.1 Write property test for Property 1 (schema conformance): generate random valid progress states with hypothesis, serialize to JSON, validate against extended schema using `validate_progress_schema`. Tag: `Feature: step-level-checkpointing, Property 1: Progress file schema conformance`. Min 100 iterations.
- [x] 8.2 Write property test for Property 2 (module completion clears step): generate random progress states where a module is completed, verify `current_step` is null after `clear_step`. Tag: `Feature: step-level-checkpointing, Property 2: Module completion clears current step`. Min 100 iterations.
- [x] 8.3 Write property test for Property 3 (checkpoint write consistency): generate random (module, step) pairs, call `write_checkpoint`, verify `current_step` and `step_history` are consistent. Tag: `Feature: step-level-checkpointing, Property 3: Checkpoint write consistency`. Min 100 iterations.
- [x] 8.4 Write property test for Property 4 (backward compatibility): generate random legacy progress files (without step fields), run `validate_progress_schema` and verify no errors for the legacy subset. Tag: `Feature: step-level-checkpointing, Property 4: Backward compatibility`. Min 100 iterations.
- [x] 8.5 Write property test for Property 5 (step display in status output): generate random progress files with `current_step` set, capture status.py output, verify step number appears. Tag: `Feature: step-level-checkpointing, Property 5: Step display in status output`. Min 100 iterations.
