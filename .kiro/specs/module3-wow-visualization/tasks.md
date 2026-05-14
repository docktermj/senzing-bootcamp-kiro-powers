# Implementation Plan

## Phase 1: Property-Based Tests (Write BEFORE implementation)

- [x] 1. Write property-based tests for data layer builders
  - **Properties P1–P4, P7**: API Response Field Completeness, Histogram Bucketing, Error Response Consistency, Merge Filter Invariant, Summary Statement Format
  - Test file: `senzing-bootcamp/tests/test_module3_wow_visualization_properties.py`
  - Write `TestApiResponseFieldCompleteness` (P1): Generate random entity data, pass through builders, assert all required fields present in output
  - Write `TestHistogramBucketingCorrectness` (P2): Generate random entity lists with varying record counts, assert histogram buckets sum to total entities, each entity in exactly one bucket, no negative counts
  - Write `TestErrorResponseConsistency` (P3): Generate random error messages, pass through error handler, assert HTTP 500 + JSON with non-empty `error` field
  - Write `TestMergeFilterInvariant` (P4): Generate random entity lists including singletons, assert merges builder returns only entities with 2+ records
  - Write `TestSummaryStatementFormat` (P7): Generate random valid stats tuples, assert summary string matches "[X] records collapsed into [Y] entities, including [Z] multi-record entities"
  - Use `@settings(max_examples=100)` per project conventions
  - These tests will initially fail (ImportError) since the builder modules don't exist yet — that's expected
  - _Requirements: 1.2, 1.3, 1.5, 2.2, 2.3, 2.5, 3.2, 3.3, 3.4, 3.5, 7.3_

- [x] 2. Write property-based tests for visualization helpers
  - **Properties P5, P6**: Data Source Color Mapping Determinism, Node Sizing Monotonicity
  - Test file: `senzing-bootcamp/tests/test_module3_wow_visualization_properties.py` (same file, additional test classes)
  - Write `TestDataSourceColorMapping` (P5): For each data source in {CUSTOMERS, REFERENCE, WATCHLIST}, assert same color returned every time, no two sources share a color
  - Write `TestNodeSizingMonotonicity` (P6): Generate pairs of record counts where A > B, assert radius(A) > radius(B); verify min 8px, max 40px bounds
  - These tests will initially fail (ImportError) since helper functions don't exist yet
  - _Requirements: 5.2, 5.3_

- [x] 3. Write property-based tests for steering file validation
  - **Properties P8, P9, P10**: Steering Visualization Completeness, Endpoint Verification Instructions, Artifact Path Isolation
  - Test file: `senzing-bootcamp/tests/test_module3_wow_visualization_properties.py` (same file, additional test classes)
  - Write `TestSteeringVisualizationCompleteness` (P8): Parse the steering file and assert it references all 3 API endpoints, all 4 tab names, and all 5 component names
  - Write `TestSteeringEndpointVerification` (P9): Parse the steering file and assert each endpoint has an HTTP 200 check, content validation, and 10-second timeout
  - Write `TestVisualizationArtifactPathIsolation` (P10): Parse the steering file and assert all artifact paths are rooted under `src/system_verification/web_service/`
  - These tests will initially fail since the steering file hasn't been updated yet
  - _Requirements: 10.3, 11.1, 11.2, 12.1, 12.2, 12.3, 12.4_

## Phase 2: Backend Implementation

