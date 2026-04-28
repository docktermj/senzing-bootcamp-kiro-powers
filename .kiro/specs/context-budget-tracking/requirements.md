# Requirements Document

## Introduction

The senzing-bootcamp power has 44 steering files that the agent loads on demand during bootcamp sessions. With no visibility into how much context budget each file consumes, the agent cannot make informed decisions about which files to load or unload as the context window fills up. This feature extends `steering-index.yaml` with per-file token counts and size categories, adds a `scripts/measure_steering.py` script to calculate and update those counts, adds context budget guidance to `agent-instructions.md`, and integrates token count validation into CI — giving the agent the data and rules it needs to manage context pressure across a session.

## Glossary

- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that provides a machine-readable mapping of steering files for agent file selection.
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` with YAML frontmatter that the AI agent loads at runtime to receive workflow instructions and behavioral rules.
- **Token_Count**: An approximate integer representing the number of tokens in a Steering_File, calculated by dividing the file's character count by four (characters ÷ 4).
- **Size_Category**: A classification label assigned to a Steering_File based on its Token_Count: `small` (under 500 tokens), `medium` (500 to 2000 tokens), or `large` (over 2000 tokens).
- **Context_Budget**: The total number of tokens available in the agent's context window for all loaded content including conversation history, tool responses, and Steering_Files.
- **Reference_Window**: A fixed token count (200,000 tokens) used as the baseline for calculating budget thresholds, representing a typical large context window.
- **Warn_Threshold**: The point at which loaded Steering_File tokens reach 60% of the Reference_Window, signaling the agent to be selective about additional file loads.
- **Critical_Threshold**: The point at which loaded Steering_File tokens reach 80% of the Reference_Window, signaling the agent to actively unload non-essential files before loading new ones.
- **Measure_Script**: The Python script at `senzing-bootcamp/scripts/measure_steering.py` that calculates Token_Counts for all Steering_Files and updates the Steering_Index.
- **Agent**: The AI agent running the bootcamp, guided by steering files and hooks.
- **CI_Workflow**: The GitHub Actions workflow at `.github/workflows/validate-power.yml` that validates power integrity on pull requests and pushes.

## Requirements

### Requirement 1: Extend Steering Index with Token Metadata

**User Story:** As a power developer, I want each steering file entry in the Steering_Index to include its token count and size category, so that the agent can assess context cost before loading a file.

#### Acceptance Criteria

1. THE Steering_Index SHALL include a `file_metadata` mapping where each key is a Steering_File filename and each value is an object containing `token_count` (integer) and `size_category` (string).
2. THE `file_metadata` mapping SHALL contain an entry for every `.md` file in the `senzing-bootcamp/steering/` directory.
3. THE `size_category` value for each entry SHALL be `small` when the Token_Count is under 500, `medium` when the Token_Count is between 500 and 2000 inclusive, and `large` when the Token_Count is over 2000.
4. THE Steering_Index SHALL include a `budget` mapping containing `total_tokens` (integer sum of all Token_Counts), `reference_window` (integer, 200000), `warn_threshold_pct` (integer, 60), and `critical_threshold_pct` (integer, 80).
5. THE Steering_Index SHALL retain all existing content (`modules`, `keywords`, `languages`, `deployment`, `references` mappings) without modification.

### Requirement 2: Create Token Measurement Script

**User Story:** As a power developer, I want a script that calculates token counts for all steering files and updates the Steering_Index, so that token metadata stays accurate as files change.

#### Acceptance Criteria

1. THE Measure_Script SHALL scan all `.md` files in the `senzing-bootcamp/steering/` directory and calculate a Token_Count for each file using the formula: file character count divided by four, rounded to the nearest integer.
2. THE Measure_Script SHALL update the `file_metadata` and `budget.total_tokens` fields in the Steering_Index file in place, preserving all other existing YAML content.
3. THE Measure_Script SHALL assign a Size_Category to each file based on its calculated Token_Count.
4. WHEN the Measure_Script encounters a `.md` file in the steering directory that has no entry in `file_metadata`, THE Measure_Script SHALL add a new entry for that file.
5. WHEN the Measure_Script encounters an entry in `file_metadata` for a file that no longer exists in the steering directory, THE Measure_Script SHALL remove that entry.
6. THE Measure_Script SHALL print a summary to stdout listing each file with its Token_Count, Size_Category, and the total token count across all files.
7. WHEN the Measure_Script is run with a `--check` flag, THE Measure_Script SHALL compare calculated token counts against the values in the Steering_Index and exit with a non-zero status code if any count differs by more than 10%, without modifying the file.
8. THE Measure_Script SHALL be executable as `python senzing-bootcamp/scripts/measure_steering.py` from the repository root with no external dependencies beyond the Python standard library.

### Requirement 3: Add Context Budget Guidance to Agent Instructions

**User Story:** As a bootcamp user, I want the agent to manage its context window intelligently, so that it does not run out of context space during long module sessions.

#### Acceptance Criteria

1. THE Agent_Instructions_File SHALL include a `Context Budget` section that instructs the Agent to consult the `file_metadata` in the Steering_Index before loading a Steering_File.
2. THE `Context Budget` section SHALL instruct the Agent to track the cumulative Token_Count of all currently loaded Steering_Files.
3. THE `Context Budget` section SHALL instruct the Agent to prefer loading `small` and `medium` files over `large` files when multiple files could satisfy a need.
4. WHEN the cumulative Token_Count of loaded Steering_Files exceeds the Warn_Threshold (60% of Reference_Window), THE `Context Budget` section SHALL instruct the Agent to load only files directly relevant to the current module or user question.
5. WHEN the cumulative Token_Count of loaded Steering_Files exceeds the Critical_Threshold (80% of Reference_Window), THE `Context Budget` section SHALL instruct the Agent to unload non-essential Steering_Files before loading new ones.
6. THE `Context Budget` section SHALL define a priority order for retaining files: (1) `agent-instructions.md` (always loaded), (2) the current module steering file, (3) language-specific steering file, (4) active troubleshooting files, (5) all other files.
7. THE `Context Budget` section SHALL instruct the Agent to mention the approximate token cost when loading a `large` Steering_File (e.g., "Loading module-07-multi-source.md (~2,450 tokens)").

### Requirement 4: Integrate Token Count Validation into CI

**User Story:** As a power developer, I want CI to verify that token counts in the Steering_Index are up to date, so that stale metadata does not mislead the agent.

#### Acceptance Criteria

1. THE CI_Workflow SHALL run the Measure_Script with the `--check` flag as a validation step.
2. WHEN the Measure_Script `--check` flag detects token counts that differ by more than 10% from calculated values, THE CI_Workflow step SHALL fail the build.
3. THE CI_Workflow SHALL run the token count validation step after the existing "Validate power integrity" step and before the "Run tests" step.

### Requirement 5: Steering Index Schema Validation

**User Story:** As a power developer, I want the power validation script to verify that the Steering_Index contains valid token metadata, so that malformed entries are caught early.

#### Acceptance Criteria

1. WHEN the `validate_power.py` script runs, THE script SHALL verify that the Steering_Index contains a `file_metadata` mapping.
2. WHEN the `validate_power.py` script runs, THE script SHALL verify that every `.md` file in the steering directory has a corresponding entry in `file_metadata` with integer `token_count` and string `size_category` fields.
3. WHEN the `validate_power.py` script runs, THE script SHALL verify that each `size_category` value is one of `small`, `medium`, or `large`.
4. WHEN the `validate_power.py` script runs, THE script SHALL verify that the Steering_Index contains a `budget` mapping with `total_tokens`, `reference_window`, `warn_threshold_pct`, and `critical_threshold_pct` fields.
5. IF any validation check fails, THEN THE `validate_power.py` script SHALL report the failure as an error and exit with a non-zero status code.

### Requirement 6: POWER.md Documentation Update

**User Story:** As a power developer, I want POWER.md to document the context budget tracking feature, so that users and contributors understand the token metadata and measurement tooling.

#### Acceptance Criteria

1. THE POWER.md file SHALL mention the `file_metadata` section in the Steering_Index in the "What's New" or feature description section.
2. THE POWER.md file SHALL list `measure_steering.py` in the "Useful Commands" section with usage examples for both update mode and `--check` mode.
3. THE POWER.md file SHALL describe the context budget thresholds (60% warn, 80% critical) in the steering files documentation section.
