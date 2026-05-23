# Requirements Document

## Introduction

This feature enhances the visualization steering files in the Senzing Bootcamp Power to replace the MCP scaffold-based generation approach with a Python generator script approach (`write_html.py` → `index.html`), add critical lessons learned from production usage, and specify UX enhancements for the Entity Graph. These are steering-only changes — no application code is modified. The visualization is generated dynamically by the agent at runtime following the updated steering instructions.

## Glossary

- **Steering_File**: A markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that guides agent behavior during bootcamp execution
- **Module_03_Phase2_Steering**: The steering file at `senzing-bootcamp/steering/module-03-phase2-visualization.md` that directs Module 3 visualization generation
- **Visualization_Guide**: The steering file at `senzing-bootcamp/steering/visualization-guide.md` that provides the authoritative visualization generation workflow used across all modules
- **Python_Generator_Script**: A Python script (`write_html.py`) that contains HTML as a triple-quoted string and writes it to `index.html`, avoiding quote-escaping conflicts
- **Entity_Graph**: The D3.js force-directed graph tab showing entity nodes and relationship edges
- **Critical_Lessons_Section**: A dedicated section in steering files documenting mandatory constraints for visualization generation to prevent known failure modes
- **Agent**: The AI assistant executing bootcamp steering instructions to generate code and artifacts for the bootcamper

## Requirements

### Requirement 1: Replace MCP Scaffold with Python Generator Approach

**User Story:** As a power maintainer, I want the steering files to mandate a Python generator script approach instead of `generate_scaffold(workflow='web_service')`, so that the agent avoids quote-escaping failures when generating HTML with embedded JavaScript.

#### Acceptance Criteria

1. WHEN the Agent generates web service visualization artifacts, THE Module_03_Phase2_Steering SHALL instruct the Agent to create a `write_html.py` Python script that outputs `index.html` using triple-quoted strings.
2. THE Module_03_Phase2_Steering SHALL remove all references to `generate_scaffold(workflow='web_service')` as the generation mechanism for visualization artifacts.
3. THE Module_03_Phase2_Steering SHALL specify that `write_html.py` resides in `src/system_verification/web_service/` alongside `server.py` and builder modules.
4. THE Module_03_Phase2_Steering SHALL specify that `server.py` uses Python stdlib HTTP server (`http.server.HTTPHandler` + `BaseHTTPRequestHandler`) with no third-party frameworks.
5. THE Module_03_Phase2_Steering SHALL specify that D3.js v7 is loaded from CDN and the generated `index.html` is a single file with embedded CSS and JavaScript.

### Requirement 2: Add Critical Lessons Section to Both Steering Files

**User Story:** As a power maintainer, I want critical lessons for visualization generation documented in both steering files, so that the agent never repeats known failure modes regardless of which file is loaded.

#### Acceptance Criteria

1. THE Module_03_Phase2_Steering SHALL contain a section titled "CRITICAL LESSONS FOR VISUALIZATION GENERATION" with all mandatory constraints.
2. THE Visualization_Guide SHALL contain a section titled "CRITICAL LESSONS FOR VISUALIZATION GENERATION" with all mandatory constraints.
3. WHEN the Agent generates HTML with embedded JavaScript, THE Critical_Lessons_Section SHALL instruct the Agent to use a Python generator script and to avoid `fs_write` or `str_replace` for HTML+JS content.
4. THE Critical_Lessons_Section SHALL instruct the Agent to validate JavaScript syntax with `node --check` after generating the HTML file.
5. THE Critical_Lessons_Section SHALL instruct the Agent to use `data-*` attributes with `querySelectorAll` event listeners instead of inline `onclick` attributes with dynamic values.
6. THE Critical_Lessons_Section SHALL instruct the Agent to use double quotes for JavaScript strings and single quotes for HTML attributes inside Python triple-quoted strings.

### Requirement 3: Entity Graph Node and Edge Labels with Click-to-Detail

