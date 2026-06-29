# Design Document

## Overview

This bugfix corrects the Module 3 Phase 2 Entity Graph rendering empty. The defect is an
edge-key mismatch between the `/api/graph` response schema
(`source_entity_id`/`target_entity_id`) and what D3's `forceLink` requires
(`source`/`target`). The fix is entirely in the bootcamp's **guidance and verification** —
no application/runtime code of the power changes and the `/api/graph` API schema is
untouched. It adds a Critical Lesson (edge-key mapping), a Step 9.4 post-generation smoke
check, and a guidance-validation test, tracing to bugfix requirements 2.1–2.3 while
preserving 3.1–3.4.

## Glossary

- **Phase2_File**: `senzing-bootcamp/steering/module-03-phase2-visualization.md` — the Module 3 Step 9 generation + verification steering.
- **ApiRef_File**: `senzing-bootcamp/steering/module-03-visualization-api-reference.md` — the `/api/graph` (and other endpoint) schema companion.
- **drawGraph**: the generated JavaScript function in `index.html` that builds the D3 force-directed Entity Graph.
- **forceLink**: D3's link force; resolves each edge's `source`/`target` against node ids.
- **Edge schema**: the `/api/graph` edge contract — `source_entity_id`, `target_entity_id`, `match_key`, `relationship_type`.
- **Critical Lesson**: a numbered item under `## CRITICAL LESSONS FOR VISUALIZATION GENERATION` in Phase2_File.
- **Smoke check**: the Step 9.4 post-generation verification that the graph will render before it is presented to the bootcamper.

## Bug Details

**Where:** Module 3 (System Verification), Step 9 — Web Service + Visualization. The
Entity Graph tab is the default view and the bootcamper's first "wow moment."

**Symptom:** The Entity Graph renders empty even though `GET /api/graph` returns a valid
payload (reported: 86 nodes, 68 edges).

**Trigger condition:** A generated graph whose edges, keyed by
`source_entity_id`/`target_entity_id`, are passed to `forceLink` without first being
mapped to `source`/`target`.

**Observable evidence:**

- `/api/graph` returns ≥1 node and ≥1 edge (server side is correct).
- The rendered SVG contains no positioned nodes or links.
- No console error is surfaced — the failure is silent.

**Why it escapes today:** Step 9.4 verifies `/api/graph` returns ≥1 node and ≥1 edge but
never inspects the generated client code or the rendered result, so a correct API response
with broken client-side mapping passes verification.

## Expected Behavior

After the fix, given the same `/api/graph` payload:

- The generated `drawGraph` maps each edge to expose `source`/`target` (from
  `source_entity_id`/`target_entity_id`) before passing edges to `forceLink`, so the
  force simulation resolves endpoints and the Entity Graph renders the returned nodes and
  edges (Req 2.1, 2.2).
- The Step 9.4 post-generation smoke check verifies the rendered graph has visible nodes
  (or, at minimum, that the generated graph code references `source`/`target`), and flags
  any failure before the graph is presented to the bootcamper (Req 2.3).
- The `/api/graph` API schema, the other Critical Lessons, the other endpoints/tabs, and
  zero-edge node-only rendering are unchanged (Req 3.1–3.4).

## Hypothesized Root Cause

D3 `forceLink().links(edges)` resolves each edge against node ids using the edge's
`source` and `target` properties. The `/api/graph` edges expose only `source_entity_id`
and `target_entity_id`, so `source`/`target` are `undefined`. The link force cannot
resolve endpoints, the simulation produces no positioned links/nodes, and D3 surfaces no
user-visible error.

The Phase2_File generation guidance never instructs the agent to map the API edge keys to
`source`/`target` before constructing the force simulation, so the generated `drawGraph`
wires API edges straight into `forceLink`. The root cause is therefore **missing
generation guidance plus a missing verification gate**, not a defect in the API schema —
`source_entity_id`/`target_entity_id` is the correct, documented contract, and the mapping
is a client-side concern.

