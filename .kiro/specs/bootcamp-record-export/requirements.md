# Requirements Document

## Introduction

After completing the Senzing Bootcamp, bootcampers have made dozens of decisions — business problem framing, SDK platform choices, data source selection, field mapping configurations, loading strategies, query programs, and optional production-readiness work. These decisions exist scattered across config files, source code, and documentation. There is no single artifact that captures the full decision trail in a portable, replayable format.

This feature adds a "record export" capability to the graduation flow that generates a structured decision manifest. The manifest captures every meaningful choice the bootcamper made, in a format that can be shared with colleagues for review or fed back into a fresh bootcamp instance to replay the same decisions on a different machine or project.

## Glossary

- **Record_Export_Generator**: The component (steering logic or script) that collects decisions from existing config files and produces the Decision_Manifest.
- **Decision_Manifest**: A structured YAML or Markdown document capturing all bootcamp decisions, configurations, and choices in a portable, replayable format.
- **Graduation_Flow**: The post-completion workflow defined in `steering/graduation.md` that transitions a bootcamp project into production readiness.
- **Module_Completion_Flow**: The workflow defined in `steering/module-completion.md` that handles track completion detection and celebration.
- **Progress_Data**: The JSON structure in `config/bootcamp_progress.json` tracking module completion state, current module, and step history.
- **Preferences_Data**: The YAML structure in `config/bootcamp_preferences.yaml` storing language, track, database type, deployment target, and other user choices.
- **Data_Sources_Registry**: The YAML file at `config/data_sources.yaml` listing registered data sources with names, file paths, and metadata.
- **Mapping_Spec**: Per-source mapping configuration files that define field-to-feature mappings and entity types.
- **Track_Endpoint**: The final module in a bootcamper's chosen track (Module 7 for Core Bootcamp, Module 11 for Advanced Topics).
- **Replay_Mode**: A theoretical future capability where the Decision_Manifest is consumed to pre-populate choices in a new bootcamp session.

## Requirements

### Requirement 1: Export Offer at Track Completion

**User Story:** As a bootcamper who just finished my track, I want to be offered the option to generate a record of my journey, so that I can share it or reuse my decisions later.

#### Acceptance Criteria

1. WHEN the bootcamper reaches their Track_Endpoint and the path completion celebration is presented, THE Module_Completion_Flow SHALL offer the export option: "Would you like a record of your bootcamp journey? You can share it with your team or use it to replay the same setup on another project."
2. THE export offer SHALL appear after the existing export-results option and before the analytics offer in the track completion sequence.
3. WHEN the bootcamper declines the export offer, THE Module_Completion_Flow SHALL proceed to the next step without generating any export file.
4. WHEN the bootcamper accepts the export offer, THE Record_Export_Generator SHALL produce the Decision_Manifest and present the output file path to the bootcamper.

### Requirement 2: Decision Manifest Output Location and Format

**User Story:** As a bootcamper, I want the export saved to a predictable location in a human-readable format, so that I can find it easily and read it without special tools.

#### Acceptance Criteria

1. THE Record_Export_Generator SHALL save the Decision_Manifest to `docs/bootcamp_record.yaml`.
2. THE Decision_Manifest SHALL use YAML format with clear section headings and inline comments explaining each field.
3. THE Decision_Manifest SHALL include a `metadata` section at the top containing the generation timestamp (ISO 8601), the bootcamp power version, and a schema version identifier.
4. THE Decision_Manifest SHALL be valid YAML parseable by any standard YAML parser.
5. WHEN `docs/bootcamp_record.yaml` already exists, THE Record_Export_Generator SHALL ask the bootcamper whether to overwrite or abort before writing.

### Requirement 3: Business Problem Capture

**User Story:** As a bootcamper, I want my business problem definition included in the record, so that colleagues understand the context behind my technical decisions.

#### Acceptance Criteria

