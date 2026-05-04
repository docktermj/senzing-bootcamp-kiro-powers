---
inclusion: manual
---

# Entity Graph Visualization Guide

**Purpose:** Walk the bootcamper through building an interactive D3.js entity graph with data extracted from Senzing in their chosen language.

**Before/After:** You have query results but no visual way to explore them. After: a self-contained HTML graph with entities, relationships, match strengths, and interactive features.

**Prerequisites:** ✅ Module 5/6 complete (data loaded) · ✅ Query programs working (Module 7 step 3)

**Triggers:** Load this file when: (1) after exploratory queries in Module 7 step 3, (2) bootcamper asks to "visualize" / "show entity graph" / "generate a visualization", (3) after documenting findings in Module 7. When done, return to `module-07-query-validation.md`.

## Agent Workflow

1. **Visualization Prompt — choose delivery mode**

   Before generating any visualization output, present this choice:

   👉 "Before I generate this visualization, would you like it as:
   1. **Static HTML file** — a self-contained file you can open directly in your browser, no server needed
   2. **Web service** — a localhost server with live SDK queries, data refresh, and interactive entity details

   Which would you prefer?"

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

   - If the bootcamper chooses **Static HTML file** → continue with step 2 below.
   - If the bootcamper chooses **Web service** → load `visualization-web-service.md` and follow that workflow instead.

2. **Gather requirements**

   👉 "Which data source(s) should the graph include? And which features: force layout, detail panel, cluster highlighting, search/filter, summary statistics?"

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

3. **Generate data extraction code**

   > **Agent instruction:** Read Chosen_Language from `config/bootcamp_preferences.yaml`. Load the appropriate language steering file. Use `get_sdk_reference` for SDK signatures. Use `generate_scaffold` with `workflow='query'`. Use `find_examples` for query patterns.

   Extraction code must: iterate over loaded records via `get_entity_by_record_id` (never guessed entity ID ranges), deduplicate entities, use `get_entity_by_entity_id` with relationship flags for edges, classify match strength per the reference below, warn if >500 entities, log per-entity/per-relationship SDK errors and continue, write JSON matching the Graph Data Model schema. Save to `src/query/extract_graph_data.[ext]`.

   👉 "Run the extraction and confirm the output JSON looks good."

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

4. **Generate HTML visualization**

   > **Agent instruction:** Generate a single self-contained HTML file (D3.js v7, CSS, data inline). Include only selected features per guidance below. Wrap D3.js init in try/catch with user-friendly error display.

   Save to `docs/entity_graph.html`.

   👉 "Open the HTML file — does it look right? Want changes?"

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

5. **Iterate and refine**

   👉 "Want any changes to the graph, features, or extraction?"

   > **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

   Regenerate affected components using the same MCP tools. When done, return to `module-07-query-validation.md`.

## Offline vs Online Decision Matrix

| Scenario | Recommended | Rationale |
| -------- | ----------- | --------- |
| Sharing with stakeholders without SDK | Static HTML | Self-contained, no server needed |
| Interactive exploration with live queries | Web Service | Real-time entity detail and search |
| No persistent network access | Static HTML | No server or database required |
| Iterating on data quality with frequent reloads | Web Service | `/refresh` avoids re-running extraction |

> **Agent guidance — MCP unavailable:** Recommend Static HTML mode. Web Service requires SDK connectivity.

## Reference

For detailed schemas, feature specifications, match strength classification, error handling, and file placement rules, load:

#[[file:senzing-bootcamp/steering/visualization-reference.md]]
