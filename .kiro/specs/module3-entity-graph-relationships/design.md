# Bugfix Design Document

## Overview

The Module 3 Entity Graph shows nodes but no edges. The visualization steering tells the agent to
generate a `graph_builder.py` whose `GET /api/graph` response carries an `edges` array, but it
never says **how** to discover relationships. Generated builders therefore read `RELATED_ENTITIES`
off a plain `export_json_entity_report`, which omits relationship data by default, so `edges`
comes back empty.

The fix is steering-only: add an explicit relationship-discovery instruction to the two Module 3
visualization steering files so the generated `graph_builder.py` reliably produces edges. Two
mechanisms are documented (either or both):

1. **`find_network_by_entity_id`** — for multi-record (and related) entities, call
   `find_network_by_entity_id` to retrieve the relationship network and derive edges from it.
2. **Relationship-inclusion export flag** — request the entity report/export with the flag that
   includes all relations (commonly `SZ_ENTITY_INCLUDE_ALL_RELATIONS`) so `RELATED_ENTITIES` is
   populated, then build edges from it.

Because the power's core constraint is "all Senzing facts come from MCP, never training data," the
exact flag/method names and the relationship-inclusion flag are confirmed at authoring time via the
Senzing MCP server (`search_docs` / `sdk_guide`). The steering presents the method names it already
references (`find_network_by_entity_id` is already listed as an allowed SDK call) and instructs the
agent to confirm the export flag via MCP when generating code.

No `src/` artifact is shipped by the power; the fix lives in the steering that drives generation,
so future Module 3 runs produce a connected graph.

## Glossary

- **Phase2_File**: `senzing-bootcamp/steering/module-03-phase2-visualization.md` (executable steps + builder table).
- **ApiRef_File**: `senzing-bootcamp/steering/module-03-visualization-api-reference.md` (`GET /api/graph` schema).
- **Graph_Builder**: the generated `src/system_verification/web_service/graph_builder.py` (node/edge construction).
- **Edge**: a `GET /api/graph` `edges` element: `source_entity_id`, `target_entity_id`, `match_key`, `relationship_type`.
- **Relationship_Discovery**: the documented method for obtaining relationships — `find_network_by_entity_id` and/or the relationship-inclusion export flag.
- **F / F'**: the steering before / after the fix.

## Bug Details

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  RETURN specifiesEdgeSchema(X) AND NOT specifiesRelationshipDiscovery(X)
END FUNCTION
```

### Examples

- **Edge schema, no discovery method (BUG)**: the steering defines the `edges` schema but the
  `graph_builder.py` description and `/api/graph` section say nothing about
  `find_network_by_entity_id` or an export relationship-inclusion flag. *Expected:* F' adds an
  explicit discovery instruction.
- **Node schema / coloring / layout (NOT a bug)**: existing node spec and Entity Graph UX.
  **Preserved.**
- **Other endpoints (NOT a bug)**: `/api/stats`, `/api/merges`, `/api/search`. **Preserved.**

## Hypothesized Root Cause

The steering specified the *output* (`edges` schema) without the *means* (how to discover
relationships). The path of least resistance — reading `RELATED_ENTITIES` from a default export —
returns nothing because the default export does not include relationships. Adding the explicit
discovery instruction (network call and/or relationship-inclusion export flag) closes the gap.

## Expected Behavior

### Preservation Requirements

All inputs where `isBugCondition(X)` is false must be completely unaffected by this fix:

- The node schema (`entity_id`, `entity_name`, `record_count`, `data_sources`, `records`) and the
  Entity Graph UX (coloring, sizing, labels, tooltip, zoom/pan, legend, `calc(100vh - 120px)`
  height) remain specified unchanged.
- The `/api/stats`, `/api/merges`, and `/api/search` endpoint specs remain unchanged.
- The SDK-only / no-direct-SQL / no-fabricated-data constraint remains in force; no MCP or external
  URL is introduced.
- Artifacts still reside in `src/system_verification/web_service/` and the server still uses the
  Python stdlib HTTP server; all unrelated files are untouched.

The only changed behavior: the steering now specifies how `graph_builder.py` discovers
relationships so `edges` is populated. The correct behavior for the buggy input is defined in
Property 1 below.

## Correctness Properties

### Property 1: Bug Condition — Steering specifies a working relationship-discovery method

_For any_ steering where the edge schema is specified but no relationship-discovery method is
(`isBugCondition(X)` true), the fixed steering SHALL specify Relationship_Discovery (a
`find_network_by_entity_id` call for multi-record/related entities AND/OR a relationship-inclusion
export flag), SHALL preserve the `edges` schema fields, and SHALL state the requirement in BOTH
Phase2_File and ApiRef_File.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Preservation — Node schema, other endpoints, and unrelated content unchanged

_For any_ input where the bug condition does not hold, the fix SHALL produce identical content
(`F'(X) = F(X)`): the node schema, Entity Graph UX (coloring, sizing, labels, tooltip, zoom/pan,
legend, `calc(100vh - 120px)` height), the `/api/stats`, `/api/merges`, `/api/search` specs, the
SDK-only/no-SQL constraint, and all unrelated files remain unchanged; no MCP/external URL is added.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### 1. `module-03-phase2-visualization.md`