1. WHEN Module 1 was completed, THE Decision_Manifest SHALL include a `business_problem` section containing the problem statement, identified data sources, and success criteria as documented during Module 1.
2. THE Record_Export_Generator SHALL extract business problem data from `docs/bootcamp_journal.md` Module 1 entries and any Module 1 artifacts in the project.
3. WHEN Module 1 data is not available, THE Decision_Manifest SHALL include the `business_problem` section with a note indicating the data was not captured.

### Requirement 4: SDK and Platform Choices Capture

**User Story:** As a bootcamper, I want my SDK setup choices recorded, so that a colleague can replicate the same development environment.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL include a `sdk_setup` section containing the chosen programming language, database type, and platform.
2. THE Record_Export_Generator SHALL extract the language value from the `language` field in Preferences_Data.
3. THE Record_Export_Generator SHALL extract the database type from the `database_type` field in Preferences_Data.
4. THE Record_Export_Generator SHALL extract the deployment target from the `deployment_target` field in Preferences_Data when present.
5. WHEN Preferences_Data is not available, THE Record_Export_Generator SHALL attempt to infer language from source file extensions in `src/` and note that preferences were unavailable.

### Requirement 5: Data Sources Capture

**User Story:** As a bootcamper, I want my data source selections recorded with their metadata, so that a replay can use the same sources.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL include a `data_sources` section listing each registered data source.
2. WHEN the Data_Sources_Registry exists at `config/data_sources.yaml`, THE Record_Export_Generator SHALL extract source names, file paths, and record counts from the registry.
3. FOR EACH data source in the registry, THE Decision_Manifest SHALL record the source name, relative file path, file format, and record count.
4. THE Decision_Manifest SHALL NOT include actual data records or PII from the source files — only structural metadata.
5. WHEN the Data_Sources_Registry does not exist, THE Record_Export_Generator SHALL scan `data/raw/` for files and record their names and sizes as a fallback.

### Requirement 6: Mapping Decisions Capture

**User Story:** As a bootcamper, I want my field mapping decisions recorded per source, so that a replay can apply the same mappings without re-doing the analysis.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL include a `mapping_decisions` section with per-source mapping configurations.
2. FOR EACH data source, THE Decision_Manifest SHALL record the entity type assigned, the field-to-feature mappings, and any transformation rules applied.
3. THE Record_Export_Generator SHALL extract mapping data from Mapping_Spec files in the project (mapping configuration files produced during Module 5).
4. WHEN mapping specs are not found, THE Record_Export_Generator SHALL check `data/transformed/` for transformation scripts and extract mapping intent from code comments or file structure.
5. THE Decision_Manifest SHALL NOT include sample data values in the mapping section — only field names, feature names, and transformation logic descriptions.

### Requirement 7: Loading Configuration Capture

**User Story:** As a bootcamper, I want my loading strategy recorded, so that a replay knows whether I used single-source or multi-source loading and what redo processing choices I made.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL include a `loading_config` section describing the loading strategy used.
2. THE Decision_Manifest SHALL record whether single-source or multi-source loading was used.
3. WHEN redo processing was configured during Module 6, THE Decision_Manifest SHALL record the redo processing choice (enabled or disabled) and the reason.
4. THE Record_Export_Generator SHALL extract loading configuration from source files in `src/load/` and from the bootcamp journal Module 6 entries.
5. WHEN loading scripts exist, THE Decision_Manifest SHALL record the script filenames and their purpose (initial load, redo, multi-source orchestration).

### Requirement 8: Query Programs Capture

**User Story:** As a bootcamper, I want my query programs referenced in the record, so that a colleague can see what queries I built and replicate them.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL include a `query_programs` section listing query scripts created during Module 7.
2. FOR EACH query script in `src/query/`, THE Decision_Manifest SHALL record the filename, the query type (search by attributes, get entity, find relationships, etc.), and a brief description extracted from code comments or the bootcamp journal.
3. THE Decision_Manifest SHALL NOT include the full source code of query programs — only filenames, types, and descriptions.
4. WHEN no query scripts exist in `src/query/`, THE Decision_Manifest SHALL note that no query programs were created.

### Requirement 9: Optional Module Decisions Capture

**User Story:** As a bootcamper who completed advanced modules, I want those decisions captured too, so that the record reflects my full journey including production-readiness work.