**User Story:** As a bootcamper, I want the Entity Graph to display node labels, edge labels, and a click-to-detail modal, so that I can identify entities and understand relationships without hovering over every element.

#### Acceptance Criteria

1. THE Module_03_Phase2_Steering SHALL specify that Entity_Graph nodes display text labels showing the entity name (truncated to a maximum character length when necessary).
2. THE Module_03_Phase2_Steering SHALL specify that Entity_Graph edges display text labels showing the match key string (e.g., +NAME+ADDRESS).
3. WHEN a bootcamper clicks an Entity_Graph node, THE Entity_Graph SHALL display a modal containing entity ID, primary name, data sources, record count, and constituent records.
4. THE Visualization_Guide SHALL specify node labels, edge labels, and click-to-detail modal as required Entity_Graph features in the Feature Guidance section.

### Requirement 4: Entity Graph Zoom, Pan, Legend, and Responsive Resize

**User Story:** As a bootcamper, I want the Entity Graph to support zoom/pan, show a color legend, and resize responsively, so that I can explore dense graphs and understand the visual encoding.

#### Acceptance Criteria

1. THE Module_03_Phase2_Steering SHALL specify that the Entity_Graph implements D3.js zoom behavior (mouse wheel to zoom, drag to pan).
2. THE Module_03_Phase2_Steering SHALL specify that the Entity_Graph displays a color legend mapping data source names to node colors.
3. WHEN the browser window is resized, THE Entity_Graph SHALL update the SVG dimensions and re-center the force simulation.
4. THE Visualization_Guide SHALL specify zoom/pan behavior, color legend, and responsive resize as required Entity_Graph features in the Feature Guidance section.

### Requirement 5: Specify Python Generator Architecture

**User Story:** As a power maintainer, I want the steering files to define the complete architecture of the visualization generation approach, so that the agent produces a consistent and working file structure.

#### Acceptance Criteria

1. THE Module_03_Phase2_Steering SHALL specify the following file architecture: `write_html.py` generates `index.html`, `server.py` provides API endpoints, and D3.js renders a force-directed graph.
2. THE Module_03_Phase2_Steering SHALL specify that `server.py` serves `index.html` at the root path and exposes API endpoints at `/api/stats`, `/api/graph`, `/api/merges`, and `/api/search`.
3. THE Visualization_Guide SHALL document the Python generator architecture as the mandated approach for all visualization generation across modules.

### Requirement 6: D3.js Code Style and SVG Constraints

**User Story:** As a power maintainer, I want the steering files to mandate specific D3.js coding patterns, so that the generated visualization avoids known browser compatibility and rendering issues.

#### Acceptance Criteria

1. THE Module_03_Phase2_Steering SHALL specify that all D3.js callback code uses `function(){}` syntax instead of arrow functions.
2. THE Module_03_Phase2_Steering SHALL specify that SVG elements use explicit `width` and `height` attributes rather than CSS-only sizing.
3. THE Visualization_Guide SHALL specify `function(){}` syntax and explicit SVG dimension attributes as mandatory constraints in the Critical_Lessons_Section.

### Requirement 7: Preserve Existing API and Tab Structure

**User Story:** As a power maintainer, I want the updated steering files to preserve the existing API endpoint specifications and tab structure, so that the visualization functionality remains complete after the generation approach changes.

#### Acceptance Criteria

1. THE Module_03_Phase2_Steering SHALL retain the specifications for `GET /api/stats`, `GET /api/graph`, `GET /api/merges`, and the Probe Panel search endpoint.
2. THE Module_03_Phase2_Steering SHALL retain the four-tab structure: Entity_Graph, Record_Merges_View, Merge_Statistics, and Probe_Panel.
3. THE Module_03_Phase2_Steering SHALL retain the Summary_Banner specification with five headline statistics displayed above tab navigation.
4. THE Module_03_Phase2_Steering SHALL retain the Web Service Delivery Sequence for server lifecycle management (start, verify, present, wait, fallback).
