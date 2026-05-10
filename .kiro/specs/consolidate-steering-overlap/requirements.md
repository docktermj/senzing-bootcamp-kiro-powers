# Requirements Document

## Introduction

The senzing-bootcamp repository has two auto-included steering files (`structure.md` and `repository-organization.md`) that overlap significantly in describing directory layout and file placement rules. Both are loaded into context for every interaction, wasting context window budget. This feature consolidates them into a single coherent steering file that preserves all rules while eliminating redundancy and staying within the 80-line best-practice limit for auto-included files.

## Glossary

- **Steering_File**: A markdown file with YAML frontmatter in `.kiro/steering/` that provides guidance to the AI agent during interactions
- **Auto_Inclusion**: A steering file inclusion mode where the file is loaded into context for every interaction regardless of file type
- **Context_Window**: The limited token budget available to the AI agent during a session
- **Power_Directory**: The `senzing-bootcamp/` directory containing all distributed power content
- **Consolidator**: The process or agent performing the steering file merge

## Requirements

### Requirement 1: Merge Into Single File

**User Story:** As a developer, I want a single steering file covering directory layout and file placement, so that context window budget is not wasted on redundant content.

#### Acceptance Criteria

1. THE Consolidator SHALL produce exactly one steering file that replaces both `structure.md` and `repository-organization.md`
2. WHEN the consolidated file is created, THE Consolidator SHALL remove the two original files from `.kiro/steering/`
3. THE consolidated Steering_File SHALL use `inclusion: auto` in its YAML frontmatter
4. THE consolidated Steering_File SHALL contain a `description` field in its YAML frontmatter that accurately summarizes its purpose

### Requirement 2: Preserve All Existing Rules

**User Story:** As a developer, I want all existing placement rules and naming conventions preserved, so that no guidance is lost during consolidation.

#### Acceptance Criteria

1. THE consolidated Steering_File SHALL include the directory tree visualization showing the Power_Directory structure
2. THE consolidated Steering_File SHALL include file placement rules with audience information (Users, Agents, Developers, Both, Framework)
3. THE consolidated Steering_File SHALL include all naming conventions (scripts, steering files, module steering, hooks, tests, configs)
4. THE consolidated Steering_File SHALL include the rule that dev notes, build artifacts, and historical files do not belong in the repository
5. THE consolidated Steering_File SHALL include the rule that power config files stay at Power_Directory root
6. THE consolidated Steering_File SHALL include the rule that hook tests validating real hook files go in repo-root `tests/`, not `senzing-bootcamp/tests/`
7. THE consolidated Steering_File SHALL include repo-level directories (`.github/workflows/`, `.kiro/specs/`, repo-root `tests/`)

### Requirement 3: Stay Within Line Budget

**User Story:** As a developer, I want the consolidated file to stay under 80 lines, so that it follows best practices for auto-included steering files and minimizes context consumption.

#### Acceptance Criteria

1. THE consolidated Steering_File SHALL contain no more than 80 lines total (including frontmatter and blank lines)
2. THE consolidated Steering_File SHALL use concise formatting (tables, compact tree, short rule statements) to maximize information density
3. THE consolidated Steering_File SHALL not include redundant explanations or verbose prose

### Requirement 4: Maintain Correct File Format

**User Story:** As a developer, I want the consolidated file to follow steering file conventions, so that it integrates correctly with the Kiro framework.

#### Acceptance Criteria

1. THE consolidated Steering_File SHALL begin with valid YAML frontmatter delimited by `---` markers
2. THE consolidated Steering_File SHALL use kebab-case naming for its filename
3. THE consolidated Steering_File SHALL be placed in the `.kiro/steering/` directory
4. THE consolidated Steering_File SHALL be valid CommonMark markdown

### Requirement 5: Update Steering Index

**User Story:** As a developer, I want the steering index updated to reflect the consolidation, so that token budget tracking remains accurate.

#### Acceptance Criteria

1. IF a `steering-index.yaml` exists in the power directory, THEN THE Consolidator SHALL update it to remove entries for the two original files and add an entry for the new consolidated file
2. IF a `steering-index.yaml` exists, THEN THE Consolidator SHALL update the token count for the new entry to reflect the actual consolidated file size
