# Requirements Document

## Introduction

No automated tests verify that all module steering files follow the banner → journey map → before/after transition pattern defined in `module-transitions.md`. This spec adds property-based tests using pytest and Hypothesis that validate three structural invariants across every module steering file: (1) a reference to `module-transitions.md` in the opening instructions, (2) a `**Before/After**` section, and (3) a success indicator at the module's end. The steering index at `senzing-bootcamp/steering/steering-index.yaml` serves as the authoritative source for which modules exist and which files belong to each module.

## Glossary

- **Module_Steering_File**: A Markdown file in `senzing-bootcamp/steering/` whose filename matches the pattern `module-NN-*.md`. These files contain the step-by-step workflows that guide bootcampers through each module.
- **Root_Module_File**: The top-level steering file for a module, identified by the `root` key in a multi-phase Steering_Index entry or as the sole filename string in a single-file entry. Every module has exactly one Root_Module_File.
- **Phase_Sub_File**: A steering file that covers one phase of a multi-phase module. Listed under the `phases` map in the Steering_Index entry for that module.
- **Last_Phase_Sub_File**: The Phase_Sub_File whose `step_range` ends with the highest step number among all phases for a given module. For single-file modules, the Root_Module_File is also the Last_Phase_Sub_File.
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps module numbers to their steering file paths and phase sub-files under the top-level `modules` key.
- **Transition_Reference**: A line in a Root_Module_File that contains the string `module-transitions.md`, indicating the module instructs the agent to follow the transition protocol (display banner, journey map, and before/after framing).
- **Before_After_Section**: A line in a Root_Module_File that contains the string `**Before/After**`, describing what the bootcamper has before the module and what they will have after completing it.
- **Success_Indicator**: A line in a Module_Steering_File that contains `**Success` (bold "Success" label) or the ✅ emoji used as a completion marker, signaling the module's success criteria or completion state. Located in the Root_Module_File for single-file modules or in the Last_Phase_Sub_File for multi-phase modules.
- **Test_Suite**: The pytest and Hypothesis test file at `senzing-bootcamp/tests/test_module_transition_properties.py` that validates transition-pattern invariants.
- **Validator**: The Test_Suite component that reads Module_Steering_Files and checks transition-pattern properties.

## Requirements

### Requirement 1: Transition Reference in Root Module Files

**User Story:** As a power maintainer, I want every root module steering file to reference `module-transitions.md` in its opening instructions, so that the agent always follows the banner → journey map → before/after transition protocol when starting a module.

#### Acceptance Criteria

1. WHEN a Root_Module_File is parsed, THE Validator SHALL search the file content for a line containing the string `module-transitions.md`
2. IF a Root_Module_File does not contain a line with `module-transitions.md`, THEN THE Validator SHALL report a failure identifying the module number and file path
3. FOR ALL Root_Module_Files listed in the Steering_Index, THE Validator SHALL verify that each file contains a Transition_Reference

### Requirement 2: Before/After Section in Root Module Files

**User Story:** As a power maintainer, I want every root module steering file to have a before/after section, so that bootcampers always know what they have now and what they will have when the module is done.

#### Acceptance Criteria

1. WHEN a Root_Module_File is parsed, THE Validator SHALL search the file content for a line containing the string `**Before/After**`
2. IF a Root_Module_File does not contain a line with `**Before/After**`, THEN THE Validator SHALL report a failure identifying the module number and file path
3. FOR ALL Root_Module_Files listed in the Steering_Index, THE Validator SHALL verify that each file contains a Before_After_Section

### Requirement 3: Success Indicator at Module End

**User Story:** As a power maintainer, I want every module to have a success indicator at its end, so that the agent and bootcamper have clear criteria for when the module is complete.

#### Acceptance Criteria

1. WHEN a single-file module is parsed, THE Validator SHALL search the Root_Module_File for a line containing `**Success` or the ✅ emoji
2. WHEN a multi-phase module is parsed, THE Validator SHALL identify the Last_Phase_Sub_File and search that file for a line containing `**Success` or the ✅ emoji
3. IF neither the Root_Module_File (for single-file modules) nor the Last_Phase_Sub_File (for multi-phase modules) contains a Success_Indicator, THEN THE Validator SHALL report a failure identifying the module number and the file path searched
4. FOR ALL modules listed in the Steering_Index, THE Validator SHALL verify that each module has a Success_Indicator in the appropriate file

### Requirement 4: Hypothesis-Based Module Number Generation

**User Story:** As a power maintainer, I want the transition validation tests to use Hypothesis to generate module numbers from the steering index, so that the test suite exercises validation logic with generated inputs and automatically covers new modules as they are added.

#### Acceptance Criteria

1. THE Test_Suite SHALL use a Hypothesis strategy that draws module numbers from the set of modules defined in the Steering_Index `modules` key
2. THE Test_Suite SHALL resolve each drawn module number to its Root_Module_File path and any Phase_Sub_File paths using the Steering_Index
3. WHEN a module number is drawn, THE Test_Suite SHALL read the corresponding files from disk and apply the transition-pattern checks from Requirements 1 through 3
4. THE Test_Suite SHALL use `@settings(max_examples=100)` for each property test
5. THE Test_Suite SHALL prefix custom Hypothesis strategies with `st_` (e.g., `st_module_number`)

### Requirement 5: Steering Index as Source of Truth

**User Story:** As a power maintainer, I want the test suite to use the steering index as the authoritative source for which modules to validate, so that new modules are automatically covered without updating the test file.

#### Acceptance Criteria

1. THE Test_Suite SHALL parse the Steering_Index at `senzing-bootcamp/steering/steering-index.yaml` to discover all module numbers and their associated file paths
2. WHEN the Steering_Index maps a module number to a simple filename string, THE Test_Suite SHALL treat that filename as both the Root_Module_File and the Last_Phase_Sub_File for that module
3. WHEN the Steering_Index maps a module number to an object with a `root` key and a `phases` map, THE Test_Suite SHALL use the `root` value as the Root_Module_File and determine the Last_Phase_Sub_File from the phase with the highest ending step number in its `step_range`
4. IF a file listed in the Steering_Index does not exist on disk, THEN THE Test_Suite SHALL report a clear error identifying the missing file path rather than silently skipping the module

### Requirement 6: Test File Location and Structure

**User Story:** As a power maintainer, I want the transition validation tests to follow the project's established test conventions, so that the tests integrate cleanly with the existing test suite and CI pipeline.

#### Acceptance Criteria

1. THE Test_Suite SHALL be located at `senzing-bootcamp/tests/test_module_transition_properties.py`
2. THE Test_Suite SHALL use class-based test organization with a class named `TestModuleTransitionProperties`
3. THE Test_Suite SHALL document which requirements each property test validates using docstrings or comments referencing the requirement numbers
4. THE Test_Suite SHALL use a custom minimal YAML parser (no PyYAML dependency) to parse the Steering_Index, consistent with the project convention for test files
