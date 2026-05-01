# Requirements Document

## Introduction

Add property-based tests that validate structural invariants across all module steering files in the senzing-bootcamp power. Currently there is no automated check that every module has before/after framing, every step has a checkpoint, every 👉 question has a STOP instruction, and no steps combine multiple questions. A test suite using pytest and Hypothesis will catch regressions and enforce consistency across all module steering files.

## Glossary

- **Module_Steering_File**: A Markdown file in `senzing-bootcamp/steering/` whose filename matches the pattern `module-NN-*.md` (root module files) or `module-NN-phase*.md` (phase sub-files). These files contain the step-by-step workflows that guide bootcampers through each module.
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps module numbers to their steering file paths and phase sub-files.
- **Before_After_Framing**: A section in a Module_Steering_File that begins with `**Before/After**:` and describes what the bootcamper has before the module and what they will have after completing it.
- **Numbered_Step**: A line in a Module_Steering_File that starts with a number followed by a period and bold text (e.g., `1. **Step title**`), representing a discrete workflow step.
- **Checkpoint_Instruction**: A line in a Module_Steering_File that contains `**Checkpoint:**` followed by a reference to writing a step number to `config/bootcamp_progress.json`.
- **Pointing_Question**: A line in a Module_Steering_File that contains the 👉 emoji followed by a quoted question, indicating a question that requires the bootcamper's response before proceeding.
- **Stop_Instruction**: A line in a Module_Steering_File that contains `STOP` or `WAIT` as a directive to halt and wait for the bootcamper's response. Typically phrased as "STOP and wait" or "WAIT for response."
- **Prerequisites_Section**: A section in a Module_Steering_File that lists the modules or conditions that must be completed before starting the current module. Identified by the keyword `Prerequisites` followed by a colon.
- **YAML_Frontmatter**: A block at the top of a steering file delimited by `---` lines, containing YAML key-value pairs including the `inclusion` field.
- **Test_Suite**: The pytest and Hypothesis test file at `senzing-bootcamp/tests/test_steering_structure_properties.py` that validates structural invariants.
- **Validator**: The Test_Suite component that reads Module_Steering_Files and checks structural properties.

## Requirements

### Requirement 1: Before/After Framing Presence

**User Story:** As a power maintainer, I want every module steering file to have a before/after framing section, so that bootcampers always know what they have now and what they will have when the module is done.

#### Acceptance Criteria

1. WHEN a Module_Steering_File is parsed, THE Validator SHALL detect the presence of a Before_After_Framing section by searching for a line containing `**Before/After**`
2. IF a Module_Steering_File lacks a Before_After_Framing section, THEN THE Validator SHALL report a failure identifying the file path
3. FOR ALL Module_Steering_Files listed in the Steering_Index (root files and phase sub-files that contain numbered steps), THE Validator SHALL verify that each file either contains a Before_After_Framing section or is a phase sub-file whose root module file contains the Before_After_Framing section

### Requirement 2: Step-Checkpoint Correspondence

**User Story:** As a power maintainer, I want every numbered step to have a corresponding checkpoint instruction, so that bootcamper progress is always persisted and resumable.

#### Acceptance Criteria

1. WHEN a Module_Steering_File containing Numbered_Steps is parsed, THE Validator SHALL extract all step numbers from the file
2. WHEN a Module_Steering_File containing Numbered_Steps is parsed, THE Validator SHALL extract all Checkpoint_Instructions and their associated step numbers from the file
3. IF a Numbered_Step has no corresponding Checkpoint_Instruction with a matching step number before the next Numbered_Step or end of file, THEN THE Validator SHALL report a failure identifying the file path and step number
4. FOR ALL Module_Steering_Files in the Steering_Index that contain Numbered_Steps, THE Validator SHALL verify that every Numbered_Step has a corresponding Checkpoint_Instruction

### Requirement 3: Pointing Question Followed by Stop Instruction

**User Story:** As a power maintainer, I want every 👉 question to be followed by a STOP or WAIT instruction, so that the agent always pauses for the bootcamper's response instead of proceeding autonomously.

#### Acceptance Criteria

1. WHEN a Module_Steering_File containing Pointing_Questions is parsed, THE Validator SHALL locate each Pointing_Question line
2. WHEN a Pointing_Question is found, THE Validator SHALL search subsequent non-blank lines (up to 5 lines or the next Numbered_Step, whichever comes first) for a Stop_Instruction containing `STOP` or `WAIT`
3. IF a Pointing_Question has no Stop_Instruction within the search window, THEN THE Validator SHALL report a failure identifying the file path and the line number of the Pointing_Question
4. FOR ALL Module_Steering_Files in the Steering_Index, THE Validator SHALL verify that every Pointing_Question is followed by a Stop_Instruction

