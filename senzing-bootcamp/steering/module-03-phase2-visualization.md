---
inclusion: manual
---

# Module 3 Phase 2: Entity Resolution Visualization

**Purpose:** Generate and verify a rich interactive visualization web service that demonstrates Senzing's entity resolution value — the bootcamper's first "wow moment."

**Prerequisites:** Phase 1 Steps 1–8 complete (all verification checks passed, TruthSet data loaded and validated)

**Pattern sources:** Follow `visualization-guide.md` Web Service Delivery Sequence for server lifecycle. Follow `visualization-protocol.md` checkpoint map entry `m3_demo_results` for offer/tracking flow.

**Implementation constraints:**

- Python stdlib HTTP server only (`http.server.HTTPServer` + `BaseHTTPRequestHandler`) — no Flask, FastAPI, or third-party HTTP frameworks
- D3.js v7 loaded from CDN (`https://d3js.org/d3.v7.min.js`) — no other external JavaScript dependencies
- Single HTML file with embedded CSS and JavaScript (aside from D3.js CDN import)
- All artifacts reside in `src/system_verification/web_service/`
- All data derived from SDK calls: `export_json_entity_report`, `get_entity_by_entity_id`, `search_by_attributes`, `find_network_by_entity_id`
- Works with three TruthSet data sources: CUSTOMERS, REFERENCE, WATCHLIST

## Step 9: Web Service + Visualization Page

Generate and verify a web service with three API endpoints and a single-page visualization with four interactive tabs.

### 9.1 Generate Web Service

Generate the web service using `generate_scaffold(workflow='web_service')` in the bootcamper's chosen language. Save all files to `src/system_verification/web_service/`.

**Required files:**

| File | Purpose |
|------|---------|
| `src/system_verification/web_service/server.py` | stdlib HTTP server with request routing |
| `src/system_verification/web_service/stats_builder.py` | Statistics computation from `export_json_entity_report` |
| `src/system_verification/web_service/graph_builder.py` | Graph node/edge construction from SDK |
| `src/system_verification/web_service/merges_builder.py` | Multi-record entity extraction from SDK |
| `src/system_verification/web_service/search_builder.py` | Search-by-attributes wrapper |
| `src/system_verification/web_service/index.html` | Single-page visualization (D3.js CDN, embedded CSS/JS) |

### 9.2 API Endpoints

The server SHALL expose these endpoints:

**`GET /api/stats`** — Aggregate entity resolution statistics

```json
{
  "records_total": 510,
  "entities_total": 395,
  "multi_record_entities": 87,
  "cross_source_entities": 42,
  "relationships_total": 156,
  "histogram": {"1": 308, "2": 65, "3": 17, "4+": 5}
}
```

Required fields: `records_total`, `entities_total`, `multi_record_entities`, `cross_source_entities`, `relationships_total`, `histogram`. The `histogram` maps record-count buckets (1, 2, 3, 4+) to entity counts.

**`GET /api/graph`** — Entity nodes and relationship edges

```json
{
  "nodes": [
    {"entity_id": 1, "entity_name": "Robert Smith", "record_count": 3, "data_sources": ["CUSTOMERS", "REFERENCE"], "records": [{"data_source": "CUSTOMERS", "record_id": "1001"}]}
  ],
  "edges": [
    {"source_entity_id": 1, "target_entity_id": 2, "match_key": "+NAME+ADDRESS", "relationship_type": "possible_match"}
  ]
}
```

Each node: `entity_id`, `entity_name`, `record_count`, `data_sources`, `records`. Each edge: `source_entity_id`, `target_entity_id`, `match_key`, `relationship_type`.

**`GET /api/merges`** — Multi-record entities with constituent records

```json
[
  {
    "entity_id": 1, "entity_name": "Robert Smith", "match_key": "+NAME+ADDRESS",
    "records": [
      {"data_source": "CUSTOMERS", "record_id": "1001", "name": "Robert Smith", "address": "123 Main St", "phone": "555-0100", "identifiers": {"SSN": "123-45-6789"}}
    ]
  }
]
```

Each entity: `entity_id`, `entity_name`, `match_key`, `records`. Each record: `data_source`, `record_id`, `name`, `address`, `phone`, `identifiers`. Only entities with 2+ records are returned.

**Error response (all endpoints):** HTTP 500 with `{"error": "<description>"}` on SDK failure.

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

4. **Probe_Panel** — One-click TruthSet entities and search
   - Pre-configured buttons for canonical TruthSet entity pairs (e.g., Robert Smith / Bob Smith)
   - Search input accepting name, address, or phone attributes
   - On click/search: query `GET /api/search` and display resolved entity with records and relationships
   - "No matching entities found" message for empty results

Summary_Banner remains visible above tabs regardless of active tab. Tab switching without page reload.

### 9.4 Start and Verify Web Service

Follow the Web Service Delivery Sequence from `visualization-guide.md`:

1. **Start the server** using `controlBashProcess` with action `start` and the appropriate start command for `src/system_verification/web_service/server.py` (e.g., python3 followed by the server path).

2. **Verify endpoints** (10-second timeout each):

   | Endpoint | Success Criteria |
   |----------|-----------------|
   | `GET /api/stats` | HTTP 200, valid JSON with all required fields (`records_total`, `entities_total`, `multi_record_entities`, `cross_source_entities`, `relationships_total`, `histogram`) |
   | `GET /api/graph` | HTTP 200, valid JSON with at least one node and one edge |
   | `GET /api/merges` | HTTP 200, valid JSON with at least one multi-record entity (2+ records) |

3. **Present to bootcamper:**
   - URL: "Your visualization is running — open `http://localhost:8080` in your browser"
   - Manual restart: "If you need to restart, run the `src/system_verification/web_service/server.py` entry point with python3"
   - Stop: "To stop the server, I can stop the background process for you, or press Ctrl+C if running manually"

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
