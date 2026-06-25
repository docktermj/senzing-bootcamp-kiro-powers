# Bugfix Requirements Document

## Introduction

In the Module 3 Phase 2 visualization, the Entity Graph tab renders entity nodes but **zero
relationship edges** — the graph appears as disconnected dots rather than a connected network.
A bootcamper observed 88 entity nodes and 0 edges on the TruthSet data.

The Module 3 visualization steering (`senzing-bootcamp/steering/module-03-phase2-visualization.md`
plus its API reference companion `module-03-visualization-api-reference.md`) instructs the agent
to generate `graph_builder.py`, whose `GET /api/graph` response must include `edges` with
`source_entity_id`, `target_entity_id`, `match_key`, and `relationship_type`. The steering lists
`find_network_by_entity_id` among the allowed SDK calls but does **not** specify how
`graph_builder.py` actually discovers relationships. As a result, generated implementations tend
to read the `RELATED_ENTITIES` array from a plain `export_json_entity_report`, which does not
surface the TruthSet's disclosed/discovered relationships by default — so the `edges` array comes
back empty even though related entities exist.

This bugfix updates the steering so the generated `graph_builder.py` populates edges reliably:
relationships are discovered via `find_network_by_entity_id` for multi-record entities, and/or the
entity export is requested with the relationship-inclusion flag (`SZ_ENTITY_INCLUDE_ALL_RELATIONS`)
so `RELATED_ENTITIES` is populated. The Senzing-specific flag/method names are confirmed against
the Senzing MCP server rather than asserted from training data.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the Entity Graph tab loads and fetches `GET /api/graph`, THE `edges` array is empty even
though the TruthSet contains related entities, so the graph renders nodes with no connecting lines.

1.2 WHEN `graph_builder.py` is generated from the current steering, THE steering provides no
explicit relationship-discovery instruction, so implementations default to reading
`RELATED_ENTITIES` from a plain `export_json_entity_report` that does not include relationship
data by default.

1.3 WHEN the `GET /api/graph` success criterion ("at least one node and one edge") is checked
against TruthSet data, THE criterion can fail or be vacuously satisfied because no edges are
produced.

### Expected Behavior (Correct)

2.1 WHEN the Entity Graph tab loads with TruthSet data that contains related entities, THE
`GET /api/graph` `edges` array SHALL contain at least one edge, each with `source_entity_id`,
`target_entity_id`, `match_key`, and `relationship_type`.

2.2 WHEN the steering specifies how `graph_builder.py` discovers relationships, THE steering SHALL
direct the generated builder to obtain relationships by calling `find_network_by_entity_id` for
multi-record (and/or related) entities, OR by requesting the entity export/report with the
relationship-inclusion flag so `RELATED_ENTITIES` is populated (the relationship-inclusion flag
name SHALL be confirmed via the Senzing MCP server, e.g. `search_docs`/`sdk_guide`, not asserted
from training data).

2.3 WHEN an edge is built, THE steering SHALL specify that `match_key` is taken from the Senzing
relationship's match-key string and `relationship_type` reflects the relationship kind (e.g.,
possible match / disclosed / discovered), and that edges are de-duplicated and only created
between entities that both appear in the graph's node set.

2.4 WHEN the agent generates the visualization, THE relationship-discovery requirement SHALL be
present in BOTH `module-03-phase2-visualization.md` (the executable steps / builder description)
AND `module-03-visualization-api-reference.md` (the `GET /api/graph` schema section).

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the Entity Graph renders nodes, THE existing node schema (`entity_id`, `entity_name`,
`record_count`, `data_sources`, `records`), node coloring, sizing, labels, tooltip, zoom/pan,
legend, and the `calc(100vh - 120px)` container height SHALL CONTINUE TO be specified unchanged.

3.2 WHEN the other endpoints (`/api/stats`, `/api/merges`, `/api/search`) are generated, THE
endpoints SHALL CONTINUE TO follow their existing schemas and builder specifications unchanged.

3.3 WHEN all visualization data is derived, THE data SHALL CONTINUE TO come only from Senzing SDK
calls (no direct SQL, no fabricated data), and no MCP server URL or external URL SHALL be
introduced into any steering file.

3.4 WHEN the steering is generated/verified, THE artifacts SHALL CONTINUE TO reside in
`src/system_verification/web_service/`, the server SHALL CONTINUE TO use the Python stdlib HTTP
server, and CommonMark validity and steering token budgets SHALL CONTINUE TO pass.

3.5 WHEN any steering file, doc, hook, script, or config unrelated to the `GET /api/graph`
edge-discovery instruction is considered, THE content SHALL CONTINUE TO be untouched.

---

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type GraphSteering (phase2_body, api_ref_body)
  OUTPUT: boolean

  // Returns true when the graph steering specifies edges in the schema but
  // gives no explicit relationship-discovery method, so edges come back empty
  RETURN specifiesEdgeSchema(X)
         AND NOT specifiesRelationshipDiscovery(X)   // no find_network_by_entity_id
                                                     // and no relationship-inclusion export flag
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — steering specifies a working relationship-discovery method
FOR ALL X WHERE isBugCondition(X) DO
  X' ← applyFix(X)
  ASSERT specifiesRelationshipDiscovery(X')   // find_network_by_entity_id OR
                                              // SZ_ENTITY_INCLUDE_ALL_RELATIONS export flag
  ASSERT edgeSchemaPreserved(X')              // source/target/match_key/relationship_type
  ASSERT presentInBothFiles(X')               // phase2 + api-reference
END FOR
```

### Preservation Property

```pascal
// Property: Preservation — node schema, other endpoints, and unrelated content unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT applyFix(X) = X
END FOR
```

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK-2.md` — "Entity Graph Missing Relationships"
- Module: 3 (System Verification — Visualization) | Priority: Medium | Category: Visualization Bug
