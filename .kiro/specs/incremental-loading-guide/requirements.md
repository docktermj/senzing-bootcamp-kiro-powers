# Requirements Document

## Introduction

The bootcamp currently teaches batch loading in Module 6: load all data sources at once, process redo records, and validate results. Real-world Senzing deployments rarely stop there — new records arrive daily or hourly, and the system must ingest them incrementally without reloading the entire dataset. Bootcampers finishing Module 6 have no guidance on how to transition from batch loading to incremental loading, how redo processing changes with incremental loads, or how to monitor the health of an ongoing ingestion pipeline.

This feature adds a dedicated guide at `docs/guides/INCREMENTAL_LOADING.md` covering incremental loading patterns: adding new records to an existing database, processing redo records after incremental loads, and monitoring incremental load health. The guide uses `generate_scaffold` for code examples and `search_docs`/`find_examples` for authoritative Senzing content. Module 6 references the guide as an advanced topic after the main loading workflow.

## Glossary

- **Incremental_Loading_Guide**: The Markdown document at `docs/guides/INCREMENTAL_LOADING.md` that explains incremental loading patterns for Senzing entity resolution.
- **Incremental_Load**: The process of adding new or updated records to an existing Senzing database without purging and reloading all previously loaded data.
- **Redo_Record**: A record that Senzing flags for reprocessing when new data changes how previously loaded records should resolve. Redo records must be processed to keep entity resolution results current.
- **Load_Health**: The observable state of an incremental loading pipeline, including throughput, error rates, redo queue depth, and entity count trends.
- **Module_6_Steering**: The steering file at `senzing-bootcamp/steering/module-06-load-data.md` that defines the Module 6 workflow for loading data.
- **Guide_Directory**: The directory at `senzing-bootcamp/docs/guides/` containing user-facing reference documentation for the bootcamp.
- **Guides_README**: The file at `senzing-bootcamp/docs/guides/README.md` that indexes all available guides with descriptions and links.
- **Batch_Load**: The process of loading an entire data source into Senzing in a single operation, as taught in Module 6.

## Requirements

### Requirement 1: Incremental Loading Guide Creation

**User Story:** As a bootcamper, I want a dedicated guide on incremental loading patterns, so that I can transition from the batch loading I learned in Module 6 to the incremental loading my production system needs.

#### Acceptance Criteria for Requirement 1

1. THE Incremental_Loading_Guide SHALL be located at `docs/guides/INCREMENTAL_LOADING.md`
2. THE Incremental_Loading_Guide SHALL open with an introduction explaining the difference between Batch_Load and Incremental_Load, and when each approach applies
3. THE Incremental_Loading_Guide SHALL use a level-1 heading with the guide title, followed by an introductory paragraph, consistent with the heading and layout conventions in the Guide_Directory

### Requirement 2: Adding New Records Pattern

**User Story:** As a bootcamper, I want to understand how to add new records to an existing Senzing database, so that I can ingest daily or hourly data without reloading everything.

#### Acceptance Criteria for Requirement 2

1. THE Incremental_Loading_Guide SHALL include a section explaining how to add new records to an existing Senzing database that already contains previously loaded data
2. THE Incremental_Loading_Guide SHALL explain record deduplication during incremental loads: what happens when a record with the same DATA_SOURCE and RECORD_ID is loaded again (replace behavior) versus when a new RECORD_ID is loaded (additive behavior)
3. THE Incremental_Loading_Guide SHALL explain how to structure incremental input files so that only new or changed records are submitted, rather than resubmitting the entire data source
4. THE Incremental_Loading_Guide SHALL include a code example for adding new records, generated using `generate_scaffold` with the `add_records` workflow in the bootcamper's chosen language

### Requirement 3: Redo Processing for Incremental Loads

**User Story:** As a bootcamper, I want to understand how redo processing works after incremental loads, so that I can keep entity resolution results accurate as new data arrives.

#### Acceptance Criteria for Requirement 3

1. THE Incremental_Loading_Guide SHALL include a section explaining why Redo_Records are generated after incremental loads and why processing them is necessary for accurate entity resolution
2. THE Incremental_Loading_Guide SHALL explain the relationship between incremental load volume and redo queue growth: larger incremental loads produce more redo records
3. THE Incremental_Loading_Guide SHALL describe a pattern for scheduling redo processing after each incremental load completes, including how to check whether the redo queue is empty
4. THE Incremental_Loading_Guide SHALL include a code example for processing redo records after an incremental load, generated using `generate_scaffold` with the redo processing workflow

