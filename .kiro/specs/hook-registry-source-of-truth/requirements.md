# Requirements Document

## Introduction

The bootcamp hooks are defined in individual `.kiro.hook` JSON files under `senzing-bootcamp/hooks/` and also documented in `senzing-bootcamp/steering/hook-registry.md`. These two sources have drifted out of sync multiple times, requiring manual fixes. This feature makes the `.kiro.hook` files the single source of truth by creating a script (`scripts/sync_hook_registry.py`) that generates `hook-registry.md` from the hook files. A CI check ensures the registry is never out of sync with the hook files.

## Glossary

- **Hook_File**: A `.kiro.hook` JSON file in `senzing-bootcamp/hooks/` that defines a single hook's name, description, event trigger, and action prompt
- **Hook_Registry**: The `senzing-bootcamp/steering/hook-registry.md` markdown file that documents all hooks for the agent to read at runtime
- **Sync_Script**: The `scripts/sync_hook_registry.py` Python script that reads all Hook_Files and generates the Hook_Registry
- **Hook_ID**: The filename stem of a Hook_File (e.g., `ask-bootcamper` from `ask-bootcamper.kiro.hook`)
- **Hook_Category**: A classification of a hook as either "Critical" (created during onboarding) or "Module" (created when a specific module starts), determined by metadata or convention
- **Event_Type**: The `when.type` field in a Hook_File (e.g., `promptSubmit`, `agentStop`, `fileEdited`, `preToolUse`, `postTaskExecution`, `fileCreated`, `userTriggered`)
- **Action_Type**: The `then.type` field in a Hook_File (e.g., `askAgent`, `runCommand`)
- **CI_Check**: A CI pipeline step that runs the Sync_Script in verification mode and fails the build if the Hook_Registry on disk does not match the generated output
- **Registry_Frontmatter**: The YAML frontmatter block at the top of the Hook_Registry (currently `inclusion: manual`)

## Requirements

### Requirement 1: Parse Hook Files

**User Story:** As a power maintainer, I want the sync script to read all `.kiro.hook` files and extract their metadata, so that the generated registry is always based on the actual hook definitions.

#### Acceptance Criteria

1. THE Sync_Script SHALL discover all files matching the pattern `*.kiro.hook` in the `senzing-bootcamp/hooks/` directory
2. WHEN a Hook_File contains valid JSON with `name`, `description`, `when.type`, and `then.type` fields, THE Sync_Script SHALL parse the Hook_ID from the filename stem and extract all four fields
3. WHEN a Hook_File contains a `then.prompt` field, THE Sync_Script SHALL extract the prompt text for inclusion in the Hook_Registry
4. WHEN a Hook_File contains a `when.filePatterns` field, THE Sync_Script SHALL extract the file patterns for inclusion in the Hook_Registry entry
5. WHEN a Hook_File contains a `when.toolTypes` field, THE Sync_Script SHALL extract the tool types for inclusion in the Hook_Registry entry
6. IF a Hook_File contains invalid JSON, THEN THE Sync_Script SHALL report an error identifying the filename and skip that file

### Requirement 2: Determine Hook Categories

**User Story:** As a power maintainer, I want the sync script to categorize hooks as Critical or Module hooks, so that the generated registry preserves the existing organizational structure.

#### Acceptance Criteria

1. THE Sync_Script SHALL accept a category mapping configuration that associates each Hook_ID with a Hook_Category and optional module number
2. WHEN a Hook_ID is mapped to the "Critical" category, THE Sync_Script SHALL place the hook entry under the "Critical Hooks" section of the Hook_Registry
3. WHEN a Hook_ID is mapped to a "Module" category with a module number, THE Sync_Script SHALL place the hook entry under the "Module Hooks" section with the associated module number
4. WHEN a Hook_ID has no category mapping, THE Sync_Script SHALL default to placing the hook under a "Module Hooks" section with the label "any module"
5. THE Sync_Script SHALL read the category mapping from a configuration file (`senzing-bootcamp/hooks/hook-categories.yaml`) rather than hardcoding the mapping

