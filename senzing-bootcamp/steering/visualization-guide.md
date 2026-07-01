---
inclusion: manual
---

# Entity Graph Visualization Guide

**Purpose:** Walk the bootcamper through building an interactive D3.js entity graph with data extracted from Senzing in their chosen language. Also serves as the single authoritative definition of the visualization offer flow used across Modules 3, 5, 7, and 8.

**Before/After:** You have query results but no visual way to explore them. After: a self-contained HTML graph with entities, relationships, match strengths, and interactive features.

**Prerequisites:** ✅ Module 5/6 complete (data loaded) · ✅ Query programs working (Module 7 step 3)

**Triggers:** Load this file when: (1) a module steering file instructs you to execute a visualization checkpoint, (2) after exploratory queries in Module 7 step 3, (3) bootcamper asks to "visualize" / "show entity graph" / "generate a visualization", (4) after documenting findings in Module 7. When done, return to the current module steering file.

## Visualization Offer Protocol

### Checkpoint Map

```yaml
checkpoints:
  module_3:
    - id: "m3_demo_results"
      trigger: "Verification results displayed successfully"
      context: "these system verification results"
      types: [Static_HTML_Report, Web_Service_Dashboard]
  module_5:
    - id: "m5_quality_assessment"
      trigger: "Quality assessment scoring complete"
      context: "this data quality assessment"
      types: [Static_HTML_Report]
  module_7:
    - id: "m7_exploratory_queries"
      trigger: "Exploratory queries produce results"
      context: "your resolved entities and relationships"
      types: [Static_HTML_Report, Interactive_D3_Graph, Web_Service_Dashboard]
    - id: "m7_findings_documented"
      trigger: "Findings documented"
      context: "your query results and validation metrics"
      types: [Static_HTML_Report, Interactive_D3_Graph, Web_Service_Dashboard]
  module_8:
    - id: "m8_performance_report"
      trigger: "Performance report generated"
      context: "the performance benchmarks and optimization results"
      types: [Static_HTML_Report, Web_Service_Dashboard]
```

### Offer Template

When you reach a checkpoint, use this exact template. Replace `{context}` with the checkpoint's context string and include only the types listed for that checkpoint.

```text
Would you like me to create a visualization of {context}?

{numbered_list_of_available_types}
```

Each type in the numbered list uses **bold name + one-line description**:

1. **Static HTML file** — a self-contained file you can open directly in your browser, no server needed
2. **Interactive D3 graph** — a force-directed network graph showing entities, relationships, and match strengths
3. **Web service** — a localhost server with live SDK queries, data refresh, and interactive details

Only include the types available for the current checkpoint. Number them sequentially starting at 1.

After presenting the options, end your response with:

> 🛑 STOP — End your response here. Wait for the bootcamper's input.

Do NOT continue past this point. Wait for the bootcamper to choose an option or decline.

### Delivery-Mode Selection

After the bootcamper selects a visualization type, present the delivery-mode choice.

**Skip condition:** If the checkpoint's available types list contains ONLY `Static_HTML_Report` (e.g., Module 5), skip this question entirely and default to static delivery.

For all other checkpoints, present:

> Now that you've chosen **{chosen_type}**, how would you like it delivered?
>
> 1. **Static HTML** — Self-contained file with data baked in. Open directly in your browser, no server needed. Does not update with new data.
> 2. **Web service + HTML** — A small localhost HTTP service with live SDK queries. Data refreshes on reload. Requires a running local process.

🛑 STOP — End your response here. Wait for the bootcamper's input before proceeding.

### Dispatch Rules

After the bootcamper selects both a visualization type and a delivery mode:

- **Web service delivery mode (any type):** Load `visualization-web-service.md` for scaffolding and lifecycle management.
- **Static HTML delivery mode (Static_HTML_Report type):** Generate the visualization inline following the generation workflow below. Do NOT load `visualization-web-service.md`.
- **Static HTML delivery mode (Interactive_D3_Graph or Web_Service_Dashboard type):** Follow the generation workflow below for graph layout, data binding, and template structure. Do NOT load `visualization-web-service.md`.

### Decline Handling

If the bootcamper declines the visualization offer:

- Acknowledge with a single sentence (e.g., "No problem — we'll continue with the module.").
- Do NOT re-offer the same visualization at this checkpoint.
- Do NOT ask follow-up questions about why they declined.
- Continue the module workflow immediately.

### Explicit-Request Override

