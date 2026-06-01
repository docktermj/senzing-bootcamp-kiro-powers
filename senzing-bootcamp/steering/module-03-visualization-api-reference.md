---
inclusion: manual
---

# Module 3 Visualization — API Reference

**Purpose:** Full API response schemas and the `search_builder.py` enrichment specification for the Module 3 Phase 2 visualization web service. This is reference material loaded on demand from `module-03-phase2-visualization.md` (Step 9). See that file for the executable generation and verification steps.

## API Endpoints

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

**`GET /api/search`** — Search entities with enriched resolution reasoning

```json
{
  "results": [
    {
      "entity_id": 1,
      "entity_name": "Robert Smith",
      "record_count": 3,
      "data_sources": ["CUSTOMERS", "REFERENCE"],
      "match_keys": {
        "entity_level": "+NAME+DOB+PHONE",
        "per_record": ["+NAME+DOB", "+PHONE", "+NAME+ADDRESS"]
      },
      "feature_scores": [
        {"feature": "NAME", "score": 97, "label": "CLOSE"},
        {"feature": "DOB", "score": 100, "label": "SAME"},
        {"feature": "PHONE", "score": 100, "label": "SAME"}
      ],
      "resolution_rules": [
        {"data_source": "CUSTOMERS", "record_id": "1001", "rule": "CNAME_CFF_CEXCL"},
        {"data_source": "REFERENCE", "record_id": "2001", "rule": "CNAME_CFF"}
      ],
      "enrichment_error": null
    }
  ],
  "query": {
    "name": "Robert Smith",
    "address": null,
    "phone": null,
    "email": null
  }
}
```

Each result includes the base fields (`entity_id`, `entity_name`, `record_count`, `data_sources`) plus enrichment fields:

| Field | Type | Description |
|-------|------|-------------|
| `match_keys.entity_level` | `string \| null` | The overall match key string for the entity |
| `match_keys.per_record` | `list[string]` | Per-record match key strings (empty list for single-record entities) |
| `feature_scores` | `list[object]` | Each entry: `feature` (string), `score` (int 0-100), `label` (string) |
| `resolution_rules` | `list[object]` | Each entry: `data_source` (string), `record_id` (string), `rule` (string) |
| `enrichment_error` | `string \| null` | Non-null if `get_entity_by_entity_id` failed; contains exception type + message |

**Error case response** — When enrichment fails for a specific entity, return the basic result with null enrichment fields and an `enrichment_error` string:

```json
{
  "entity_id": 5,
  "entity_name": "Jane Doe",
  "record_count": 2,
  "data_sources": ["WATCHLIST"],
  "match_keys": null,
  "feature_scores": null,
  "resolution_rules": null,
  "enrichment_error": "SzError: Entity 5 not found in repository"
}
```

**Single-record entity response** — When an entity has only one record (no inter-record resolution occurred), return an empty `per_record` list and empty `resolution_rules` list:

```json
{
  "entity_id": 10,
  "entity_name": "Alice Johnson",
  "record_count": 1,
  "data_sources": ["CUSTOMERS"],
  "match_keys": {
    "entity_level": "+NAME",
    "per_record": []
  },
  "feature_scores": [
    {"feature": "NAME", "score": 95, "label": "CLOSE"}
  ],
  "resolution_rules": [],
  "enrichment_error": null
}
```

**Error response (all endpoints):** HTTP 500 with `{"error": "<description>"}` on SDK failure.

## search_builder.py — Entity Enrichment Specification

The `search_builder.py` module SHALL implement the following enrichment behavior:

**Enrichment flow:**

1. Call `search_by_attributes` with the query parameters to get matching entities
2. For each matched entity (up to a maximum of 10), call `get_entity_by_entity_id` to retrieve full resolution detail
3. Extract match keys, feature scores, and resolution rules from the entity detail response
4. Return enriched results combining basic search info with resolution reasoning

**Enrichment cap:** Enrichment is capped at 10 entities maximum. If a search returns more than 10 matching entities, only the first 10 are enriched with resolution detail. Remaining entities (positions 11+) are returned as basic search results with null values for `match_keys`, `feature_scores`, and `resolution_rules`.

**Extraction functions:**

| Function | Input | Output |
|----------|-------|--------|
| `_extract_match_keys(entity_detail)` | Full entity detail JSON | `{"entity_level": "+NAME+DOB", "per_record": ["+NAME+DOB", "+PHONE"]}` — entity-level match key string + list of per-record match key strings |
| `_extract_feature_scores(search_match_info)` | Search match comparison info | `[{"feature": "NAME", "score": 97, "label": "CLOSE"}, ...]` — feature name, numeric percentage (0-100), classification label |
| `_extract_resolution_rules(entity_detail)` | Full entity detail JSON | `[{"data_source": "CUSTOMERS", "record_id": "1001", "rule": "CNAME_CFF_CEXCL"}, ...]` — per-record data source, record ID, and resolution rule string |

**Graceful degradation:** If `get_entity_by_entity_id` raises any exception for a specific entity, the search builder SHALL return the basic search result for that entity with:

- `match_keys`: null
- `feature_scores`: null
- `resolution_rules`: null
- `enrichment_error`: a non-empty string containing the exception type and message (e.g., `"SzError: Entity 5 not found in repository"`)

One entity's enrichment failure SHALL NOT prevent enrichment of remaining entities.
