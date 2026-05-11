# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power lacks a single high-level document explaining how its components (steering files, hooks, scripts, MCP server, configuration files, and modules) relate to each other. Contributors and advanced users must piece together the architecture from individual files. This feature creates `senzing-bootcamp/docs/guides/ARCHITECTURE.md` — a comprehensive architecture overview document that serves as the single entry point for understanding the system.

## Glossary

- **Architecture_Document**: The `ARCHITECTURE.md` file located at `senzing-bootcamp/docs/guides/ARCHITECTURE.md` that describes the system architecture
- **Component**: A major subsystem of the senzing-bootcamp power (steering, hooks, scripts, config, MCP, modules)
- **Steering_File**: A Markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that provides agent behavior instructions
- **Hook**: A Kiro hook definition (`.kiro.hook` JSON file) that automates agent actions based on IDE events
- **Module**: One of the 11 bootcamp curriculum units that guides a user through a topic
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides facts, code generation, and tool assistance
- **Context_Budget**: The token-based system for managing which steering files are loaded into the agent context window
- **Module_Lifecycle**: The sequence of states a module passes through from loading to completion
- **ASCII_Diagram**: A text-based diagram using box-drawing or standard ASCII characters, requiring no external rendering tools
- **Contributor**: A developer who modifies or extends the senzing-bootcamp power itself
- **Bootcamper**: An end user progressing through the bootcamp modules

## Requirements

### Requirement 1: Component Overview Section

**User Story:** As a contributor, I want a section that describes what each major component does, so that I can understand the system without reading every individual file.

#### Acceptance Criteria

1. THE Architecture_Document SHALL contain a "Component Overview" section that describes the purpose of each Component (steering, hooks, scripts, config, MCP, modules)
2. WHEN a reader views the Component Overview section, THE Architecture_Document SHALL present each Component with its directory location, file format, and primary responsibility
3. THE Architecture_Document SHALL include an ASCII_Diagram showing the top-level directory layout and how Components relate to each other

### Requirement 2: Data Flow Section

**User Story:** As a contributor, I want to understand how a bootcamp session flows from onboarding through module completion, so that I can trace the path a user takes through the system.

#### Acceptance Criteria

1. THE Architecture_Document SHALL contain a "Data Flow" section that describes the end-to-end flow of a bootcamp session
2. THE Architecture_Document SHALL include an ASCII_Diagram showing the sequence from session start through onboarding, module execution, and session resume
3. WHEN describing the data flow, THE Architecture_Document SHALL identify which configuration files are read or written at each stage (bootcamp_progress.json, bootcamp_preferences.yaml, data_sources.yaml)
4. THE Architecture_Document SHALL describe how the agent determines whether to load `onboarding-flow.md` or `session-resume.md` at session start

### Requirement 3: Module Lifecycle Section

**User Story:** As a contributor, I want to understand how a module is loaded, executed, checkpointed, and completed, so that I can modify module behavior or add new modules.

#### Acceptance Criteria

1. THE Architecture_Document SHALL contain a "Module Lifecycle" section that describes the states a module passes through
2. THE Architecture_Document SHALL include an ASCII_Diagram showing the module lifecycle states: prerequisite check, steering file load, step execution, checkpointing, gate evaluation, and completion
3. WHEN describing module execution, THE Architecture_Document SHALL explain how split modules use phase-level loading from `steering-index.yaml`
4. THE Architecture_Document SHALL describe how `module-dependencies.yaml` gates control transitions between modules
5. THE Architecture_Document SHALL explain how step-level checkpointing updates `bootcamp_progress.json` after each numbered step

### Requirement 4: Hook Architecture Section

**User Story:** As a contributor, I want to understand how hooks are triggered, categorized, and interact with the agent, so that I can create or modify hooks.

#### Acceptance Criteria

