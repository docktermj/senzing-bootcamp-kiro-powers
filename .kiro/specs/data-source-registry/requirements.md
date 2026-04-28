# Requirements Document

## Introduction

Bootcampers working through Modules 4–7 collect, evaluate, map, and load multiple data sources — but there is no single place that tracks the lifecycle state of each source across these modules. The agent re-discovers source metadata each time it starts a new module, and bootcampers have no quick way to see which sources are ready, which need quality fixes, and which have been loaded. This feature adds a `config/data_sources.yaml` registry that the agent maintains automatically as sources move through the pipeline, a `scripts/data_sources.py` CLI for viewing and managing the registry, and integration with the existing `status.py` script — giving both the agent and the bootcamper a single source of truth for data source state.

## Glossary

- **Registry**: The YAML file at `config/data_sources.yaml` in the bootcamper's project directory that stores metadata for every data source tracked by the bootcamp.
- **Registry_Entry**: A single data source record within the Registry, keyed by the DATA_SOURCE name (the Senzing identifier such as `CUSTOMERS_CRM`).
- **Agent**: The AI agent running the bootcamp, guided by steering files and hooks.
- **Quality_Score**: An integer from 0 to 100 representing the overall data quality of a source, calculated during Module 5 using the weighted formula defined in `docs/guides/QUALITY_SCORING_METHODOLOGY.md`.
- **Mapping_Status**: A string indicating the transformation state of a source: `pending` (not yet mapped), `in_progress` (mapping started), or `complete` (transformation program exists and validated).
- **Load_Status**: A string indicating the Senzing loading state of a source: `not_loaded`, `loading`, `loaded`, or `failed`.
- **Data_Sources_Script**: The Python script at `senzing-bootcamp/scripts/data_sources.py` that reads and displays the Registry from the command line.
- **Status_Script**: The existing Python script at `senzing-bootcamp/scripts/status.py` that shows bootcamp progress and project health.
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that the Agent loads at runtime for workflow instructions.
- **Quality_Threshold**: The minimum Quality_Score (70) below which the Agent recommends fixing data quality before loading.

## Requirements

### Requirement 1: Registry Schema Definition

**User Story:** As a power developer, I want a well-defined YAML schema for the data source registry, so that the agent and CLI tools can read and write it consistently.

#### Acceptance Criteria

1. THE Registry SHALL be a YAML file located at `config/data_sources.yaml` in the bootcamper's project directory.
2. THE Registry SHALL contain a top-level `version` field set to the string `"1"`.
3. THE Registry SHALL contain a top-level `sources` mapping where each key is a DATA_SOURCE name (uppercase, underscores allowed) and each value is a Registry_Entry.
4. EACH Registry_Entry SHALL contain the following fields: `name` (string, human-readable display name), `file_path` (string, relative path to the source file in `data/raw/` or `data/transformed/`), `format` (string, one of `csv`, `json`, `jsonl`, `xlsx`, `parquet`, `xml`, or `other`), `record_count` (integer or null), `file_size_bytes` (integer or null), `quality_score` (integer 0–100 or null), `mapping_status` (string, one of `pending`, `in_progress`, `complete`), `load_status` (string, one of `not_loaded`, `loading`, `loaded`, `failed`), `added_at` (ISO 8601 timestamp string), and `updated_at` (ISO 8601 timestamp string).
5. EACH Registry_Entry SHALL default `quality_score` to null, `mapping_status` to `pending`, and `load_status` to `not_loaded` when first created.
6. IF a Registry_Entry contains a field value that is not one of the allowed values for that field, THEN THE Agent SHALL reject the update and report the invalid value to the bootcamper.

### Requirement 2: Auto-Populate Registry During Data Collection

**User Story:** As a bootcamper, I want the registry to be populated automatically when I collect data sources in Module 4, so that I do not have to manually track each source.

#### Acceptance Criteria

