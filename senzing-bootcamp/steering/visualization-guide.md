---
inclusion: manual
---

# Entity Graph Visualization Guide

**Purpose:** Walk the bootcamper through building an interactive D3.js entity graph with data extracted from Senzing in their chosen language.

**Before/After:** You have query results but no visual way to explore them. After: a self-contained HTML graph with entities, relationships, match strengths, and interactive features.

**Prerequisites:** ✅ Module 5/6 complete (data loaded) · ✅ Query programs working (Module 7 step 3)

**Triggers:** Load this file when: (1) after exploratory queries in Module 7 step 3, (2) bootcamper asks to "visualize" / "show entity graph" / "generate a visualization", (3) after documenting findings in Module 7. When done, return to `module-07-query-validation.md`.

## Agent Workflow

1. **Confirm intent**

   👉 "Would you like me to help you build an interactive entity graph? It shows resolved entities as a force-directed network with clustering, search, and detail panels."

   If declined, return to `module-07-query-validation.md`. WAIT for response.

2. **Gather requirements**

   👉 "Which data source(s) should the graph include? And which features: force layout, detail panel, cluster highlighting, search/filter, summary statistics?"

   WAIT for response.

3. **Generate data extraction code**

   > **Agent instruction:** Read Chosen_Language from `config/bootcamp_preferences.yaml`. Load the appropriate language steering file. Use `get_sdk_reference` for SDK signatures. Use `generate_scaffold` with `workflow='query'`. Use `find_examples` for query patterns.

   Extraction code must: iterate over loaded records via `get_entity_by_record_id` (never guessed entity ID ranges), deduplicate entities, use `get_entity_by_entity_id` with relationship flags for edges, classify match strength per table below, warn if >500 entities, log per-entity/per-relationship SDK errors and continue, write JSON matching the Graph Data Model schema. Save to `src/query/extract_graph_data.[ext]`.

   👉 "Run the extraction and confirm the output JSON looks good." WAIT for response.

4. **Generate HTML visualization**

   > **Agent instruction:** Generate a single self-contained HTML file (D3.js v7, CSS, data inline). Include only selected features per guidance below. Wrap D3.js init in try/catch with user-friendly error display.

   Save to `docs/entity_graph.html`.

   👉 "Open the HTML file — does it look right? Want changes?" WAIT for response.

5. **Optional web server**

   👉 "Would you like a web server for live data refresh?"

   If yes, follow Web Server Guidance below. If no, skip. WAIT for response.

6. **Iterate and refine**

   👉 "Want any changes to the graph, features, or extraction?"

   Regenerate affected components using the same MCP tools. When done, return to `module-07-query-validation.md`. WAIT for response.

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

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve visualization HTML |
| `/health` | GET | `{ "status": "ok", "lastRefresh": "<ISO timestamp>" }` |
| `/refresh` | POST | Re-query Senzing, regenerate graph data, return JSON |

> **Agent instruction:** Ask preferred framework (WAIT for response). Use `generate_scaffold` with chosen language/framework. Save to `src/server/`. Container deployment → generate `src/server/Dockerfile`.

No server requested → produce only the self-contained HTML file.

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