1. THE Architecture_Document SHALL contain a "Hook Architecture" section that describes how hooks function within the system
2. THE Architecture_Document SHALL describe the two hook categories defined in `hook-categories.yaml`: critical hooks (created during onboarding) and module hooks (created when the associated module starts)
3. THE Architecture_Document SHALL include an ASCII_Diagram showing the hook trigger flow from IDE event through hook evaluation to agent action
4. WHEN describing hook behavior, THE Architecture_Document SHALL explain the hook silence rule (zero output when a check passes)
5. THE Architecture_Document SHALL describe how the `ask-bootcamper` hook owns all closing questions

### Requirement 5: Configuration Relationships Section

**User Story:** As a contributor, I want to understand how the configuration files relate to each other, so that I can trace data dependencies between them.

#### Acceptance Criteria

1. THE Architecture_Document SHALL contain a "Configuration Relationships" section that describes how `module-dependencies.yaml`, `steering-index.yaml`, `hook-categories.yaml`, and `bootcamp_progress.json` relate to each other
2. THE Architecture_Document SHALL include an ASCII_Diagram showing the data flow between configuration files
3. WHEN describing configuration relationships, THE Architecture_Document SHALL explain which files are read-only power assets versus which are mutable user state
4. THE Architecture_Document SHALL describe how `bootcamp_preferences.yaml` stores user choices that influence agent behavior (verbosity, conversation style, hooks installed)

### Requirement 6: MCP Integration Section

**User Story:** As a contributor, I want to understand how the Senzing MCP server integrates with the bootcamp, so that I can understand what capabilities come from MCP versus local files.

#### Acceptance Criteria

1. THE Architecture_Document SHALL contain an "MCP Integration" section that describes how the Senzing MCP server provides facts, code generation, and tool assistance
2. THE Architecture_Document SHALL describe the rule that all Senzing facts come from MCP tools and never from training data
3. WHEN describing MCP integration, THE Architecture_Document SHALL list the primary MCP tool categories (discovery, mapping, code generation, reference, diagnostics)
4. THE Architecture_Document SHALL include an ASCII_Diagram showing the boundary between local power assets and remote MCP capabilities
5. THE Architecture_Document SHALL describe the MCP failure and offline fallback behavior

### Requirement 7: Context Budget Management Section

**User Story:** As a contributor, I want to understand how steering files are loaded and unloaded based on token pressure, so that I can author steering files that respect context limits.

#### Acceptance Criteria

1. THE Architecture_Document SHALL contain a "Context Budget Management" section that describes how the agent manages context window pressure
2. THE Architecture_Document SHALL describe the three budget states: normal (below 60%), warn (60-80%), and critical (above 80%)
3. WHEN describing context management, THE Architecture_Document SHALL explain the retention priority order (agent-instructions > current module > language file > troubleshooting > everything else)
4. THE Architecture_Document SHALL describe how `steering-index.yaml` provides `token_count` and `size_category` metadata for each file
5. THE Architecture_Document SHALL explain how split modules reduce context pressure by loading only the current phase

### Requirement 8: Document Format and Accessibility

**User Story:** As a reader, I want the architecture document to be self-contained and readable in any text editor, so that I do not need external tools to understand the diagrams.

#### Acceptance Criteria

1. THE Architecture_Document SHALL use only ASCII characters or Unicode box-drawing characters for all diagrams
2. THE Architecture_Document SHALL require no external image files or rendering tools
3. THE Architecture_Document SHALL be valid CommonMark Markdown
4. THE Architecture_Document SHALL include a table of contents with anchor links to each major section
5. THE Architecture_Document SHALL be written for two audiences: contributors (who modify the power) and advanced bootcampers (who want to understand the system they are using)

### Requirement 9: Documentation Index Integration

**User Story:** As a reader, I want the architecture document to be discoverable from existing documentation entry points, so that I can find it without knowing it exists.

#### Acceptance Criteria

1. WHEN the Architecture_Document is created, THE docs/README.md SHALL be updated to reference it in the guides section
2. WHEN the Architecture_Document is created, THE docs/guides/README.md SHALL list it with a description
3. THE Architecture_Document SHALL cross-reference related documentation (POWER.md, GLOSSARY.md, STEERING_INDEX.md) with relative links
