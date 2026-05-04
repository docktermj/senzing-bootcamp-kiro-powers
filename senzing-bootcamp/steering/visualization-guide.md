---
inclusion: manual
---

# Entity Graph Visualization Guide

**Purpose:** Walk the bootcamper through building an interactive D3.js entity graph with data extracted from Senzing in their chosen language.

**Before/After:** You have query results but no visual way to explore them. After: a self-contained HTML graph with entities, relationships, match strengths, and interactive features.

**Prerequisites:** ✅ Module 5/6 complete (data loaded) · ✅ Query programs working (Module 7 step 3)

**Triggers:** Load this file when: (1) after exploratory queries in Module 7 step 3, (2) bootcamper asks to "visualize" / "show entity graph" / "generate a visualization", (3) after documenting findings in Module 7. When done, return to `module-07-query-validation.md`.

## Agent Workflow

1. **Visualization Prompt — choose delivery mode**

   Before generating any visualization output, present this choice:

   👉 "Before I generate this visualization, would you like it as:
   1. **Static HTML file** — a self-contained file you can open directly in your browser, no server needed
   2. **Web service** — a localhost server with live SDK queries, data refresh, and interactive entity details

   Which would you prefer?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   The agent MUST wait for a response. If no response, the agent waits — it does not default to either option. WAIT for response.

   - If the bootcamper chooses **Static HTML file** → continue with step 2 below (existing static workflow).
   - If the bootcamper chooses **Web service** → skip to the **Web Server Guidance** section below and follow that workflow instead.

2. **Confirm intent**

   👉 "Would you like me to help you build an interactive entity graph? It shows resolved entities as a force-directed network with clustering, search, and detail panels."

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   If declined, return to `module-07-query-validation.md`. WAIT for response.

3. **Gather requirements**

   👉 "Which data source(s) should the graph include? And which features: force layout, detail panel, cluster highlighting, search/filter, summary statistics?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   WAIT for response.

4. **Generate data extraction code**

   > **Agent instruction:** Read Chosen_Language from `config/bootcamp_preferences.yaml`. Load the appropriate language steering file. Use `get_sdk_reference` for SDK signatures. Use `generate_scaffold` with `workflow='query'`. Use `find_examples` for query patterns.

   Extraction code must: iterate over loaded records via `get_entity_by_record_id` (never guessed entity ID ranges), deduplicate entities, use `get_entity_by_entity_id` with relationship flags for edges, classify match strength per table below, warn if >500 entities, log per-entity/per-relationship SDK errors and continue, write JSON matching the Graph Data Model schema. Save to `src/query/extract_graph_data.[ext]`.

   👉 "Run the extraction and confirm the output JSON looks good."

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   WAIT for response.

5. **Generate HTML visualization**

   > **Agent instruction:** Generate a single self-contained HTML file (D3.js v7, CSS, data inline). Include only selected features per guidance below. Wrap D3.js init in try/catch with user-friendly error display.

   Save to `docs/entity_graph.html`.

   👉 "Open the HTML file — does it look right? Want changes?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   WAIT for response.

6. **Iterate and refine**

   👉 "Want any changes to the graph, features, or extraction?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   Regenerate affected components using the same MCP tools. When done, return to `module-07-query-validation.md`. WAIT for response.

## Offline vs Online

The visualization feature offers two delivery modes: **Static HTML** (offline) and **Web Service** (online). Static HTML produces a self-contained file you can open in any browser with no server, SDK, or network required. Web Service launches a localhost server backed by live Senzing SDK queries, enabling real-time search, entity detail fetching, and data refresh. Choose the mode that fits your environment and goals — the decision matrix below maps common scenarios to the recommended option.

### Decision Matrix

