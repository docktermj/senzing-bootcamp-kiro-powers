# Implementation Plan: Senzing Visualization Steering File

## Overview

This plan creates the `senzing-bootcamp/steering/visualization-guide.md` steering file and updates cross-references in `module-08-query-validation.md` and `steering-index.yaml`. Every task writes or updates markdown/YAML content — no Python scripts, no test files, no executable code. The steering file follows the same conventions as all other files in `senzing-bootcamp/steering/`.

## Tasks

- [x] 1. Create the steering file with YAML frontmatter and header
  - Create `senzing-bootcamp/steering/visualization-guide.md`
  - Add YAML frontmatter with `inclusion: manual`
  - Write the header, one-line purpose, before/after framing, and prerequisites section
  - Document the three trigger points where the agent should offer visualization (after Module 8 step 3 queries, on explicit user request, after Module 8 step 6 validation)
  - Reference `module-08-query-validation.md` for returning to Module 8 after visualization is complete
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 6.1, 6.2, 6.3, 6.4_

- [x] 2. Write the Graph Data Model schema section
  - [x] 2.1 Document the top-level JSON structure (metadata, nodes, edges) with field names, types, and descriptions
    - Include the `metadata` object fields: dataSource, generatedAt, entityCount, recordCount, relationshipCount, dataSources
    - _Requirements: 3.1_
  - [x] 2.2 Document the EntityNode schema table: entityId, primaryName, recordCount, dataSources, primaryDataSource, records, features — with types and descriptions for each field
    - _Requirements: 3.1, 3.5_
  - [x] 2.3 Document the RelationshipEdge schema table: sourceEntityId, targetEntityId, matchLevel, matchStrength, sharedFeatures — with types and descriptions for each field
    - _Requirements: 3.1, 3.6_

