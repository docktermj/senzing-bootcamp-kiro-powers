---
inclusion: manual
---

# Hook Registry — Module 8 (Full Prompts)

Full hook prompts for Module 8, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 8 Hooks

**enforce-visualization-offers** (agentStop → askAgent)

Prompt:

````text
If `config/.question_pending` exists, produce no output at all — defer to `ask-bootcamper`.

Read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT in {3, 5, 7, 8}, do nothing — let the conversation end normally.

If the current module IS in {3, 5, 7, 8}, load `visualization-guide.md` and read the Checkpoint Map section. Identify all checkpoints defined for the current module.

Next, read `config/visualization_tracker.json`. For each checkpoint in the current module's checkpoint map, check whether a tracker entry with that `checkpoint_id` exists.

If ALL checkpoints for the current module have tracker entries (regardless of status — offered, accepted, declined, or generated), do nothing — all offers were made.

If ANY checkpoint is missing a tracker entry, offer the missed visualization(s) before the conversation ends. For each missing checkpoint, use the Visualization Offer Protocol's offer template:

Would you like me to create a visualization of {context}?

Present only the types listed for that checkpoint in the checkpoint map, using the standard numbered list format with bold names and one-line descriptions. End with the STOP directive and wait for the bootcamper's response.

After the bootcamper responds (accept or decline), update `config/visualization_tracker.json` accordingly following the Visualization Tracker section in the guide.

Process missed checkpoints one at a time. Do not batch multiple offers into a single message.
````

- id: `enforce-visualization-offers`
- name: `to offer visualizations`
- description: `When the agent stops during a visualization-capable module (3, 5, 7, 8), checks the visualization tracker to verify all required offers were made. Prompts for missed offers.`

**validate-benchmark-results** (fileEdited → askAgent, filePatterns: `tests/performance/*.*`)

Prompt:

````text
A benchmark script in tests/performance/ was just modified. Before recording results, verify: (1) The script runs without errors on a small sample. (2) Output includes required metrics: records/sec for loading benchmarks, or p50/p95/p99 latency for query benchmarks. (3) Results are written to a structured format (JSON or markdown table) that can be compared across runs. If the script fails or produces unparseable output, suggest fixes before the bootcamper records baselines.
````

- id: `validate-benchmark-results`
- name: `to validate benchmark results`
- description: `When benchmark scripts are created or modified in tests/performance/, validates that they produce parseable output with required metrics (records/sec, latency percentiles).`
