# Requirements Document

## Introduction

The Senzing Bootcamp visualization feature offers two delivery modes: a static HTML file that works offline and a web service that requires a running SDK. Currently, the tradeoff between these modes is implicit — the agent presents a choice in `visualization-guide.md` but neither the guide nor the module documentation explicitly explains when each mode is appropriate, what works without network or SDK access, and what requires a live environment. This feature adds a clear "Offline vs Online" section to `visualization-guide.md` and updates module documentation (`MODULE_7_QUERY_VALIDATION.md`, `MODULE_8_PERFORMANCE_TESTING.md`) to surface this distinction so bootcampers can make an informed choice before committing to a delivery mode.

## Glossary

- **Visualization_Guide**: The `senzing-bootcamp/steering/visualization-guide.md` steering file that instructs the agent on generating entity graph visualizations
- **Static_HTML_Mode**: The visualization delivery mode that produces a self-contained HTML file with inline data, requiring no running server or SDK at view time
- **Web_Service_Mode**: The visualization delivery mode that produces a localhost web server with live SDK queries, requiring a running Senzing SDK and database at view time
- **Module_Documentation**: The user-facing markdown files in `senzing-bootcamp/docs/modules/` that describe each bootcamp module
- **Offline_Online_Section**: The new documentation section titled "Offline vs Online" that explains the tradeoffs between Static_HTML_Mode and Web_Service_Mode
- **MCP_Offline_Fallback**: The `senzing-bootcamp/steering/mcp-offline-fallback.md` steering file that documents what operations work without MCP connectivity
- **Decision_Matrix**: A structured table mapping user scenarios to the recommended visualization delivery mode

## Requirements

### Requirement 1: Offline vs Online Section in Visualization Guide

**User Story:** As a bootcamp agent, I want a dedicated "Offline vs Online" section in the Visualization_Guide, so that I can explain the tradeoffs to the bootcamper before they choose a delivery mode.

#### Acceptance Criteria

1. THE Visualization_Guide SHALL contain a section titled "Offline vs Online" placed immediately after the "Agent Workflow" section and before the "Graph Data Model Schema" section
2. THE Offline_Online_Section SHALL contain a Decision_Matrix table with columns for scenario, recommended mode, and rationale
3. THE Offline_Online_Section SHALL list all capabilities available in Static_HTML_Mode without any running server or SDK
4. THE Offline_Online_Section SHALL list all capabilities exclusive to Web_Service_Mode that require a running SDK and database
5. THE Offline_Online_Section SHALL state that Static_HTML_Mode data becomes stale after generation and requires re-running the extraction script to update
6. THE Offline_Online_Section SHALL state that Web_Service_Mode provides live data refresh via the `/refresh` endpoint

### Requirement 2: Decision Matrix Content

**User Story:** As a bootcamper, I want a clear mapping of my situation to the recommended visualization mode, so that I can choose the right option without trial and error.

#### Acceptance Criteria

1. THE Decision_Matrix SHALL include a row for the scenario where the bootcamper wants to share results with stakeholders who lack SDK access, recommending Static_HTML_Mode
2. THE Decision_Matrix SHALL include a row for the scenario where the bootcamper wants to explore entities interactively with live SDK queries, recommending Web_Service_Mode
3. THE Decision_Matrix SHALL include a row for the scenario where the bootcamper is working in an environment without persistent network access, recommending Static_HTML_Mode
4. THE Decision_Matrix SHALL include a row for the scenario where the bootcamper needs to search entities by attributes in real time, recommending Web_Service_Mode
5. THE Decision_Matrix SHALL include a row for the scenario where the bootcamper wants a quick snapshot for documentation purposes, recommending Static_HTML_Mode
6. THE Decision_Matrix SHALL include a row for the scenario where the bootcamper is iterating on data quality and reloading data frequently, recommending Web_Service_Mode

### Requirement 3: Module Documentation Updates

**User Story:** As a bootcamper reading module documentation, I want to understand the offline vs online tradeoff before reaching the visualization step, so that I can plan my environment accordingly.

#### Acceptance Criteria

1. THE Module_Documentation for Module 7 (`MODULE_7_QUERY_VALIDATION.md`) SHALL contain a note in the visualization-related section stating that the static HTML visualization works offline while the web service requires a running SDK
2. THE Module_Documentation for Module 7 SHALL reference the Offline_Online_Section in the Visualization_Guide for detailed tradeoff information
3. WHEN the Module_Documentation for Module 8 (`MODULE_8_PERFORMANCE_TESTING.md`) references visualization or dashboards, THE Module_Documentation SHALL note that performance dashboards generated as static HTML are viewable offline but do not reflect live performance data

### Requirement 4: Cross-Reference with MCP Offline Fallback

**User Story:** As a bootcamp agent, I want the offline visualization documentation to be consistent with the MCP offline fallback guide, so that bootcampers receive coherent guidance when working without connectivity.

#### Acceptance Criteria

1. THE Offline_Online_Section SHALL reference the MCP_Offline_Fallback file (`mcp-offline-fallback.md`) for general offline operation guidance
2. THE MCP_Offline_Fallback SHALL be updated to include a row in the "Continuable Operations" documentation section noting that viewing previously generated static HTML visualizations requires no MCP connection
3. WHEN the MCP server is unavailable, THE Visualization_Guide agent workflow SHALL instruct the agent to recommend Static_HTML_Mode and explain that Web_Service_Mode is unavailable without SDK connectivity

### Requirement 5: Static HTML Limitations Documentation

**User Story:** As a bootcamper, I want to understand what I lose by choosing the static HTML option, so that I do not expect live features from an offline artifact.

#### Acceptance Criteria

1. THE Offline_Online_Section SHALL list the following limitations of Static_HTML_Mode: no live entity detail fetching, no real-time search by attributes, no data refresh without re-running extraction, and data size limited by browser memory for inline JSON
2. THE Offline_Online_Section SHALL state the recommended maximum entity count for Static_HTML_Mode as 500 entities, consistent with the existing warning threshold in the Visualization_Guide
3. THE Offline_Online_Section SHALL note that Static_HTML_Mode retains full feature parity for force layout, cluster highlighting, local search and filter, detail panel (from inline data), and statistics display

### Requirement 6: Web Service Requirements Documentation

**User Story:** As a bootcamper, I want to understand the prerequisites for running the web service mode, so that I can verify my environment before choosing that option.

#### Acceptance Criteria

1. THE Offline_Online_Section SHALL list the prerequisites for Web_Service_Mode: Senzing SDK installed and configured (Module 2 complete), database populated with data (Module 6 complete), and an available port on localhost (default 8080)
2. THE Offline_Online_Section SHALL note that Web_Service_Mode requires the server process to remain running for the duration of the visualization session
3. THE Offline_Online_Section SHALL reference the "Lifecycle Management" section of the Visualization_Guide for start, stop, and troubleshooting instructions
4. IF the bootcamper's environment lacks any Web_Service_Mode prerequisite, THEN THE agent SHALL recommend Static_HTML_Mode and explain which prerequisite is missing