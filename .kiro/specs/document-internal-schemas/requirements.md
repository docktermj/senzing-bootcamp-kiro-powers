# Requirements Document

## Introduction

Three internal configuration files used by the senzing-bootcamp power are undocumented: `config/bootcamp_progress.json` (session progress tracking), `config/data_sources.yaml` (data source registry), and `senzing-bootcamp/steering/steering-index.yaml` (steering file index). Bootcampers encountering these files have no reference for understanding their structure, and maintainers editing them risk introducing invalid data without knowing the schema constraints.

This feature adds three schema guide documents to `docs/guides/`: `PROGRESS_FILE_SCHEMA.md`, `DATA_SOURCE_REGISTRY.md`, and `STEERING_INDEX.md`. Each guide documents the file's field definitions, types, valid values, a complete example, and which scripts and steering files read or write the file. The guides follow the existing documentation style in `docs/guides/`.

## Glossary

- **Progress_File**: The JSON file at `config/bootcamp_progress.json` that stores completed modules, current module, current step, step history, data sources, and database type. Created during onboarding and updated after each step checkpoint.
- **Data_Source_Registry**: The YAML file at `config/data_sources.yaml` that tracks every data source the bootcamper registers, including file path, format, record count, quality score, mapping status, and load status. Created when the first data source is added in Module 4 or 5.
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps module numbers to steering file paths, defines keyword-to-file lookups, lists language and deployment file mappings, stores per-file token counts and size categories, and tracks the overall context budget.
- **Schema_Guide**: A Markdown document in `docs/guides/` that describes the structure, field definitions, types, valid values, and usage of an internal configuration file.
- **Guide_Directory**: The directory at `senzing-bootcamp/docs/guides/` containing user-facing reference documentation for the bootcamp.
- **Guides_README**: The file at `senzing-bootcamp/docs/guides/README.md` that indexes all available guides with descriptions and links.

## Requirements

### Requirement 1: Progress File Schema Guide

**User Story:** As a bootcamper, I want a schema guide for `bootcamp_progress.json`, so that I can understand what each field means and how the file tracks my progress through the bootcamp.

#### Acceptance Criteria

1. THE Schema_Guide SHALL be located at `docs/guides/PROGRESS_FILE_SCHEMA.md`
2. THE Schema_Guide SHALL include a field definitions section that documents every top-level field in the Progress_File: `modules_completed`, `current_module`, `current_step`, `step_history`, `data_sources`, `database_type`, and `language`
3. WHEN documenting a field, THE Schema_Guide SHALL specify the field name, JSON type, whether the field is required or optional, valid values or constraints, and a one-line description
4. THE Schema_Guide SHALL include a complete example showing a valid Progress_File with at least two completed modules, a current module with an active step, populated step_history entries, and at least one data source
5. THE Schema_Guide SHALL include a "Read By" section listing the scripts and steering files that read the Progress_File: `status.py`, `validate_module.py`, `repair_progress.py`, `export_results.py`, `rollback_module.py`, `session-resume.md`, and `agent-instructions.md`
6. THE Schema_Guide SHALL include a "Written By" section listing the scripts and steering files that create or update the Progress_File: `progress_utils.py` (step checkpoints), `repair_progress.py --fix` (reconstruction), and the agent during onboarding and module transitions

### Requirement 2: Progress File Step History Documentation

**User Story:** As a maintainer, I want the progress file schema guide to document the `step_history` nested structure, so that I can correctly implement step-level checkpointing in new scripts.

#### Acceptance Criteria

1. THE Schema_Guide for the Progress_File SHALL document the `step_history` object structure: keys are string representations of module numbers ("1" through "11"), values are objects containing `last_completed_step` (integer) and `updated_at` (ISO 8601 UTC string)
2. THE Schema_Guide SHALL document that `current_step` accepts both integer values (whole-step checkpoints) and null (module completion), and note that sub-step string identifiers (e.g., "5.3", "7a") are supported per the mid-module session persistence feature
3. THE Schema_Guide SHALL document the validation rules enforced by `progress_utils.validate_progress_schema`: `current_step` must be int or null, `step_history` keys must be string integers in range 1-12, and each entry must contain `last_completed_step` (int) and `updated_at` (valid ISO 8601)

### Requirement 3: Data Source Registry Schema Guide

**User Story:** As a bootcamper, I want a schema guide for `data_sources.yaml`, so that I can understand the registry structure and what each status value means for my data sources.

#### Acceptance Criteria

1. THE Schema_Guide SHALL be located at `docs/guides/DATA_SOURCE_REGISTRY.md`
2. THE Schema_Guide SHALL document the top-level structure: `version` (string, currently "2") and `sources` (mapping of DATA_SOURCE keys to entry objects)
3. THE Schema_Guide SHALL document the DATA_SOURCE key constraint: must match the pattern `^[A-Z][A-Z0-9_]*$`
4. THE Schema_Guide SHALL document every entry field: `name`, `file_path`, `format`, `record_count`, `file_size_bytes`, `quality_score`, `mapping_status`, `load_status`, `test_load_status`, `test_entity_count`, `added_at`, `updated_at`, and `issues`
5. WHEN documenting an entry field, THE Schema_Guide SHALL specify the field name, YAML type, whether the field is required or optional, valid values (including enum sets for status fields), and a one-line description
6. THE Schema_Guide SHALL document the valid enum values: `format` accepts csv, json, jsonl, xlsx, parquet, xml, or other; `mapping_status` accepts pending, in_progress, or complete; `load_status` accepts not_loaded, loading, loaded, or failed; `test_load_status` accepts complete or skipped