- In the builder table row for `graph_builder.py` (currently "Graph node/edge construction from
  SDK"), expand to specify relationship discovery: edges are built by calling
  `find_network_by_entity_id` for multi-record/related entities and/or by requesting the entity
  export/report with the relationship-inclusion flag so `RELATED_ENTITIES` is populated; confirm
  the flag name via the Senzing MCP server.
- In the `GET /api/graph` summary bullet, add that edges are discovered via Relationship_Discovery
  (not from a default export), are de-duplicated, and connect only entities present in the node set.
- Keep the `GET /api/graph` success criterion ("at least one node and one edge") and note it must
  hold on TruthSet data.

### 2. `module-03-visualization-api-reference.md`

- In the `GET /api/graph` section, add an "Edge discovery" subsection stating that
  `graph_builder.py` obtains relationships via `find_network_by_entity_id` for multi-record
  entities and/or an entity export requested with the relationship-inclusion flag
  (`SZ_ENTITY_INCLUDE_ALL_RELATIONS`, to be confirmed via the Senzing MCP server), and maps each
  relationship to an `Edge` (`match_key` from the relationship match-key string, `relationship_type`
  from the relationship kind), de-duplicating and restricting to entities in the node set.
- Leave the example JSON and node schema unchanged.

> All Senzing flag/method names referenced are confirmed via the Senzing MCP server when the agent
> generates code; the steering refers to the MCP server by name only — no URL.

## Testing Strategy

### Validation Approach

A new test module `senzing-bootcamp/tests/test_module3_entity_graph_relationships.py`
(stdlib + pytest, per `python-conventions.md`), authored against the unfixed steering so the
fix-checking tests FAIL before the edit and PASS after.

### Fix Checking (Property 1)

- **test_phase2_specifies_relationship_discovery**: read Phase2_File; assert it mentions
  `find_network_by_entity_id` AND/OR a relationship-inclusion export flag in the context of
  building graph edges (not merely in the generic allowed-SDK-calls list). FAILS on unfixed code.
- **test_apiref_specifies_edge_discovery**: read ApiRef_File; assert the `GET /api/graph` section
  describes how edges are discovered (network call and/or relationship-inclusion flag). FAILS on
  unfixed code.
- **test_edge_schema_fields_present**: assert both files still describe `source_entity_id`,
  `target_entity_id`, `match_key`, `relationship_type`.

### Preservation Checking (Property 2)

- **test_node_schema_and_ux_preserved**: assert the node schema, the `calc(100vh - 120px)` height,
  coloring hex values, and tab structure remain in Phase2_File.
- **test_other_endpoints_unchanged**: assert `/api/stats`, `/api/merges`, `/api/search` specs are
  unchanged (string presence of their required fields).
- **test_no_urls_added**: assert neither edited file contains an MCP URL or an external URL.

### Integration Tests

- Run `python senzing-bootcamp/scripts/validate_commonmark.py` — both edited files stay valid.
- Run `python senzing-bootcamp/scripts/measure_steering.py --check`; if either file exceeds its
  budget after the edit, update its `steering-index.yaml` entry and re-run.
- (Manual, where a live SDK + TruthSet is available) generate the visualization and confirm
  `GET /api/graph` returns a non-empty `edges` array and the Entity Graph renders connecting lines.
