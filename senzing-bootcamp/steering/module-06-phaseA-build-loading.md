---
inclusion: manual
---
## Before Loading: Conditional Workflow and Pre-Load Checks

> **Agent instruction:** Complete the following three checks before starting Phase A step 1.

### Conditional Workflow: Check Phase 3 Status

> **Agent instruction:** Before starting any loading, read `config/data_sources.yaml` and check the `test_load_status` field for each data source.
>
> - **If `test_load_status: complete`** — Phase 3 was completed in Module 5. Acknowledge the test load results: "You already test-loaded this source in Module 5 Phase 3 and saw [entity_count] entities. Module 6 builds on those results with production-quality loading — error handling, progress tracking, throughput optimization, redo processing, and incremental loading strategies." Skip the basic test loading steps and proceed directly to the production loading workflow below.
> - **If `test_load_status: skipped` or missing** — Phase 3 was not completed. Include a brief test load step: run `mapping_workflow` steps 5–8 (or a quick manual load of 10–100 records) to verify the data loads correctly before proceeding to production concerns. Update `test_load_status` to `complete` after the test load succeeds.
>
> Also check for anti-patterns before starting: `search_docs(query="loading", category="anti_patterns", version="current")`.

> **Agent instruction — Phase 3 Results Integration:** Read `config/data_sources.yaml` and check `test_load_status` and `test_entity_count` for each source. If Phase 3 was completed for multiple sources, reference the test load results when planning load order and dependency management:
>
> - Use `test_entity_count` values to estimate total entity volume and plan resource allocation
> - Use quality assessments from Phase 3 to inform which sources to load first (higher quality → stronger entity baseline)
> - Note any issues discovered during Phase 3 test loading that may affect production orchestration

### Pre-Load Data Freshness Check

> **Agent instruction:** Before starting any loading workflow, run the CORD data freshness check to verify data files haven't changed since download (CORD data is downloaded via `get_sample_data`).
>
> Run: `python senzing-bootcamp/scripts/cord_metadata.py check`
>
> Handle the result based on the output:
>
> - **Fresh** (output contains "✅"): Tell the bootcamper "Your CORD data is up to date — proceeding with loading." and continue to the next section.
> - **Stale** (output contains "⚠️"): Present the warning to the bootcamper exactly as shown in the output, including the three options: (a) re-download fresh data via `get_sample_data`, (b) proceed with current files, (c) check what changed. Wait for the bootcamper to choose before proceeding. This is advisory only — never block loading regardless of their choice.
> - **Skipped** (no metadata found, or output mentions "Skipping"): Proceed silently without mentioning freshness to the bootcamper. This means either the bootcamper is using their own data (not CORD) or metadata was not captured during Module 4.

### Agent Workflow

> **Agent instruction:** Before starting, call `search_docs(query="loading", category="anti_patterns", version="current")`. Key pitfalls: bulk loading issues, threading problems, redo processing, load order dependencies.

---

## Phase A: Build Loading Program