### Requirement 4: Data Source Registry Usage and Examples

**User Story:** As a maintainer, I want the data source registry guide to include a complete example and list which scripts interact with the file, so that I can safely modify the registry or write new tooling.

#### Acceptance Criteria

1. THE Schema_Guide for the Data_Source_Registry SHALL include a complete example showing a valid registry with version "2" and at least two data source entries demonstrating different status combinations (e.g., one loaded source and one pending source)
2. THE Schema_Guide SHALL include a "Read By" section listing: `data_sources.py` (CLI views and recommendations), `status.py` (dashboard integration via `render_data_sources_section`), and the agent during Modules 4 through 7
3. THE Schema_Guide SHALL include a "Written By" section listing: the agent during data source registration (Modules 4-5), `data_sources.py --migrate` (schema migration), and the agent during loading status updates (Module 6)
4. THE Schema_Guide SHALL document the schema migration path: version "1" registries are automatically migrated to version "2" by backfilling `test_load_status` and `test_entity_count` as null

### Requirement 5: Steering Index Schema Guide

**User Story:** As a maintainer, I want a schema guide for `steering-index.yaml`, so that I can correctly add new modules, keywords, or steering files without breaking the agent's file selection logic.

#### Acceptance Criteria

1. THE Schema_Guide SHALL be located at `docs/guides/STEERING_INDEX.md`
2. THE Schema_Guide SHALL document all top-level sections: `modules`, `keywords`, `languages`, `deployment`, `file_metadata`, and `budget`
3. THE Schema_Guide SHALL document the two module entry formats: simple (module number maps to a filename string) and split (module number maps to an object with `root` key and `phases` mapping, where each phase has `file`, `token_count`, `size_category`, and `step_range`)
4. THE Schema_Guide SHALL document the `keywords` section as a mapping of trigger words to steering filenames, used by the agent to load context-relevant files when the bootcamper mentions a keyword
5. THE Schema_Guide SHALL document the `languages` and `deployment` sections as mappings of language names or deployment targets to their respective steering filenames

### Requirement 6: Steering Index File Metadata and Budget Documentation

**User Story:** As a maintainer, I want the steering index guide to document the file_metadata and budget sections, so that I can keep token counts accurate and understand the context budget thresholds.

#### Acceptance Criteria

1. THE Schema_Guide for the Steering_Index SHALL document the `file_metadata` section: each key is a steering filename, each value contains `token_count` (integer, approximate tokens calculated as characters divided by 4) and `size_category` (string: "small", "medium", or "large")
2. THE Schema_Guide SHALL document the `budget` section fields: `total_tokens` (integer, sum of all file token counts), `reference_window` (integer, the context window size used for threshold calculations), `warn_threshold_pct` (integer, percentage at which to start deferring file loads), `critical_threshold_pct` (integer, percentage at which to unload non-essential files), and `split_threshold_tokens` (integer, token count above which a steering file should be split into phases)
3. THE Schema_Guide SHALL include a complete example showing a valid steering index with at least one simple module entry, one split module entry with phases, two keyword entries, one language entry, one deployment entry, two file_metadata entries, and a budget section
4. THE Schema_Guide SHALL include a "Read By" section listing: the agent (module steering selection, keyword lookup, context budget tracking), `validate_power.py` (cross-reference checks), `measure_steering.py --check` (token count verification), and `lint_steering.py` (structural validation)
5. THE Schema_Guide SHALL include a "Written By" section listing: `measure_steering.py` (updates file_metadata and budget after scanning), `split_steering.py` (adds phase entries for split modules), and maintainers (manual edits to modules, keywords, languages, and deployment sections)

### Requirement 7: Consistent Documentation Style

**User Story:** As a bootcamper, I want the new schema guides to follow the same style as existing guides, so that the documentation feels cohesive and I can find information in a predictable structure.

#### Acceptance Criteria

1. WHEN creating a Schema_Guide, THE Schema_Guide SHALL use a level-1 heading with the guide title, followed by an introductory paragraph explaining what the file is and why it matters
2. THE Schema_Guide SHALL organize content under level-2 headings in this order: an overview or introduction, field definitions (using a Markdown table or definition list), a complete example (in a fenced code block with the appropriate language tag), a "Read By" section, and a "Written By" section
3. THE Schema_Guide SHALL use fenced code blocks with language identifiers (`json` for the Progress_File example, `yaml` for the Data_Source_Registry and Steering_Index examples) for all file examples
4. THE Schema_Guide SHALL define technical terms on first use, consistent with the inline-definition convention described in `agent-instructions.md`

### Requirement 8: Guides README Integration

**User Story:** As a bootcamper, I want the new schema guides listed in the guides README, so that I can discover them from the central documentation index.

#### Acceptance Criteria

1. WHEN all three Schema_Guides are created, THE Guides_README SHALL include entries for `PROGRESS_FILE_SCHEMA.md`, `DATA_SOURCE_REGISTRY.md`, and `STEERING_INDEX.md` in the "Reference Documentation" section
2. WHEN listing a Schema_Guide in the Guides_README, THE entry SHALL include the filename as a Markdown link, a bold title, and a two-to-three line description of what the guide covers
3. THE Guides_README SHALL list the three new guides in the Documentation Structure tree under the `guides/` directory
