# Implementation Plan

## Overview

Add an explicit relationship-discovery instruction to the two Module 3 visualization steering
files so generated `graph_builder.py` produces non-empty `edges`: discover relationships via
`find_network_by_entity_id` for multi-record/related entities and/or request the entity export
with the relationship-inclusion flag (`SZ_ENTITY_INCLUDE_ALL_RELATIONS`, confirmed via the Senzing
MCP server). Steering-only change plus a content test.

## Tasks

- [x] 1. Confirm Senzing flag/method names via the Senzing MCP server
  - Use `search_docs` / `sdk_guide` to confirm the relationship-inclusion export flag name (e.g.
    `SZ_ENTITY_INCLUDE_ALL_RELATIONS`) and that `find_network_by_entity_id` returns relationship
    data with match keys
  - Record the confirmed names to use in the steering edits (do not assert from training data)
  - _Requirements: 2.2_

- [x] 2. Write fix-checking and preservation tests (before the edit)
  - Create `senzing-bootcamp/tests/test_module3_entity_graph_relationships.py` (stdlib + pytest,
    `from __future__ import annotations`, class-based, per `python-conventions.md`)
  - **test_phase2_specifies_relationship_discovery** (Property 1): assert Phase2_File mentions
    `find_network_by_entity_id` and/or a relationship-inclusion export flag in the edge-building
    context — authored to FAIL on unfixed content
  - **test_apiref_specifies_edge_discovery** (Property 1): assert the `GET /api/graph` section of
    ApiRef_File describes edge discovery — authored to FAIL on unfixed content
  - **test_edge_schema_fields_present** (Property 1): assert both files still describe
    `source_entity_id`, `target_entity_id`, `match_key`, `relationship_type`
  - **test_node_schema_and_ux_preserved** (Property 2): assert node schema, `calc(100vh - 120px)`,
    color hex values, and tab structure remain — PASS on unfixed content
  - **test_other_endpoints_unchanged** (Property 2): assert `/api/stats`, `/api/merges`,
    `/api/search` required fields remain — PASS on unfixed content
  - **test_no_urls_added** (Property 2): assert neither file contains an MCP URL or external URL
  - Run: confirm the discovery tests FAIL and preservation tests PASS
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_

- [x] 3. Add edge-discovery instruction to `module-03-phase2-visualization.md`
  - Expand the `graph_builder.py` builder-table row to specify edges are built via
    `find_network_by_entity_id` for multi-record/related entities and/or an export requested with
    the relationship-inclusion flag (confirmed via MCP)
  - Update the `GET /api/graph` summary bullet to state edges are discovered via this method (not a
    default export), de-duplicated, and limited to entities in the node set; keep the
    "at least one node and one edge" success criterion and note it must hold on TruthSet data
  - Do not change node schema, Entity Graph UX, container height, or other endpoints; no URLs
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.3_

- [x] 4. Add "Edge discovery" subsection to `module-03-visualization-api-reference.md`
  - In the `GET /api/graph` section, document that `graph_builder.py` obtains relationships via
    `find_network_by_entity_id` and/or the relationship-inclusion export flag, mapping each
    relationship to an `Edge` (`match_key` from the relationship match-key string,
    `relationship_type` from the relationship kind), de-duplicated and restricted to node-set
    entities
  - Leave the example JSON, node schema, and other endpoint sections unchanged; no URLs
  - _Requirements: 2.2, 2.3, 2.4, 3.2, 3.3_

- [x] 5. Verify tests, CommonMark, and token budgets
  - Run `pytest senzing-bootcamp/tests/test_module3_entity_graph_relationships.py` — all PASS
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` — passes
  - Run `python senzing-bootcamp/scripts/measure_steering.py --check`; if either edited file
    exceeds budget, update its `steering-index.yaml` entry and re-run
  - Confirm no MCP server URL or external URL was introduced
  - _Requirements: 3.3, 3.4, 3.5_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3", "4"] },
    { "id": 2, "tasks": ["5"] }
  ]
}
```

- **Wave 0** — `[1, 2]`: confirm Senzing flag/method names via MCP and author the fix-checking +
  preservation tests (discovery tests FAIL, preservation PASSES on unfixed content).
- **Wave 1** — `[3, 4]`: edit the two steering files (Phase2_File and ApiRef_File) — distinct files,
  independent.
- **Wave 2** — `[5]`: verify tests, CommonMark, and steering token budgets.

## Notes

- Steering-only fix: it changes the instructions that drive `graph_builder.py` generation; the
  power does not ship `src/` artifacts.
- Senzing flag/method names (e.g. `SZ_ENTITY_INCLUDE_ALL_RELATIONS`, `find_network_by_entity_id`)
  are confirmed via the Senzing MCP server, never asserted from training data.
- Refer to the Senzing MCP server by name only — no MCP URL, no external URL (security gate).
- A live SDK + TruthSet run to confirm non-empty `edges` is a manual check where available.