#### Acceptance Criteria

1. WHEN Module 8 (Performance) was completed, THE Decision_Manifest SHALL include a `performance_tuning` section recording tuning decisions, baseline metrics, and optimization choices.
2. WHEN Module 9 (Security) was completed, THE Decision_Manifest SHALL include a `security_hardening` section recording security choices from the security checklist.
3. WHEN Module 10 (Monitoring) was completed, THE Decision_Manifest SHALL include a `monitoring_config` section recording monitoring tool choices and alert configurations.
4. WHEN Module 11 (Deployment) was completed, THE Decision_Manifest SHALL include a `deployment` section recording the deployment target, infrastructure choices, and deployment method.
5. WHEN an optional module was not completed, THE Decision_Manifest SHALL omit the corresponding section entirely rather than including empty placeholders.

### Requirement 10: Track and Progress Metadata

**User Story:** As a bootcamper, I want the record to show which track I took and which modules I completed or skipped, so that the context of my journey is clear.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL include a `track_progress` section recording the track name (Core Bootcamp or Advanced Topics), track identifier, and total module count for the track.
2. THE Decision_Manifest SHALL list all modules completed with their completion dates where available from Progress_Data.
3. THE Decision_Manifest SHALL list any modules that were skipped and the skip reason if recorded.
4. THE Decision_Manifest SHALL record the total elapsed time from first module start to track completion when timestamps are available in Progress_Data.

### Requirement 11: Security and Privacy Constraints

**User Story:** As a bootcamper, I want assurance that the exported record contains no sensitive information, so that I can safely share it with colleagues.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL NOT contain any actual data records, PII, or sample values from data source files.
2. THE Decision_Manifest SHALL NOT contain API keys, secrets, credentials, database connection strings, or authentication tokens.
3. THE Decision_Manifest SHALL NOT contain absolute file paths — all paths SHALL be relative to the project root.
4. THE Record_Export_Generator SHALL scan generated content for common secret patterns (strings matching API key formats, connection strings, tokens) and redact any matches before writing.
5. IF the Record_Export_Generator detects potential sensitive content during generation, THEN THE Record_Export_Generator SHALL warn the bootcamper and omit the suspect content.

### Requirement 12: Data Source Aggregation from Existing Files

**User Story:** As a bootcamper, I want the export to pull all information from existing config files rather than asking me to re-enter anything, so that the process is effortless.

#### Acceptance Criteria

1. THE Record_Export_Generator SHALL read from `config/bootcamp_progress.json` for module completion data.
2. THE Record_Export_Generator SHALL read from `config/bootcamp_preferences.yaml` for language, track, database, and deployment choices.
3. THE Record_Export_Generator SHALL read from `config/data_sources.yaml` for data source metadata.
4. THE Record_Export_Generator SHALL read from `docs/bootcamp_journal.md` for module narratives and artifact descriptions.
5. THE Record_Export_Generator SHALL scan `src/load/` and `src/query/` for script filenames and code comments.
6. THE Record_Export_Generator SHALL NOT prompt the bootcamper for any information that is available in existing files.
7. WHEN a required source file is missing, THE Record_Export_Generator SHALL log a warning and continue with available data rather than failing.

### Requirement 13: Replay Schema Compatibility

**User Story:** As a bootcamper, I want the export format to be structured enough that it could theoretically drive an automated replay, so that the record has long-term utility beyond documentation.

#### Acceptance Criteria

1. THE Decision_Manifest SHALL use a versioned schema (starting at `schema_version: "1.0"`) to support future format evolution.
2. THE Decision_Manifest SHALL use consistent key naming (snake_case) throughout all sections.
3. EACH decision entry in the Decision_Manifest SHALL include a `module` field indicating which module produced the decision.
4. THE Decision_Manifest SHALL structure choices as key-value pairs with machine-readable values (not free-text prose) wherever possible.
5. THE Decision_Manifest SHALL include a `replay_notes` section at the end listing any decisions that could not be captured in machine-readable form and would require manual input during replay.
