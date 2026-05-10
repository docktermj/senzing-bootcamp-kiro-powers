# Requirements Document

## Introduction

The senzing-bootcamp power has three manual steering workflow files (`.kiro/steering/add-new-module.md`, `.kiro/steering/add-new-script.md`, `.kiro/steering/validation-suite.md`) that reference project files by path but don't use Kiro's `#[[file:relative/path]]` syntax. Adding these references will give the agent automatic access to referenced file content when a workflow is activated, eliminating the need for separate file reads and keeping the agent grounded in source-of-truth documents.

## Glossary

- **Steering_File**: A Markdown file in `.kiro/steering/` with YAML frontmatter that provides workflow instructions to the Kiro agent
- **File_Reference**: A `#[[file:relative/path]]` annotation in a steering file that causes Kiro to automatically load the referenced file's content when the steering file is activated
- **Workflow_File**: A manual-inclusion steering file that defines a step-by-step procedure for a development task
- **Context_Budget**: The limited token window available to the agent; file references consume budget proportional to the referenced file's size
- **Power_Directory**: The `senzing-bootcamp/` directory containing all distributed power assets

## Requirements

### Requirement 1: Add file references to add-new-module workflow

**User Story:** As a developer activating the add-new-module workflow, I want the agent to automatically have access to the module dependency config and prerequisite table, so that it can correctly determine the next module number and update all required files without separate reads.

#### Acceptance Criteria

1. WHEN the add-new-module workflow is activated, THE Steering_File SHALL include a File_Reference to `senzing-bootcamp/config/module-dependencies.yaml`
2. WHEN the add-new-module workflow is activated, THE Steering_File SHALL include a File_Reference to `senzing-bootcamp/steering/module-prerequisites.md`
3. THE Steering_File SHALL NOT include a File_Reference to `senzing-bootcamp/scripts/lint_steering.py` because the script exceeds 1000 lines and would consume excessive Context_Budget
4. THE Steering_File SHALL NOT include a File_Reference to `senzing-bootcamp/steering/steering-index.yaml` because the file exceeds 400 lines and the agent only needs to know the update location, not the full content

### Requirement 2: Add file references to add-new-script workflow

**User Story:** As a developer activating the add-new-script workflow, I want the agent to automatically have access to the Python conventions guide, so that it can generate scripts conforming to project patterns without needing to separately read the conventions file.

#### Acceptance Criteria

1. WHEN the add-new-script workflow is activated, THE Steering_File SHALL include a File_Reference to `.kiro/steering/python-conventions.md`
2. THE Steering_File SHALL NOT include a File_Reference to `senzing-bootcamp/scripts/measure_steering.py` because the agent only needs to run the script, not read its implementation
3. THE Steering_File SHALL NOT include a File_Reference to `senzing-bootcamp/steering/steering-index.yaml` because the file exceeds 400 lines and the agent only needs to know the update location

### Requirement 3: Add file references to validation-suite workflow

**User Story:** As a developer activating the validation-suite workflow, I want the agent to have the commands and fix instructions readily available, so that it can run the suite and troubleshoot failures without needing to read individual script files.

#### Acceptance Criteria

1. THE Steering_File for validation-suite SHALL NOT include File_References to any script files because the workflow only needs to run the scripts via shell commands, not read their implementations
2. THE Steering_File for validation-suite SHALL remain unchanged because all necessary information (commands and fix instructions) is already inline

### Requirement 4: File reference placement and formatting

**User Story:** As a power maintainer, I want file references to follow a consistent placement convention, so that steering files remain readable and maintainable.

#### Acceptance Criteria

1. THE Steering_File SHALL place all File_References in a dedicated section after the YAML frontmatter and before the first heading
2. WHEN a File_Reference is added, THE Steering_File SHALL use the path relative to the workspace root
3. THE Steering_File SHALL include one File_Reference per line with no additional commentary on the reference lines
4. WHEN a File_Reference is added, THE Steering_File SHALL NOT duplicate information already available in the referenced file — verbose inline descriptions that restate referenced content SHALL be removed or condensed

### Requirement 5: Context budget guardrails

**User Story:** As a power maintainer, I want guardrails on which files can be referenced, so that activating a workflow does not bloat the agent's context window with unnecessarily large files.

#### Acceptance Criteria

1. THE Steering_File SHALL NOT include a File_Reference to any file exceeding 200 lines unless the agent requires the full content to execute the workflow correctly
2. WHEN deciding whether to add a File_Reference, THE decision SHALL consider whether the agent needs to read the file content versus merely run or update the file
3. IF a referenced file is a script that the agent only executes (not reads or modifies), THEN THE Steering_File SHALL NOT include a File_Reference to that script
