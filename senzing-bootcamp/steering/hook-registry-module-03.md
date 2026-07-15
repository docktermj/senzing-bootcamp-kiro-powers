---
inclusion: manual
---

# Hook Registry — Module 3 (Full Prompts)

Full hook prompts for Module 3, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 3 Hooks

**enforce-gate-on-stop** (Stop → agent)

Prompt:

````text
If `config/.question_pending` exists, produce no output at all — defer to `ask-bootcamper`.

CHECK — Read `config/bootcamp_progress.json` and evaluate:

1. Is `current_module` equal to 3?
2. Is `current_step` greater than or equal to 9?

If EITHER condition is false: produce no output. Do nothing.

If BOTH are true: Check whether the ⛔ mandatory gate for Step 9 has been satisfied:

CONDITION A — Step 9 checkpoints exist:
- `module_3_verification.checks.web_service.status` equals `"passed"`
- `module_3_verification.checks.web_page.status` equals `"passed"`

If CONDITION A is true: produce no output. The mandatory gate is satisfied.

If CONDITION A is not met: The agent has reached or passed Step 9 without executing it. This is a ⛔ mandatory gate violation. Output exactly:

⛔ MANDATORY GATE VIOLATION DETECTED: Step 9 (Web Service + Visualization) has not been executed but the agent has advanced past it. This step CANNOT be skipped by the agent under any circumstances. Load `module-03-phase2-visualization.md` and execute Step 9 NOW — generate the web service, start the server, verify all 3 API endpoints, and present the URL to the bootcamper. Do not proceed with any other work until Step 9 is complete and checkpoints are written to bootcamp_progress.json.
````

- id: `enforce-gate-on-stop`
- name: `to enforce mandatory gate execution on agent stop`
- trigger: `Stop`
- action: `agent`

**enforce-mandatory-gate** (PreToolUse → agent, matcher: `fs_write|str_replace|fs_append`)

Prompt:

````text
CHECK — Is this write updating `config/bootcamp_progress.json` to advance `current_step` past Step 9 (the ⛔ mandatory gate step for Web Service + Visualization)?

If NO (not writing to `config/bootcamp_progress.json`, or not changing `current_step`, or `current_step` is not being set to a value greater than 9): produce no output at all. Do nothing.

If YES (the write sets `current_step` to 10 or higher, advancing past the ⛔ mandatory gate Step 9): Read the CURRENT contents of `config/bootcamp_progress.json` and check TWO conditions:

CONDITION A — Step 9 checkpoints exist:
- `module_3_verification.checks.web_service.status` equals `"passed"`
- `module_3_verification.checks.web_page.status` equals `"passed"`

If CONDITION A is true: produce no output at all. Do nothing. The mandatory gate has been satisfied.

If CONDITION A is not met: STOP. Do NOT allow this write. Block the operation. Output exactly:

⛔ BLOCKED: Cannot advance past Step 9 — this is a mandatory gate step (Web Service + Visualization). The ⛔ designation means this step must be executed unconditionally. No agent-internal reason (session length, context budget, perceived redundancy) can justify skipping a mandatory gate. Load `module-03-phase2-visualization.md` and execute the full visualization step (generate web service, start server, verify 3 API endpoints, present URL to bootcamper). Only after web_service and web_page checkpoints show 'passed' in bootcamp_progress.json can current_step advance past 9.

Do not proceed with the write operation.
````

- id: `enforce-mandatory-gate`
- name: `to enforce mandatory gate step execution before advancement`
- trigger: `PreToolUse`
- matcher: `fs_write|str_replace|fs_append`
- action: `agent`

**enforce-visualization-offers** (Stop → agent)

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
- trigger: `Stop`
- action: `agent`

**gate-module3-visualization** (PreToolUse → agent, matcher: `fs_write|str_replace|fs_append`)

Prompt:

````text
CHECK — Is this write updating `config/bootcamp_progress.json` to mark Module 3 as complete (adding 3 to modules_completed, or setting module_3_verification.status to 'passed')?

If NO (not a Module 3 completion write, or not writing to bootcamp_progress.json): produce no output at all. Do nothing.

If YES: Read the CURRENT contents of `config/bootcamp_progress.json` and check this condition:

CONDITION A — Step 9 checkpoints exist:
- `module_3_verification.checks.web_service.status` equals `"passed"`
- `module_3_verification.checks.web_page.status` equals `"passed"`

If CONDITION A is true: produce no output at all. Do nothing.

If CONDITION A is not met: STOP. Do NOT allow this write. Output exactly:

⛔ BLOCKED: Module 3 cannot be marked complete — Step 9 (Web Service + Visualization) has not been executed. Load `module-03-phase2-visualization.md` and execute the full visualization step (generate web service, start server, verify 3 API endpoints, present URL to bootcamper). Only after web_service and web_page checkpoints show 'passed' can Module 3 be completed.

Do not proceed with the write operation.
````

- id: `gate-module3-visualization`
- name: `to gate Module 3 completion on visualization step`
- trigger: `PreToolUse`
- matcher: `fs_write|str_replace|fs_append`
- action: `agent`

**verify-demo-results** (PostTaskExec → agent)

Prompt:

````text
Read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT 3, produce no output at all — do not acknowledge, do not explain, do not print anything. If the current module IS 3, verify the system verification results by checking:

1. **Entities were resolved** — Confirm that verification produced more than zero resolved entities from the loaded TruthSet records.
2. **Matches were found** — Confirm that at least two records were resolved to the same entity (i.e., the engine found genuine matches, not just singletons).
3. **TruthSet expectations met** — Compare the actual entity counts against the expected TruthSet results retrieved via MCP. Flag any deviation.

If verification produced only singletons (every record became its own entity with no matches), report this: "Verification ran but produced only singletons — no records were matched together. This indicates an engine or configuration problem, since the Senzing TruthSet contains records designed to match. Check the SDK configuration and database setup before proceeding."

If actual counts diverge from the TruthSet expectations, report the specific deltas: "Expected N resolved entities, got M. This deviation suggests a configuration issue. Review the TruthSet documentation via `search_docs` and check engine configuration before proceeding."

If the results match the TruthSet expectations, confirm success: "System verification passed — entity counts match the Senzing TruthSet expected output. Your setup is working correctly. Ready to proceed to Module 4."
````

- id: `verify-demo-results`
- name: `to verify demo results`
- trigger: `PostTaskExec`
- action: `agent`
