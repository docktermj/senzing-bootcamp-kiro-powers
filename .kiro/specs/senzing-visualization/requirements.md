# Requirements Document

## Introduction

This feature adds a visualization steering file (`senzing-bootcamp/steering/visualization-guide.md`) to the Senzing Bootcamp Power. The steering file is a markdown document that guides the agent when a bootcamper decides to build their own interactive entity graph visualization during or after Module 8. No code ships with the power. The agent uses the steering file's knowledge — data extraction patterns, graph data model, D3.js integration, interactive features, web server options — combined with MCP tools (`generate_scaffold`, `get_sdk_reference`, `find_examples`) to help the bootcamper write the visualization code themselves, in their chosen language, with their chosen web framework, for their own data. The deliverable is a single steering file that follows the same conventions as all other steering files in `senzing-bootcamp/steering/`.

## Glossary

- **Steering_File**: A markdown document in `senzing-bootcamp/steering/` with YAML frontmatter that the agent loads at runtime to guide a bootcamper through a specific workflow; the steering file for this feature is `visualization-guide.md`
- **Agent**: The AI assistant that loads the Steering_File and uses its guidance to help the Bootcamper write code
- **Bootcamper**: A user working through the Senzing Bootcamp modules who decides to build a visualization
- **MCP_Tools**: The Senzing MCP server tools available to the Agent, including `generate_scaffold`, `get_sdk_reference`, `find_examples`, `search_docs`, and `explain_error_code`
- **Graph_Data_Model**: The intermediate JSON structure that the Bootcamper's extraction code produces — containing entity nodes, relationship edges, and metadata — which the visualization frontend consumes
- **Entity_Node**: A JSON object in the Graph_Data_Model representing a single resolved entity with its ID, primary name, record count, contributing data sources, and record list
- **Relationship_Edge**: A JSON object in the Graph_Data_Model representing a connection between two entities with match level and shared features
- **Chosen_Language**: The programming language the Bootcamper selected during onboarding (Python, Java, C#, Rust, or TypeScript), stored in `config/bootcamp_preferences.yaml`
- **Chosen_Framework**: The web server framework the Bootcamper selects when they want to serve the visualization (any framework they prefer — Flask, FastAPI, Express, Spring Boot, ASP.NET, Actix, etc.)
- **WAIT_Marker**: A convention in steering files where the Agent must pause and wait for the Bootcamper's response before proceeding to the next step

## Requirements

### Requirement 1: Steering File Structure and Inclusion Mode

**User Story:** As a power maintainer, I want the visualization guide to follow the same structural conventions as all other steering files, so that the agent can load and use it consistently.

#### Acceptance Criteria for Requirement 1

1. THE Steering_File SHALL be located at `senzing-bootcamp/steering/visualization-guide.md`
2. THE Steering_File SHALL include YAML frontmatter with `inclusion: manual` so the Agent loads it only when visualization is requested
3. THE Steering_File SHALL use the same formatting conventions as other steering files in `senzing-bootcamp/steering/`: numbered workflow steps, agent instruction blocks prefixed with `> **Agent instruction:**`, WAIT_Markers after every question to the Bootcamper, and `👉` prefixes on input-required questions
4. THE Steering_File SHALL be registered in `senzing-bootcamp/steering/steering-index.yaml` under the `keywords` section with entries for `visualization`, `graph`, and `entity graph`
5. THE Steering_File SHALL contain no executable code that ships as part of the power — all code is generated dynamically by the Agent using MCP_Tools and the Steering_File's guidance

### Requirement 2: Agent Workflow for Guiding Visualization Construction

**User Story:** As a bootcamper, I want the agent to walk me through building a visualization step by step, so that I understand each component and can customize it for my needs.

#### Acceptance Criteria for Requirement 2

1. THE Steering_File SHALL define a sequential workflow that the Agent follows: (a) confirm the Bootcamper wants a visualization, (b) gather requirements (what data, what features), (c) generate data extraction code, (d) generate the HTML/JavaScript visualization, (e) optionally generate a web server, (f) test and iterate
2. THE Steering_File SHALL include a WAIT_Marker after each major workflow step so the Agent pauses for the Bootcamper's input before proceeding
3. THE Steering_File SHALL instruct the Agent to use `generate_scaffold` with the Bootcamper's Chosen_Language for all backend code generation (data extraction, web server)
4. THE Steering_File SHALL instruct the Agent to use `get_sdk_reference` to obtain correct Senzing SDK method signatures for the Bootcamper's Chosen_Language before generating any SDK-calling code
5. THE Steering_File SHALL instruct the Agent to use `find_examples` to locate relevant query and visualization patterns before generating code
6. WHEN the Bootcamper requests changes to the generated code, THE Agent SHALL regenerate the affected component using the same MCP_Tools and the Steering_File's guidance
7. THE Steering_File SHALL instruct the Agent to save all generated code to the Bootcamper's project directory following the standard project structure: extraction code in `src/query/`, HTML output in `docs/`, server code in `src/server/`

### Requirement 3: Data Extraction Guidance

**User Story:** As a bootcamper, I want the steering file to teach the agent what data to extract from Senzing and how to structure it, so that the agent can generate correct extraction code in my language.

#### Acceptance Criteria for Requirement 3

1. THE Steering_File SHALL document the Graph_Data_Model schema: an array of Entity_Node objects and an array of Relationship_Edge objects, with field names, types, and descriptions for each
2. THE Steering_File SHALL specify that extraction code must iterate over loaded records using `get_entity_by_record_id(data_source, record_id)` and must not iterate over guessed entity ID ranges
3. THE Steering_File SHALL specify that extraction code must use `get_entity_by_entity_id` with relationship flags to retrieve relationship data between entities
4. THE Steering_File SHALL specify that extraction code must deduplicate entities (since multiple records map to the same entity) before building the Graph_Data_Model
5. THE Steering_File SHALL specify that extraction code must capture for each Entity_Node: entity ID, primary name, record count, list of contributing data sources, and list of records with record IDs
6. THE Steering_File SHALL specify that extraction code must capture for each Relationship_Edge: source entity ID, target entity ID, match level, and list of shared features
7. IF the Senzing SDK returns an error during extraction, THEN THE Steering_File SHALL instruct the Agent to generate error handling that logs the error with entity or record context and continues processing remaining entities
8. WHEN the extracted dataset exceeds 500 entities, THE Steering_File SHALL instruct the Agent to generate code that warns the Bootcamper about potential rendering performance degradation and offers to limit output

### Requirement 4: Visualization Feature Options

**User Story:** As a bootcamper, I want the agent to offer me a menu of interactive visualization features to choose from, so that I can build exactly the visualization I need.

#### Acceptance Criteria for Requirement 4

1. THE Steering_File SHALL define the following visualization features the Agent must offer to the Bootcamper: force-directed graph layout, entity detail panel, cluster highlighting by data source or match strength, search and filter by name or record ID, and summary statistics display
2. THE Steering_File SHALL instruct the Agent to present the feature menu and ask the Bootcamper which features to include, using a WAIT_Marker for the response
3. THE Steering_File SHALL provide D3.js force-directed layout guidance: node sizing proportional to record count, edge coloring by match strength (green for strong, orange for moderate, red for weak), drag-to-reposition, zoom, and pan
4. THE Steering_File SHALL provide entity detail panel guidance: click a node to display entity ID, primary name, all contributing data sources, record list, and shared features that caused resolution
5. THE Steering_File SHALL provide cluster highlighting guidance: a control to switch between data source coloring, match strength coloring, and no clustering, with a legend for the active mode
6. THE Steering_File SHALL provide search and filter guidance: a text input that highlights matching nodes and dims non-matching nodes, with a "no matches found" message when appropriate
7. THE Steering_File SHALL provide summary statistics guidance: total entity count, total record count, total relationship count, number of data sources, and cross-source match rate percentage
8. THE Steering_File SHALL instruct the Agent to generate a single self-contained HTML file (all JavaScript, CSS, and data inline) that the Bootcamper can open in any modern browser without a web server

### Requirement 5: Web Server Integration Guidance

**User Story:** As a bootcamper, I want the option to serve my visualization through a web server of my choice, so that I can share it with teammates or add dynamic data refresh.

#### Acceptance Criteria for Requirement 5

1. WHEN the Bootcamper requests a served deployment, THE Steering_File SHALL instruct the Agent to ask which web framework the Bootcamper prefers, using a WAIT_Marker for the response
2. THE Steering_File SHALL provide framework-agnostic server guidance: serve the HTML visualization, expose a `/health` endpoint, and expose a `/refresh` endpoint that re-queries the Senzing SDK and regenerates graph data
3. THE Steering_File SHALL instruct the Agent to use `generate_scaffold` with the Bootcamper's Chosen_Language and Chosen_Framework to generate the server code
4. THE Steering_File SHALL instruct the Agent to save server code to `src/server/` in the Bootcamper's project directory
5. WHERE the Bootcamper chooses container deployment, THE Steering_File SHALL instruct the Agent to generate a Dockerfile appropriate for the Chosen_Language and Chosen_Framework
6. IF the Bootcamper does not request a served deployment, THEN THE Steering_File SHALL instruct the Agent to produce only the self-contained HTML file

### Requirement 6: Module 8 Integration and Trigger Points

**User Story:** As a bootcamper, I want the visualization to be offered naturally during Module 8 query and validation work, so that I can build it when it is most useful.

#### Acceptance Criteria for Requirement 6

1. THE Steering_File SHALL document the trigger points where the Agent should offer visualization: (a) after running exploratory queries in Module 8 step 3, (b) when the Bootcamper asks to "visualize", "show me the entity graph", or "generate a visualization", and (c) after validation results are presented in Module 8 step 6
2. THE Steering_File SHALL instruct the Agent to load `visualization-guide.md` when any trigger point is activated
3. WHEN the Bootcamper declines the visualization offer, THE Agent SHALL continue with the Module 8 workflow without loading the Steering_File
4. THE Steering_File SHALL reference the Module 8 steering file (`module-08-query-validation.md`) so the Agent can return to the Module 8 workflow after visualization is complete
5. THE module-08-query-validation.md steering file SHALL be updated to reference `visualization-guide.md` instead of the current `senzing-bootcamp/scripts/generate_visualization.py` script at the "Offer entity graph visualization" step in step 3

### Requirement 7: Language-Agnostic Code Generation

**User Story:** As a bootcamper, I want the agent to generate visualization code in whatever language I chose for the bootcamp, so that the visualization integrates naturally with my existing project code.

#### Acceptance Criteria for Requirement 7

1. THE Steering_File SHALL instruct the Agent to read the Bootcamper's Chosen_Language from `config/bootcamp_preferences.yaml` before generating any code
2. THE Steering_File SHALL contain language-agnostic descriptions of all extraction and server logic (what to do, not how to do it in a specific language) so the Agent can generate code in any supported language
3. THE Steering_File SHALL instruct the Agent to use `generate_scaffold` with the `language` parameter set to the Bootcamper's Chosen_Language for all backend code generation
4. THE Steering_File SHALL instruct the Agent to load the appropriate language steering file (`lang-python.md`, `lang-java.md`, `lang-csharp.md`, `lang-rust.md`, or `lang-typescript.md`) for language-specific best practices before generating code
5. THE Steering_File SHALL specify that the HTML/JavaScript visualization frontend is always generated in JavaScript (using D3.js) regardless of the Bootcamper's Chosen_Language, since it runs in the browser