If the bootcamper explicitly requests a visualization at any point — regardless of prior declines or existing tracker entries — honor the request immediately. Update any `"declined"` tracker entry to `"offered"` and proceed.

### Deferred First-Visualization Guarantee

This reuses the existing offer flow above — no new offer template, tracker, or checkpoint map. When Module 3 is opted out and the standalone demo is declined, a `first_visualization: owed` marker persists in `config/bootcamp_progress.json` (see `module-03-phase1-verification.md`). The first later module with resolved data satisfies that owed marker through its existing offer.

When a visualization is **generated** (the existing `config/visualization_tracker.json` entry reaches status → `generated`) at either of these existing checkpoints AND `first_visualization` is `owed`:

- **Module 6 results dashboard** (the results-dashboard offer in `module-06-phaseD-validation.md`): after generating, call `clear_first_visualization_owed(satisfied_by="module_6_deferred")` from `scripts/progress_utils.py`.
- **Module 7 `m7_exploratory_queries`** (entity graph checkpoint): after generating, call `clear_first_visualization_owed(satisfied_by="module_7_deferred")` from `scripts/progress_utils.py`.

Check the owed state with `is_first_visualization_owed(progress)` before clearing; the clear is idempotent and a no-op when nothing is owed. This is journey-level only — it does not weaken the Module 3 Step 9 gate, which stays unconditional whenever Module 3 runs.

## CRITICAL LESSONS FOR VISUALIZATION GENERATION

1. **Use Python generator script** — Create `write_html.py` with HTML as a triple-quoted string. Run `python3 write_html.py` to produce `index.html`. NEVER use `fs_write` or `str_replace` to write HTML+JS content directly.
2. **Validate JavaScript syntax** — After generating `index.html`, run `node --check index.html` equivalent validation or embed the JS in a way that can be syntax-checked.
3. **No inline onclick with dynamic values** — Use `data-*` attributes and `querySelectorAll` event listeners. Inline `onclick="fn('${value}')"` causes quote-escaping failures.
4. **Quote discipline** — Inside Python triple-quoted strings: use double quotes for JavaScript strings, single quotes for HTML attributes.
5. **D3.js callback syntax** — Use `function(){}` for all D3.js callbacks, NOT arrow functions. Arrow functions break `this` binding to DOM elements.
6. **Explicit SVG dimensions** — Set `width` and `height` attributes on SVG elements. Do not rely on CSS-only sizing.

## Python Generator Architecture

The Python generator script approach is the **MANDATED** method for all visualization generation across modules. Every module that produces HTML visualization artifacts MUST use this pattern.

### Pattern: `write_html.py` → `index.html`

1. Create a Python script named `write_html.py` that contains the complete HTML document as a triple-quoted string.
2. The script writes the string to `index.html` when executed: `python3 write_html.py`.
3. The generated `index.html` is a single self-contained file with embedded CSS, JavaScript, and D3.js v7 loaded from CDN.

### File Placement

`write_html.py` resides alongside `server.py` in the web service directory:

```text
src/system_verification/web_service/
├── write_html.py      # Python generator script (triple-quoted HTML string)
├── index.html         # Generated output (produced by write_html.py)
├── server.py          # Python stdlib HTTP server
└── *_builder.py       # Data builder modules
```

### Why This Approach

Using `fs_write` or `str_replace` to write HTML+JS content directly causes quote-escaping conflicts — nested single quotes, double quotes, backticks, and template literals in JavaScript collide with the tool's own string delimiters. The Python triple-quoted string (`"""..."""`) eliminates these conflicts entirely because the HTML+JS content is never parsed by the file-writing tool's string handling.

## Static HTML Generation Workflow

1. **Gather requirements**

   👉 "Which data source(s) should the graph include?"

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

2. **Generate data extraction code**

   > **Agent instruction:** Read Chosen_Language from `config/bootcamp_preferences.yaml`. Load the appropriate language steering file. Use `get_sdk_reference` for SDK signatures. Use `generate_scaffold` with `workflow='query'`. Use `find_examples` for query patterns.

   Extraction code must: iterate over loaded records via `get_entity_by_record_id` (never guessed entity ID ranges), deduplicate entities, use `get_entity_by_entity_id` with relationship flags for edges, classify match strength per the reference below, warn if >500 entities, log per-entity/per-relationship SDK errors and continue, write JSON matching the Graph Data Model schema. Save to `src/query/extract_graph_data.[ext]`.

   👉 "Run the extraction and confirm the output JSON looks good."

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

