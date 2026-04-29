# Requirements Document

## Introduction

The steering file corpus (markdown files in `senzing-bootcamp/steering/`, hooks in `senzing-bootcamp/hooks/`, and the steering index YAML) has grown to 45+ files with dense cross-references, module numbering conventions, WAIT instructions, and checkpoint requirements. Bugs in these files — orphaned references, misnumbered modules, WAIT instructions that conflict with hook ownership, missing checkpoints — are only caught during live bootcamp sessions. This feature adds a `scripts/lint_steering.py` script that statically validates the steering corpus and runs in CI, catching structural issues before they ship.

## Glossary

- **Linter**: The `scripts/lint_steering.py` script that scans steering files and reports violations
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that provides agent workflow instructions
- **Hook_Definition**: A `.kiro.hook` JSON file in `senzing-bootcamp/hooks/` that defines an automated agent action
- **Hook_Registry**: The `senzing-bootcamp/steering/hook-registry.md` file that documents all hook definitions for the agent
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file that maps modules, keywords, and metadata to steering files
- **Cross_Reference**: A reference from one file to another, using either `#[[file:path]]` include syntax or backtick-quoted filenames (e.g., `module-completion.md`)
- **Checkpoint_Instruction**: A line in a module steering file matching the pattern `**Checkpoint:** Write step N to \`config/bootcamp_progress.json\`.` that tells the agent to persist step-level progress
- **WAIT_Instruction**: A directive in a steering file (e.g., `WAIT for response.`) that tells the agent to pause and wait for user input before continuing
- **Closing_Question_Rule**: The rule in `agent-instructions.md` that the `ask-bootcamper` hook owns all closing questions, so steering files must not place a WAIT instruction at the very end of their output
- **Module_Steering_File**: A steering file named `module-NN-*.md` that contains the numbered steps for a specific bootcamp module
- **Numbered_Step**: A step in a module steering file identified by a number (e.g., `1.`, `2.`) that represents a discrete unit of work requiring a checkpoint
- **Lint_Violation**: A single issue found by the Linter, classified as either an error (blocks CI) or a warning (informational)
- **Exit_Code**: The integer returned by the Linter process; `0` means no errors, `1` means one or more errors were found

## Requirements

### Requirement 1: Orphaned Cross-Reference Detection

**User Story:** As a power maintainer, I want the linter to detect references to files that do not exist, so that agents never try to load missing steering files at runtime.

#### Acceptance Criteria

1. WHEN a Steering_File contains a `#[[file:path]]` include reference, THE Linter SHALL verify that the referenced path exists relative to the repository root
2. WHEN a Steering_File contains a backtick-quoted filename matching `*.md` that corresponds to a known steering file naming pattern, THE Linter SHALL verify that the file exists in the `senzing-bootcamp/steering/` directory
3. WHEN a referenced file does not exist, THE Linter SHALL report an error Lint_Violation identifying the source file, line number, and missing target path
4. WHEN the Steering_Index references a steering file in any of its mapping sections (modules, keywords, languages, deployment), THE Linter SHALL verify that the referenced file exists in the `senzing-bootcamp/steering/` directory
5. WHEN a Steering_Index reference points to a nonexistent file, THE Linter SHALL report an error Lint_Violation identifying the mapping key and missing filename

### Requirement 2: Module Numbering Consistency

**User Story:** As a power maintainer, I want the linter to catch inconsistent module numbering between the steering index, module filenames, and module file contents, so that agents load the correct steering file for each module.

#### Acceptance Criteria

1. THE Linter SHALL verify that every module number in the Steering_Index `modules` mapping has a corresponding Module_Steering_File in the `senzing-bootcamp/steering/` directory with the naming pattern `module-NN-*.md`
2. WHEN a Module_Steering_File exists on disk but is not listed in the Steering_Index `modules` mapping, THE Linter SHALL report a warning Lint_Violation identifying the unlisted file
3. THE Linter SHALL verify that the module number embedded in each Module_Steering_File's filename (the `NN` in `module-NN-*.md`) is a zero-padded two-digit integer matching its Steering_Index entry
4. WHEN the Steering_Index `modules` mapping contains a gap in the sequence (e.g., modules 1-5 and 7-11 but no 6), THE Linter SHALL report a warning Lint_Violation identifying the missing number

### Requirement 3: WAIT Instruction and Hook Ownership Conflict Detection

**User Story:** As a power maintainer, I want the linter to flag WAIT instructions that conflict with the closing-question ownership rule, so that agents do not produce duplicate closing questions.

#### Acceptance Criteria

1. THE Linter SHALL identify all WAIT_Instructions in each Steering_File by scanning for the pattern `WAIT for` (case-sensitive)
2. WHEN a WAIT_Instruction appears in the final substantive line of a Steering_File (ignoring trailing blank lines and comments), THE Linter SHALL report a warning Lint_Violation noting the potential conflict with the Closing_Question_Rule
3. WHEN a WAIT_Instruction appears in the Hook_Registry inside a hook prompt definition that is associated with an `agentStop` event type, THE Linter SHALL treat the WAIT_Instruction as valid and not report a conflict (the hook itself owns the closing interaction)
4. WHEN a Steering_File contains a `👉` question followed by a WAIT_Instruction on the same line or the next non-blank line, THE Linter SHALL treat the pair as a valid mid-conversation interaction and not report a conflict unless it is the final substantive content of the file

### Requirement 4: Missing Checkpoint Instruction Detection

**User Story:** As a power maintainer, I want the linter to detect numbered steps in module steering files that lack a checkpoint instruction, so that step-level progress tracking is never silently skipped.