1. **Assess production record volume:**

   👉 How many records do you expect to load in a production system?

   🛑 STOP — do not proceed until the bootcamper responds.

   Here are some example ranges to help you answer:
   - Fewer than 500 — demo/evaluation
   - 500 to 500,000 — small production
   - 500,000 to 10,000,000 — medium production
   - 10,000,000+ — large production

   > **Agent instruction — Volume Classification:**
   >
   > **Bind first (numbered option list answers).** The example ranges above (and the clarifying follow-up below) present the four tiers as a numbered option list. When the question presented that numbered list, FIRST attempt to bind the bootcamper's reply to it with `answer_binding.bind_option(reply, ["demo", "small", "medium", "large"])` from `senzing-bootcamp/scripts/answer_binding.py` (helper functions: `parse_option_token`, `bind_option`, `is_bare_matching_token`). The presented option list is ordered 1→demo, 2→small, 3→medium, 4→large, so a bound 1-based index selects the tier directly via this option→tier map:
   > - 1 → demo
   > - 2 → small
   > - 3 → medium
   > - 4 → large
   >
   > `bind_option` only binds a bare matching token (e.g. `3`, `3.`, `(3)`); replies that carry additional free-text meaning (e.g. `3 million`, `around 3`) return `None` and fall through to the parse path below.
   >
   > - **If `bind_option` returns an index (1–4):** select the mapped tier directly, persist the selection using `volume_utils.persist_volume_selection` with `preferences_path="config/bootcamp_preferences.yaml"`, `progress_path="config/bootcamp_progress.json"`, and `step_number=1`, then advance. Do NOT re-present the Module 6 banner or the volume question — the bootcamper already answered.
   > - **If `bind_option` returns `None`:** the reply is not a bare matching token — fall through to the parse path below.
   >
   > **Fall-through (free-text parsing).** Only when `bind_option` returns `None`:
   > 1. Parse the bootcamper's response using `volume_utils.parse_volume_input`.
   > 2. Classify the parsed value using `volume_utils.classify_tier`.
   > 3. Persist the selection using `volume_utils.persist_volume_selection` with `preferences_path="config/bootcamp_preferences.yaml"`, `progress_path="config/bootcamp_progress.json"`, and `step_number=1`.
   > 4. If `parse_volume_input` returns `None` (unparseable): ask ONE clarifying follow-up question presenting the four tier options as a numbered list:
   >    1. Fewer than 500 (demo/evaluation)
   >    2. 500 to 500,000 (small production)
   >    3. 500,000 to 10,000,000 (medium production)
   >    4. 10,000,000+ (large production)
   >    Then bind the follow-up reply with `answer_binding.bind_option` against this numbered list first (same 1→demo, 2→small, 3→medium, 4→large map); only fall through to `parse_volume_input` again when it returns `None`.
   > 5. If the follow-up response is still unparseable: default to the demo tier, inform the bootcamper that demo/evaluation has been selected as the default, and proceed.

   > **Agent instruction — License framing (default + expansion paths):** After the tier is classified, present licensing as a default the bootcamper already has, never as a hard cap. Build the wording with `volume_utils.get_license_guidance(tier, capacity=<from MCP>, validity=<from MCP>, submit_feedback_available=<from gate>, has_existing_license=<from prefs>)` and present its output.
   > - Frame the built-in evaluation license as the default the bootcamper already has, and present the expansion paths (apply an existing license, request one through the external channel, and — when available — request one in-flow via the Senzing MCP server) before any mention of downsizing. Downsizing (sampling or a smaller subset) is one option among these, not the only path.
   > - Source the record capacity and validity period from a Senzing MCP server tool during this session and present exactly what it returns. If a value is unavailable or the MCP server cannot be reached, omit the figure and say the value is currently unavailable from the MCP server — never substitute a remembered figure.
   > - Gate the in-flow path exactly as Module 1 Step 6d does: check `submit_feedback` availability via `get_capabilities` (wait up to 30s), and omit the in-flow path when it is unavailable, errors, or does not respond. If the bootcamper already has a license (`license` set in `config/bootcamp_preferences.yaml`), route them to the apply-an-existing-license path and omit the in-flow option. Refer to the Senzing MCP server by name only — do not state any URL.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Identify the input data:** Determine where the Senzing-formatted JSON records are for the first data source:
   - Output from a transformation program (Module 5)
   - Direct Entity Specification-compliant data files
   - Database query results or API responses

   > **Agent instruction — Data Source Registry:** Update the source's `load_status` to `loading` in `config/data_sources.yaml` and set `updated_at`.

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Create the production loading program:** Help the user build a complete, production-quality loading program for this data source.

   **IMPORTANT:** All generated code must follow the coding standards for the bootcamper's chosen language (see `docs/policies/CODE_QUALITY_STANDARDS.md`).

   > **Agent instruction — Volume-Aware Scaffold:** Read the `production_volume` key from `config/bootcamp_preferences.yaml`.
   > - If the tier is `medium` or `large`: call `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current', record_count=<raw_value>)` to get threaded loading patterns. Include a comment in the generated code stating the tier name and architecture recommendation (multi-threaded with thread pool for medium, distributed/queue-based for large).
   > - If the tier is `demo` or `small`, or if `production_volume` is missing: call `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` without `record_count`. Include a comment in the generated code stating the tier name (or "no volume selection found" if missing) and that single-threaded loading is recommended.

   > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`
   > to get the current loading pattern. Do not use inline examples — they may use outdated SDK patterns. Customize the scaffold with the user's file path, data source name, and progress reporting.
   >
   > **CRITICAL:** If the generated scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths. No files may be placed outside the working directory.

   The program must include production-quality features:
   - **Robust error handling:** Per-record error logging with record ID, error code, and error message. Failed records are logged to `logs/loading_errors.json` without stopping the load.
   - **Progress tracking with throughput reporting:** Display progress every N records (e.g., every 100 or 1000) showing records loaded, error count, elapsed time, and records/second throughput.
   - **Statistics reporting:** At completion, report total records attempted, loaded, failed, duration, throughput, and error summary.
   - SDK initialization, record loading loop, and proper cleanup.

   **Save the program:** Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]` using the appropriate file extension for the chosen language).

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

4. **Use MCP tools for code generation:** Call `generate_scaffold` with workflow `add_records` and the bootcamper's chosen language to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

---
