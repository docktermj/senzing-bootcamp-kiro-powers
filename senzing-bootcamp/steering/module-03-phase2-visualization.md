---
inclusion: manual
---

# Module 3 Phase 2: Entity Resolution Visualization

**Purpose:** Generate and verify a rich interactive visualization web service that demonstrates Senzing's entity resolution value — the bootcamper's first "wow moment."

**Prerequisites:** Phase 1 Steps 1–8 complete (all verification checks passed, TruthSet data loaded and validated)

**Pattern sources:** Follow `visualization-guide.md` Web Service Delivery Sequence for server lifecycle. Follow `visualization-guide.md` checkpoint map entry `m3_demo_results` for offer/tracking flow.

**Implementation constraints:**

- Python stdlib HTTP server only (`http.server.HTTPServer` + `BaseHTTPRequestHandler`) — no Flask, FastAPI, or third-party HTTP frameworks
- D3.js v7 loaded from the d3js.org CDN (`d3js.org/d3.v7.min.js`) — no other external JavaScript dependencies
- Single HTML file with embedded CSS and JavaScript (aside from the D3.js CDN import)
- All artifacts reside in `src/system_verification/web_service/`
- All data derived from SDK calls: `export_json_entity_report`, `get_entity_by_entity_id`, `search_by_attributes`, `find_network_by_entity_id`
- Works with three TruthSet data sources: CUSTOMERS, REFERENCE, WATCHLIST

## CRITICAL LESSONS FOR VISUALIZATION GENERATION

1. **Use Python generator script** — Create `write_html.py` with HTML as a triple-quoted string. Run `python3 write_html.py` to produce `index.html`. NEVER use `fs_write` or `str_replace` to write HTML+JS content directly.
2. **Validate JavaScript syntax** — After generating `index.html`, run `node --check index.html` equivalent validation or embed the JS in a way that can be syntax-checked.
3. **No inline onclick with dynamic values** — Use `data-*` attributes and `querySelectorAll` event listeners. Inline `onclick="fn('${value}')"` causes quote-escaping failures.
4. **Quote discipline** — Inside Python triple-quoted strings: use double quotes for JavaScript strings, single quotes for HTML attributes.
5. **D3.js callback syntax** — Use `function(){}` for all D3.js callbacks, NOT arrow functions. Arrow functions break `this` binding to DOM elements.
6. **Explicit SVG dimensions** — Set `width` and `height` attributes on SVG elements. Do not rely on CSS-only sizing.
7. **Map graph edge keys for D3 `forceLink`** — `/api/graph` returns edges keyed by `source_entity_id`/`target_entity_id` (the API contract). D3's `forceLink` resolves each edge against node ids via `source`/`target`. In `drawGraph`, map every edge to expose `source`/`target` (set from `source_entity_id`/`target_entity_id`) **before** passing edges to `forceLink().links(...)`. Skipping this map is a **silent failure**: no console error is raised and the Entity Graph renders empty even though `/api/graph` returned nodes and edges. Preserve node `id`/`entity_id` so the mapped `source`/`target` values resolve to nodes.

---

## ⚠️ DO NOT SKIP — Phase 2 Execution Is Mandatory

> ⛔ **MANDATORY GATE — UNCONDITIONAL EXECUTION REQUIREMENT**
>
> **This phase is MANDATORY. It is NOT optional. NEVER skip it.** This is an
> absolute, non-negotiable rule.
>
> Phase 2 visualization generation MUST be executed in full, regardless of ANY
> internal consideration. No agent-initiated skip is permitted under any
> circumstance. DO NOT transition to Module 4 until Phase 2 is complete and the
> bootcamper has confirmed they have explored the visualization.
>
> **Prohibited rationalizations (the agent must NEVER use these as justification to skip):**
>
> - Session length ("given the length of this session")
> - Context budget pressure ("running low on context")
> - Perceived redundancy ("similar to what was already demonstrated")
> - Time constraints ("to save time")
> - Any other agent-internal reasoning
>
> **NEVER clause:** There is NO condition, threshold, or scenario under which the agent
> may self-initiate a skip of this step. The ⛔ designation is absolute. Only the
> bootcamper can attempt a skip via the skip-step protocol — and the protocol itself
> refuses mandatory gates. The agent cannot override, deprioritize, or rationalize
> around this constraint.
>
> Skipping Phase 2 deprives the bootcamper of their first "wow moment" with entity
> resolution results.

