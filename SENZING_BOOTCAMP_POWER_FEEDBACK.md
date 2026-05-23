# Senzing Bootcamp Power Feedback

**Started using:** 2026-05-22

---

## Your Feedback

## Improvement: MCP server must be consulted before every response and action

**Date:** 2026-05-22
**Module:** General
**Priority:** High
**Category:** Workflow

### What Happened

The Senzing MCP server MUST be consulted before creating a response and before performing an action. This is an invariant that must be upheld throughout the bootcamp.

### Why It's a Problem

If the agent responds from training data without consulting the MCP server first, it risks providing wrong attribute names, outdated API patterns, incorrect method signatures, or fabricated configuration options. The MCP server contains authoritative, current Senzing information.

### Suggested Fix

Enforce as an invariant: always call the appropriate MCP tool (search_docs, get_sdk_reference, generate_scaffold, etc.) before presenting any Senzing-related information or generating any Senzing-related code.

### Workaround Used

None

### Context When Reported

- **Current Module**: Onboarding (Module 0)
- **What You Were Doing**: Starting the bootcamp, received welcome banner
- **Open Files**: None

---

## Improvement: Suppress write-policy-gate reasoning output from bootcamper view

**Date:** 2026-05-22
**Module:** General
**Priority:** High
**Category:** UX

### What Happened

After the write-policy-gate hook intercepts a write, the agent outputs internal reasoning like "The write passes the fast path: it's inside the working directory, doesn't end with .question_pending, and contains no SQL targeting Senzing databases." This is visible to the bootcamper.

### Why It's a Problem

This internal hook-processing output is not valuable to the bootcamper. It's confusing noise that breaks the flow of the bootcamp experience.

### Suggested Fix

Suppress all write-policy-gate fast-path reasoning from the bootcamper-facing output. When the fast path passes, proceed silently without narrating the check.

### Workaround Used

None

### Context When Reported

- **Current Module**: Onboarding (Module 0)
- **What You Were Doing**: Verbosity selection, comprehension check
- **Open Files**: None

---

## Improvement: Suppress write-policy-gate "Fast path passes" narration

**Date:** 2026-05-22
**Module:** General
**Priority:** High
**Category:** UX

### What Happened

After "Ask Kiro Hook to process your response", the agent outputs: "Fast path passes — file is inside the working directory, not .question_pending, no SQL targeting Senzing databases. Proceeding:" — this is visible to the bootcamper.

### Why It's a Problem

This is internal hook-processing reasoning that provides no value to the bootcamper. It clutters the conversation and breaks flow.

### Suggested Fix

When the write-policy-gate fast path passes and the tool needs to be re-invoked, do so silently without any narration.

### Workaround Used

None

### Context When Reported

- **Current Module**: Onboarding (Module 0)
- **What You Were Doing**: Comprehension check after verbosity selection
- **Open Files**: None

---

## Improvement: Suppress question-format-gate reasoning output

**Date:** 2026-05-22
**Module:** General
**Priority:** High
**Category:** UX

### What Happened

After the "to enforce single-question format on agent output" hook fires, the agent outputs reasoning like: "The 👉 question contains 'or' joining alternatives in prose... this is a compound question. Let me rewrite:" — this is visible to the bootcamper.

### Why It's a Problem

This is internal hook-processing reasoning that provides no value to the bootcamper. It's visual clutter that breaks the flow.

### Suggested Fix

When the question-format-gate detects a compound question and rewrites it, just output the corrected question silently without explaining why it was rewritten.

### Workaround Used

None

### Context When Reported

- **Current Module**: Module 1 (Business Problem)
- **What You Were Doing**: Gap-filling — asking about desired outcome
- **Open Files**: None

---

## Improvement: Never skip the executive summary offer (Step 17)

**Date:** 2026-05-22
**Module:** 1
**Priority:** High
**Category:** Workflow

### What Happened

After the bootcamper confirmed the problem statement (Step 16), the agent skipped Step 17 (stakeholder summary offer) and jumped directly to the module completion transition. The workflow explicitly requires asking the bootcamper whether they want an executive summary, with a 🛑 STOP directive.

### Why It's a Problem

The bootcamper was denied a choice that the workflow guarantees. Skipping steps — even ones that seem optional — violates the bootcamper's agency. Every numbered step with a 👉 question must be asked.

### Suggested Fix

Root cause: the agent combined steps to "save time" instead of following the sequential workflow. Fix: never skip a numbered step. After each 🛑 STOP, end the turn and wait for the bootcamper's response before proceeding to the next step.