- [x] 4. Implement `stats_builder.py`
  - Create `src/system_verification/web_service/stats_builder.py` (note: this is a path the AGENT generates in the bootcamper's project, but the steering file describes what to generate — for testing purposes, create a reference implementation)
  - Implement `Stats` dataclass with fields: `records_total`, `entities_total`, `multi_record_entities`, `cross_source_entities`, `relationships_total`, `histogram`
  - Implement `build() -> dict` that computes stats from `export_json_entity_report` output
  - Implement `compute_histogram(entities) -> dict[str, int]` that buckets entities into 1, 2, 3, 4+ categories
  - Implement `format_summary(stats) -> str` that produces "[X] records collapsed into [Y] entities, including [Z] multi-record entities"
  - All SDK interactions via a passed-in engine reference (dependency injection for testability)
  - Error handling: catch SDK exceptions, return `{"error": str(e)}` with HTTP 500
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.3_

- [x] 5. Implement `graph_builder.py`
  - Create `src/system_verification/web_service/graph_builder.py`
  - Implement `GraphNode` and `GraphEdge` dataclasses per design
  - Implement `build() -> dict` returning `{"nodes": [...], "edges": [...]}`
  - Use `get_entity_by_entity_id` and `find_network_by_entity_id` for data retrieval
  - Include `data_sources` list and `records` list in each node
  - Include `match_key` and `relationship_type` in each edge
  - Error handling: catch SDK exceptions, return `{"error": str(e)}` with HTTP 500
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Implement `merges_builder.py`
  - Create `src/system_verification/web_service/merges_builder.py`
  - Implement `MergeEntity` dataclass per design
  - Implement `build() -> list[dict]` returning only entities with 2+ records
  - Each record includes: `data_source`, `record_id`, `name`, `address`, `phone`, `identifiers`
  - Include `match_key` explaining why records resolved together
  - Filter: never return single-record entities (Property P4)
  - Error handling: catch SDK exceptions, return `{"error": str(e)}` with HTTP 500
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Implement `search_builder.py`
  - Create `src/system_verification/web_service/search_builder.py`
  - Implement `search(name, address, phone) -> dict` returning `{"results": [...], "query": {...}}`
  - Use `search_by_attributes` SDK call
  - Validate at least one search parameter is provided (return HTTP 400 if none)
  - Return empty results array (not error) when no matches found
  - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [x] 8. Implement `server.py`
  - Create `src/system_verification/web_service/server.py`
  - Implement `VisualizationHandler(BaseHTTPRequestHandler)` with routing table:
    - `GET /` → serve `index.html`
    - `GET /api/stats` → `StatsBuilder.build()`
    - `GET /api/graph` → `GraphBuilder.build()`
    - `GET /api/merges` → `MergesBuilder.build()`
    - `GET /api/search` → `SearchBuilder.search()` with query params
    - Other → 404 JSON response
  - Implement `main()` entry point that starts `HTTPServer` on configurable port (default 8080)
  - Set CORS headers for local development
  - JSON serialization with `json.dumps()` for all API responses
  - Implement color mapping function: CUSTOMERS→#3b82f6, REFERENCE→#22c55e, WATCHLIST→#f59e0b
  - Implement node sizing function: `radius = min(max(8 + record_count * 4, 8), 40)`
  - _Requirements: 1.1, 2.1, 3.1, 10.1_

- [x] 9. Verify Phase 1 property tests pass for backend (P1–P7)
  - Run: `pytest senzing-bootcamp/tests/test_module3_wow_visualization_properties.py -k "not Steering" -v`
  - All data layer property tests (P1–P7) should now PASS
  - Fix any failures before proceeding
  - _Requirements: 1.2, 1.3, 1.5, 2.2, 2.3, 2.5, 3.2, 3.3, 3.4, 3.5, 5.2, 5.3, 7.3_

## Phase 3: Frontend Implementation

- [x] 10. Implement `index.html` — page structure and tab navigation
  - Create `src/system_verification/web_service/index.html`
  - Load D3.js v7 from CDN: `https://d3js.org/d3.v7.min.js`
  - Implement Summary_Banner section with 5 stat placeholders and arrow indicators
  - Implement tab navigation with exactly 4 tabs: Entity Graph, Record Merges, Merge Statistics, Probe Entities
  - Default to Entity Graph tab on load
  - Summary_Banner remains visible above tabs regardless of active tab
  - Tab switching without page reload (JavaScript show/hide)
  - Embedded CSS for layout, colors, responsive design
  - _Requirements: 4.1, 4.2, 9.1, 9.2, 9.3, 9.4, 10.2, 10.6_

- [x] 11. Implement Entity Graph tab (D3 force-directed)
  - In `index.html`, implement the Entity Graph tab content
  - Fetch data from `GET /api/graph` on tab load
  - D3 force-directed layout with nodes and edges
  - Nodes colored by primary data source (CUSTOMERS=#3b82f6, REFERENCE=#22c55e, WATCHLIST=#f59e0b)
  - Nodes sized proportionally to record count (formula from design)
  - Edges labeled with Match_Key strings
  - Tooltip on hover: entity name, entity ID, record count, data sources
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 12. Implement Record Merges tab (card-based)
  - In `index.html`, implement the Record Merges tab content
  - Fetch data from `GET /api/merges` on tab load
  - Card layout: one card per multi-record entity
  - Side-by-side display of constituent records with data source and record ID labels
  - Highlight matching features (name, address, phone, identifiers)
  - Match_Key chips on each card
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 13. Implement Merge Statistics tab (D3 histogram)
  - In `index.html`, implement the Merge Statistics tab content
  - Fetch histogram data from `GET /api/stats` on tab load
  - D3 bar chart with buckets: 1 record, 2 records, 3 records, 4+ records
  - Summary statement: "[X] records collapsed into [Y] entities, including [Z] multi-record entities"
  - Labeled axes and count annotations on bars
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 14. Implement Probe Entities tab (search + buttons)
  - In `index.html`, implement the Probe Entities tab content
  - Pre-configured one-click buttons for canonical TruthSet entities (Robert Smith / Bob Smith)
  - Search input field accepting name, address, or phone
  - On button click: query `GET /api/search` and display resolved entity with records and relationships
  - On search submit: query `GET /api/search` and display results
  - "No matching entities found" message for empty results
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Implement Summary Banner data loading and error handling
  - In `index.html`, implement the Summary_Banner fetch logic
  - On page load: fetch `GET /api/stats` and populate 5 statistics
  - Left-to-right flow with arrow indicators between stats
  - Error state: display "Could not load data" message if fetch fails
  - Client-side error handling for all tabs (network errors, empty data, D3 failures)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

## Phase 4: Steering File Update

- [x] 16. Update Module 3 steering file with visualization requirements
  - Read current `senzing-bootcamp/steering/module-03-system-verification.md` to understand Step 9
  - Determine if token budget requires splitting into a phase file
  - If split needed: create `senzing-bootcamp/steering/module-03-phase2-visualization.md` with the visualization step content, and update the main file to reference it
  - If no split needed: update Step 9 in-place
  - The steering content must specify:
    - All 3 API endpoints (`/api/stats`, `/api/graph`, `/api/merges`) with response schemas
    - All 4 tabs (Entity Graph, Record Merges, Merge Statistics, Probe Entities)
    - Summary_Banner with 5 headline numbers
    - Entity_Graph with source-colored nodes and match-key edges
    - Record_Merges_View with side-by-side cards and match-key chips
    - Merge_Statistics histogram with summary statement
    - Probe_Panel with one-click TruthSet entities and search
    - Implementation constraints (stdlib server, D3 CDN, single HTML, artifact path)
  - Reference `visualization-guide.md` and `visualization-protocol.md` as pattern sources
  - Follow Web Service Delivery Sequence from `visualization-guide.md`
  - Maintain compatibility with `visualization-protocol.md` checkpoint map entry for `m3_demo_results`
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 17. Add endpoint verification checks to steering file
  - In the steering file (or phase file), add verification instructions:
    - After server start: verify `/api/stats` returns HTTP 200 with valid JSON containing all required fields (10s timeout)
    - Verify `/api/graph` returns HTTP 200 with at least one node and one edge (10s timeout)
    - Verify `/api/merges` returns HTTP 200 with at least one multi-record entity (10s timeout)
  - On failure: report endpoint name, HTTP status, and provide Fix_Instruction
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] 18. Update `steering-index.yaml` with new token counts
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get updated token counts
  - Update `steering-index.yaml` entry for `module-03-system-verification.md`
  - If phase file was created, add entry for `module-03-phase2-visualization.md`
  - Verify the file remains within the `large` size category or is properly split
  - _Requirements: 13.1, 13.2, 13.3_

## Phase 5: Verification

- [x] 19. Verify steering file property tests pass (P8, P9, P10)
  - Run: `pytest senzing-bootcamp/tests/test_module3_wow_visualization_properties.py -k "Steering" -v`
  - All steering file property tests should now PASS
  - Fix any failures before proceeding
  - _Requirements: 10.3, 11.1, 11.2, 12.1, 12.2, 12.3, 12.4_

- [x] 20. Run full test suite and CI validation
  - Run full property tests: `pytest senzing-bootcamp/tests/test_module3_wow_visualization_properties.py -v`
  - All 10 properties (P1–P10) must pass
  - Run CI validation: `python3 senzing-bootcamp/scripts/measure_steering.py --check`
  - Run CommonMark validation: `python3 senzing-bootcamp/scripts/validate_commonmark.py`
  - Verify no other tests in the repository are broken
  - Ask the user if questions arise