#### Acceptance Criteria

1. THE Linter SHALL parse each Module_Steering_File to identify all Numbered_Steps by scanning for lines matching the pattern of a numbered list item (e.g., `1. `, `2. `) at the top level of the document
2. WHEN a Numbered_Step does not have a corresponding Checkpoint_Instruction before the next Numbered_Step or end of file, THE Linter SHALL report an error Lint_Violation identifying the module file and step number
3. WHEN a Checkpoint_Instruction references a step number that does not match the Numbered_Step it follows, THE Linter SHALL report an error Lint_Violation identifying the mismatched step numbers
4. WHEN a Module_Steering_File contains zero Numbered_Steps, THE Linter SHALL skip checkpoint validation for that file without reporting a violation

### Requirement 5: Steering Index Completeness

**User Story:** As a power maintainer, I want the linter to verify that every steering file on disk is accounted for in the steering index metadata, so that token budget tracking is accurate.

#### Acceptance Criteria

1. THE Linter SHALL verify that every `.md` file in `senzing-bootcamp/steering/` has a corresponding entry in the Steering_Index `file_metadata` section
2. WHEN a steering file exists on disk but has no `file_metadata` entry, THE Linter SHALL report an error Lint_Violation identifying the missing file
3. THE Linter SHALL verify that each `file_metadata` entry contains both a `token_count` (positive integer) and a `size_category` (one of `small`, `medium`, `large`)
4. WHEN a `file_metadata` entry has an invalid or missing `token_count` or `size_category`, THE Linter SHALL report an error Lint_Violation identifying the file and the invalid field

### Requirement 6: Hook Registry and Hook File Consistency

**User Story:** As a power maintainer, I want the linter to verify that every hook documented in the hook registry has a corresponding `.kiro.hook` file and vice versa, so that the registry stays in sync with the actual hook definitions.

#### Acceptance Criteria

1. THE Linter SHALL extract all hook IDs from the Hook_Registry by scanning for lines matching the pattern `- id: \`hook-id\``
2. WHEN a hook ID in the Hook_Registry has no corresponding `.kiro.hook` file in `senzing-bootcamp/hooks/`, THE Linter SHALL report an error Lint_Violation identifying the missing hook file
3. WHEN a `.kiro.hook` file exists in `senzing-bootcamp/hooks/` but its ID is not documented in the Hook_Registry, THE Linter SHALL report a warning Lint_Violation identifying the undocumented hook
4. WHEN the Hook_Registry documents an event type for a hook (e.g., `promptSubmit → askAgent`) that does not match the `when.type` field in the corresponding `.kiro.hook` file, THE Linter SHALL report an error Lint_Violation identifying the hook and the mismatched event types

### Requirement 7: Frontmatter Validation

**User Story:** As a power maintainer, I want the linter to verify that every steering file has valid YAML frontmatter with a recognized inclusion mode, so that the agent framework loads files correctly.

#### Acceptance Criteria

1. THE Linter SHALL verify that every Steering_File (excluding `steering-index.yaml`) begins with a YAML frontmatter block delimited by `---`
2. WHEN a Steering_File lacks a frontmatter block, THE Linter SHALL report an error Lint_Violation identifying the file
3. THE Linter SHALL verify that each frontmatter block contains an `inclusion` field with a value of `always`, `auto`, `fileMatch`, or `manual`
4. WHEN the `inclusion` value is `fileMatch`, THE Linter SHALL verify that the frontmatter also contains a `fileMatchPattern` field with a non-empty string value
5. WHEN the frontmatter is missing the `inclusion` field or contains an unrecognized value, THE Linter SHALL report an error Lint_Violation identifying the file and the invalid value

### Requirement 8: CLI Interface and CI Integration

**User Story:** As a CI pipeline maintainer, I want the linter to run as a standalone Python script with a clear pass/fail exit code, so that it integrates into any CI system without additional dependencies.

#### Acceptance Criteria

1. THE Linter SHALL run as `python scripts/lint_steering.py` from the repository root with no third-party dependencies beyond the Python standard library
2. WHEN the Linter finds zero error-level Lint_Violations, THE Linter SHALL exit with Exit_Code 0
3. WHEN the Linter finds one or more error-level Lint_Violations, THE Linter SHALL exit with Exit_Code 1
4. THE Linter SHALL print each Lint_Violation to stdout in the format `{level}: {file}:{line}: {message}` where level is `ERROR` or `WARNING`, file is the relative path, and line is the line number (or `0` when not applicable)
5. THE Linter SHALL print a summary line at the end of output showing the total count of errors and warnings
6. WHEN the `--warnings-as-errors` flag is passed, THE Linter SHALL treat warning-level Lint_Violations as errors for the purpose of determining the Exit_Code

### Requirement 9: Steering File Internal Link Validation

**User Story:** As a power maintainer, I want the linter to detect references to steering files mentioned in prose (e.g., "load `module-completion.md`") that do not exist, so that agent instructions never reference phantom files.

#### Acceptance Criteria

1. WHEN a Steering_File contains a prose reference to another steering file using the pattern `load \`filename.md\`` or `follow \`filename.md\`` or `see \`filename.md\``, THE Linter SHALL verify that the referenced file exists in `senzing-bootcamp/steering/`
2. WHEN a prose-referenced steering file does not exist, THE Linter SHALL report an error Lint_Violation identifying the source file, line number, and missing target
3. WHEN a Steering_File references a file inside a fenced code block (between ``` delimiters), THE Linter SHALL skip validation for that reference to avoid false positives on example code