1. WHEN the Agent identifies a new data source file in `data/raw/` during Module 4, THE Agent SHALL create a Registry_Entry for that source with the `name`, `file_path`, `format`, `record_count`, and `file_size_bytes` fields populated from the file.
2. WHEN the Agent creates a new Registry_Entry, THE Agent SHALL set `added_at` and `updated_at` to the current ISO 8601 timestamp.
3. WHEN the Agent creates a new Registry_Entry, THE Agent SHALL set `quality_score` to null, `mapping_status` to `pending`, and `load_status` to `not_loaded`.
4. IF the Registry file does not exist when the Agent attempts to add a source, THEN THE Agent SHALL create the Registry file with `version: "1"` and an empty `sources` mapping before adding the entry.
5. IF a Registry_Entry already exists for a DATA_SOURCE name, THEN THE Agent SHALL update the existing entry rather than creating a duplicate, and SHALL update the `updated_at` timestamp.

### Requirement 3: Update Quality Score During Data Quality Assessment

**User Story:** As a bootcamper, I want the registry to reflect my data quality scores after Module 5 assessment, so that I can see at a glance which sources need quality improvement.

#### Acceptance Criteria

1. WHEN the Agent completes a quality assessment for a data source during Module 5 Phase 1, THE Agent SHALL update the corresponding Registry_Entry `quality_score` field with the calculated overall score (integer 0–100).
2. WHEN the Agent updates a Registry_Entry `quality_score`, THE Agent SHALL update the `updated_at` timestamp.
3. WHEN the Agent updates a `quality_score` that is below the Quality_Threshold (70), THE Agent SHALL log a warning in the Registry_Entry by adding an `issues` list field containing a string describing the quality concern.

### Requirement 4: Update Mapping Status During Data Mapping

**User Story:** As a bootcamper, I want the registry to track which sources have been mapped, so that I know which sources are ready for loading.

#### Acceptance Criteria

1. WHEN the Agent starts the mapping workflow for a data source during Module 5 Phase 2, THE Agent SHALL update the corresponding Registry_Entry `mapping_status` to `in_progress` and update the `updated_at` timestamp.
2. WHEN the Agent completes the mapping workflow and saves a transformation program for a data source, THE Agent SHALL update the corresponding Registry_Entry `mapping_status` to `complete` and update the `updated_at` timestamp.
3. WHEN the Agent completes mapping for a source, THE Agent SHALL update the Registry_Entry `file_path` to point to the transformed output file in `data/transformed/` if a transformation was created.

### Requirement 5: Update Load Status During Source Loading

**User Story:** As a bootcamper, I want the registry to track which sources have been loaded into Senzing, so that I can see the overall loading progress across all sources.

#### Acceptance Criteria

1. WHEN the Agent begins loading a data source during Module 6 or Module 7, THE Agent SHALL update the corresponding Registry_Entry `load_status` to `loading` and update the `updated_at` timestamp.
2. WHEN the Agent completes loading a data source successfully, THE Agent SHALL update the corresponding Registry_Entry `load_status` to `loaded` and update the `updated_at` timestamp.
3. IF loading fails for a data source, THEN THE Agent SHALL update the corresponding Registry_Entry `load_status` to `failed`, add an `issues` list field containing a string describing the failure, and update the `updated_at` timestamp.
4. WHEN the Agent updates `load_status` to `loaded`, THE Agent SHALL update the `record_count` field with the actual number of records loaded if it differs from the original estimate.

### Requirement 6: Agent Recommendations Based on Registry

**User Story:** As a bootcamper, I want the agent to use the registry to give me smarter recommendations, so that I avoid loading low-quality data or missing unmapped sources.

#### Acceptance Criteria

1. WHEN the Agent begins Module 6 or Module 7, THE Agent SHALL read the Registry and present a summary table of all sources with their `quality_score`, `mapping_status`, and `load_status`.
2. WHEN the Agent reads the Registry and finds a source with `quality_score` below the Quality_Threshold (70) and `load_status` of `not_loaded`, THE Agent SHALL recommend fixing data quality before loading that source, citing the specific score.
3. WHEN the Agent reads the Registry and finds a source with `mapping_status` of `pending` and `load_status` of `not_loaded`, THE Agent SHALL recommend completing mapping before loading that source.
4. WHEN the Agent reads the Registry during Module 7 to determine load order, THE Agent SHALL use `quality_score` values to recommend loading higher-quality sources first.

### Requirement 7: CLI Script for Viewing and Managing the Registry

**User Story:** As a bootcamper, I want a command-line tool to view and manage the data source registry, so that I can check source status without starting an agent session.

