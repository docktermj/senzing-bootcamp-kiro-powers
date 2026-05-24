# Requirements Document

## Introduction

The MCP `mapping_workflow` tool generates files (Python scripts, markdown docs, JSONL data, JSON configs) into the project root or a flat workspace directory. This feature adds a Python script that relocates generated files to the correct project subdirectories based on file extension, and updates the Module 5 steering files to instruct the agent to invoke the script after mapping workflow steps produce output.

## Glossary

- **Organizer_Script**: A Python CLI tool at `senzing-bootcamp/scripts/organize_mapping_files.py` that moves mapping workflow output files from a source directory to their correct project subdirectories based on file extension.
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that provides agent instructions for a bootcamp module phase.
- **Routing_Rule**: A mapping from a file extension to a target subdirectory (e.g., `.py` → `scripts/`, `.md` → `docs/`, `.jsonl` → `data/`, `.json` → `config/`).
- **Source_Directory**: The directory where `mapping_workflow` deposits generated files (typically the project root or a workspace directory).
- **Target_Directory**: The project subdirectory where a file belongs based on its extension.

## Requirements

### Requirement 1: Extension-Based File Routing

**User Story:** As a bootcamp developer, I want mapping workflow output files automatically sorted into the correct project subdirectories, so that my project stays organized without manual file moves.

#### Acceptance Criteria

1. WHEN the Organizer_Script is invoked with a Source_Directory, THE Organizer_Script SHALL move files with `.py` extension to the `scripts/` subdirectory relative to the project root.
2. WHEN the Organizer_Script is invoked with a Source_Directory, THE Organizer_Script SHALL move files with `.md` extension to the `docs/` subdirectory relative to the project root.
3. WHEN the Organizer_Script is invoked with a Source_Directory, THE Organizer_Script SHALL move files with `.jsonl` extension to the `data/` subdirectory relative to the project root.
4. WHEN the Organizer_Script is invoked with a Source_Directory, THE Organizer_Script SHALL move files with `.json` extension to the `config/` subdirectory relative to the project root.
5. IF a file in the Source_Directory has an extension not covered by any Routing_Rule, THEN THE Organizer_Script SHALL leave the file in place and print a warning to stderr identifying the unrouted file.

### Requirement 2: Idempotent Operation

**User Story:** As a bootcamp developer, I want the organize script to be safe to run multiple times, so that re-running it after a session resume or retry does not corrupt or duplicate files.

#### Acceptance Criteria

1. IF a file with the same name already exists in the Target_Directory, THEN THE Organizer_Script SHALL skip the move for that file and print a notice to stderr.
2. WHEN the Organizer_Script is invoked on a Source_Directory containing no files matching any Routing_Rule, THE Organizer_Script SHALL exit with code 0 and produce no file system changes.
3. WHEN the Organizer_Script is invoked multiple times on the same Source_Directory with the same files, THE Organizer_Script SHALL produce the same final file layout as a single invocation.

### Requirement 3: Target Directory Creation

**User Story:** As a bootcamp developer, I want the script to create target subdirectories if they do not exist, so that it works on fresh projects without manual setup.

#### Acceptance Criteria

1. IF a Target_Directory does not exist when the Organizer_Script attempts to move a file, THEN THE Organizer_Script SHALL create the Target_Directory (including intermediate directories) before moving the file.
2. WHEN the Target_Directory already exists, THE Organizer_Script SHALL proceed without error.

### Requirement 4: CLI Interface

**User Story:** As a bootcamp developer, I want the organize script to accept command-line arguments for source and project root directories, so that it works in different project layouts.

#### Acceptance Criteria

1. THE Organizer_Script SHALL accept a `--source` argument specifying the Source_Directory to scan for generated files.
2. THE Organizer_Script SHALL accept a `--project-root` argument specifying the base directory for Target_Directory resolution.
3. IF the `--source` argument is omitted, THEN THE Organizer_Script SHALL default to the current working directory as the Source_Directory.
4. IF the `--project-root` argument is omitted, THEN THE Organizer_Script SHALL default to the current working directory as the project root.
5. THE Organizer_Script SHALL exit with code 0 on success and code 1 on any fatal error.
6. WHEN the `--source` path does not exist, THE Organizer_Script SHALL print an error to stderr and exit with code 1.

### Requirement 5: Dry-Run Mode

**User Story:** As a bootcamp developer, I want to preview what the script would do before it moves files, so that I can verify the routing is correct.

#### Acceptance Criteria

1. WHEN the `--dry-run` flag is provided, THE Organizer_Script SHALL print the planned moves to stdout without modifying the file system.
2. WHEN the `--dry-run` flag is provided, THE Organizer_Script SHALL exit with code 0 regardless of whether files would be moved.

### Requirement 6: Steering File Integration for Phase 2

**User Story:** As a bootcamp agent, I want the Module 5 Phase 2 steering file to instruct me to run the organize script after mapping workflow steps generate files, so that output lands in the correct directories automatically.

#### Acceptance Criteria

1. THE Steering_File `module-05-phase2-data-mapping.md` SHALL contain an agent instruction directing the agent to invoke the Organizer_Script after `mapping_workflow` generates output files.
2. THE Steering_File instruction SHALL specify the `--source` argument pointing to the mapping workflow workspace directory.
3. THE Steering_File instruction SHALL specify the `--project-root` argument pointing to the bootcamper's project root.

### Requirement 7: Steering File Integration for Phase 3

**User Story:** As a bootcamp agent, I want the Module 5 Phase 3 steering file to instruct me to run the organize script after test-load workflow steps generate files, so that output lands in the correct directories automatically.

#### Acceptance Criteria

1. THE Steering_File `module-05-phase3-test-load.md` SHALL contain an agent instruction directing the agent to invoke the Organizer_Script after `mapping_workflow` steps 5–8 generate output files.
2. THE Steering_File instruction SHALL specify the `--source` argument pointing to the mapping workflow workspace directory.
3. THE Steering_File instruction SHALL specify the `--project-root` argument pointing to the bootcamper's project root.

### Requirement 8: Reporting

**User Story:** As a bootcamp developer, I want the script to summarize what it did, so that I can confirm files were organized correctly.

#### Acceptance Criteria

1. WHEN the Organizer_Script completes successfully with at least one file moved, THE Organizer_Script SHALL print a summary to stdout listing each file moved and its destination.
2. WHEN the Organizer_Script completes with no files moved, THE Organizer_Script SHALL print a message to stdout indicating no files required organization.
