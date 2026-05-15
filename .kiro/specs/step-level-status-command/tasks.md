# Implementation Plan: Step-Level Status Command

## Overview

Add a `--step` flag to `senzing-bootcamp/scripts/status.py` that displays step-level progress within the current module. The implementation adds two new functions (`_show_step_detail` and `_get_module_total_steps`), integrates the flag into the existing CLI, and updates documentation. All code is Python 3.11+ stdlib-only.

## Tasks

- [x] 1. Implement steering-index parsing and step detail functions
  - [x] 1.1 Add `_get_module_total_steps` function to `scripts/status.py`
    - Implement a function that reads `steering/steering-index.yaml` as text
    - Use regex/line-by-line parsing to extract `step_range` values for a given module number
    - Return the maximum upper-bound across all phases, or `None` for modules without phases (e.g., modules 4 and 7)
    - No PyYAML dependency — use stdlib regex parsing only
    - _Requirements: 3_

  - [x] 1.2 Add `_show_step_detail` function to `scripts/status.py`
    - Implement a function that takes `current_module`, `progress_data` dict, and `steering_index_path`
    - Look up `step_history[str(current_module)]` from progress data
    - Call `_get_module_total_steps` to get total step count
    - Format and print the step-detail section with proper edge-case handling:
      - No step history → "Not started"
      - `current_step` is `None` → "Between steps"
      - Sub-step identifiers (e.g., "5.3") → display as-is
      - Module without phases → omit "of Y" from format
      - Missing `updated_at` → omit timestamp line
    - Output format: "Module N: [Name] — Step X of Y completed" with optional active step and timestamp lines
    - _Requirements: 2, 3, 4, 5, 6_

  - [x] 1.3 Write property test for total steps extraction (Property 3)
    - **Property 3: Total steps extraction from steering-index**
    - For each module with phases in steering-index.yaml, verify `_get_module_total_steps` returns the maximum upper-bound of all `step_range` entries
    - For modules without phases (4, 7), verify it returns `None`
    - Use Hypothesis with `@settings(max_examples=20)`
    - **Validates: Requirements 3**

- [x] 2. Integrate `--step` flag into CLI and terminal output
  - [x] 2.1 Add `--step` argparse argument to `main()` in `scripts/status.py`
    - Add `parser.add_argument("--step", action="store_true", help="Show step-level progress for the current module")`
    - Pass `args.step` through to `_show_terminal_status`
    - _Requirements: 1_

  - [x] 2.2 Wire `_show_step_detail` into `_show_terminal_status`
    - After the existing terminal output (before "Quick Commands"), call `_show_step_detail` when `args.step` is True
    - Pass `current_module`, the raw progress data dict, and the path to `steering/steering-index.yaml`
    - Handle the case where no progress file exists (skip step detail section)
    - Preserve backward compatibility — existing output unchanged without `--step`
    - _Requirements: 1, 2, 7_

  - [x] 2.3 Write property test for step detail output format (Property 1)
    - **Property 1: Step detail output format correctness**
    - Generate random module numbers (1-11 with phases), random step values (int 1-max), random totals
    - Assert output contains "Module N: [Name] — Step X of Y completed"
    - Use Hypothesis with `@settings(max_examples=20)`
    - **Validates: Requirements 2, 3**

  - [x] 2.4 Write property test for active step and timestamp display (Property 2)
    - **Property 2: Active step and timestamp display**
    - Generate random `current_step` values (int, dotted sub-step, lettered sub-step, None)
    - Generate random valid ISO 8601 timestamps
    - Assert correct active step text and timestamp in output; null → "Between steps"
    - Use Hypothesis with `@settings(max_examples=20)`
    - **Validates: Requirements 4, 5, 6**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Write unit tests for the `--step` flag
  - [x] 4.1 Create `senzing-bootcamp/tests/test_status_step_detail.py` with unit tests
    - Test: `--step` flag accepted by argparse
    - Test: No progress file → step section skipped
    - Test: Empty step_history → "Not started"
    - Test: Valid step_history → correct format "Module N: [Name] — Step X of Y completed"
    - Test: `current_step` integer → "Active step: Step N"
    - Test: `current_step` sub-step "5.3" → "Active step: Step 5.3"
    - Test: `current_step` null → "Between steps"
    - Test: Module completed → step detail still shows last step
    - Test: Module without phases → "Step X completed" (no total)
    - Test: Timestamp displayed from `updated_at`
    - Follow existing pattern from `test_status_steps.py` (monkeypatch, tmp_path, StringIO capture)
    - _Requirements: 10_

- [x] 5. Update documentation
  - [x] 5.1 Update POWER.md "Useful Commands" section
    - Add `python3 senzing-bootcamp/scripts/status.py --step` with description to the Useful Commands section
    - _Requirements: 8_

  - [x] 5.2 Update `docs/guides/SCRIPT_REFERENCE.md`
    - Add `--step` to the status.py flags table with description: "Show step-level progress for the current module"
    - _Requirements: 9_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The design uses Python (matching the existing `status.py`), so no language selection was needed
- All code must be stdlib-only (no PyYAML) per project conventions
- Tests go in `senzing-bootcamp/tests/` following the existing `test_status_steps.py` pattern

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1"] },
    { "id": 3, "tasks": ["2.2"] },
    { "id": 4, "tasks": ["2.3", "2.4", "4.1"] },
    { "id": 5, "tasks": ["5.1", "5.2"] }
  ]
}
```