### Workaround Used

Bootcamper asked why it was skipped; agent corrected and asked the question.

### Context When Reported

- **Current Module**: Module 1 (Business Problem) — completing
- **What You Were Doing**: Module 1 completion, stakeholder summary offer was skipped
- **Open Files**: None

---

## Improvement: Always ask before skipping steps to "save time"

**Date:** 2026-05-22
**Module:** General
**Priority:** High
**Category:** Workflow

### What Happened

The agent skipped the stakeholder summary offer (Step 17) without asking, rationalizing it as "saving time."

### Why It's a Problem

The bootcamper's agency is paramount. The agent should never unilaterally decide to skip workflow steps on the bootcamper's behalf. Even if a step seems optional, the bootcamper must be the one to decide.

### Suggested Fix

Before doing anything to "save time," ask the bootcamper if they want to save time. Never skip a workflow step without explicit bootcamper consent.

### Workaround Used

Bootcamper called it out; agent corrected.

### Context When Reported

- **Current Module**: Module 1 (Business Problem) — completing
- **What You Were Doing**: Discussing the skipped stakeholder summary offer
- **Open Files**: None

---

## Improvement: Suppress question-format-gate reasoning output (all cases)

**Date:** 2026-05-22
**Module:** General
**Priority:** High
**Category:** UX

### What Happened

After the "to enforce single-question format on agent output" hook fires, the agent outputs its internal reasoning about whether the question is compound or not (e.g., "The 👉 question contains 'or' joining two alternatives... however, this is asking about a single concept..."). This is visible to the bootcamper.

### Why It's a Problem

This internal hook-processing reasoning is not important for the bootcamper. It's visual clutter regardless of whether the question is flagged or not.

### Suggested Fix

When the question-format-gate hook fires: if no rewrite is needed, output only ".". If a rewrite is needed, output only the corrected question. Never output reasoning about the detection process.

### Workaround Used

None

### Context When Reported

- **Current Module**: Module 2 (SDK Setup) — license question
- **What You Were Doing**: Asked about Senzing license file
- **Open Files**: docs/stakeholder_summary_module1.md

---

## Improvement: Suppress all write-policy-gate reasoning including edge-case explanations

**Date**: 2026-05-22
**Module**: General
**Priority**: High
**Category**: UX

### What Happened

After the write-policy-gate hook intercepted a write to engine_config.json, the agent output reasoning explaining why the fast path applies: "The content references G2C.db but does NOT contain SQL patterns... This is a JSON configuration file with a connection string — not SQL code. The fast path applies."

### Why It's a Problem

Any write-policy-gate reasoning output — whether it's the simple "fast path passes" message or a more detailed edge-case explanation — is internal processing noise that the bootcamper does not need to see.

### Suggested Fix

Never output any write-policy-gate reasoning to the bootcamper. When the hook intercepts and the fast path applies, re-invoke the tool silently with zero narration. This includes edge cases where the content references Senzing indicators but doesn't contain SQL patterns.

### Workaround Used

None

### Context When Reported

- **Current Module**: Module 2 (SDK Setup) — engine configuration
- **What You Were Doing**: Creating config/engine_config.json
- **Open Files**: docs/stakeholder_summary_module1.md

---

## Improvement: Entity Graph needs labeled nodes, edges, and click-to-detail

**Date**: 2026-05-22
**Module**: 3
**Priority**: Medium
**Category**: UX

### What Happened

The Entity Graph visualization shows colored circles and lines but doesn't label the nodes with entity names or the edges with match keys. Clicking a node does nothing — there's no pop-up with entity details.

### Why It's a Problem

Without labels, the graph is visually interesting but not informative. The bootcamper can't tell which entity is which or what caused the relationship without hovering over every node. Click-to-detail is expected interactive behavior.

### Suggested Fix

1. Add text labels to nodes showing the entity name (truncated if needed)
2. Add text labels to edges showing the match key (e.g., +NAME+ADDRESS)
3. On node click, show a pop-up/modal with full entity details: name, ID, record count, data sources, and constituent records

### Workaround Used

Hover tooltip shows some info, but it's not as discoverable or usable as labels and click-to-detail.

### Context When Reported

- **Current Module**: Module 3 (System Verification) — Step 9 visualization
- **What You Were Doing**: Exploring the Entity Graph visualization
- **Open Files**: src/system_verification/verify_pipeline.py

---

## Improvement: Entity Graph needs zoom, scroll, and legend

