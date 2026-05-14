# Requirements Document

## Introduction

Replace Module 3's minimal smoke-test UI (plain HTML form with JSON dump) with a rich interactive visualization that demonstrates Senzing's entity resolution value, and codify this visualization in the Module 3 steering file (`module-03-system-verification.md`, Step 9) so the agent always builds it for every future bootcamper.

Module 3 is the first time the bootcamper sees their own running Senzing engine processing curated data — it should be the "wow moment" of the bootcamp. The visualization uses a stdlib HTTP server with a single HTML page powered by D3.js (loaded from CDN) to show entity resolution results across the three TruthSet data sources (CUSTOMERS, REFERENCE, WATCHLIST).

This spec covers both the visualization behavior (what the agent generates) and the steering file update (how to make it reproducible across all sessions and users).

## Glossary

- **Steering_File**: The Markdown document `module-03-system-verification.md` in `senzing-bootcamp/steering/` that guides agent behavior during Module 3
- **Web_Service**: The stdlib HTTP server (no third-party frameworks) that serves the visualization page and API endpoints from `src/system_verification/web_service/`
- **Visualization_Page**: The single HTML page served by the Web_Service containing all interactive visualization tabs
- **Summary_Banner**: A horizontal row of 5 headline statistics displayed at the top of the Visualization_Page
- **Entity_Graph**: A D3.js force-directed graph showing resolved entities as nodes and relationships as edges
- **Record_Merges_View**: A card-based display showing multi-record entities with side-by-side constituent records and matching features highlighted
- **Merge_Statistics**: A histogram showing the distribution of records-per-entity counts
- **Probe_Panel**: A UI section with one-click buttons for canonical TruthSet entities and a search input
- **Match_Key**: A Senzing-generated string (e.g., +NAME+ADDRESS, +PHONE) describing which features caused two records to resolve together
- **Multi_Record_Entity**: A resolved entity composed of two or more source records that Senzing determined belong to the same real-world entity
- **Cross_Source_Entity**: A resolved entity whose constituent records originate from two or more distinct data sources
- **TruthSet**: The deterministic Senzing test dataset containing records from three data sources (CUSTOMERS, REFERENCE, WATCHLIST)
- **D3.js**: A JavaScript library for data visualization, loaded from CDN in the browser
- **SDK**: The Senzing SDK used to perform entity resolution queries (export_json_entity_report, get_entity_by_entity_id, search_by_attributes, find_network_by_entity_id)
- **Token_Budget**: The tracked token count for each steering file, maintained in `steering-index.yaml`

## Requirements

### Requirement 1: Statistics API Endpoint

**User Story:** As a bootcamper, I want a single API endpoint that returns aggregate entity resolution statistics, so that the visualization can display headline numbers demonstrating the value of ER.

#### Acceptance Criteria

1. THE Web_Service SHALL expose a `GET /api/stats` endpoint that returns a JSON response
2. THE `GET /api/stats` response SHALL include the fields: `records_total`, `entities_total`, `multi_record_entities`, `cross_source_entities`, `relationships_total`, and `histogram`
3. THE `histogram` field SHALL contain a mapping of record-count buckets (1, 2, 3, 4+) to the number of entities in each bucket
4. WHEN the `GET /api/stats` endpoint is called, THE Web_Service SHALL compute statistics from the SDK using `export_json_entity_report`
5. IF the SDK returns an error during statistics computation, THEN THE Web_Service SHALL return HTTP 500 with a JSON object containing an `error` field describing the failure

### Requirement 2: Graph API Endpoint

**User Story:** As a bootcamper, I want a graph endpoint that returns entity nodes and relationship edges, so that the visualization can render a force-directed entity graph.

#### Acceptance Criteria

1. THE Web_Service SHALL expose a `GET /api/graph` endpoint that returns a JSON response containing `nodes` and `edges` arrays
2. EACH node in the `nodes` array SHALL include: `entity_id`, `entity_name`, `record_count`, `data_sources` (list of source names contributing records), and `records` (list of constituent record summaries)
3. EACH edge in the `edges` array SHALL include: `source_entity_id`, `target_entity_id`, `match_key`, and `relationship_type`
4. WHEN the `GET /api/graph` endpoint is called, THE Web_Service SHALL retrieve entity and relationship data using `get_entity_by_entity_id` and `find_network_by_entity_id`
5. IF the SDK returns an error during graph data retrieval, THEN THE Web_Service SHALL return HTTP 500 with a JSON object containing an `error` field describing the failure

### Requirement 3: Merges API Endpoint

**User Story:** As a bootcamper, I want a merges endpoint that returns multi-record entities with their constituent records and match keys, so that the visualization can show why records resolved together.

#### Acceptance Criteria

