# Requirements Document

## Introduction

Add a "Discover" phase to Module 7 (Query, Visualize & Discover) that proactively introduces bootcampers to advanced Senzing capabilities after the Query and Visualize portions are complete. Currently the module moves directly to completion without showcasing deeper analytical features like why/how analysis, relationship networks, and data-specific visualizations.

The Discover phase analyzes the bootcamper's loaded data structure and uses Senzing SDK capabilities to suggest and demonstrate queries and visualizations the bootcamper may not have considered. This fulfills the "Discover" portion of the module's title and helps bootcampers understand the full breadth of Senzing's entity resolution capabilities.

## Glossary

- **Steering_File**: The Markdown document `module-07-query-visualize-discover.md` in `senzing-bootcamp/steering/` that guides agent behavior during Module 7
- **Discover_Phase**: The new phase added after the Query and Visualize steps in Module 7, introducing advanced Senzing capabilities through concrete examples from the bootcamper's data
- **Why_Analysis**: Senzing SDK methods (`why_entities`, `why_records`, `why_record_in_entity`) that explain the specific features and principles that drove a resolution decision between records or entities
- **How_Analysis**: The Senzing SDK method (`how_entity`) that shows the step-by-step construction history of an entity as records were added over time
- **Relationship_Network**: A graph of connections between entities discovered through shared attributes, explored via `find_network` and `find_path` SDK methods
- **Feature_Score**: A numeric value indicating how closely two feature values match (e.g., name similarity score), included when using `SZ_INCLUDE_FEATURE_SCORES` flag
- **Match_Key**: A Senzing-generated string (e.g., +NAME+ADDRESS, +PHONE) describing which features caused two records to resolve together
- **Multi_Record_Entity**: A resolved entity composed of two or more source records that Senzing determined belong to the same real-world entity
- **Cross_Source_Entity**: A resolved entity whose constituent records originate from two or more distinct data sources
- **Data_Pattern_Analysis**: The process of examining loaded data to identify interesting entities and relationships suitable for demonstrating advanced capabilities
- **SDK**: The Senzing SDK accessed via MCP tools, providing entity resolution query and analysis capabilities
- **Bootcamper**: The developer learning Senzing entity resolution through the bootcamp modules

## Requirements

### Requirement 1: Data Pattern Analysis

**User Story:** As a bootcamper, I want the agent to analyze my loaded data and identify interesting patterns, so that the Discover phase demonstrations use concrete examples from my own data rather than generic illustrations.

#### Acceptance Criteria

1. WHEN the Discover_Phase begins, THE Steering_File SHALL instruct the agent to identify at least one Multi_Record_Entity with three or more constituent records from the bootcamper's resolved data
2. WHEN the Discover_Phase begins, THE Steering_File SHALL instruct the agent to identify at least one Cross_Source_Entity suitable for demonstrating Why_Analysis
3. WHEN the Discover_Phase begins, THE Steering_File SHALL instruct the agent to identify entity clusters with relationships suitable for demonstrating Relationship_Network exploration
4. THE Steering_File SHALL instruct the agent to present a brief summary of discovered data patterns to the bootcamper before proceeding with demonstrations (e.g., "I found N large entities, M cross-source matches, and K relationship clusters in your data")
5. IF the bootcamper's data contains fewer than two Multi_Record_Entities, THEN THE Steering_File SHALL instruct the agent to explain that the data has limited resolution results and adapt demonstrations to use available entities

### Requirement 2: Why Analysis Introduction

**User Story:** As a bootcamper, I want to understand WHY Senzing decided two records belong to the same entity, so that I can evaluate resolution decisions and explain them to stakeholders.

#### Acceptance Criteria