---

## Step 9: Web Service + Visualization Page

Generate and verify a web service with four API endpoints and a single-page visualization with four interactive tabs.

### 9.1 Generate Web Service

Generate the web service artifacts in `src/system_verification/web_service/`. Use a **Python generator script** (`write_html.py`) to produce the visualization HTML — do NOT use `fs_write` or `str_replace` to write HTML+JS content directly.

**Generation approach:**

1. Create `write_html.py` in `src/system_verification/web_service/` that contains the complete `index.html` content as a Python triple-quoted string and writes it to `index.html` in the same directory.
2. Run `python3 src/system_verification/web_service/write_html.py` to produce `index.html`.
3. Create `server.py` using Python stdlib HTTP server (`http.server.HTTPServer` + `BaseHTTPRequestHandler`) — no Flask, FastAPI, or third-party HTTP frameworks.
4. Create builder modules (`stats_builder.py`, `graph_builder.py`, `merges_builder.py`, `search_builder.py`) for data computation.

The generated `index.html` is a single file with embedded CSS and JavaScript. D3.js v7 is loaded from the d3js.org CDN (`d3js.org/d3.v7.min.js`) — no other external JavaScript dependencies.

**Required files:**

| File | Purpose |
|------|---------|
| `src/system_verification/web_service/write_html.py` | Python generator script: triple-quoted HTML string → writes `index.html` |
| `src/system_verification/web_service/server.py` | Python stdlib HTTP server (`http.server.HTTPServer` + `BaseHTTPRequestHandler`) with request routing |
| `src/system_verification/web_service/stats_builder.py` | Statistics computation from `export_json_entity_report` |
| `src/system_verification/web_service/graph_builder.py` | Graph node/edge construction from SDK. **Edges require explicit relationship discovery** — a default `export_json_entity_report` does NOT include relationships, so reading `RELATED_ENTITIES` off a plain export yields zero edges. Discover relationships by calling `find_network_by_entity_id` for multi-record/related entities (it returns the relationship network with match keys) AND/OR by requesting the entity export/report with the relationship-inclusion flag (confirm the exact flag name — e.g. `SZ_ENTITY_INCLUDE_ALL_RELATIONS` — via the Senzing MCP server) so `RELATED_ENTITIES` is populated. Build one `edge` per relationship: `match_key` from the relationship match-key string, `relationship_type` from the relationship kind (possible match / disclosed / discovered); de-duplicate edges and only create an edge when both endpoints appear in the node set. |
| `src/system_verification/web_service/merges_builder.py` | Multi-record entity extraction from SDK |
| `src/system_verification/web_service/search_builder.py` | Search-by-attributes wrapper with entity enrichment: calls `search_by_attributes`, then `get_entity_by_entity_id` for each matched entity (up to 10) to retrieve match keys, feature scores, and resolution rules (full enrichment spec in the API reference companion) |
| `src/system_verification/web_service/index.html` | Generated output from `write_html.py` (single-page visualization, D3.js v7 CDN, embedded CSS/JS) |

### 9.2 API Endpoints

The server SHALL expose four endpoints. Compact summaries follow — the full JSON
response schemas, field tables, and the `search_builder.py` enrichment specification
live in the API reference companion (see below):