Confidence: high. The reporter independently confirmed it by mapping the edge keys in
`write_html.py`'s `drawGraph` and regenerating `index.html`, after which the graph
rendered correctly.

## Correctness Properties

### Property 1: Graph renders

Given `/api/graph` returns N≥1 nodes and any edge set, the generated graph maps every edge
to `source`/`target` before `forceLink`, so the simulation produces visible nodes.

**Validates: Requirements 2.1, 2.2**

### Property 2: Empty graph is detected

If a generated graph omits the `source`/`target` mapping, the Step 9.4 smoke check fails
and blocks presentation to the bootcamper.

**Validates: Requirements 2.3**

### Property 3: API schema preserved

The `/api/graph` edge schema continues to expose `source_entity_id`, `target_entity_id`,
`match_key`, `relationship_type` in both Phase2_File and ApiRef_File.

**Validates: Requirements 3.1**

### Property 4: No collateral change

The other six Critical Lessons, the other endpoints/tabs, and zero-edge node-only
rendering are unchanged.

**Validates: Requirements 3.2, 3.3, 3.4**

## Fix Implementation

### Change 1 — New Critical Lesson: edge-key mapping (Req 2.1, 2.2 → P1)

**File:** Phase2_File. **Location:** the `## CRITICAL LESSONS FOR VISUALIZATION
GENERATION` numbered list (append as item 7, same imperative style as the existing six).

Proposed lesson text (final wording applied in tasks):

> 7. **Map graph edge keys for D3 `forceLink`** — `/api/graph` returns edges keyed by
>    `source_entity_id`/`target_entity_id` (the API contract). D3's `forceLink` resolves
>    each edge against node ids via `source`/`target`. In `drawGraph`, map every edge to
>    expose `source`/`target` (set from `source_entity_id`/`target_entity_id`) **before**
>    passing edges to `forceLink().links(...)`. Skipping this map is a **silent failure**:
>    no console error is raised and the Entity Graph renders empty even though `/api/graph`
>    returned nodes and edges. Preserve node `id`/`entity_id` so the mapped `source`/
>    `target` values resolve to nodes.

### Change 2 — Companion note in the Entity Graph component spec (Req 2.2 → P1)

**File:** Phase2_File. **Location:** Step 9.3, the `Entity_Graph` tab section near the
existing "D3.js Code Style Constraints."

Add a short bullet: before constructing the force simulation, edges from `/api/graph` must
be mapped so each exposes `source`/`target`. Keeps the mapping discoverable at the point
the graph is built, reinforcing the Critical Lesson without duplicating its rationale.

### Change 3 — API reference cross-note (Req 3.1 → P3)

**File:** ApiRef_File. **Location:** the `GET /api/graph` section, immediately after the
edge schema description.

Add a one-line note: the edge keys `source_entity_id`/`target_entity_id` are the API
contract and remain unchanged; mapping to D3's `source`/`target` is a **client-side**
concern handled in `drawGraph` (see the Critical Lesson in Phase2_File). This records that
the API schema is not modified and prevents a future "fix" from renaming the API fields.

### Change 4 — Post-generation smoke check in Step 9.4 (Req 2.3 → P2)

**File:** Phase2_File. **Location:** Step 9.4 "Start and Verify Web Service," running
**after** `index.html` is generated and **before** the Guided Tour / presentation `🛑 STOP`
gate.

The bootcamp ships no static graph code (`write_html.py` generates `index.html`), so the
smoke check is expressed against generated output and live endpoints in two layers:

1. **Generated-code check (static, always runs):** Inspect the generated
   `src/system_verification/web_service/index.html` (`drawGraph` region) to confirm it maps
   edges to `source`/`target` (derived from `source_entity_id`/`target_entity_id`) before
   `forceLink`. If absent, fail with a Fix_Instruction to add the mapping (per Critical
   Lesson 7) and regenerate.
2. **Rendered/data check (dynamic):** Reuse the existing `GET /api/graph` ≥1 node / ≥1 edge
   assertion as the precondition and add a node-visibility expectation: when `/api/graph`
   returns N≥1 nodes, the rendered graph must contain visible node elements (SVG
   `circle`/node-group count > 0). Where direct DOM inspection is unavailable in the
   session, the layer-1 generated-code check is the minimum bar required by Req 2.3.

