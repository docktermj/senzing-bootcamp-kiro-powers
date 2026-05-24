# Implementation Plan: Visualization Enhancements

## Overview

Update two steering files (`module-03-phase2-visualization.md` and `visualization-guide.md`) to replace the MCP scaffold-based generation approach with a Python generator script pattern, add Critical Lessons sections, specify Entity Graph UX enhancements, and mandate D3.js code style constraints. Property-based tests validate that all required content is present in both steering files using pytest + Hypothesis.

## Tasks

- [x] 1. Update Module 03 Phase 2 steering with Python generator approach
  - [x] 1.1 Replace `generate_scaffold(workflow='web_service')` with `write_html.py` generator instructions
    - Remove all references to `generate_scaffold(workflow='web_service')` in Step 9.1
    - Add instructions for creating `write_html.py` that outputs `index.html` using triple-quoted strings
    - Specify file resides in `src/system_verification/web_service/` alongside `server.py` and builder modules
    - Specify `server.py` uses Python stdlib HTTP server (`http.server.HTTPServer` + `BaseHTTPRequestHandler`)
    - Specify D3.js v7 loaded from CDN, single-file `index.html` with embedded CSS and JavaScript
    - Update required files table to include `write_html.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.2 Add "CRITICAL LESSONS FOR VISUALIZATION GENERATION" section to Module 03 Phase 2
    - Add section after Implementation constraints
    - Include all 6 mandatory constraints: (1) Python generator script, (2) no fs_write/str_replace for HTML+JS, (3) JavaScript syntax validation, (4) data-* attributes over inline onclick, (5) quote discipline, (6) function(){} for D3.js callbacks, (7) explicit SVG dimensions
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6, 6.1, 6.2_

  - [x] 1.3 Add Entity Graph UX enhancements to Module 03 Phase 2
    - Specify node labels showing entity name (truncated to 20 characters max)
    - Specify edge labels showing match key string (e.g., +NAME+ADDRESS)
    - Specify click-to-detail modal with entity ID, primary name, data sources, record count, constituent records
    - Specify D3.js zoom behavior (mouse wheel to zoom, drag to pan)
    - Specify color legend mapping data source names to node colors (CUSTOMERS=#3b82f6, REFERENCE=#22c55e, WATCHLIST=#f59e0b)
    - Specify responsive resize (window resize → update SVG dimensions and re-center force simulation)
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3_

  - [x] 1.4 Add D3.js code style constraints to Module 03 Phase 2
    - Mandate `function(){}` syntax for all D3.js callbacks (no arrow functions)
    - Mandate explicit `width` and `height` attributes on SVG elements (no CSS-only sizing)
    - _Requirements: 6.1, 6.2_

- [x] 2. Checkpoint - Verify Module 03 Phase 2 steering updates
  - Ensure all modifications are present: no `generate_scaffold` references, `write_html.py` instructions added, Critical Lessons section complete, Entity Graph UX features specified, D3.js constraints added. Verify existing API endpoints, tab structure, Summary_Banner, and Delivery Sequence are preserved. Ask the user if questions arise.

- [x] 3. Update Visualization Guide steering file
  - [x] 3.1 Add "CRITICAL LESSONS FOR VISUALIZATION GENERATION" section to Visualization Guide
    - Add section after "Visualization Offer Protocol" section
    - Include all 7 mandatory constraints identical to Module 03 Phase 2 version
    - Include `function(){}` syntax and explicit SVG dimension attributes
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 6.3_

  - [x] 3.2 Add Python Generator Architecture section to Visualization Guide
    - Document the Python generator approach as mandated for all visualization generation
    - Specify `write_html.py` → `index.html` pattern with triple-quoted strings
    - _Requirements: 5.3_

  - [x] 3.3 Update Feature Guidance with required Entity Graph features
    - Add node labels, edge labels, click-to-detail modal as required features
    - Add zoom/pan behavior, color legend, responsive resize as required features
    - _Requirements: 3.4, 4.4_

- [x] 4. Checkpoint - Verify Visualization Guide steering updates
  - Ensure Critical Lessons section is present and complete, Python Generator Architecture section added, Feature Guidance updated with all 6 Entity Graph UX features. Verify existing sections preserved (Offer Protocol, Graph Data Model, Match Strength, Static HTML, Error Handling, File Placement, Tracker). Ask the user if questions arise.

- [x] 5. Verify preservation of existing API and tab structure
  - [x] 5.1 Verify API endpoints and tab structure in Module 03 Phase 2
    - Confirm `/api/stats`, `/api/graph`, `/api/merges`, and search endpoint specifications are intact
    - Confirm four-tab structure preserved: Entity_Graph, Record_Merges_View, Merge_Statistics, Probe_Panel
    - Confirm Summary_Banner with five headline statistics is preserved
    - Confirm Web Service Delivery Sequence reference is preserved
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 6. Write property-based tests for visualization enhancements
  - [x] 6.1 Create test file with shared fixtures and helpers
    - Create `senzing-bootcamp/tests/test_visualization_enhancements_properties.py`
    - Load both steering files at module level using `Path(__file__).resolve().parent.parent / "steering" / ...`
    - Define constants for required constraints, features, endpoints, tabs, and modal fields
    - _Requirements: 2.1, 2.2_

  - [x] 6.2 Write property test: Critical Lessons section completeness
    - **Property 1: Critical Lessons section completeness across steering files**
    - Use `st.sampled_from()` over the set of 7 mandatory constraints
    - For each constraint drawn, verify it appears in both steering files' Critical Lessons sections
    - **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 6.1, 6.2, 6.3**

  - [x] 6.3 Write property test: Feature Guidance contains all required Entity Graph features
    - **Property 2: Visualization Guide Feature Guidance contains all required Entity Graph features**
    - Use `st.sampled_from()` over {node labels, edge labels, click-to-detail modal, zoom/pan, color legend, responsive resize}
    - For each feature drawn, verify the Visualization Guide's Feature Guidance section references it
    - **Validates: Requirements 3.4, 4.4**

  - [x] 6.4 Write property test: Click-to-detail modal specifies all required fields
    - **Property 3: Click-to-detail modal specifies all required fields**
    - Use `st.sampled_from()` over {entity ID, primary name, data sources, record count, constituent records}
    - For each field drawn, verify Module 03 Phase 2 steering mentions it in the Entity Graph specification
    - **Validates: Requirements 3.3**

  - [x] 6.5 Write property test: All required API endpoints are specified
    - **Property 4: All required API endpoints are specified**
    - Use `st.sampled_from()` over {/api/stats, /api/graph, /api/merges, search}
    - For each endpoint drawn, verify Module 03 Phase 2 steering specifies it
    - **Validates: Requirements 5.2, 7.1**

  - [x] 6.6 Write property test: All required tabs are specified
    - **Property 5: All required tabs are specified**
    - Use `st.sampled_from()` over {Entity_Graph, Record_Merges_View, Merge_Statistics, Probe_Panel}
    - For each tab drawn, verify Module 03 Phase 2 steering references it
    - **Validates: Requirements 7.2**

- [x] 7. Write example-based unit tests
  - [x] 7.1 Write unit tests for scaffold removal and generator presence
    - `test_no_generate_scaffold_reference` — verify absence of `generate_scaffold(workflow='web_service')` in Module 03
    - `test_write_html_py_in_required_files` — verify `write_html.py` mentioned as generator
    - `test_critical_lessons_heading_in_module03` — verify section heading exists
    - `test_critical_lessons_heading_in_viz_guide` — verify section heading exists
    - _Requirements: 1.1, 1.2, 2.1, 2.2_

  - [x] 7.2 Write unit tests for Entity Graph UX features
    - `test_node_labels_specified` — node text labels with truncation
    - `test_edge_labels_specified` — edge text labels with match key
    - `test_zoom_pan_specified` — D3.js zoom behavior
    - `test_color_legend_specified` — color legend
    - `test_responsive_resize_specified` — responsive resize
    - _Requirements: 3.1, 3.2, 4.1, 4.2, 4.3_

  - [x] 7.3 Write unit tests for preservation requirements
    - `test_python_generator_architecture_in_viz_guide` — mandated approach in Visualization Guide
    - `test_summary_banner_preserved` — Summary_Banner with 5 stats
    - `test_delivery_sequence_reference_preserved` — Web Service Delivery Sequence
    - _Requirements: 5.3, 7.3, 7.4_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Implementation language is Python 3.11+ (pytest + Hypothesis) per the project's tech stack
- These are steering-only changes — no application code is modified
- Both steering files retain their existing YAML frontmatter (`inclusion: manual`)
- All modifications to existing sections are additive — existing content (API endpoints, tabs, Summary_Banner, Delivery Sequence) must be preserved
- Test file follows the established pattern in `test_visualization_enforcement_properties.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 2, "tasks": ["5.1"] },
    { "id": 3, "tasks": ["6.1"] },
    { "id": 4, "tasks": ["6.2", "6.3", "6.4", "6.5", "6.6", "7.1", "7.2", "7.3"] }
  ]
}
```