- **`GET /api/stats`** — Aggregate entity resolution statistics. Required fields: `records_total`, `entities_total`, `multi_record_entities`, `cross_source_entities`, `relationships_total`, `histogram` (record-count buckets 1/2/3/4+ → entity counts).
- **`GET /api/graph`** — Entity nodes and relationship edges. Each node: `entity_id`, `entity_name`, `record_count`, `data_sources`, `records`. Each edge: `source_entity_id`, `target_entity_id`, `match_key`, `relationship_type`. Edges are **discovered via relationship discovery, not a default export**: call `find_network_by_entity_id` for multi-record/related entities and/or request the entity export with the relationship-inclusion flag (e.g. `SZ_ENTITY_INCLUDE_ALL_RELATIONS`, confirmed via the Senzing MCP server). Edges are de-duplicated and limited to entities present in the node set.
- **`GET /api/merges`** — Multi-record entities (2+ records only) with constituent records. Each entity: `entity_id`, `entity_name`, `match_key`, `records`; each record: `data_source`, `record_id`, `name`, `address`, `phone`, `identifiers`.
- **`GET /api/search`** — Search entities with enriched resolution reasoning. Each result has base fields (`entity_id`, `entity_name`, `record_count`, `data_sources`) plus enrichment fields: `match_keys` (`entity_level` + `per_record`), `feature_scores`, `resolution_rules`, and `enrichment_error`. Enrichment is capped at 10 entities; on per-entity enrichment failure the result carries null enrichment fields and a non-empty `enrichment_error`.
- **Error response (all endpoints):** HTTP 500 with `{"error": "<description>"}` on SDK failure.

> **Full response schemas (all four endpoints), the `search_builder.py` enrichment
> specification (enrichment flow, the 10-entity cap, extraction functions, and graceful
> degradation), and the error-case / single-record response examples are in the API
> reference companion. Load it on demand:**
>
> #[[file:senzing-bootcamp/steering/module-03-visualization-api-reference.md]]

### 9.3 Visualization Page Components

The `src/system_verification/web_service/index.html` SHALL contain:

**Summary_Banner** — 5 headline statistics displayed above the tab navigation:

1. Records Loaded
2. Resolved Entities
3. Multi-Record Entities
4. Cross-Source Matches
5. Relationships Discovered

Presented left-to-right with arrow indicators conveying the resolution pipeline narrative. Fetches from `GET /api/stats` on page load.

**Tab Navigation** — Exactly 4 tabs, defaulting to Entity Graph on load:

1. **Entity_Graph** — D3.js force-directed graph
   - Nodes colored by primary data source: CUSTOMERS=#3b82f6, REFERENCE=#22c55e, WATCHLIST=#f59e0b
   - Nodes sized proportionally to record count (radius = min(max(8 + record_count × 4, 8), 40))
   - Edges labeled with Match_Key strings (e.g., +NAME+ADDRESS, +PHONE)
   - Tooltip on hover: entity name, entity ID, record count, data sources
   - Fetches from `GET /api/graph`

   **Graph container height:** The `#graph-container` element SHALL use viewport-relative height:

   ```css
   #graph-container {
     height: calc(100vh - 120px);
     /* 120px offset = fixed header (~50px) + summary banner (~40px) + tab navigation (~30px) */
   }
   ```

   Do NOT use a fixed pixel height (e.g., `600px`) for the graph container. The graph must fill the remaining viewport space below the fixed UI elements.

   **Entity Graph UX Features:**

   - **Node labels:** Each node displays a text label showing the entity name, truncated to 20 characters maximum with ellipsis (e.g., "Robert Smith-Johnso…"). Labels are positioned below the node circle.
   - **Edge labels:** Each edge displays a text label showing the match key string (e.g., +NAME+ADDRESS). Labels are positioned at the midpoint of the edge line.
   - **Click-to-detail modal:** Clicking a node opens a modal overlay displaying:
     - Entity ID
     - Primary name
     - Data sources (list)
     - Record count
     - Constituent records (data_source + record_id for each)
     The modal includes a close button and closes on overlay background click.
   - **Zoom and pan:** Implement D3.js zoom behavior — mouse wheel to zoom, drag to pan the graph viewport. Apply zoom transform to the SVG group containing nodes and edges.
   - **Color legend:** Display a color legend mapping data source names to node colors:
     - CUSTOMERS = #3b82f6
     - REFERENCE = #22c55e
     - WATCHLIST = #f59e0b
     The legend is positioned in the top-right corner of the graph container.
   - **Responsive resize:** On window resize, update SVG dimensions and re-center the force simulation. Use a `resize` event listener to recalculate width/height and restart the force layout center.