### Requirement 3: Generate Hook Registry Markdown

**User Story:** As a power maintainer, I want the sync script to produce a complete `hook-registry.md` file from the parsed hook data, so that the registry is always consistent with the hook files.

#### Acceptance Criteria

1. THE Sync_Script SHALL generate a Hook_Registry that begins with the Registry_Frontmatter block (`---\ninclusion: manual\n---`)
2. THE Sync_Script SHALL generate a title line `# Hook Registry` followed by an introductory paragraph stating the total hook count and explaining the Critical/Module distinction
3. THE Sync_Script SHALL generate a `## Critical Hooks` section listing all Critical-category hooks sorted alphabetically by Hook_ID
4. THE Sync_Script SHALL generate a `## Module Hooks` section listing all Module-category hooks sorted by module number and then alphabetically by Hook_ID within the same module
5. WHEN generating an entry for a hook, THE Sync_Script SHALL produce the format: bold Hook_ID, parenthesized event flow (e.g., `promptSubmit → askAgent`), the prompt text as a paragraph, and a bullet list with `id`, `name`, and `description` fields
6. WHEN a hook has `filePatterns` or `toolTypes`, THE Sync_Script SHALL include them in the parenthesized event flow (e.g., `fileEdited → askAgent, filePatterns: \`*.py\``)

### Requirement 4: Write or Verify Mode

**User Story:** As a CI pipeline maintainer, I want the sync script to support both a write mode (overwrite the registry) and a verify mode (check if the registry is up to date), so that the same script serves both local development and CI.

#### Acceptance Criteria

1. WHEN the Sync_Script is invoked with no flags or with the `--write` flag, THE Sync_Script SHALL write the generated Hook_Registry to `senzing-bootcamp/steering/hook-registry.md`
2. WHEN the Sync_Script is invoked with the `--verify` flag, THE Sync_Script SHALL compare the generated Hook_Registry content against the existing file on disk without modifying the file
3. WHEN the `--verify` flag is used and the generated content matches the file on disk, THE Sync_Script SHALL exit with code 0
4. WHEN the `--verify` flag is used and the generated content differs from the file on disk, THE Sync_Script SHALL exit with code 1 and print a message identifying that the Hook_Registry is out of sync
5. WHEN the `--verify` flag is used and the Hook_Registry file does not exist on disk, THE Sync_Script SHALL exit with code 1 and print a message stating the file is missing

### Requirement 5: CI Integration

**User Story:** As a power maintainer, I want a CI check that fails the build when the hook registry is out of sync with the hook files, so that drift is caught before merging.

#### Acceptance Criteria

1. THE CI_Check SHALL run `python scripts/sync_hook_registry.py --verify` as a pipeline step
2. WHEN the Sync_Script exits with code 0, THE CI_Check SHALL pass
3. WHEN the Sync_Script exits with code 1, THE CI_Check SHALL fail the build with a message instructing the developer to run `python scripts/sync_hook_registry.py --write` locally
4. THE Sync_Script SHALL depend only on the Python standard library so that no additional CI dependencies are required

### Requirement 6: Round-Trip Fidelity

**User Story:** As a power maintainer, I want the generated registry to be identical when regenerated from the same hook files, so that CI checks are deterministic and do not produce false positives.

#### Acceptance Criteria

1. FOR ALL sets of valid Hook_Files, generating the Hook_Registry and then regenerating from the same Hook_Files SHALL produce byte-identical output (deterministic generation)
2. THE Sync_Script SHALL use a stable sort order (alphabetical by Hook_ID within each category section) to ensure deterministic output regardless of filesystem ordering
3. THE Sync_Script SHALL normalize line endings to Unix-style (`\n`) in the generated output to prevent platform-dependent differences