1. THE Web_Service SHALL expose a `GET /api/merges` endpoint that returns a JSON response containing an array of multi-record entity objects
2. EACH multi-record entity object SHALL include: `entity_id`, `entity_name`, `match_key`, and a `records` array containing the constituent source records
3. EACH record in the `records` array SHALL include: `data_source`, `record_id`, and the record's feature values (name, address, phone, identifiers)
4. THE `GET /api/merges` endpoint SHALL only return entities with two or more constituent records
5. IF the SDK returns an error during merge data retrieval, THEN THE Web_Service SHALL return HTTP 500 with a JSON object containing an `error` field describing the failure

### Requirement 4: Summary Banner Display

**User Story:** As a bootcamper, I want to see 5 headline numbers across the top of the page showing the entity resolution pipeline results, so that I immediately understand the value of ER in one glance.

#### Acceptance Criteria

1. THE Visualization_Page SHALL display a Summary_Banner containing exactly 5 statistics: records loaded, resolved entities, multi-record entities, cross-source matches, and relationships discovered
2. THE Summary_Banner SHALL present the statistics in a left-to-right flow with arrow indicators between them to convey the resolution pipeline narrative
3. WHEN the page loads, THE Visualization_Page SHALL fetch data from `GET /api/stats` and populate the Summary_Banner
4. IF the `GET /api/stats` request fails, THEN THE Visualization_Page SHALL display an error message in the Summary_Banner area indicating data could not be loaded

### Requirement 5: Entity Graph Tab

**User Story:** As a bootcamper, I want an interactive force-directed graph showing resolved entities and their relationships, so that I can visually explore how records connect across data sources.

#### Acceptance Criteria

1. THE Visualization_Page SHALL include an Entity Graph tab containing a D3.js force-directed graph
2. EACH node in the Entity_Graph SHALL be colored by its primary data source (distinct colors for CUSTOMERS, REFERENCE, and WATCHLIST)
3. EACH node in the Entity_Graph SHALL be sized proportionally to its record count (entities with more constituent records appear larger)
4. EACH edge in the Entity_Graph SHALL display its Match_Key as a label (e.g., +NAME+ADDRESS, +PHONE)
5. WHEN the bootcamper hovers over a node, THE Entity_Graph SHALL display a tooltip showing the entity name, entity ID, record count, and data sources
6. WHEN the page loads the Entity Graph tab, THE Visualization_Page SHALL fetch data from `GET /api/graph` and render the force-directed layout

### Requirement 6: Record Merges Tab

**User Story:** As a bootcamper, I want to see multi-record entities displayed as cards with side-by-side source records and highlighted matching features, so that I understand why Senzing merged those records.

#### Acceptance Criteria

1. THE Visualization_Page SHALL include a Record Merges tab displaying cards for each Multi_Record_Entity
2. EACH card SHALL display the constituent records side-by-side with their data source and record ID clearly labeled
3. EACH card SHALL highlight the matching features (name, address, phone, identifiers) that caused the records to resolve together
4. EACH card SHALL display Match_Key chips indicating which feature combinations triggered the merge
5. WHEN the page loads the Record Merges tab, THE Visualization_Page SHALL fetch data from `GET /api/merges` and render the merge cards

### Requirement 7: Merge Statistics Tab

**User Story:** As a bootcamper, I want to see a histogram of records-per-entity distribution with a summary framing, so that I understand the deduplication impact of entity resolution.

#### Acceptance Criteria

1. THE Visualization_Page SHALL include a Merge Statistics tab containing a histogram of records-per-entity distribution
2. THE histogram SHALL display buckets for entities with 1 record, 2 records, 3 records, and 4+ records
3. THE Merge Statistics tab SHALL display a summary statement in the format: "[X] records collapsed into [Y] entities, including [Z] multi-record entities"
4. WHEN the page loads the Merge Statistics tab, THE Visualization_Page SHALL fetch data from `GET /api/stats` and render the histogram using D3.js

### Requirement 8: Probe Entities Tab

**User Story:** As a bootcamper, I want one-click buttons for canonical TruthSet entities and a search input, so that I can immediately explore real merges and relationships without typing anything.

#### Acceptance Criteria

1. THE Visualization_Page SHALL include a Probe Entities tab with pre-configured one-click buttons for canonical TruthSet entity pairs (e.g., Robert Smith / Bob Smith)
2. WHEN the bootcamper clicks a probe button, THE Visualization_Page SHALL query the Web_Service using `search_by_attributes` and display the resolved entity with its constituent records and relationships
3. THE Probe Entities tab SHALL include a search input field that accepts name, address, or phone attributes
4. WHEN the bootcamper submits a search query, THE Visualization_Page SHALL call the Web_Service search endpoint and display matching entities
5. IF a search or probe query returns no results, THEN THE Visualization_Page SHALL display a message indicating no matching entities were found