3. **Generate HTML visualization**

   > **Agent instruction:** Generate a single self-contained HTML file (D3.js v7, CSS, data inline). Include only selected features per guidance below. Wrap D3.js init in try/catch with user-friendly error display.

   Save to `docs/entity_graph.html`.

   👉 "Open the HTML file — does it look right?"

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

4. **Iterate and refine**

   👉 "Want any changes to the graph, features, or extraction?"

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

   Regenerate affected components using the same MCP tools. When done, return to the current module steering file.

## Web Service Delivery Sequence

When presenting a completed web service to the bootcamper, the server is started automatically as a background process. ALWAYS follow this exact 5-step sequence:

1. **Start the server automatically:** Use `controlBashProcess` with action `start` and the language-appropriate start command.
2. **Verify the server is running:** Read the process output and confirm the server started successfully — look for "running on", "listening on", or "started on port".
3. **Present URL, manual restart command, and stop instructions.**
4. **Wait for user confirmation:** End your response with a 👉 question and a 🛑 STOP directive. Wait for the bootcamper to confirm they have finished exploring the visualization. Do NOT proceed to cleanup, checkpoint writes, or any subsequent steps until the bootcamper confirms they are done. Example prompt:

   > 👉 Take your time exploring. Let me know when you're ready and I'll continue with cleanup.
   >
   > 🛑 STOP — End your response here. Wait for the bootcamper's real input.
5. **Fallback on failure:** Report the error, provide troubleshooting guidance, fall back to manual instructions.

**NEVER present a localhost URL before confirming the server is actually running.**

## Offline vs Online Decision Matrix

| Scenario | Recommended | Rationale |
| -------- | ----------- | --------- |
| Sharing with stakeholders without SDK | Static HTML | Self-contained, no server needed |
| Interactive exploration with live queries | Web Service | Real-time entity detail and search |
| No persistent network access | Static HTML | No server or database required |
| Iterating on data quality with frequent reloads | Web Service | `/refresh` avoids re-running extraction |

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

### Required Entity Graph Features

| Feature | Specification |
|---------|--------------|
| Node labels | Text labels showing entity name, truncated to 20 characters max |
| Edge labels | Text labels showing match key string (e.g., +NAME+ADDRESS) |
| Click-to-detail modal | Click node → modal with entity ID, primary name, data sources, record count, constituent records |
| Zoom/pan | D3.js zoom behavior: mouse wheel to zoom, drag to pan |
| Color legend | Legend mapping data source names to node colors (CUSTOMERS=#3b82f6, REFERENCE=#22c55e, WATCHLIST=#f59e0b) |
| Responsive resize | Window resize → update SVG dimensions and re-center force simulation |

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

## Visualization Tracker

The visualization tracker lives at `config/visualization_tracker.json`. Use it to record and check visualization offer state.

### Schema

```json
{
  "version": "1.1.0",
  "offers": [
    {
      "module": 7,
      "checkpoint_id": "m7_exploratory_queries",
      "timestamp": "2025-07-15T10:30:00Z",
      "status": "offered",
      "chosen_type": null,
      "delivery_mode": null,
      "output_path": null
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| module | integer | Module number (3, 5, 7, or 8) |
| checkpoint_id | string | Checkpoint identifier from the map above |
| timestamp | string (ISO 8601) | When the event occurred |
| status | string | One of: `offered`, `accepted`, `declined`, `generated` |
| chosen_type | string or null | Set on accept |
| delivery_mode | string or null | `"static"` or `"web_service"`. Null when `offered`. Defaults to `"static"` for Module 5. |
| output_path | string or null | Set on generate (relative path to the output file) |

### Valid State Transitions

- `offered` → `accepted`: Set `chosen_type` AND `delivery_mode`
- `offered` → `declined`: Leave `delivery_mode` as `null`
- `accepted` → `generated`: Set `output_path`

### Read/Write Instructions

1. **Before offering:** Read `config/visualization_tracker.json`. If an entry with the current `checkpoint_id` exists, skip the offer.
2. **On offer:** Write a new entry with `status: "offered"`.
3. **On accept:** Update `status` to `"accepted"`, set `chosen_type` and `delivery_mode`.
4. **On decline:** Update `status` to `"declined"`.
5. **On generate:** Update `status` to `"generated"` and set `output_path`.

If `config/visualization_tracker.json` does not exist, create it with `{"version": "1.1.0", "offers": []}`.