### Requirement 4: Monitoring Incremental Load Health

**User Story:** As a bootcamper, I want to know how to monitor the health of my incremental loading pipeline, so that I can detect problems before they affect entity resolution quality.

#### Acceptance Criteria for Requirement 4

1. THE Incremental_Loading_Guide SHALL include a section on monitoring Load_Health for incremental loading pipelines
2. THE Incremental_Loading_Guide SHALL describe at least four health indicators: records loaded per interval, error count and error rate, redo queue depth over time, and entity count trend after each incremental load
3. THE Incremental_Loading_Guide SHALL explain warning signs that indicate an unhealthy incremental pipeline: growing redo queue that never drains, declining throughput, increasing error rate, or entity count not changing despite new records being loaded
4. THE Incremental_Loading_Guide SHALL include a code example that queries Senzing for current entity and record counts, suitable for use in a monitoring script or health check

### Requirement 5: MCP Tool Usage for Authoritative Content

**User Story:** As a bootcamper, I want the incremental loading guide to use authoritative Senzing content, so that the patterns and examples reflect current SDK behavior rather than outdated information.

#### Acceptance Criteria for Requirement 5

1. WHEN generating code examples for the Incremental_Loading_Guide, THE guide author SHALL use `generate_scaffold` from the Senzing MCP server to produce SDK code rather than hand-writing Senzing API calls
2. WHEN explaining Senzing concepts such as redo processing or record replacement, THE guide author SHALL use `search_docs` to retrieve current documentation rather than relying on training data
3. WHEN providing example patterns, THE guide author SHALL use `find_examples` to reference working code from indexed Senzing GitHub repositories where applicable
4. THE Incremental_Loading_Guide SHALL include a "Further Reading" section that directs bootcampers to use `search_docs` and `find_examples` for the latest incremental loading guidance

### Requirement 6: Module 6 Cross-Reference

**User Story:** As a bootcamper finishing Module 6, I want to be pointed toward the incremental loading guide, so that I know where to learn about incremental patterns after completing the batch loading workflow.

#### Acceptance Criteria for Requirement 6

1. THE Module_6_Steering SHALL include a reference to the Incremental_Loading_Guide as an advanced topic, placed after the Phase D validation section
2. WHEN referencing the Incremental_Loading_Guide from Module_6_Steering, THE reference SHALL describe the guide as covering incremental loading patterns for production systems that receive ongoing data
3. THE reference in Module_6_Steering SHALL not add the Incremental_Loading_Guide as a required step — it SHALL be presented as optional further reading for bootcampers interested in production incremental loading

### Requirement 7: Guides README Integration

**User Story:** As a bootcamper, I want the incremental loading guide listed in the guides README, so that I can discover it from the central documentation index.

#### Acceptance Criteria for Requirement 7

1. WHEN the Incremental_Loading_Guide is created, THE Guides_README SHALL include an entry for `INCREMENTAL_LOADING.md` in the "Reference Documentation" section or a new "Advanced Topics" section
2. WHEN listing the Incremental_Loading_Guide in the Guides_README, THE entry SHALL include the filename as a Markdown link, a bold title, and a two-to-three line description covering incremental record loading, redo processing, and pipeline health monitoring
3. THE Guides_README SHALL list `INCREMENTAL_LOADING.md` in the Documentation Structure tree under the `guides/` directory

### Requirement 8: Practical Focus and SDK Consistency

**User Story:** As a bootcamper, I want the incremental loading guide to build on the SDK patterns I already learned in Module 6, so that I can apply the patterns without learning a new toolset.

#### Acceptance Criteria for Requirement 8

1. THE Incremental_Loading_Guide SHALL use the same SDK functions and patterns taught in Module 6 (e.g., `add_record`, redo processing functions) rather than introducing new APIs the bootcamper has not encountered
2. THE Incremental_Loading_Guide SHALL reference the bootcamper's existing loading program from Module 6 as the starting point for incremental loading, explaining what modifications are needed
3. THE Incremental_Loading_Guide SHALL avoid recommending third-party tools or libraries beyond what the bootcamp has already introduced, keeping the focus on patterns implementable with the Senzing SDK
4. IF the Incremental_Loading_Guide includes file-watching or scheduling patterns, THEN THE Incremental_Loading_Guide SHALL present them as conceptual approaches with pseudocode rather than requiring specific scheduling frameworks