**D3.js Code Style Constraints:**

- **Use `function(){}` syntax for all D3.js callbacks** — Do NOT use arrow functions (`() => {}`) in D3.js event handlers, `.each()`, `.attr()` callbacks, or any other D3 method that binds `this` to the DOM element. Arrow functions break `this` binding to DOM elements in D3 callbacks, causing silent failures when accessing the current element via `d3.select(this)`.
- **Explicit `width` and `height` attributes on SVG elements** — Always set `width` and `height` as attributes on `<svg>` elements (e.g., `.attr('width', width).attr('height', height)`). Do NOT rely on CSS-only sizing (e.g., `width: 100%` in a stylesheet without corresponding attributes). CSS-only sizing causes rendering issues in some browsers and when SVG is embedded in flex containers.
- **Map graph edges to `source`/`target` before the force simulation** — In `drawGraph`, map each `/api/graph` edge to expose `source`/`target` (from `source_entity_id`/`target_entity_id`) before passing edges to `forceLink`, or the graph renders empty (see Critical Lesson 7).

2. **Record_Merges_View** — Card-based display of multi-record entities
   - One card per entity with side-by-side constituent records
   - Each record labeled with data source and record ID
   - Matching features highlighted (name, address, phone, identifiers)
   - Match_Key chips indicating which feature combinations triggered the merge
   - Fetches from `GET /api/merges`

3. **Merge_Statistics** — D3.js histogram of records-per-entity distribution
   - Buckets: 1 record, 2 records, 3 records, 4+ records
   - Summary statement: "[X] records collapsed into [Y] entities, including [Z] multi-record entities"
   - Labeled axes and count annotations on bars
   - Fetches from `GET /api/stats`

4. **Probe_Panel** — One-click TruthSet entities and search with resolution reasoning
   - Pre-configured buttons for canonical TruthSet entity pairs (e.g., Robert Smith / Bob Smith)
   - Search input accepting name, address, or phone attributes
   - On click/search: query `GET /api/search` and display resolved entity with records, relationships, and resolution reasoning
   - "No matching entities found" message for empty results

   **Resolution Reasoning Display:**

   For each search result, the Probe_Panel SHALL display match keys, feature scores, and resolution rules from the enriched `/api/search` response:

   **Match Key Chips:**
   - Display the entity-level match key string for each resolved entity (e.g., `+NAME+DOB+PHONE`)
   - Each individual feature indicator within a match key (e.g., `+NAME`, `+DOB`, `+PHONE`) SHALL be rendered as a separate inline `<span>` element with a visible border and background color distinguishing it from adjacent indicators and surrounding text
   - If a resolved entity contains multiple records, display per-record match keys indicating which features linked each record into the entity
   - If a resolved entity contains only one record, omit the per-record match key section for that entity
   - If an entity has no match key data available (i.e., `match_keys` is null), display a placeholder label: "No match key information available"

   **Feature Scores:**
   - Display feature scores for the search match comparison as a structured list
   - Each feature score SHALL show the feature name, numeric percentage, and classification label (e.g., `NAME: 97% CLOSE`)
   - When multiple features were compared, list all scored features in a structured format, one per line

   **Resolution Rules:**
   - Display the resolution rule applied to each record within the entity (e.g., `CNAME_CFF_CEXCL`)
   - Per-record rule strings SHALL be displayed in monospace/code-style format (e.g., `<code>` or `font-family: monospace`) to distinguish them from natural language text
   - When an entity contains multiple records, show the resolution rule next to each constituent record with its data source and record ID

Summary_Banner remains visible above tabs regardless of active tab. Tab switching without page reload.

### 9.4 Start and Verify Web Service

Follow the Web Service Delivery Sequence from `visualization-guide.md`:

1. **Start the server** using `controlBashProcess` with action `start` and the appropriate start command for `src/system_verification/web_service/server.py` (e.g., python3 followed by the server path).