**Date**: 2026-05-22
**Module**: 3
**Priority**: Medium
**Category**: UX

### What Happened

The Entity Graph visualization doesn't support zooming in/out, scrolling/panning, or have a legend explaining what the node colors mean.

### Why It's a Problem

With 88 nodes, the graph is dense. Without zoom/pan the bootcamper can't focus on specific clusters. Without a legend, the color coding (blue=CUSTOMERS, green=REFERENCE, amber=WATCHLIST) isn't self-explanatory.

### Suggested Fix

1. Add D3.js zoom behavior (mouse wheel to zoom, drag to pan)
2. Add a color legend showing data source to color mapping
3. Ensure the graph container supports scrolling if content overflows

### Workaround Used

None

### Context When Reported

- **Current Module**: Module 3 (System Verification) — Step 9 visualization
- **What You Were Doing**: Exploring the Entity Graph visualization
- **Open Files**: src/system_verification/verify_pipeline.py

---

## Improvement: Entity Graph should resize with browser window

**Date**: 2026-05-22
**Module**: 3
**Priority**: Low
**Category**: UX

### What Happened

The Entity Graph has a fixed viewBox size set at render time. Resizing the browser window doesn't re-render or rescale the graph.

### Why It's a Problem

Users may want to expand the browser to see more detail or shrink it for multitasking. The graph should adapt.

### Suggested Fix

Add a window resize listener that updates the SVG viewBox and re-centers the force simulation when the window size changes.

### Workaround Used

Refresh the page after resizing.

### Context When Reported

- **Current Module**: Module 3 (System Verification) — Step 9 visualization
- **What You Were Doing**: Exploring the Entity Graph visualization
- **Open Files**: src/system_verification/verify_pipeline.py

---

## Improvement: Capture the working visualization approach for future reproducibility

**Date**: 2026-05-23
**Module**: 3
**Priority**: High
**Category**: Workflow

### What Happened

The Module 3 Entity Graph visualization took many iterations to get working. The final working approach uses a Python generator script (`write_html.py`) that outputs the complete HTML file, avoiding all string escaping issues that plagued inline file writes.

### Why It's a Problem

Future bootcamp sessions will hit the same issues if the power tries to write HTML with embedded JavaScript using `fs_write` or `str_replace` — quote escaping conflicts between Python strings, JavaScript strings, and HTML attributes are nearly impossible to get right in a single pass.

### Suggested Fix

Update the Kiro Power's Module 3 Phase 2 steering to mandate this approach:

**CRITICAL LESSONS FOR VISUALIZATION GENERATION:**

1. **NEVER write HTML+JS directly via fs_write or str_replace** — quote escaping between Python, JS, and HTML is fragile and produces silent JS syntax errors.

2. **ALWAYS use a Python generator script** (`write_html.py`) that contains the HTML as a triple-quoted string and writes it to `index.html`. This keeps the HTML clean and avoids escaping conflicts.

3. **ALWAYS validate JS syntax with `node --check`** after generating the HTML. Extract the script content and run it through Node.js before presenting to the bootcamper.

4. **NEVER use inline `onclick` attributes with dynamic values** — they require nested quote escaping that breaks. Instead, use `data-*` attributes and attach event listeners via `document.querySelectorAll("[data-attr]").forEach(...)`.

5. **Use only double quotes for JS strings and single quotes for HTML attributes** inside the Python triple-quoted string. This avoids all conflicts.

6. **Key architecture that works:**
   - `write_html.py` — Python script that generates `index.html`
   - `server.py` — stdlib HTTP server with API endpoints
   - `index.html` — generated single-page app with D3.js
   - All D3 code uses `function(){}` syntax (not arrow functions)
   - SVG uses explicit `width`/`height` attributes (not just CSS)
   - Modal uses separate div outside the content area
   - Data attributes for click handlers on dynamic content

7. **Features the visualization must include:**
   - Summary banner with 5 headline stats
   - 4 tabs: Entity Graph, Record Merges, Statistics, Probe
   - Entity Graph: D3 force-directed, zoom/pan, color legend, node labels, edge labels, click-to-detail modal, responsive resize
   - Record detail: click record in modal to fetch full JSON via `/api/record`

### Workaround Used

Wrote `write_html.py` as a generator script, validated with `node --check`, used data attributes instead of inline onclick.

### Context When Reported

- **Current Module**: Module 3 (System Verification) — Step 9 complete
- **What You Were Doing**: Confirmed visualization is working correctly
- **Open Files**: None

---