**Failure handling:** report as a Step 9.4 verification failure (consistent with the
existing "On verification failure" block), give the Fix_Instruction (add edge-key mapping,
regenerate `index.html`, re-verify), and do **not** proceed to the Guided Tour until the
graph passes.

Add a row to the Step 9.4 verification table:

| Check | Success Criteria |
|---|---|
| Graph edge-key mapping | Generated `index.html` `drawGraph` maps `source_entity_id`/`target_entity_id` → `source`/`target` before `forceLink`; rendered graph shows visible nodes when `/api/graph` returns ≥1 node |

### Change 5 — Guidance-validation test (locks the fix → P1–P4)

**File:** `senzing-bootcamp/tests/test_module3_entity_graph_edge_key_mapping.py` (new).
**Convention:** pytest + Hypothesis, class-based, mirroring
`test_module3_entity_graph_relationships.py`. Asserts steering content (not runtime
rendering), consistent with how the related-edges fix is locked:

- Critical Lessons section contains an edge-key-mapping lesson mentioning `source`/`target`,
  `source_entity_id`/`target_entity_id`, and `forceLink`.
- Step 9.4 contains a smoke/verification check referencing the graph edge-key mapping
  before the bootcamper presentation gate.
- Regression guard: the edge schema fields remain in both Phase2_File and ApiRef_File
  (P3), and the original six Critical Lessons remain present (P4).

### Affected artifacts

| Artifact | Type | Change |
|---|---|---|
| Phase2_File | Steering (agent guidance) | New Critical Lesson 7; Step 9.3 edge-map note; Step 9.4 smoke check |
| ApiRef_File | Steering (reference) | Cross-note: API schema unchanged, mapping is client-side |
| `tests/test_module3_entity_graph_edge_key_mapping.py` | Test (pytest) | New guidance-validation test |
| Generated `index.html` (`drawGraph`) | User-generated output (not shipped) | Behavior governed by the new lesson; verified by smoke check |

## Error Handling

- **Smoke-check failure (mapping absent or empty render):** treated as a Step 9.4
  verification failure; agent emits a Fix_Instruction and blocks the Guided Tour until the
  graph passes. No silent pass-through (core of Req 2.3 / P2).
- **Zero-edge data sets:** when `/api/graph` returns nodes but zero edges, the
  node-visibility expectation still holds and nodes render without error; the edge-mapping
  code is a no-op on an empty edge list and must not throw (Req 3.4 / P4).
- **MCP-sourced facts:** any Senzing SDK flag/method names referenced while regenerating
  remain confirmed via the Senzing MCP server, never asserted from training data
  (existing constraint, unchanged).

## Testing Strategy

| Requirement / Property | Verification |
|---|---|
| 2.1 / P1 Critical Lesson present | New test asserts the lesson text (source/target, source_entity_id/target_entity_id, forceLink) in the Critical Lessons section |
| 2.2 / P1 Edges expose source/target | Step 9.4 generated-code smoke check; test asserts the guidance requires it |
| 2.3 / P2 Post-generation smoke check | Test asserts Step 9.4 contains the smoke check before the presentation gate; manual run: regenerate a graph and confirm visible nodes |
| 3.1 / P3 API schema unchanged | Regression guard asserts edge schema fields unchanged in both steering files |
| 3.2 / P4 Existing Critical Lessons unchanged | Test asserts the original six lessons remain present |
| 3.3 / P4 Other endpoints/tabs unchanged | Existing `test_visualization_enhancements_properties.py` and `test_module3_entity_graph_relationships.py` continue to pass |
| 3.4 / P4 Zero-edge graphs render | Smoke-check node-visibility expectation; edge-map no-op on empty list |

Full suite run via the CI pipeline (`validate_power.py`, `measure_steering.py --check`,
`validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest) to confirm no
steering token-budget or CommonMark regressions from the added guidance.