1. THE Steering_File SHALL instruct the agent to introduce `why_entities` and `why_records` SDK methods using a concrete Cross_Source_Entity identified from the bootcamper's data
2. WHEN demonstrating Why_Analysis, THE Steering_File SHALL instruct the agent to call the SDK with `SZ_INCLUDE_FEATURE_SCORES` and `SZ_INCLUDE_MATCH_KEY_DETAILS` flags to provide full scoring detail
3. THE Steering_File SHALL instruct the agent to explain the Why_Analysis output in plain language, covering: which features matched, the Feature_Scores for each comparison, and the matching principle that applied (exact match, close match, likely match)
4. THE Steering_File SHALL instruct the agent to present the Match_Key breakdown showing which feature combinations triggered the resolution decision
5. WHEN the Why_Analysis demonstration is complete, THE Steering_File SHALL instruct the agent to explain when why analysis is useful in practice (auditing decisions, debugging unexpected merges, compliance reporting)

### Requirement 3: How Analysis Introduction

**User Story:** As a bootcamper, I want to understand HOW an entity was constructed step by step, so that I can see the resolution history and understand how adding records changes entity composition.

#### Acceptance Criteria

1. THE Steering_File SHALL instruct the agent to introduce the `how_entity` SDK method using a Multi_Record_Entity with three or more records identified from the bootcamper's data
2. WHEN demonstrating How_Analysis, THE Steering_File SHALL instruct the agent to call the SDK with `SZ_INCLUDE_FEATURE_SCORES` flag to show scoring at each resolution step
3. THE Steering_File SHALL instruct the agent to present the How_Analysis output as a chronological narrative showing each step where a new record was added to the entity and which features caused the merge at that step
4. THE Steering_File SHALL instruct the agent to explain the difference between Why_Analysis (comparing two specific records or entities) and How_Analysis (showing the full construction history of one entity)
5. WHEN the How_Analysis demonstration is complete, THE Steering_File SHALL instruct the agent to explain when how analysis is useful in practice (understanding entity growth over time, investigating over-merging, data stewardship)

### Requirement 4: Relationship Network Exploration

**User Story:** As a bootcamper, I want to see how entities connect to each other through shared attributes, so that I can explore relationship networks and discover hidden connections in my data.

#### Acceptance Criteria

1. THE Steering_File SHALL instruct the agent to introduce `find_network` and `find_path` SDK methods using entities identified from the bootcamper's data that have disclosed relationships or shared attributes
2. WHEN demonstrating Relationship_Network exploration, THE Steering_File SHALL instruct the agent to call `find_network` with a set of related entity IDs and present the resulting network structure
3. THE Steering_File SHALL instruct the agent to explain the network output showing: which entities are connected, what attributes they share, and the degrees of separation between them
4. THE Steering_File SHALL instruct the agent to demonstrate `find_path` between two entities that are indirectly connected, showing the shortest path of relationships between them
5. WHEN the Relationship_Network demonstration is complete, THE Steering_File SHALL instruct the agent to explain practical use cases (fraud ring detection, supply chain analysis, beneficial ownership tracing, customer household grouping)
6. IF the bootcamper's data contains no entity relationships or disclosed connections, THEN THE Steering_File SHALL instruct the agent to explain what relationship networks would look like with connected data and skip the live demonstration

### Requirement 5: Data-Specific Visualization Suggestions

**User Story:** As a bootcamper, I want the agent to suggest visualizations specific to my data structure, so that I can see what additional analytical views are possible beyond the standard query results.

#### Acceptance Criteria

1. WHEN the Discover_Phase demonstrations are complete, THE Steering_File SHALL instruct the agent to suggest at least two visualizations tailored to the bootcamper's data structure and resolution results
2. THE Steering_File SHALL instruct the agent to select visualization suggestions from a catalog that includes: cross-source overlap heatmap, entity size distribution chart, relationship network graph, match key frequency analysis, and feature score distribution
3. THE Steering_File SHALL instruct the agent to explain what each suggested visualization would reveal about the bootcamper's data and why it is relevant to their specific data sources
4. WHEN the bootcamper selects a visualization to explore, THE Steering_File SHALL instruct the agent to generate the visualization using the bootcamper's chosen language and the visualization patterns from `visualization-guide.md`
5. IF the bootcamper declines all visualization suggestions, THEN THE Steering_File SHALL instruct the agent to acknowledge the decision and proceed to the module completion gate

### Requirement 6: Discover Phase Checkpointing

