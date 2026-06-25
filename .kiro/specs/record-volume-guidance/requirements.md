# Requirements Document

## Introduction

Add a record volume guidance step early in Module 6 (Data Processing) that asks the bootcamper about their expected production record volume. The response drives personalized guidance on licensing, loading architecture, database selection, and performance expectations. This helps bootcampers think ahead about production requirements while learning, making the transition from bootcamp to production smoother.

## Glossary

- **Module_6_Root**: The steering file at `senzing-bootcamp/steering/module-06-data-processing.md` that serves as the entry point for Module 6.
- **Phase_A**: The steering sub-file at `senzing-bootcamp/steering/module-06-phaseA-build-loading.md` containing steps 1–3 (Build Loading Program).
- **Volume_Step**: The new numbered step inserted into Module 6 that asks the bootcamper about expected production record volume.
- **Volume_Tier**: One of four categories derived from the bootcamper's stated record count: Demo (fewer than 500), Small (500 to 500K), Medium (500K to 10M), or Large (10M+).
- **Bootcamp_Preferences**: The YAML file at `config/bootcamp_preferences.yaml` that stores bootcamper choices and configuration.
- **Bootcamp_Progress**: The JSON file at `config/bootcamp_progress.json` that tracks step-level progress.
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides SDK guidance, licensing tools, and architecture recommendations.
- **Data_Sources_Registry**: The YAML file at `config/data_sources.yaml` that tracks data source metadata and load status.

## Requirements

### Requirement 1: Ask the bootcamper about expected production record volume

**User Story:** As a bootcamper, I want to be asked about my expected production record volume early in Module 6, so that subsequent guidance is tailored to my scale.

#### Acceptance Criteria

1.1 WHEN Module 6 Phase A begins and before the loading program is created in Phase A Step 2, THE Volume_Step SHALL ask the bootcamper how many records they expect to load in a production system.

1.2 THE Volume_Step SHALL present the question using a pointing question (👉) followed by a 🛑 STOP directive, consistent with the existing step format in Module 6, and SHALL NOT proceed until the bootcamper responds.

1.3 THE Volume_Step SHALL provide example ranges to help the bootcamper answer: fewer than 500 (demo/evaluation), 500 to 500,000 (small production), 500,000 to 10,000,000 (medium production), 10,000,000+ (large production).

1.4 THE Volume_Step SHALL accept free-text answers containing digits, numeric abbreviations (e.g., "1M", "500k", "10 million"), or plain-language numeric expressions and classify them into the appropriate Volume_Tier.

1.5 IF the bootcamper provides an answer that cannot be parsed as a numeric value or mapped to a single Volume_Tier, THEN THE Volume_Step SHALL ask exactly one clarifying follow-up question presenting the four tier options as a numbered list.

1.6 WHEN the Volume_Tier is determined, THE Volume_Step SHALL persist the classified tier and the bootcamper's raw answer to `config/bootcamp_preferences.yaml` so that downstream steps can tailor architecture, threading, and database guidance accordingly.

1.7 IF the bootcamper does not provide a classifiable answer after the clarifying follow-up question, THEN THE Volume_Step SHALL default to the "fewer than 500 (demo/evaluation)" tier, inform the bootcamper of the default, and proceed.

### Requirement 2: Persist the volume selection

**User Story:** As a bootcamper, I want my volume selection to be saved, so that later modules can reference it without asking again.

#### Acceptance Criteria

2.1 WHEN the bootcamper provides a valid volume answer, THE Volume_Step SHALL record a `production_volume` key in Bootcamp_Preferences containing two fields: `raw_value` (the numeric record count as an integer) and `tier` (the derived Volume_Tier string: one of `demo`, `small`, `medium`, or `large`).

2.2 WHEN the Volume_Step has recorded the volume selection in Bootcamp_Preferences, THE Volume_Step SHALL write a checkpoint to Bootcamp_Progress with the Volume_Step's step number to mark the step as complete.

2.3 WHEN a session is resumed and a `production_volume` key exists in Bootcamp_Preferences with both a valid numeric `raw_value` and a recognized `tier` value, THE Volume_Step SHALL skip the volume question and proceed to the next step.

