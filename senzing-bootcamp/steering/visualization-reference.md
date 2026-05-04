---
inclusion: manual
---

# Visualization Reference

Detailed schemas, feature specs, and error handling for entity graph visualizations. Loaded on demand via `#[[file:]]` from `visualization-guide.md`.

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

## Match Strength Classification

| Senzing Match Level | Category | Edge Color | Hex |
|---------------------|----------|------------|-----|
| 1 (resolved) | strong | green | #22c55e |
| 2 (possibly same) | moderate | orange | #f59e0b |
| 3+ (possibly related) | weak | red | #ef4444 |

Cluster node coloring by average match level: ≤1.5 → green, ≤2.5 → orange, >2.5 → red, no relationships → gray (#9ca3af).

## Visualization Feature Guidance

- **D3.js Force Layout:** D3.js v7 force simulation. Node radius proportional to record count. Edge color by match strength. Drag-to-reposition, zoom, pan. Tooltip on hover.
- **Detail Panel:** Click node → side panel with entity ID, primary name, data sources, record list, shared features. Click away to dismiss.
- **Cluster Highlighting:** Dropdown: data source coloring (`schemeCategory10`), match strength coloring, no clustering. Legend updates per mode.
- **Search & Filter:** Text input filtering by name or record ID (case-insensitive substring). Matches highlighted, non-matches dimmed. Clear button.
- **Statistics:** Total entities, records, relationships. Unique data source count. Cross-source match rate.

## Static HTML Capabilities

Fully available without any running server: force layout, cluster highlighting, local search/filter, detail panel (from inline JSON), statistics display.

**Limitations:** No live entity detail fetching, no real-time search by attributes, no data refresh without re-running extraction. Recommended max: 500 entities.

## Error Handling

| Error Condition | Handling | User Feedback |
|-----------------|----------|---------------|
| SDK not initialized / missing DB | Exit with error | "Senzing database not found. Complete Module 5 first." |
| Empty database | Exit with error | "No entities found. Load data first." |
| Per-entity SDK error | Log, skip, continue | "Warning: Failed to retrieve entity for record {record_id}. Skipping." |
| Per-relationship SDK error | Log, skip, continue | "Warning: Failed to retrieve relationships for entity {entity_id}. Skipping." |
| Entity count > 500 | Warn, offer limit | "Warning: {count} entities. Rendering may be slow. Limit to 500?" |
| No relationships | Continue, isolated nodes | "No relationships found. Graph will show isolated nodes." |

Browser-side: try/catch around D3.js init; display user-friendly error on failure.

## File Placement

| Generated File | Location |
|----------------|----------|
| Extraction code | `src/query/extract_graph_data.[ext]` |
| Graph data JSON | `data/temp/graph_data.json` |
| Visualization HTML | `docs/entity_graph.html` |
| Server code | `src/server/` (web service only) |
