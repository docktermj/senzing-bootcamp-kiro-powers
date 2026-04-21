# Requirements Document

## Introduction

The `module-transitions.md` steering file in the Senzing Bootcamp Power uses `inclusion: auto`, which causes it to be loaded into the agent's context window on every interaction. This wastes context budget because the module transition guidance (banners, journey maps, before/after framing, step-level progress) is only needed at module boundaries — when a user starts or completes a module. The file should use `inclusion: fileMatch` with a pattern targeting `config/bootcamp_progress.json`, which the agent reads and writes at module boundaries. The `agent-instructions.md` file must also be updated to reflect that `module-transitions.md` is now conditionally loaded rather than always present.

## Glossary

- **Steering_File**: A markdown file with YAML front matter that the AI agent loads at runtime to receive workflow instructions and behavioral rules
- **Context_Window**: The limited token budget available to the AI agent for processing instructions, conversation history, and file content
- **Module_Transitions_File**: The `senzing-bootcamp/steering/module-transitions.md` steering file that provides module start banners, journey maps, before/after framing, and step-level progress guidance
- **Agent_Instructions_File**: The `senzing-bootcamp/steering/agent-instructions.md` steering file that provides core rules and references to other steering files
- **Progress_File**: The `config/bootcamp_progress.json` file that the agent reads and writes at module start and module completion to track bootcamp progress
- **Frontmatter**: The YAML metadata block at the top of a steering file delimited by `---` lines that controls inclusion behavior

## Requirements

### Requirement 1: Change Module Transitions Inclusion Strategy

**User Story:** As a power developer, I want `module-transitions.md` to load only when the progress file is being accessed, so that context window space is not wasted on non-module-boundary interactions.

#### Acceptance Criteria

1. THE Module_Transitions_File SHALL use `inclusion: fileMatch` in its Frontmatter instead of `inclusion: auto`
2. THE Module_Transitions_File SHALL specify `fileMatchPattern: "config/bootcamp_progress.json"` in its Frontmatter so that the file loads when the Progress_File is read or written
3. THE Module_Transitions_File SHALL retain all existing content (module start banner template, journey map format, before/after framing instructions, step-level progress rules, module completion summary rules) without modification

### Requirement 2: Add Description to Module Transitions Frontmatter

**User Story:** As a power developer, I want `module-transitions.md` to have a description field in its frontmatter, so that the file's purpose is discoverable without reading its full content.

#### Acceptance Criteria

1. THE Module_Transitions_File SHALL include a `description` field in its Frontmatter that summarizes the file's purpose as providing module boundary guidance including banners, journey maps, and progress tracking

### Requirement 3: Update Agent Instructions Cross-Reference

**User Story:** As a power developer, I want `agent-instructions.md` to accurately describe how `module-transitions.md` is loaded, so that the agent understands the file is conditionally available rather than always present.

#### Acceptance Criteria

1. THE Agent_Instructions_File SHALL note that `module-transitions.md` is conditionally loaded when the Progress_File is accessed, not auto-included on every interaction
2. THE Agent_Instructions_File SHALL retain all existing content and structure outside the module transitions reference without modification