2.4 IF a session is resumed and the `production_volume` key in Bootcamp_Preferences is missing, empty, or contains an unrecognized `tier` value, THEN THE Volume_Step SHALL re-ask the volume question as if no prior selection existed.

### Requirement 3: Provide license guidance based on volume

**User Story:** As a bootcamper, I want to understand what Senzing license I need for my target volume, so that I can plan licensing conversations early.

#### Acceptance Criteria

3.1 WHEN the Volume_Tier is Demo, THE Volume_Step SHALL inform the bootcamper that the built-in 500-record evaluation license is sufficient for their stated volume and that no additional license action is needed.

3.2 WHEN the Volume_Tier is Small, Medium, or Large, THE Volume_Step SHALL inform the bootcamper that a production license is required and that license capacity scales with record count.

3.3 WHEN the Volume_Tier is Small, Medium, or Large, THE Volume_Step SHALL state that the bootcamper can request an evaluation license through the MCP_Server or contact Senzing sales for production licensing, and SHALL present both options as concrete next actions the bootcamper can take after completing the bootcamp.

3.4 THE Volume_Step SHALL present license guidance without a STOP instruction and SHALL proceed to the next step automatically after displaying the guidance, requiring no user action to continue.

3.5 IF the Volume_Tier has not been recorded in Bootcamp_Preferences when the license guidance step executes, THEN THE Volume_Step SHALL skip license guidance and proceed to the next step without error.

### Requirement 4: Provide architecture guidance based on volume

**User Story:** As a bootcamper, I want to understand what loading architecture fits my volume, so that the loading program I build in Module 6 is appropriate for my production needs.

#### Acceptance Criteria

4.1 WHEN the Volume_Tier is Demo, THE Volume_Step SHALL recommend single-threaded loading as sufficient for the stated volume and indicate that no additional architecture planning is needed.

4.2 WHEN the Volume_Tier is Small, THE Volume_Step SHALL recommend single-threaded loading for initial loads and mention that multi-threading becomes beneficial beyond 100,000 records.

4.3 WHEN the Volume_Tier is Medium, THE Volume_Step SHALL recommend multi-threaded loading with a thread pool and reference the MCP_Server `generate_scaffold` tool with `record_count` parameter for production patterns.

4.4 WHEN the Volume_Tier is Large, THE Volume_Step SHALL recommend distributed or queue-based loading architecture and reference the MCP_Server `sdk_guide` tool with `topic='load'` for platform-specific patterns.

4.5 WHEN the Volume_Step presents architecture guidance for any Volume_Tier, THE Volume_Step SHALL label the guidance as a production recommendation and include a statement that the bootcamp itself uses single-threaded loading for learning purposes regardless of tier.

4.6 IF the MCP_Server tool referenced in the architecture guidance is unavailable, THEN THE Volume_Step SHALL still present the tier-appropriate architecture recommendation and inform the bootcamper that they can invoke the MCP_Server tool manually later for detailed patterns.

### Requirement 5: Provide database guidance based on volume

**User Story:** As a bootcamper, I want to understand what database is appropriate for my volume, so that I can plan infrastructure decisions.

#### Acceptance Criteria

5.1 WHEN the Volume_Tier is Demo or Small, THE Volume_Step SHALL confirm that SQLite is sufficient for production use at their stated volume and that no database change is needed.

5.2 WHEN the Volume_Tier is Medium or Large, THE Volume_Step SHALL recommend PostgreSQL for production use and explain that SQLite is limited to a single concurrent writer, which becomes a bottleneck when loading or querying at volumes above 500K records.

5.3 THE Volume_Step SHALL clarify that the bootcamp continues using the currently configured database regardless of the recommendation, and that database migration is covered in a later module of the bootcamp.

5.4 IF the bootcamper's currently configured database is already PostgreSQL, THEN THE Volume_Step SHALL acknowledge the existing configuration and skip the SQLite-specific limitation explanation.

### Requirement 6: Provide performance expectations based on volume