## Improvement: When bootcamper confirms readiness, proceed immediately

**Date:** 2026-05-23
**Module:** 4
**Priority:** High
**Category:** Workflow

### What Happened

After the bootcamper said "Yes" to move to Module 5, the agent output nothing (just ".") instead of proceeding with the next module.

### Why It's a Problem

The bootcamper confirmed they want to move forward. The agent should act on that confirmation immediately — either start the next module or ask the next workflow question. Outputting nothing leaves the bootcamper waiting with no indication of what to do next.

### Suggested Fix

When the bootcamper confirms a transition question (yes, ready, let's go, etc.), the agent must immediately proceed to the next step in the same turn. Never output just "." after a confirmation.

### Workaround Used

Bootcamper had to provide additional feedback to get the agent moving.

### Context When Reported

- **Current Module**: Module 4 (Data Collection) — transitioning to Module 5
- **What You Were Doing**: Confirmed readiness to proceed to Module 5
- **Open Files**: None

---

## Improvement: Python scripts should go in src/ directory, not project root

**Date**: 2026-05-23
**Module**: 5
**Priority**: Medium
**Category**: Workflow

### What Happened

The mapper scripts (existing_customers_mapper.py, new_applications_mapper.py) were created in the project root instead of the appropriate `src/transform/` directory.

### Why It's a Problem

The project structure defines `src/transform/` for transformation code, `src/load/` for loading code, and `src/query/` for query code. Putting scripts in the root clutters the project and violates the documented structure.

### Suggested Fix

Always place generated scripts in the correct `src/` subdirectory: mappers in `src/transform/`, loaders in `src/load/`, query programs in `src/query/`.

### Workaround Used

Bootcamper pointed it out; scripts will be moved.

### Context When Reported

- **Current Module**: Module 5 (Data Quality & Mapping) — complete
- **What You Were Doing**: Transitioning to Module 6
- **Open Files**: None

---

## Improvement: Utility scripts (analyzer, profiler) should not be in project root

**Date**: 2026-05-23
**Module**: 5
**Priority**: Medium
**Category**: Workflow

### What Happened

The MCP-downloaded utility scripts (sz_json_analyzer.py, sz_schema_generator.py) were placed in the project root instead of `scripts/`.

### Why It's a Problem

Clutters the project root. The project structure defines `scripts/` for utility scripts.

### Suggested Fix

When downloading MCP workflow resources, place utility scripts in `scripts/` and reference docs in `docs/`. Never put them in the project root.

### Workaround Used

Bootcamper pointed it out; scripts moved to `scripts/`.

### Context When Reported

- **Current Module**: Module 5 (Data Quality & Mapping) — complete
- **What You Were Doing**: Transitioning to Module 6
- **Open Files**: None

---

## Improvement: Reference docs should go in docs/, not project root

**Date:** 2026-05-23
**Module:** 5
**Priority:** Medium
**Category:** Workflow

### What Happened

MCP-downloaded reference documents (senzing_entity_specification.md, senzing_mapping_examples.md, identifier_crosswalk.json) were placed in the project root instead of `docs/`.

### Why It's a Problem

Clutters the project root. The project structure defines `docs/` for documentation.

### Suggested Fix

When downloading MCP workflow resources: utility scripts go in `scripts/`, reference docs go in `docs/`, and source code goes in the appropriate `src/` subdirectory. Nothing goes in the project root except config files (.gitignore, .env, README.md, requirements.txt).

### Workaround Used

Bootcamper pointed it out; files moved to `docs/`.

### Context When Reported

- **Current Module**: Module 5 — transitioning to Module 6
- **What You Were Doing**: Cleaning up file placement
- **Open Files**: None

---

## Improvement: All created markdown files must go in docs/, not project root

**Date:** 2026-05-23
**Module:** General
**Priority:** High
**Category:** Workflow

### What Happened

Multiple markdown files (profile_report.md, existing_customers_analysis.md, mapping specs) were created in the project root.

### Why It's a Problem

Violates the project structure. Only README.md belongs in the root.

### Suggested Fix

Generalized rule: ALL created markdown files go in `docs/` (or a subdirectory of `docs/`). The only exception is `README.md` which stays in the project root. Similarly, all `.jsonl` sample/intermediate files go in `data/samples/` or `data/temp/`, not the root.

### Workaround Used

Bootcamper pointed it out; files moved.

### Context When Reported

- **Current Module**: Module 5 — transitioning to Module 6
- **What You Were Doing**: Cleaning up file placement
- **Open Files**: None
