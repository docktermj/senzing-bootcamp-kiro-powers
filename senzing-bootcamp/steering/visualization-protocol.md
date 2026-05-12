---
inclusion: manual
---

# Visualization Protocol

**Purpose:** Single authoritative definition of the visualization offer flow used across Modules 3, 5, 7, and 8. All module steering files reference this protocol rather than implementing ad-hoc offer language.

**Triggers:** Load this file when a module steering file instructs you to execute a visualization checkpoint.

## Checkpoint Map

```yaml
checkpoints:
  module_3:
    - id: "m3_demo_results"
      trigger: "Demo results displayed successfully"
      context: "these entity resolution demo results"
      types: [Static_HTML_Report, Web_Service_Dashboard]
  module_5:
    - id: "m5_quality_assessment"
      trigger: "Quality assessment scoring complete"
      context: "this data quality assessment"
      types: [Static_HTML_Report]
  module_7:
    - id: "m7_exploratory_queries"
      trigger: "Exploratory queries produce results"
      context: "your resolved entities and relationships"
      types: [Static_HTML_Report, Interactive_D3_Graph, Web_Service_Dashboard]
    - id: "m7_findings_documented"
      trigger: "Findings documented"
      context: "your query results and validation metrics"
      types: [Static_HTML_Report, Interactive_D3_Graph, Web_Service_Dashboard]
  module_8:
    - id: "m8_performance_report"
      trigger: "Performance report generated"
      context: "the performance benchmarks and optimization results"
      types: [Static_HTML_Report, Web_Service_Dashboard]
```

## Offer Template

When you reach a checkpoint, use this exact template. Replace `{context}` with the checkpoint's context string and include only the types listed for that checkpoint.

```text
Would you like me to create a visualization of {context}?

{numbered_list_of_available_types}
```

Each type in the numbered list uses **bold name + one-line description**. The full type descriptions are:

1. **Static HTML file** — a self-contained file you can open directly in your browser, no server needed
2. **Interactive D3 graph** — a force-directed network graph showing entities, relationships, and match strengths
3. **Web service** — a localhost server with live SDK queries, data refresh, and interactive details

Only include the types available for the current checkpoint. Number them sequentially starting at 1.

After presenting the options, end your response with:

> 🛑 STOP — End your response here. Wait for the bootcamper's input.

Do NOT continue past this point. Wait for the bootcamper to choose an option or decline.

## Delivery-Mode Selection

After the bootcamper selects a visualization type, present the delivery-mode choice. This determines how the visualization is served.

**Skip condition:** If the checkpoint's available types list contains ONLY `Static_HTML_Report` (e.g., Module 5), skip this question entirely and default to static delivery. Do not present the choice.

For all other checkpoints, present:

> Now that you've chosen **{chosen_type}**, how would you like it delivered?
>
> 1. **Static HTML** — Self-contained file with data baked in. Open directly in your browser, no server needed. Does not update with new data.
> 2. **Web service + HTML** — A small localhost HTTP service with live SDK queries. Data refreshes on reload. Requires a running local process.

🛑 STOP — End your response here. Wait for the bootcamper's input before proceeding.

## Dispatch Rules

After the bootcamper selects both a visualization type and a delivery mode:

- **Web service delivery mode (any type):** Load `visualization-web-service.md` for scaffolding and lifecycle management. That file is the authoritative source for endpoint specs, framework selection, code generation, and server lifecycle — regardless of the chosen visualization type.
- **Static HTML delivery mode (Static_HTML_Report type):** Generate the visualization inline following the current module's existing generation logic. Do NOT load `visualization-web-service.md`. No additional steering file is needed.
- **Static HTML delivery mode (Interactive_D3_Graph or Web_Service_Dashboard type):** Load `visualization-guide.md` for generation logic only (graph layout, data binding, template structure). Do NOT load `visualization-web-service.md` — no server scaffolding is applied.

If `visualization-guide.md` includes additional sub-choices (such as feature selection), present those after the delivery-mode selection following the guide's own STOP directives.

## Decline Handling

If the bootcamper declines the visualization offer:

- Acknowledge with a single sentence (e.g., "No problem — we'll continue with the module.").
- Do NOT re-offer the same visualization at this checkpoint.
- Do NOT ask follow-up questions about why they declined.
- Continue the module workflow immediately.

## Tracker Instructions

The visualization tracker lives at `config/visualization_tracker.json`. Use it to record and check visualization offer state.

### Schema

```json
{
  "version": "1.1.0",
  "offers": [
    {
      "module": 7,
      "checkpoint_id": "m7_exploratory_queries",
      "timestamp": "2025-07-15T10:30:00Z",
      "status": "offered",
      "chosen_type": null,
      "delivery_mode": null,
      "output_path": null
    }
  ]
}
```

Each entry has these fields:

| Field | Type | Description |
|-------|------|-------------|
| module | integer | Module number (3, 5, 7, or 8) |
| checkpoint_id | string | Checkpoint identifier from the map above |
| timestamp | string (ISO 8601) | When the event occurred |
| status | string | One of: `offered`, `accepted`, `declined`, `generated` |
| chosen_type | string or null | Set on accept (Static_HTML_Report, Interactive_D3_Graph, or Web_Service_Dashboard) |
| delivery_mode | string or null | Set on accept: `"static"` or `"web_service"`. Null when status is `offered`. Defaults to `"static"` for Module 5 (static-only checkpoint). |
| output_path | string or null | Set on generate (relative path to the output file) |

### Valid State Transitions

- `offered` → `accepted`: Set `chosen_type` AND `delivery_mode`
- `offered` → `declined`: Leave `delivery_mode` as `null`
- `accepted` → `generated`: Set `output_path`

No other transitions are valid.

### Read/Write Instructions

1. **Before offering:** Read `config/visualization_tracker.json`. Check if an entry with the current `checkpoint_id` already exists. If yes, skip the offer — do not prompt again.
2. **On offer:** Write a new entry with `status: "offered"`, the current module number, checkpoint_id, and timestamp. Set `chosen_type`, `delivery_mode`, and `output_path` to null.
3. **On accept:** Update the existing entry's `status` to `"accepted"`, set `chosen_type` to the selected type, and set `delivery_mode` to the bootcamper's delivery choice (`"static"` or `"web_service"`). For static-only checkpoints (Module 5), set `delivery_mode` to `"static"` automatically.
4. **On decline:** Update the existing entry's `status` to `"declined"`. Leave `delivery_mode` as `null`.
5. **On generate:** Update the existing entry's `status` to `"generated"` and set `output_path` to the relative path of the created file.

If `config/visualization_tracker.json` does not exist, create it with `{"version": "1.1.0", "offers": []}` before writing the first entry.

## Explicit-Request Override

If the bootcamper explicitly requests a visualization at any point — regardless of prior declines or existing tracker entries — honor the request immediately.

- If a tracker entry exists for the relevant checkpoint with status `"declined"`, update it to `"offered"` and proceed with the offer flow.
- If no tracker entry exists, create one as normal.
- Explicit requests override all decline history. The bootcamper always has the right to request a visualization.

An explicit request is any message where the bootcamper asks for a visualization directly (e.g., "Can you create a visualization?", "Show me a graph", "I'd like a dashboard"). This is distinct from the agent-initiated checkpoint offers.
