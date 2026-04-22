# Requirements Document

## Introduction

The hooks-and-scripts feature provides 13 Kiro hooks and 10 Python utility scripts that automate quality checks, enforce policies, and streamline common operations throughout the Senzing Bootcamp. An interactive installer script copies hooks from the power distribution into the workspace `.kiro/hooks/` directory.

## Glossary

- **Hook**: A JSON configuration file (`.kiro.hook`) that maps an IDE event to an agent action
- **Hook_Installer**: The `install_hooks.py` script that copies hook files from the power directory to `.kiro/hooks/`
- **Script**: A cross-platform Python utility in `senzing-bootcamp/scripts/` that performs a bootcamp operation
- **Power_Directory**: The `senzing-bootcamp/` directory containing the distributed power files
- **Workspace_Hooks_Directory**: The `.kiro/hooks/` directory where active hooks are installed

## Requirements

### Requirement 1: Kiro Hooks

**User Story:** As a bootcamp user, I want automated hooks that enforce quality standards and provide contextual reminders, so that I catch issues early and follow best practices without manual effort.

#### Acceptance Criteria

1. WHEN a source code file with extension `.py`, `.java`, `.cs`, `.rs`, `.ts`, or `.js` is edited, THE Hook SHALL prompt the agent to check language-appropriate coding standards.
2. WHEN a transformation program in `src/transform/` is edited, THE Hook SHALL prompt the agent to remind the user to validate data quality.
3. WHEN a loading program in `src/load/` is edited, THE Hook SHALL prompt the agent to remind the user to back up the database before running.
4. WHEN a Senzing JSON file in `data/transformed/` is edited, THE Hook SHALL prompt the agent to validate records against the Senzing Generic Entity Specification.
5. WHEN the user manually triggers the backup hook, THE Hook SHALL prompt the agent to run the backup script.
6. WHEN a Markdown file is edited, THE Hook SHALL prompt the agent to check CommonMark compliance and auto-fix issues.
7. WHEN a write operation is about to occur (preToolUse), THE Hook SHALL prompt the agent to verify Senzing-specific content via MCP tools before writing.
8. WHEN a new Senzing JSON file is created in `data/transformed/`, THE Hook SHALL prompt the agent to run `analyze_record` validation before proceeding to loading.
9. WHEN source code in `src/load/`, `src/query/`, or `src/transform/` is edited, THE Hook SHALL prompt the agent to run the test suite.
10. WHEN the user manually triggers the git commit hook, THE Hook SHALL prompt the agent to suggest a descriptive commit message based on the current module.
11. WHEN a write operation is about to occur (preToolUse), THE Hook SHALL prompt the agent to verify file paths do not reference locations outside the working directory.
12. WHEN the agent stops (agentStop), THE Hook SHALL prompt the agent to summarize what was accomplished, which files changed, and the next step.
13. WHEN new source files are created in `src/transform/`, `src/load/`, or `src/query/`, THE Hook SHALL prompt the agent to run the code on sample data and verify it works.

### Requirement 2: Utility Scripts

**User Story:** As a bootcamp user, I want cross-platform Python scripts for common operations, so that I can check status, validate progress, manage backups, and verify my environment without manual steps.

#### Acceptance Criteria

1. THE Script `status.py` SHALL display the current module, progress percentage, project health score, and next steps.
2. THE Script `validate_module.py` SHALL validate that a module's prerequisites and success criteria are met by checking for expected files and directories.
3. THE Script `check_prerequisites.py` SHALL verify that required tools (git, language runtimes) and optional tools are installed, and report pass/fail/warning counts.
4. THE Script `backup_project.py` SHALL create a timestamped ZIP archive of project data in the `backups/` directory, excluding build artifacts and temporary files.
5. THE Script `restore_project.py` SHALL extract a backup ZIP archive to restore project files, with confirmation prompts before overwriting.
6. THE Script `clone_example.py` SHALL copy an example project from the power's `examples/` directory into the user's workspace.
7. THE Script `preflight_check.py` SHALL verify core system requirements (language runtimes, disk space, memory, write permissions) before starting the bootcamp.
8. THE Script `validate_commonmark.py` SHALL run markdownlint on all Markdown files and report CommonMark compliance issues.
9. THE Script `validate_power.py` SHALL validate the power's internal consistency by checking hooks, steering files, scripts, module docs, and cross-references.

### Requirement 3: Hook Installer

**User Story:** As a bootcamp user, I want an interactive installer that copies hooks to my workspace, so that I can enable hooks without manually copying files.

#### Acceptance Criteria

1. WHEN the user runs `install_hooks.py`, THE Hook_Installer SHALL discover all `.kiro.hook` files in the power hooks directory.
2. THE Hook_Installer SHALL present three installation options: all hooks, essential hooks only, or individual selection.
3. WHEN the user selects "all hooks", THE Hook_Installer SHALL copy every discovered hook file to the Workspace_Hooks_Directory.
4. WHEN the user selects "essential hooks", THE Hook_Installer SHALL copy only the essential subset (code-style-check, backup-before-load, backup-project-on-request).
5. IF a hook file already exists in the Workspace_Hooks_Directory, THEN THE Hook_Installer SHALL skip that file and report it as already installed.
6. THE Hook_Installer SHALL create the `.kiro/hooks/` directory if it does not exist.

### Requirement 4: Cross-Platform Compatibility

**User Story:** As a bootcamp user on any operating system, I want all scripts and hooks to work on Linux, macOS, and Windows, so that I am not blocked by platform differences.

#### Acceptance Criteria

1. THE Script collection SHALL use only Python standard library modules (no third-party dependencies required).
2. THE Script collection SHALL use `pathlib.Path` for file path operations to ensure cross-platform path handling.
3. THE Script collection SHALL detect terminal color support and disable ANSI codes when the terminal does not support them.