**User Story:** As a bootcamp maintainer, I want the Discover phase to have proper checkpointing, so that session resumption works correctly and progress is tracked through the new steps.

#### Acceptance Criteria

1. THE Steering_File SHALL define checkpoints for each Discover_Phase step: data pattern analysis (step 4a), why analysis (step 4b), how analysis (step 4c), relationship networks (step 4d), and visualization suggestions (step 4e)
2. WHEN each Discover_Phase step is completed, THE Steering_File SHALL instruct the agent to write the step completion to `config/bootcamp_progress.json`
3. WHEN a session resumes mid-Discover_Phase, THE Steering_File SHALL instruct the agent to read the last completed checkpoint and resume from the next incomplete step
4. THE Steering_File SHALL instruct the agent to skip previously completed Discover_Phase steps during session resumption without re-running demonstrations

### Requirement 7: Discover Phase Gating and Flow

**User Story:** As a bootcamper, I want the Discover phase to be an engaging guided exploration that I can exit early if needed, so that I am not forced through demonstrations that are not relevant to my goals.

#### Acceptance Criteria

1. THE Steering_File SHALL position the Discover_Phase after step 3d (results dashboard visualization) and before the Query Completeness Gate
2. WHEN the Discover_Phase begins, THE Steering_File SHALL instruct the agent to present a brief introduction explaining what capabilities will be demonstrated and ask the bootcamper if they want to proceed
3. IF the bootcamper declines the Discover_Phase, THEN THE Steering_File SHALL instruct the agent to skip directly to the Query Completeness Gate
4. WHEN each Discover_Phase demonstration is complete, THE Steering_File SHALL instruct the agent to ask the bootcamper if they want to continue to the next demonstration or proceed to module completion
5. THE Steering_File SHALL update the Query Completeness Gate to include a check that the Discover_Phase was either completed or explicitly skipped by the bootcamper

### Requirement 8: SDK Flag Usage and Query Quality

**User Story:** As a bootcamp maintainer, I want the Discover phase to use appropriate SDK flags for all advanced queries, so that demonstrations show full detail and teach the bootcamper about flag selection.

#### Acceptance Criteria

1. WHEN calling `why_entities` or `why_records`, THE Steering_File SHALL instruct the agent to use both `SZ_INCLUDE_FEATURE_SCORES` and `SZ_INCLUDE_MATCH_KEY_DETAILS` flags
2. WHEN calling `how_entity`, THE Steering_File SHALL instruct the agent to use `SZ_INCLUDE_FEATURE_SCORES` flag
3. WHEN calling `find_network` or `find_path`, THE Steering_File SHALL instruct the agent to look up available flags via `get_sdk_reference(method='<method>', topic='flags')` and select flags appropriate for relationship exploration
4. THE Steering_File SHALL instruct the agent to explain each flag choice to the bootcamper: "I'm using [flag] so we can see [what it provides]"
5. THE Steering_File SHALL instruct the agent to iterate over known record IDs from the bootcamper's loaded data when selecting entities for demonstration, using `get_entity_by_record_id(data_source, record_id)` rather than guessing entity IDs

### Requirement 9: Steering File Integration

**User Story:** As a bootcamp maintainer, I want the Discover phase integrated into the existing Module 7 steering file structure, so that it follows established patterns and maintains compatibility with existing hooks and protocols.

#### Acceptance Criteria

1. THE Steering_File SHALL add the Discover_Phase as a new numbered step section (step 4) following the existing visualization checkpoints (steps 3c and 3d)
2. THE Steering_File SHALL update the Success Criteria section to include: "✅ Discover phase completed or explicitly skipped"
3. THE Steering_File SHALL update the Query Completeness Gate to verify the Discover_Phase status before allowing module completion
4. THE Steering_File SHALL reference `visualization-guide.md` for any visualization generation during the Discover_Phase
5. THE Steering_File SHALL follow the existing agent instruction format (blockquote with "> **Agent instruction:**") for implementation guidance within the Discover_Phase steps
6. WHEN the Steering_File update is complete, THE `steering-index.yaml` SHALL be updated with the new token count for `module-07-query-visualize-discover.md`