- [x] 3. Write the match strength classification section
  - Document the match level → category → color mapping table: level 1 → strong → #22c55e, level 2 → moderate → #f59e0b, level 3+ → weak → #ef4444
  - Document the node clustering color rules: average ≤ 1.5 → green, average ≤ 2.5 → orange, average > 2.5 → red, no relationships → gray (#9ca3af)
  - _Requirements: 4.3, 4.5_

- [x] 4. Write the 6-step agent workflow
  - [x] 4.1 Write Step 1 (Confirm intent) and Step 2 (Gather requirements)
    - Step 1: Ask bootcamper if they want a visualization, WAIT marker, decline path returns to Module 8
    - Step 2: Ask what data sources and which interactive features to include (present feature menu), WAIT marker
    - Use `👉` prefix on input-required questions and `> **Agent instruction:**` blocks per steering file conventions
    - _Requirements: 2.1, 2.2, 4.2_
  - [x] 4.2 Write Step 3 (Generate data extraction code)
    - Agent instruction block: read Chosen_Language from `config/bootcamp_preferences.yaml`, load appropriate language steering file, use `get_sdk_reference` for SDK signatures, use `generate_scaffold` with `workflow='query'`
    - Document language-agnostic extraction logic: iterate over loaded records via `get_entity_by_record_id`, deduplicate entities, extract entity and relationship fields per the schema, classify match strength
    - Include the 500-entity threshold warning guidance
    - WAIT marker for bootcamper to run extraction and confirm output
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 3.2, 3.3, 3.4, 3.7, 3.8, 7.1, 7.2, 7.3, 7.4_
  - [x] 4.3 Write Step 4 (Generate HTML visualization)
    - Agent instruction block: generate a single self-contained HTML file using D3.js with only the features the bootcamper selected
    - Reference the visualization feature guidance sections written in task 5
    - Save to `docs/entity_graph.html`, WAIT marker for feedback
    - _Requirements: 2.1, 4.8, 7.5_
  - [x] 4.4 Write Step 5 (Optional web server) and Step 6 (Iterate and refine)
    - Step 5: Ask if bootcamper wants served deployment, if yes follow web server guidance (task 6), if no skip, WAIT marker
    - Step 6: Ask if bootcamper wants changes, regenerate affected components, WAIT marker, return to Module 8 when done
    - _Requirements: 2.1, 2.2, 2.6, 5.1, 5.6_

- [x] 5. Write the visualization feature guidance sections
  - [x] 5.1 Write D3.js force-directed layout guidance
    - D3.js v7 force simulation, node sizing proportional to record count, edge coloring by match strength, drag-to-reposition, zoom, pan, hover tooltip
    - _Requirements: 4.3_
  - [x] 5.2 Write entity detail panel guidance
    - Click node to open side panel showing entity ID, primary name, data sources, record list, shared features; click away to dismiss
    - _Requirements: 4.4_
  - [x] 5.3 Write cluster highlighting guidance
    - Control to switch between data source coloring (D3 schemeCategory10), match strength coloring, and no clustering; legend updates per active mode
    - _Requirements: 4.5_
  - [x] 5.4 Write search and filter guidance
    - Text input for case-insensitive name/record ID matching, highlight matches, dim non-matches, "no matches found" message, clear button
    - _Requirements: 4.6_
  - [x] 5.5 Write summary statistics guidance
    - Total entity count, record count, relationship count, data source count, cross-source match rate percentage
    - _Requirements: 4.7_

- [x] 6. Write the web server guidance section
  - Document framework-agnostic server endpoints: `GET /` (serve HTML), `GET /health`, `POST /refresh`
  - Instruct agent to ask bootcamper's preferred framework (WAIT marker), use `generate_scaffold` with chosen language and framework
  - Document file placement: server code to `src/server/`, optional Dockerfile to `src/server/Dockerfile`
  - Document the "no server" path: produce only the self-contained HTML file
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 7. Write the error handling guidance section
  - Document error handling table: SDK not initialized, empty database, per-entity SDK error, per-relationship SDK error, entity count > 500, no relationships found
  - Include user feedback messages for each error condition
  - Document browser-side error handling: try/catch wrapper around D3.js initialization with user-friendly error display
  - _Requirements: 3.7, 3.8_

- [x] 8. Write the file placement rules section
  - Document where generated files go: extraction code in `src/query/extract_graph_data.[ext]`, graph data JSON in `data/temp/graph_data.json`, HTML in `docs/entity_graph.html`, server code in `src/server/`, Dockerfile in `src/server/Dockerfile`
  - _Requirements: 2.7_

- [x] 9. Checkpoint — Review steering file completeness
  - Verify all 6 workflow steps have WAIT markers
  - Verify all `> **Agent instruction:**` blocks and `👉` prefixes are present
  - Verify Graph Data Model schema documents all EntityNode and RelationshipEdge fields
  - Verify all 5 visualization feature guidance sections are present
  - Ensure no executable code ships in the file (no `if __name__`, no shebang lines)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Update module-08-query-validation.md cross-reference
  - In `senzing-bootcamp/steering/module-08-query-validation.md` step 3, replace the reference to `senzing-bootcamp/scripts/generate_visualization.py` with guidance to load `visualization-guide.md` and walk the bootcamper through building their own visualization
  - Update the offer text from running a script to loading the steering file
  - _Requirements: 6.5_

- [x] 11. Update steering-index.yaml with visualization keywords
  - Add `visualization: visualization-guide.md`, `graph: visualization-guide.md`, and `entity graph: visualization-guide.md` entries under the `keywords` section in `senzing-bootcamp/steering/steering-index.yaml`
  - _Requirements: 1.4_

- [x] 12. Final validation
  - Run `python senzing-bootcamp/scripts/validate_power.py` to check cross-references and structural integrity
  - Verify `visualization-guide.md` is loadable (YAML frontmatter parses, `inclusion: manual` is set)
  - Verify `steering-index.yaml` keyword entries resolve to the correct file
  - Verify `module-08-query-validation.md` no longer references `generate_visualization.py`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This is a documentation/steering file feature — all tasks write or update markdown and YAML content
- No Python scripts, test files, or executable code are created
- The steering file follows the same conventions as all other files in `senzing-bootcamp/steering/`
- Checkpoints validate structural correctness of the steering file content
- Each task references specific requirements for traceability