| Scenario | Recommended Mode | Rationale |
|----------|-----------------|-----------|
| Sharing results with stakeholders who lack SDK access | Static HTML | Self-contained file, no server needed |
| Interactive exploration with live SDK queries | Web Service | Real-time entity detail and search |
| Working without persistent network access | Static HTML | No server or database required |
| Real-time entity search by attributes | Web Service | Requires live SDK queries |
| Quick snapshot for documentation purposes | Static HTML | Single file, easy to embed or attach |
| Iterating on data quality with frequent reloads | Web Service | `/refresh` endpoint avoids re-running extraction |

### Static HTML Capabilities

The following features are fully available in Static HTML mode without any running server or SDK:

- Force-directed graph layout with interactive pan/zoom
- Cluster highlighting and color coding
- Local search and filter (within inline data)
- Detail panel (from inline JSON data)
- Statistics display (entity count, relationship count)

### Web Service Capabilities

The following features require a running Senzing SDK and database (Web Service mode only):

- Live entity detail fetching via `/entity/{entityId}`
- Real-time search by attributes via `/search`
- Data refresh via the `/refresh` endpoint

### Static HTML Limitations

Static HTML mode has the following limitations:

- No live entity detail fetching
- No real-time search by attributes
- No data refresh without re-running the extraction script
- Data size limited by browser memory for inline JSON
- Recommended maximum: **500 entities** (consistent with the existing warning threshold — see Error Handling Guidance)

### Static HTML Feature Parity

Despite the limitations above, Static HTML retains full feature parity for:

- Force layout (D3.js v7 force simulation with drag, zoom, pan)
- Cluster highlighting (data source coloring, match strength coloring)
- Local search and filter (text input filtering by name or record ID)
- Detail panel (from inline JSON data)
- Statistics display (entity count, relationship count, cross-source match rate)

### Data Staleness and Refresh

- **Static HTML:** Data becomes stale after generation. To update the visualization with new or changed data, re-run the extraction script and regenerate the HTML file.
- **Web Service:** Provides live data refresh via the `/refresh` endpoint. Click the refresh button to re-query the SDK and update the displayed data without re-running extraction or reloading the page.

### Web Service Prerequisites

To use Web Service mode, your environment must meet these prerequisites:

1. **Senzing SDK installed and configured** — Module 2 complete
2. **Database populated with data** — Module 6 complete
3. **Available port on localhost** — default 8080