### Requirement 9: Tab Navigation and Page Structure

**User Story:** As a bootcamper, I want a tabbed interface that organizes the visualization into logical sections, so that I can explore different aspects of entity resolution without page reloads.

#### Acceptance Criteria

1. THE Visualization_Page SHALL provide tab navigation with exactly 4 tabs: Entity Graph, Record Merges, Merge Statistics, and Probe Entities
2. THE Summary_Banner SHALL remain visible above the tab navigation regardless of which tab is active
3. WHEN the bootcamper clicks a tab, THE Visualization_Page SHALL display the corresponding content without a full page reload
4. THE Visualization_Page SHALL default to the Entity Graph tab on initial load

### Requirement 10: Implementation Constraints

**User Story:** As a power maintainer, I want the visualization to follow the bootcamp's architectural constraints, so that it remains consistent with the rest of the system verification module.

#### Acceptance Criteria

1. THE Web_Service SHALL use only Python stdlib HTTP server capabilities (no Flask, FastAPI, or other third-party HTTP frameworks)
2. THE Visualization_Page SHALL load D3.js from a CDN (requiring browser internet access) with no other external JavaScript dependencies
3. ALL visualization artifacts (server code, HTML, JavaScript) SHALL reside in `src/system_verification/web_service/`
4. THE Web_Service SHALL derive all displayed data from existing SDK calls: `export_json_entity_report`, `get_entity_by_entity_id`, `search_by_attributes`, and `find_network_by_entity_id`
5. THE visualization SHALL work with the three TruthSet data sources: CUSTOMERS, REFERENCE, and WATCHLIST
6. THE Visualization_Page SHALL be a single HTML file with embedded CSS and JavaScript (aside from the D3.js CDN import)

### Requirement 11: Steering File Codification

**User Story:** As a bootcamp maintainer, I want the Module 3 steering file to require this visualization, so that the agent always builds it for every future bootcamper rather than the minimal JSON-dump UI.

#### Acceptance Criteria

1. THE Steering_File SHALL be updated at Step 9 to require the Web_Service with all endpoints (`/api/stats`, `/api/graph`, `/api/merges`) and the full Visualization_Page with all four tabs
2. THE Steering_File SHALL specify the Summary_Banner with five headline numbers, the Entity_Graph with source-colored nodes and match-key edges, the Record_Merges_View with side-by-side cards, the Merge_Statistics histogram, and the Probe_Panel with one-click TruthSet entities
3. THE Steering_File SHALL reference `visualization-guide.md` and `visualization-protocol.md` as pattern sources for the Module 3 visualization implementation
4. THE Steering_File SHALL follow the Web Service Delivery Sequence defined in `visualization-guide.md` for starting, verifying, and presenting the web service to the bootcamper
5. THE Steering_File SHALL maintain compatibility with the `visualization-protocol.md` checkpoint map entry for `m3_demo_results`

### Requirement 12: Endpoint Verification Checks

**User Story:** As a bootcamp maintainer, I want the steering file to include verification checks for the new endpoints, so that the agent confirms the visualization backend works before presenting it to the bootcamper.

#### Acceptance Criteria

1. WHEN the Web_Service is started, THE Steering_File SHALL instruct the agent to verify the Stats endpoint returns HTTP 200 with valid JSON containing all required fields within 10 seconds
2. WHEN the Web_Service is started, THE Steering_File SHALL instruct the agent to verify the Graph endpoint returns HTTP 200 with valid JSON containing at least one node and one edge within 10 seconds
3. WHEN the Web_Service is started, THE Steering_File SHALL instruct the agent to verify the Merges endpoint returns HTTP 200 with valid JSON containing at least one multi-record entity within 10 seconds
4. IF any endpoint verification fails, THEN THE Steering_File SHALL instruct the agent to report the failure with a Fix_Instruction and include the endpoint name and HTTP status in the error output

### Requirement 13: Token Budget Awareness

**User Story:** As a bootcamp maintainer, I want the steering file update to remain within acceptable token budget limits, so that the Module 3 steering does not exceed the critical threshold for agent context loading.

#### Acceptance Criteria

1. THE Steering_File SHALL remain within the `large` size category after the update (the current token count is 5452; the split threshold is 5000 tokens per `steering-index.yaml`)
2. IF the updated Steering_File exceeds the split threshold significantly, THEN the implementation SHALL split Step 9 into a separate phase file (following the pattern used by Modules 5, 6, and 8)
3. WHEN the update is complete, THE `steering-index.yaml` SHALL be updated with the new token count for `module-03-system-verification.md`
