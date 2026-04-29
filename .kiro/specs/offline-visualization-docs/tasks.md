# Tasks

## Task 1: Add "Offline vs Online" section to visualization-guide.md

- [x] 1.1 Add a new "Offline vs Online" section to `senzing-bootcamp/steering/visualization-guide.md` placed immediately after the "Agent Workflow" section and before the "Graph Data Model Schema" section, containing an introductory paragraph explaining the two delivery modes
- [x] 1.2 Add the Decision Matrix table within the "Offline vs Online" section with columns for Scenario, Recommended Mode, and Rationale, containing 6 rows: (1) sharing with stakeholders → Static HTML, (2) interactive exploration → Web Service, (3) no network access → Static HTML, (4) real-time search → Web Service, (5) quick snapshot → Static HTML, (6) iterating on data quality → Web Service
- [x] 1.3 Add a "Static HTML Capabilities" subsection listing: force-directed graph layout, cluster highlighting, local search and filter, detail panel from inline data, statistics display; and a "Web Service Capabilities" subsection listing: live entity detail fetching, real-time search by attributes, data refresh via `/refresh` endpoint
- [x] 1.4 Add staleness statement noting Static HTML data becomes stale after generation and requires re-running the extraction script, and live refresh statement noting Web Service provides data refresh via the `/refresh` endpoint

## Task 2: Add limitations and prerequisites documentation

- [x] 2.1 Add a "Static HTML Limitations" subsection listing: no live entity detail fetching, no real-time search by attributes, no data refresh without re-running extraction, data size limited by browser memory for inline JSON, and recommended maximum of 500 entities (consistent with existing warning threshold)
- [x] 2.2 Add a "Static HTML Feature Parity" note listing features retained: force layout, cluster highlighting, local search and filter, detail panel (from inline data), and statistics display
- [x] 2.3 Add a "Web Service Prerequisites" subsection listing: (1) Senzing SDK installed and configured (Module 2 complete), (2) database populated with data (Module 6 complete), (3) available port on localhost (default 8080); note that server process must remain running for session duration; reference the "Lifecycle Management" section for start/stop/troubleshooting
- [x] 2.4 Add agent guidance: if bootcamper's environment lacks any Web Service prerequisite, recommend Static HTML mode and explain which prerequisite is missing

## Task 3: Update MCP offline fallback and agent workflow

- [x] 3.1 Add a cross-reference to `mcp-offline-fallback.md` in the "Offline vs Online" section, directing readers to the MCP offline fallback guide for general offline operation guidance
- [x] 3.2 Update `senzing-bootcamp/steering/mcp-offline-fallback.md` to include a row in the "Continuable Operations" section noting that viewing previously generated static HTML visualizations requires no MCP connection
- [x] 3.3 Add MCP unavailability guidance to the agent workflow section in `visualization-guide.md`: when MCP server is unavailable, instruct the agent to recommend Static HTML mode and explain that Web Service mode is unavailable without SDK connectivity

## Task 4: Update module documentation

- [x] 4.1 Add a note to `senzing-bootcamp/docs/modules/MODULE_7_QUERY_VALIDATION.md` in the visualization-related section stating that static HTML visualization works offline while the web service requires a running SDK, with a cross-reference to the "Offline vs Online" section in the Visualization Guide
- [x] 4.2 Add a note to `senzing-bootcamp/docs/modules/MODULE_8_PERFORMANCE_TESTING.md` where visualization or dashboards are referenced, noting that performance dashboards generated as static HTML are viewable offline but do not reflect live performance data

## Task 5: Verify documentation consistency

- [x] 5.1 Review all modified files (`visualization-guide.md`, `mcp-offline-fallback.md`, `MODULE_7_QUERY_VALIDATION.md`, `MODULE_8_PERFORMANCE_TESTING.md`) to verify cross-references are bidirectional and consistent, the 500-entity threshold matches the existing warning threshold, and all section placements are correct
- [x] 5.2 Verify the decision matrix contains exactly 6 rows with the correct scenario-to-mode mappings and that all capabilities, limitations, and prerequisites lists are complete per the requirements