### Requirement 4: Single Question Per Step

**User Story:** As a power maintainer, I want no step to combine multiple 👉 questions, so that the agent asks one question at a time and waits for each response before continuing.

#### Acceptance Criteria

1. WHEN a Module_Steering_File is parsed, THE Validator SHALL group Pointing_Questions by the Numbered_Step they belong to (a Pointing_Question belongs to the most recent preceding Numbered_Step)
2. IF a Numbered_Step contains more than one Pointing_Question, THEN THE Validator SHALL report a failure identifying the file path, the step number, and the count of Pointing_Questions found
3. FOR ALL Module_Steering_Files in the Steering_Index that contain Numbered_Steps, THE Validator SHALL verify that each Numbered_Step contains at most one Pointing_Question

### Requirement 5: Prerequisites Listed

**User Story:** As a power maintainer, I want every module steering file to list its prerequisites, so that the agent and bootcamper know what must be completed before starting a module.

#### Acceptance Criteria

1. WHEN a Module_Steering_File is parsed, THE Validator SHALL detect the presence of a Prerequisites_Section by searching for a line containing `Prerequisites` followed by a colon
2. IF a root Module_Steering_File lacks a Prerequisites_Section, THEN THE Validator SHALL report a failure identifying the file path
3. FOR ALL root Module_Steering_Files listed in the Steering_Index, THE Validator SHALL verify that each file contains a Prerequisites_Section

### Requirement 6: YAML Frontmatter with Manual Inclusion

**User Story:** As a power maintainer, I want every module steering file to have YAML frontmatter with `inclusion: manual`, so that module files are only loaded on demand and do not consume context budget unnecessarily.

#### Acceptance Criteria

1. WHEN a Module_Steering_File is parsed, THE Validator SHALL extract the YAML_Frontmatter block delimited by `---` lines at the top of the file
2. IF a Module_Steering_File lacks a YAML_Frontmatter block, THEN THE Validator SHALL report a failure identifying the file path
3. WHEN a YAML_Frontmatter block is present, THE Validator SHALL verify that it contains an `inclusion` key with the value `manual`
4. IF the `inclusion` key is missing or has a value other than `manual`, THEN THE Validator SHALL report a failure identifying the file path and the actual inclusion value found
5. FOR ALL Module_Steering_Files listed in the Steering_Index (root files and phase sub-files), THE Validator SHALL verify YAML_Frontmatter compliance

### Requirement 7: Hypothesis-Based Property Test Structure

**User Story:** As a power maintainer, I want the structural validation tests to use Hypothesis to generate module numbers and verify properties across all modules, so that the test suite is robust and exercises the validation logic with generated inputs.

#### Acceptance Criteria

1. THE Test_Suite SHALL use a Hypothesis strategy that draws module numbers from the set of modules defined in the Steering_Index
2. THE Test_Suite SHALL resolve each drawn module number to its corresponding Module_Steering_File paths (root file and any phase sub-files) using the Steering_Index
3. WHEN a module number is drawn, THE Test_Suite SHALL read the corresponding Module_Steering_Files from disk and apply the structural validation checks from Requirements 1 through 6
4. THE Test_Suite SHALL use `@settings(max_examples=100)` for each property test
5. THE Test_Suite SHALL be located at `senzing-bootcamp/tests/test_steering_structure_properties.py`

### Requirement 8: Steering Index as Source of Truth

**User Story:** As a power maintainer, I want the test suite to use the steering index as the authoritative source for which files to validate, so that new modules are automatically covered without updating the test file.

#### Acceptance Criteria

1. THE Test_Suite SHALL parse the Steering_Index at `senzing-bootcamp/steering/steering-index.yaml` to discover all module numbers and their associated file paths
2. WHEN the Steering_Index maps a module number to a simple filename string, THE Test_Suite SHALL treat that filename as the sole Module_Steering_File for that module
3. WHEN the Steering_Index maps a module number to an object with a `root` key and a `phases` map, THE Test_Suite SHALL collect the root file and all phase sub-files as Module_Steering_Files for that module
4. IF a file listed in the Steering_Index does not exist on disk, THEN THE Test_Suite SHALL report a clear error rather than silently skipping the module