**User Story:** As a bootcamper, I want realistic throughput expectations for my volume, so that I can plan timelines and resources.

#### Acceptance Criteria

6.1 WHEN the Volume_Tier is Demo or Small, THE Volume_Step SHALL indicate that loading completes in seconds to minutes and that no additional configuration beyond default settings is needed for acceptable load performance.

6.2 WHEN the Volume_Tier is Medium, THE Volume_Step SHALL indicate that loading takes minutes to hours depending on CPU core count and thread configuration, and that Module 8 (Performance) covers optimization techniques for this scale.

6.3 WHEN the Volume_Tier is Large, THE Volume_Step SHALL indicate that loading takes hours to days, that distributed architecture and hardware planning are required for production deployment at this scale, and that Modules 8 and 11 cover optimization and deployment.

6.4 THE Volume_Step SHALL reference the MCP_Server `search_docs` tool with `category="configuration"` as the source for current performance guidance rather than stating specific throughput numbers.

6.5 THE Volume_Step SHALL present performance expectations as informational guidance without blocking module progress, consistent with the pattern used in license and database guidance.

### Requirement 7: Preserve existing Module 6 structure and test compliance

**User Story:** As a bootcamp developer, I want the volume step to integrate cleanly into Module 6 without breaking existing steps, numbering, or CI tests.

#### Acceptance Criteria

7.1 WHEN the Volume_Step is inserted into Phase A, THE Volume_Step SHALL become step 1, and all existing Phase A steps SHALL be renumbered by incrementing their step numbers by 1 (e.g., former step 1 becomes step 2, former step 2 becomes step 3, former step 3 becomes step 4).

7.2 WHEN the Volume_Step is inserted, THE Module_6_Root "Phase Sub-Files" section SHALL update the Phase A entry to reflect the new step range [1, 4], and Phase B, Phase C, and Phase D entries SHALL update their step ranges by incrementing both start and end values by 1.

7.3 THE Volume_Step SHALL follow the existing step format: a numbered markdown line with bold title text, one or more agent instruction blockquotes (lines beginning with `>`), and a checkpoint instruction line reading "Write step N to `config/bootcamp_progress.json`" where N is the step number.

7.4 THE Volume_Step SHALL not modify any existing step content in Phase A, Phase B, Phase C, or Phase D beyond incrementing step numbers in headings, checkpoint instructions, and step range references.

7.5 WHEN the Volume_Step is inserted, THE steering-index.yaml SHALL update the Module 6 phase entries so that `phase1-build-loading-program` has `step_range: [1, 4]`, `phase2-load-first-source` has its start and end values incremented by 1, `phase3-multi-source-orchestration` has its start and end values incremented by 1, and `phase4-validation` has its start and end values incremented by 1.

7.6 WHEN the Volume_Step is inserted, THE CI validation pipeline (validate_power.py, measure_steering.py --check, validate_commonmark.py, and pytest) SHALL pass without errors.

### Requirement 8: Integrate volume context into subsequent Phase A steps

**User Story:** As a bootcamper, I want the loading program built in Phase A to reflect my volume tier, so that the code I produce is appropriate for my production needs.

#### Acceptance Criteria

8.1 WHEN the Volume_Tier is Medium or Large, THE Phase_A loading program step SHALL include an agent instruction to read the `record_count` value from the `production_volume` key in Bootcamp_Preferences and pass it to the MCP_Server `generate_scaffold` call so that threaded loading patterns are returned.

8.2 WHEN the Volume_Tier is Demo or Small, THE Phase_A loading program step SHALL call MCP_Server `generate_scaffold` without passing `record_count`, producing a single-threaded loading scaffold.

8.3 THE Phase_A loading program step SHALL include a comment in the generated code stating the Volume_Tier name and the tier-specific architecture recommendation defined in Requirement 4 (single-threaded, multi-threaded with thread pool, or distributed/queue-based).

8.4 IF the `production_volume` key is absent from Bootcamp_Preferences when the Phase_A loading program step executes, THEN THE Phase_A loading program step SHALL fall back to the Demo tier behavior and include a comment indicating that no volume selection was found.