The server process must remain running for the duration of the visualization session. See the [Lifecycle Management](#lifecycle-management) section for start, stop, and troubleshooting instructions.

> **Agent guidance:** If the bootcamper's environment lacks any Web Service prerequisite, recommend Static HTML mode and explain which prerequisite is missing. For example: "Your environment doesn't have the Senzing SDK configured yet (Module 2). I recommend using Static HTML mode for now — it produces a self-contained file that works without the SDK."

### MCP Offline Fallback

For general guidance on what operations work without MCP connectivity, see [`mcp-offline-fallback.md`](mcp-offline-fallback.md).

> **Agent guidance — MCP unavailable:** When the MCP server is unavailable, recommend Static HTML mode. Web Service mode requires SDK connectivity, which depends on MCP for code generation and SDK reference lookups. Explain to the bootcamper: "The MCP server isn't available right now, so Web Service mode can't be set up. I recommend Static HTML mode — it produces a self-contained visualization file that works without any server or SDK connection."

## Graph Data Model Schema

Top-level: `{ "metadata": {...}, "nodes": [EntityNode], "edges": [RelationshipEdge] }`
Metadata: `dataSource` (string), `generatedAt` (ISO 8601), `entityCount` (number), `recordCount` (number), `relationshipCount` (number), `dataSources` (string[])

| EntityNode Field | Type | Description |
|------------------|------|-------------|
| entityId | number | Senzing entity ID |
| primaryName | string | Best name from resolved entity |
| recordCount | number | Contributing record count |
| dataSources | string[] | Unique data source names |
| primaryDataSource | string | Data source with most records |
| records | object[] | `{ recordId, dataSource }` per record |
| features | object | Feature type → string[] (NAME, ADDRESS, PHONE, EMAIL) |

| RelationshipEdge Field | Type | Description |
|------------------------|------|-------------|
| sourceEntityId | number | Source entity ID |
| targetEntityId | number | Target entity ID |
| matchLevel | number | Senzing match level integer |
| matchStrength | string | "strong", "moderate", or "weak" |
| sharedFeatures | string[] | Feature types shared between entities |

Example: `{ "metadata": { "dataSource": "CUSTOMERS", "entityCount": 150, "recordCount": 200, "relationshipCount": 45, "dataSources": ["CUSTOMERS","CRM"] }, "nodes": [{ "entityId": 1, "primaryName": "John Smith", "recordCount": 3, "dataSources": ["CUSTOMERS","CRM"], "primaryDataSource": "CUSTOMERS", "records": [{"recordId":"CUST-001","dataSource":"CUSTOMERS"}], "features": {"NAME":["John Smith","J. Smith"]} }], "edges": [{ "sourceEntityId": 1, "targetEntityId": 2, "matchLevel": 1, "matchStrength": "strong", "sharedFeatures": ["NAME","ADDRESS"] }] }`

## Match Strength Classification

| Senzing Match Level | Category | Edge Color | Hex |
|---------------------|----------|------------|-----|
| 1 (resolved) | strong | green | #22c55e |
| 2 (possibly same) | moderate | orange | #f59e0b |
| 3+ (possibly related) | weak | red | #ef4444 |

Cluster node coloring by average match level: ≤1.5 → green, ≤2.5 → orange, >2.5 → red, no relationships → gray (#9ca3af).

## Visualization Feature Guidance

- **D3.js Force Layout:** D3.js v7 force simulation. Node radius proportional to record count (minimum for single-record). Edge color by match strength. Drag-to-reposition, zoom, pan on SVG. Tooltip on hover with entity name.

- **Detail Panel:** Click node → side panel with entity ID, primary name, data sources, record list (ID + source), shared features. Click away to dismiss.

- **Cluster Highlighting:** Dropdown to switch: data source coloring (D3 `schemeCategory10` by `primaryDataSource`), match strength coloring (average match level), no clustering. Legend updates per mode.

- **Search & Filter:** Text input filtering by name or record ID (case-insensitive substring). Matches highlighted, non-matches dimmed. "No matches found" message. Clear button to reset.

- **Statistics:** Total entities, records, relationships. Unique data source count. Cross-source match rate: (entities with >1 data source / total) × 100%.

## Web Server Guidance

#[[file:senzing-bootcamp/steering/visualization-web-service.md]]

## Error Handling Guidance

| Error Condition | Handling | User Feedback |
|-----------------|----------|---------------|
| SDK not initialized / missing DB | Exit with error | "Senzing database not found at database/G2C.db. Complete Module 5 first." |
| Empty database | Exit with error | "No entities found. Load data using Module 5 first." |
| Per-entity SDK error | Log, skip, continue | "Warning: Failed to retrieve entity for record {record_id}. Skipping." |
| Per-relationship SDK error | Log, skip, continue | "Warning: Failed to retrieve relationships for entity {entity_id}. Skipping." |
| Entity count > 500 | Warn, offer limit | "Warning: {count} entities. Rendering may be slow. Limit to 500?" |
| No relationships | Continue, isolated nodes | "No relationships found. Graph will show isolated nodes." |

Browser-side: try/catch around D3.js init; display user-friendly error in graph area on failure.

## File Placement Rules

| Generated File | Location | Notes |
|----------------|----------|-------|
| Extraction code | `src/query/extract_graph_data.[ext]` | Extension matches chosen language |
| Graph data JSON | `data/temp/graph_data.json` | Intermediate output |
| Visualization HTML | `docs/entity_graph.html` | Self-contained, any browser |
| Server code | `src/server/` | Only if served deployment |
| Dockerfile | `src/server/Dockerfile` | Only if container deployment |
