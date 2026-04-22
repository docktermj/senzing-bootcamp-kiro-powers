# Requirements Document

## Introduction

This spec retroactively documents the core agent behavior rules and communication patterns defined in `senzing-bootcamp/steering/agent-instructions.md` and related features delivered across v0.3.0–v0.8.0. It covers the agent-instructions/onboarding split, language steering files, MCP tool rules, file placement policy, interactive data visualization, zero-matches handling, SQLite record recommendations, and AWS CDK guidance.

## Glossary

- **Agent**: The AI assistant executing the Senzing Bootcamp steering files.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent_Instructions**: The always-loaded steering file (`senzing-bootcamp/steering/agent-instructions.md`) containing core rules for file placement, MCP usage, communication, and module steering.
- **Language_Steering_File**: One of five language-specific steering files (`lang-python.md`, `lang-java.md`, `lang-csharp.md`, `lang-rust.md`, `lang-typescript.md`) loaded via `fileMatch` on matching extensions.
- **MCP_Tools**: The Senzing MCP server tools (`mapping_workflow`, `generate_scaffold`, `sdk_guide`, `get_sdk_reference`, `explain_error_code`, `search_docs`, `find_examples`, `get_capabilities`).
- **Working_Directory**: The project root directory; all generated files must reside within it.

## Requirements

### Requirement 1: Agent Instructions Split and Context Optimization

**User Story:** As a Bootcamper, I want the agent to load only essential core rules by default and defer onboarding to a separate file, so that context budget is preserved for module work.

#### Acceptance Criteria

1. THE Agent_Instructions SHALL use `inclusion: always` frontmatter so it loads automatically every session.
2. THE Agent_Instructions SHALL contain only core rules: file placement, MCP rules, MCP failure handling, module steering references, state management, communication patterns, and hook installation.
3. WHEN a new Bootcamper starts (no `config/bootcamp_progress.json`), THE Agent SHALL load `onboarding-flow.md` as a separate steering file rather than including onboarding steps in Agent_Instructions.
4. WHEN a returning Bootcamper starts (`config/bootcamp_progress.json` exists), THE Agent SHALL load `session-resume.md` instead of `onboarding-flow.md`.

### Requirement 2: Language Steering and MCP Tool Routing

**User Story:** As a Bootcamper, I want language-specific guidance loaded automatically when I edit code files, and I want all Senzing information sourced from MCP tools, so that I get accurate, language-appropriate help.

#### Acceptance Criteria

1. THE Agent SHALL provide five Language_Steering_Files with `fileMatch` inclusion patterns: `lang-python.md` (*.py), `lang-java.md` (*.java), `lang-csharp.md` (*.cs), `lang-rust.md` (*.rs), `lang-typescript.md` (*.ts).
2. THE Agent SHALL route MCP tool calls by purpose: `mapping_workflow` for attribute names, `generate_scaffold`/`sdk_guide` for SDK code, `get_sdk_reference` for method signatures, `explain_error_code` for errors, `search_docs` for documentation, `find_examples` for examples.
3. THE Agent SHALL source all Senzing facts from MCP_Tools and never from training data.
4. IF an MCP tool call fails, THEN THE Agent SHALL retry once, then load the "MCP Server Unavailable" section from `common-pitfalls.md` for fallback guidance.
5. THE Agent SHALL flag MCP responses referencing data mart tables (`sz_dm_report`), beta features, or non-core SDK references as potentially unreliable.

### Requirement 3: File Placement and Working Directory Policy

**User Story:** As a Bootcamper, I want all generated files placed within my project directory using the defined layout, so that my project stays organized and portable.

#### Acceptance Criteria

1. THE Agent SHALL place all generated files within the Working_Directory using the defined layout: `src/` for code, `scripts/` for scripts, `docs/` for documentation, `data/` for data files, `database/` for SQLite, `config/` for configuration, `data/temp/` for temporary files.
2. THE Agent SHALL reject file paths outside the Working_Directory including `/tmp`, `%TEMP%`, and `~/Downloads`.
3. WHEN an MCP tool returns a path outside the Working_Directory (e.g., `/tmp/` or `ExampleEnvironment`), THE Agent SHALL override the path to a project-relative equivalent.
4. WHEN the Bootcamper uses SQLite as the database, THE Agent SHALL recommend keeping the record count at or below 1,000 records for the best bootcamp experience.
5. WHEN the Bootcamper asks about deploying to AWS, THE Agent SHALL recommend AWS CDK for infrastructure-as-code.

### Requirement 4: Communication Patterns and Data Presentation

**User Story:** As a Bootcamper, I want clear communication with one question at a time, visual markers for required input, and the option to visualize data results interactively, so that I can follow along without confusion.

#### Acceptance Criteria

1. THE Agent SHALL ask one question at a time and WAIT for the Bootcamper's response before proceeding.
2. WHEN asking a question that requires Bootcamper input, THE Agent SHALL prefix the question with a 👉 marker.
3. WHEN presenting data results (entity resolution results, quality analysis, match explanations, statistics), THE Agent SHALL offer: "👉 Would you like me to visualize this data as a web page?" and, if accepted, ask what interactive features the Bootcamper wants.
4. WHEN generating a data visualization, THE Agent SHALL save the output to `docs/` or `data/temp/`.
5. WHEN Module 8 entity resolution produces zero matches, THE Agent SHALL handle the result gracefully by explaining the outcome and guiding the Bootcamper through possible causes.
