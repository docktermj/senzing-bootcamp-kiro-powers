---
inclusion: manual
---

# Module 6: Load Single Data Source

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md`.

## Workflow: Quick SDK Test Load — Part B: Create Loading Programs (Module 6)

Use this workflow for each data source that needs to be loaded into Senzing. Create a separate loading program for each data source.

**Before/After:** You have Senzing-formatted JSON files but they're just files on disk. After this module, your data is loaded into the Senzing engine and entity resolution has begun — duplicates are being matched automatically.

**Before starting:** Identify which data sources are ready to load:

> **Agent instruction:** Before starting any loading, check for anti-patterns:
> `search_docs(query="loading", category="anti_patterns", version="current")`.
> This catches known pitfalls like bulk loading issues, threading problems, and
> PostgreSQL schema DDL requirements.

- Data sources that were mapped in Module 5 (have transformation program output)
- Data sources that were Senzing Entity Specification (SGES)-compliant from Module 5 (can load directly)

**For each data source:**

1. **Identify the input data:** Determine where the Senzing-formatted JSON records are:
   - Output from a transformation program (Module 5)
   - Direct Entity Specification-compliant data files
   - Database query results
   - API responses

   > **Agent instruction — Data Source Registry:** Update the source's `load_status` to `loading` in `config/data_sources.yaml` and set `updated_at`.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Create the loading program:** Help the user build a complete program that loads this specific data source.

   **IMPORTANT:** All generated code must follow the coding standards for the bootcamper's chosen language (see `docs/policies/CODE_QUALITY_STANDARDS.md`).

   > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`
   > to get the current loading pattern. Do not use the inline example below — it uses V3 patterns
   > (G2Engine, init/destroy) that are incorrect for V4. Customize the scaffold with the user's
   > file path, data source name, and progress reporting.
   >
   > **CRITICAL:** If the generated scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths. No files may be placed outside the working directory.

   The program should handle: SDK initialization, record loading loop, error handling per record, progress tracking, and statistics reporting.

   **Save the program:** Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]` using the appropriate file extension for the chosen language).

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Use MCP tools for code generation:** Call `generate_scaffold` with workflow `add_records` and the bootcamper's chosen language to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

4. **Test with sample data:** Run the loading program on a small subset first:
   - Start with 10-100 records
   - Verify the program connects to the engine
   - Check that records are being added successfully
   - Observe any errors or warnings

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Observe entity resolution in real time:** As records load, Senzing resolves entities automatically:
   - Watch the console output for resolution activity
   - Note how entities are being formed
   - See how new records match or create entities
   - This gives immediate feedback on data quality and matching behavior

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Load the full dataset:** Once testing is successful, run the program on the complete data source:
   - Monitor progress and performance
   - Watch for any errors or issues
   - Note loading statistics (time, throughput, error rate)

   > **Agent instruction — Data Source Registry:** On success, update `load_status` to `loaded` and `record_count` to the actual loaded count in `config/data_sources.yaml`. On failure, set `load_status` to `failed` and add an `issues` entry describing the error. Update `updated_at` in either case.

   **⚠️ SQLite performance note:** On SQLite with single-threaded loading, entity resolution gets progressively slower as the database grows. For the bootcamp learning experience, recommend loading ≤1,000 records initially. This is enough to see meaningful entity resolution results without long waits. If the user has more data, suggest: "Let's start with the first 1,000 records so we can see results quickly. Once we validate the results here, we can load the full dataset — or switch to PostgreSQL for better performance with larger volumes (Module 9 covers this)."

   **Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

7. **Save the loading program:** Document and save the program:
   - Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]`)
   - All loading programs must be in the `src/load/` directory
   - Document how to run it (command line, configuration)
   - Note any prerequisites or dependencies
   - Keep it for future reloads or updates

   **Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

8. **Process redo records:** After loading completes, drain the redo queue. Redo records are deferred re-evaluations that refine the entity resolution graph — without processing them, results are incomplete.

   Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` to get the redo processing pattern. The loading program (or a separate script) should sequentially process all pending redos until the queue is empty.

   **CRITICAL:** If the generated redo scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db`.

   Include a comment in the code explaining that in production, redos are typically handled by an always-running redo processor that wakes up, checks for pending redos, processes them, and sleeps when the queue is empty.

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

9. **Mark data source as loaded:** Once loading and redo processing are complete, mark this data source as loaded and move to the next data source.

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

10. **Repeat for remaining data sources:** If there are more data sources to load, repeat this entire workflow for each one. Each data source should have its own loading program.

    **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

11. **Validate match accuracy:** Now that loading is complete, review the entity resolution results for this data source:
    - Query a sample of known records using `get_entity_by_record_id` to check how they resolved
    - Look for expected matches — are records that should match resolving to the same entity?
    - Look for false positives — are unrelated records being incorrectly merged?
    - Look for false negatives — are records that should match resolving to separate entities?
    - If match accuracy is poor, revisit data quality (Module 5) or mapping before proceeding

    **Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

12. **Run basic UAT for single-source:** Validate that the loaded data meets business expectations:
    - Verify record counts — does the number of loaded records match expectations?
    - Spot-check entity resolution — pick 5-10 known entities and confirm they resolved correctly
    - Document any issues found in `docs/uat_results.md`
    - If critical issues are found, fix and reload before proceeding

    **Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

13. **Document results and offer visualization:** Record the validation findings:
    - Save validation results to `docs/results_validation.md`
    - Include: total records loaded, entities created, match rate, any issues found and their resolution
    - This becomes the baseline for comparison if you load additional sources in Module 7

    **⛔ MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD**

    **🛑 DO NOT SKIP THIS STEP. You MUST offer the results dashboard visualization and WAIT for the user's response before proceeding.**

    👉 **Ask the bootcamper:** "Would you like me to create a results dashboard showing your entity resolution results? It'll have entity counts, match statistics, and sample resolved entities — saved as `docs/results_dashboard.html`."

    **⚠️ WAIT — Do NOT proceed until the bootcamper responds.**

    - If they say **yes**: Generate the HTML dashboard and save to `docs/results_dashboard.html`.
    - If they say **no** or **not now**: Acknowledge and proceed.
    - If they are **unsure**: Briefly explain the value, then wait for their decision.

    **Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

14. **Transition to Module 7:** Once all data sources have been loaded and validation is complete, proceed to Module 7 (Multi-Source Orchestration) to orchestrate loading of multiple sources with dependencies. If you only have one data source, skip to Module 8 (Query and Visualize).

    **Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

## Recovery from Failed Load

If loading fails partway through (crash, error, disk full, etc.):

1. **Check what loaded** — query a few known RECORD_IDs using `get_entity_by_record_id` to see if they exist. The loading program's progress counter tells you approximately how far it got.
2. **Decide — wipe and restart vs. resume:**
   - **Wipe and restart** (simpler): Restore the database from the backup created before loading (use `python scripts/restore_project.py`), fix the issue, and re-run the loading program from the beginning.
   - **Resume from where it stopped** (faster for large loads): Modify the loading program to skip records that are already loaded. The simplest approach is to track the last successfully loaded RECORD_ID and start from the next one.
3. **If the database is corrupted** — restore from backup. This is why the `backup-before-load` hook exists. If no backup exists, delete `database/G2C.db` and re-run Module 2's database configuration step, then reload.
4. **Common causes of mid-load failure:**
   - Disk full → free space or move database to a larger volume
   - Out of memory → reduce batch size or add RAM
   - Invalid records → check the error log, fix the transformation, and reload the bad records
   - Network timeout (remote database) → check connection and retry