2. **Verify endpoints** (10-second timeout each):

   | Endpoint | Success Criteria |
   |----------|-----------------|
   | `GET /api/stats` | HTTP 200, valid JSON with all required fields (`records_total`, `entities_total`, `multi_record_entities`, `cross_source_entities`, `relationships_total`, `histogram`) |
   | `GET /api/graph` | HTTP 200, valid JSON with at least one node and one edge — this must hold on the loaded TruthSet data (relationship discovery, per `graph_builder.py` above, produces the edges) |
   | `GET /api/merges` | HTTP 200, valid JSON with at least one multi-record entity (2+ records) |

3. **Present to bootcamper:**
   - URL: "Your visualization is running — open `http://localhost:8080` in your browser"
   - Manual restart: "If you need to restart, run the `src/system_verification/web_service/server.py` entry point with python3"
   - Stop: "To stop the server, I can stop the background process for you, or press Ctrl+C if running manually"

**Graph render smoke check** (run after `index.html` is generated, before the Guided Tour — do **not** present the graph until it passes):

   - **Generated-code check (static, always runs):** Inspect the generated `index.html` `drawGraph` and confirm it maps each edge to expose `source`/`target` (set from `source_entity_id`/`target_entity_id`) **before** `forceLink().links(...)`. If the mapping is absent, fail.
   - **Rendered/data check (dynamic):** Using the `GET /api/graph` ≥1 node / ≥1 edge result above as precondition, when `/api/graph` returns ≥1 node the rendered graph must show visible node elements (SVG `circle`/node-group count > 0).

   | Check | Success Criteria |
   |---|---|
   | Graph edge-key mapping | Generated `index.html` `drawGraph` maps `source_entity_id`/`target_entity_id` → `source`/`target` before `forceLink`; rendered graph shows visible nodes when `/api/graph` returns ≥1 node |

   **Fix_Instruction (on failure):** add the edge-key mapping per Critical Lesson 7, regenerate `index.html`, and re-verify. Do not proceed to the Guided Tour until the graph passes.

**Guided Tour — deliver the following as a single structured chat message
(no interactive pauses):**

Present this guided tour to the bootcamper immediately after confirming
the URL is accessible:

---

🗺️ **What You're Looking At — A Quick Tour**

**Entity Graph tab (default view):**

- **Cross-source matches:** Nodes with multiple colors represent entities
  resolved across data sources (e.g., a CUSTOMERS record matched to a
  REFERENCE record). These are Senzing's highest-value findings.
- **Name variations:** Senzing resolves name variants automatically —
  look for entities like "Robert Smith" that merged records originally
  entered as "Bob Smith" or "R. Smith".
- **Relationship edges:** Lines between nodes show relationships.
  The labels (e.g., +NAME+ADDRESS, +PHONE) are match keys — they tell
  you which features Senzing used to link those entities.

**Merge Statistics tab:**

- The **records-per-entity histogram** shows how many records collapsed
  into each entity. A tall "1" bar means many unique entities; bars at
  "2", "3", "4+" show where Senzing found duplicates across sources.

---

   👉 Take your time exploring the visualization. Let me know when you're ready and I'll continue with cleanup.

   🛑 STOP — End your response here and wait for the bootcamper to confirm they are done exploring.

4. **On verification failure:** Report the specific endpoint that failed, the HTTP status received, and provide a Fix_Instruction:
   - Port 8080 in use → suggest alternative port or kill existing process
   - SDK error → re-run SDK initialization (Step 3)
   - HTML file missing → regenerate web service artifacts
   - Timeout → check server process is running, check for import errors

**Checkpoint:** Write to `config/bootcamp_progress.json`:

```json
{
  "module_3_verification": {
    "checks": {
      "web_service": {"status": "passed|failed", "port": 8080},
      "web_page": {"status": "passed|failed", "url": "http://localhost:8080/"}
    }
  }
}
```

**Success indicator:** ✅ Web service running on port 8080 with entity resolution visualization page accessible and rendering correctly.