#### Acceptance Criteria

1. THE Data_Sources_Script SHALL be located at `senzing-bootcamp/scripts/data_sources.py` and SHALL be executable as `python senzing-bootcamp/scripts/data_sources.py` from the repository root with no external dependencies beyond the Python standard library.
2. WHEN the Data_Sources_Script is run with no arguments, THE script SHALL display a formatted table of all Registry_Entries showing DATA_SOURCE name, record count, quality score, mapping status, and load status.
3. WHEN the Data_Sources_Script is run with a `--detail <DATA_SOURCE>` argument, THE script SHALL display all fields for the specified Registry_Entry.
4. WHEN the Data_Sources_Script is run with a `--summary` argument, THE script SHALL display aggregate statistics: total sources, sources by mapping status count, sources by load status count, average quality score, and total record count.
5. IF the Registry file does not exist when the Data_Sources_Script runs, THEN THE script SHALL print a message stating that no data sources have been registered and exit with status code 0.
6. IF the `--detail` argument specifies a DATA_SOURCE name that does not exist in the Registry, THEN THE script SHALL print an error message listing the available DATA_SOURCE names and exit with a non-zero status code.

### Requirement 8: Integration with Status Script

**User Story:** As a bootcamper, I want the existing status command to include a data source summary, so that I get a complete picture of my bootcamp progress in one place.

#### Acceptance Criteria

1. WHEN the Status_Script runs and the Registry file exists, THE Status_Script SHALL display a "Data Sources" section after the "Project Health" section showing the count of sources by load status (loaded, not loaded, loading, failed).
2. WHEN the Status_Script runs and the Registry file exists and contains at least one source with a `quality_score` below the Quality_Threshold (70), THE Status_Script SHALL display a warning line listing the source names that need quality improvement.
3. WHEN the Status_Script runs and the Registry file does not exist, THE Status_Script SHALL not display the "Data Sources" section.

### Requirement 9: Steering File Updates for Registry Maintenance

**User Story:** As a power developer, I want the module steering files to instruct the agent to maintain the registry, so that the registry stays current as bootcampers progress through modules.

#### Acceptance Criteria

1. THE Module 4 Steering_File SHALL include instructions for the Agent to create or update Registry_Entries when data source files are collected.
2. THE Module 5 Steering_File SHALL include instructions for the Agent to update `quality_score` after Phase 1 assessment and `mapping_status` during Phase 2 mapping.
3. THE Module 6 Steering_File SHALL include instructions for the Agent to update `load_status` when loading begins, completes, or fails.
4. THE Module 7 Steering_File SHALL include instructions for the Agent to read the Registry for load order planning and update `load_status` for each source during orchestration.

### Requirement 10: POWER.md Documentation Update

**User Story:** As a power developer, I want POWER.md to document the data source registry feature, so that users and contributors understand the registry and its tooling.

#### Acceptance Criteria

1. THE POWER.md file SHALL mention the data source registry in the feature description or "What's New" section.
2. THE POWER.md file SHALL list `data_sources.py` in the "Useful Commands" section with usage examples for the default view, `--detail`, and `--summary` modes.
3. THE POWER.md file SHALL describe the `config/data_sources.yaml` file in the "Project Directory Structure" section or its equivalent.

### Requirement 11: Registry File Validation

**User Story:** As a power developer, I want the registry to be validated for structural correctness, so that malformed entries do not cause agent or script errors.

#### Acceptance Criteria

1. WHEN the Data_Sources_Script reads the Registry, THE script SHALL verify that the `version` field is present and equals `"1"`.
2. WHEN the Data_Sources_Script reads the Registry, THE script SHALL verify that each Registry_Entry contains all required fields (`name`, `file_path`, `format`, `record_count`, `quality_score`, `mapping_status`, `load_status`, `added_at`, `updated_at`).
3. WHEN the Data_Sources_Script reads the Registry, THE script SHALL verify that `mapping_status` values are one of `pending`, `in_progress`, or `complete` and that `load_status` values are one of `not_loaded`, `loading`, `loaded`, or `failed`.
4. IF validation fails, THEN THE Data_Sources_Script SHALL print a descriptive error message identifying the invalid entry and field, and exit with a non-zero status code.
