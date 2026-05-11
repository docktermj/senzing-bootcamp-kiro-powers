# Requirements Document

## Introduction

This feature adds an end-to-end integration test that simulates a complete bootcamp run through each of the three tracks (Quick Demo, Core Bootcamp, Advanced Topics). The test validates that module transitions, gate conditions, prerequisite enforcement, progress state management, steering file resolution, and phase transitions all work correctly when exercised as a cohesive flow — filling the gap between the existing 1,577 unit/property tests and real user experience.

## Glossary

- **Test_Runner**: The pytest-based integration test suite that orchestrates simulated bootcamp flows
- **Progress_Tracker**: The component that reads and writes `bootcamp_progress.json` to record module completion state
- **Gate_Evaluator**: The logic that checks gate conditions defined in `module-dependencies.yaml` before allowing module transitions
- **Steering_Resolver**: The component that maps a module number and phase to the correct steering file using `steering-index.yaml`
- **Module_Validator**: The `validate_module.py` script that checks whether a module's artifacts are present on disk
- **Track**: A named sequence of modules (Quick Demo, Core Bootcamp, or Advanced Topics) defined in `module-dependencies.yaml`
- **Phase**: A sub-division within a multi-phase module, each with its own steering file and step range
- **Skip_Condition**: A condition defined per module in `module-dependencies.yaml` under `skip_if` that allows bypassing a module

## Requirements

### Requirement 1: Track-Level End-to-End Flow

**User Story:** As a power maintainer, I want an integration test that walks through every module in each track sequentially, so that I can verify the entire bootcamp flow works without regressions.

#### Acceptance Criteria

1. WHEN the Quick Demo track is executed, THE Test_Runner SHALL validate modules 2 and 3 in sequence, confirming each module's validator passes after artifacts are created
2. WHEN the Core Bootcamp track is executed, THE Test_Runner SHALL validate modules 1, 2, 3, 4, 5, 6, and 7 in sequence, confirming each module's validator passes after artifacts are created
3. WHEN the Advanced Topics track is executed, THE Test_Runner SHALL validate modules 1 through 11 in sequence, confirming each module's validator passes after artifacts are created
4. THE Test_Runner SHALL read track definitions from `module-dependencies.yaml` rather than hardcoding module lists

### Requirement 2: Prerequisite Enforcement

**User Story:** As a power maintainer, I want the test to verify that module prerequisites block progression when unsatisfied, so that I can be confident the bootcamp never allows skipping required work.

#### Acceptance Criteria

1. WHEN a module's prerequisites (as defined in `module-dependencies.yaml`) are not satisfied, THE Test_Runner SHALL confirm that the Module_Validator reports failure for that module
2. WHEN all prerequisites for a module are satisfied, THE Test_Runner SHALL confirm that the Module_Validator reports success for that module
3. FOR ALL modules with non-empty `requires` lists, THE Test_Runner SHALL verify that attempting validation without prerequisite artifacts produces at least one failure

### Requirement 3: Gate Condition Verification

**User Story:** As a power maintainer, I want the test to verify that gate conditions between modules are enforced, so that I can ensure transitions only happen when the prior module's work is complete.

#### Acceptance Criteria

1. WHEN a gate transition (e.g., "5->6") is evaluated, THE Gate_Evaluator SHALL check that the source module's artifacts exist before allowing the transition
2. THE Test_Runner SHALL verify every gate defined in `module-dependencies.yaml` by simulating the transition with and without required artifacts
3. IF a gate's requirements are not met, THEN THE Gate_Evaluator SHALL report the transition as blocked

### Requirement 4: Progress State Management

**User Story:** As a power maintainer, I want the test to verify that progress state is correctly updated at each module transition, so that I can trust the bootcamp accurately tracks where the user is.

#### Acceptance Criteria

1. WHEN a module is completed, THE Progress_Tracker SHALL add the module number to `modules_completed` in `bootcamp_progress.json`
2. WHEN a module transition occurs, THE Progress_Tracker SHALL update `current_module` to the next module in the track
3. WHEN a module transition occurs, THE Progress_Tracker SHALL reset `current_step` to 1
4. THE Test_Runner SHALL verify that after completing all modules in a track, the `modules_completed` list contains exactly the modules in that track
5. FOR ALL valid progress states, writing then reading `bootcamp_progress.json` SHALL produce an identical object (round-trip property)

### Requirement 5: Steering File Resolution

**User Story:** As a power maintainer, I want the test to verify that the correct steering file is loaded for each module and phase, so that I can ensure users always see the right instructions.

#### Acceptance Criteria

1. WHEN a single-phase module is active, THE Steering_Resolver SHALL return the file path specified in `steering-index.yaml` for that module
2. WHEN a multi-phase module is active and a phase is specified, THE Steering_Resolver SHALL return the file path for that specific phase
3. THE Test_Runner SHALL verify that every steering file referenced in `steering-index.yaml` exists on disk
4. FOR ALL modules defined in `steering-index.yaml`, THE Steering_Resolver SHALL return a non-empty file path

### Requirement 6: Phase Transitions Within Multi-Phase Modules

**User Story:** As a power maintainer, I want the test to verify that phase transitions within multi-phase modules work correctly, so that I can ensure users progress through sub-steps in the right order.

#### Acceptance Criteria

1. WHEN a multi-phase module is active, THE Test_Runner SHALL verify that phases are traversed in the order defined in `steering-index.yaml`
2. WHEN a phase transition occurs within a module, THE Steering_Resolver SHALL return the next phase's steering file
3. THE Test_Runner SHALL verify that step ranges across phases within a module are contiguous and non-overlapping
4. FOR ALL multi-phase modules (1, 5, 6, 8, 9, 10, 11), THE Test_Runner SHALL verify that all defined phases have valid steering file references

### Requirement 7: Skip Condition Evaluation

**User Story:** As a power maintainer, I want the test to verify that skip conditions are properly evaluated, so that I can ensure modules can be bypassed when appropriate without breaking the flow.

#### Acceptance Criteria

1. WHEN a module's `skip_if` condition is non-null and the skip is applied, THE Test_Runner SHALL verify that the track can proceed to the next module without completing the skipped module's artifacts
2. WHEN a module's `skip_if` condition is null, THE Test_Runner SHALL verify that the module cannot be bypassed
3. THE Test_Runner SHALL verify that skipping a module does not break prerequisite chains for downstream modules
4. FOR ALL modules with non-null `skip_if` values, THE Test_Runner SHALL simulate both the skipped and non-skipped paths

### Requirement 8: Configuration-Driven Test Design

**User Story:** As a power maintainer, I want the test to derive all expectations from YAML configuration files rather than hardcoded values, so that the test remains correct as the bootcamp evolves.

#### Acceptance Criteria

1. THE Test_Runner SHALL parse `module-dependencies.yaml` to determine track compositions, prerequisites, gates, and skip conditions
2. THE Test_Runner SHALL parse `steering-index.yaml` to determine module-to-file mappings and phase structures
3. WHEN `module-dependencies.yaml` is updated with a new module or gate, THE Test_Runner SHALL automatically cover the new configuration without code changes
4. IF `module-dependencies.yaml` or `steering-index.yaml` cannot be parsed, THEN THE Test_Runner SHALL fail with a descriptive error message
