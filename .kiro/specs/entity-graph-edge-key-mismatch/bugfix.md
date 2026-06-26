# Bugfix Requirements Document

## Introduction

In Module 3 (System Verification, Step 9 — Web Service + Visualization), the bootcamp
generates an interactive D3.js force-directed Entity Graph as the bootcamper's first
"wow moment." The generated graph renders empty even though the `/api/graph` endpoint
returns data (reported: 86 nodes, 68 edges).

The root cause is an edge-key mismatch. The documented `/api/graph` schema gives each
edge `source_entity_id` and `target_entity_id`, but D3's `forceLink` force requires each
edge to expose `source` and `target`. The Module 3 visualization-generation guidance does
not instruct the agent to map `source_entity_id`/`target_entity_id` to `source`/`target`
before passing edges to `forceLink`, so the generated graph code wires the API edges
straight into `forceLink`. The link force then fails silently (no console error is
surfaced), and the force-directed graph never renders. Because there is no
post-generation smoke check, the empty-graph regression is not caught before the graph
is presented to the bootcamper.

This bugfix targets the bootcamp's Module 3 visualization-generation guidance and its
post-generation verification step. The fix adds a Critical Lesson covering the edge-key
mapping and a smoke check that catches an empty graph (or missing `source`/`target`
mapping) before presentation. The documented `/api/graph` API schema itself is correct
and remains unchanged — the mapping is a client-side concern in the generated graph code.

## Bug Analysis

### Current Behavior (Defect)

What currently happens when the bug is triggered:

1.1 WHEN the Module 3 Step 9 visualization-generation guidance is followed to build the D3 force-directed Entity Graph THEN the system provides no instruction to map the API edge keys `source_entity_id`/`target_entity_id` to the `source`/`target` properties that D3 `forceLink` requires

1.2 WHEN the generated graph code passes edges keyed by `source_entity_id`/`target_entity_id` directly to D3 `forceLink` THEN the link force fails silently (no console error is surfaced) and the Entity Graph tab renders empty even though `/api/graph` returns a valid set of nodes and edges

1.3 WHEN the Step 9.4 web-service verification runs after the visualization is generated THEN the system performs no post-generation smoke check that the rendered graph has visible nodes (or that the generated graph code references `source`/`target`), so the empty-graph regression is not detected before the graph is presented to the bootcamper

### Expected Behavior (Correct)

What should happen instead:

2.1 WHEN the Module 3 Step 9 visualization-generation guidance is followed to build the D3 force-directed Entity Graph THEN the system SHALL include a Critical Lesson instructing the agent to map the API edge keys `source_entity_id`/`target_entity_id` to `source`/`target` before passing edges to D3 `forceLink`

2.2 WHEN the generated graph code supplies edges to D3 `forceLink` THEN each edge SHALL expose `source`/`target` properties so the link force resolves and the Entity Graph tab renders the nodes and edges returned by `/api/graph`

2.3 WHEN the Step 9.4 web-service verification runs after the visualization is generated THEN the system SHALL perform a post-generation smoke check that verifies the rendered graph has visible nodes (or, at minimum, that the generated graph code references `source`/`target`), and SHALL flag the failure before the graph is presented to the bootcamper

### Unchanged Behavior (Regression Prevention)

Existing behavior that must be preserved:

3.1 WHEN the `/api/graph` endpoint returns its response THEN the system SHALL CONTINUE TO use the documented API schema in which each edge carries `source_entity_id`, `target_entity_id`, `match_key`, and `relationship_type` (the mapping is client-side; the API schema is unchanged)

3.2 WHEN the visualization-generation guidance is applied THEN the system SHALL CONTINUE TO produce the existing Critical Lessons unchanged (Python generator script, JavaScript syntax validation, no inline `onclick` with dynamic values, quote discipline, `function(){}` callbacks, explicit SVG dimensions)

3.3 WHEN the other Step 9 endpoints and tabs are generated and verified (`/api/stats`, `/api/merges`, `/api/search`, and the Merge Statistics / Record Merges / Probe Panel views) THEN the system SHALL CONTINUE TO generate and verify them as before

3.4 WHEN `/api/graph` returns nodes but zero edges for a data set with no discovered relationships THEN the graph SHALL CONTINUE TO render its nodes without error
