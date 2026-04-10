---
inclusion: manual
---

# Module 6: Load Single Data Source

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md`.

## Workflow: Quick SDK Test Load — Part B: Create Loading Programs (Module 6)

Use this workflow for each data source that needs to be loaded into Senzing. Create a separate loading program for each data source.

**Before/After**: You have Senzing-formatted JSON files but they're just files on disk. After this module, your data is loaded into the Senzing engine and entity resolution has begun — duplicates are being matched automatically.

**Before starting:** Identify which data sources are ready to load:

> **Agent instruction:** Before starting any loading, check for anti-patterns:
> `search_docs(query="loading", category="anti_patterns", version="current")`.
> This catches known pitfalls like bulk loading issues, threading problems, and
> PostgreSQL schema DDL requirements.

- Data sources that were mapped in Module 5 (have transformation program output)
- Data sources that were SGES-compliant from Module 4 (can load directly)

**For each data source:**

1. **Identify the input data:** Determine where the Senzing-formatted JSON records are:
   - Output from a transformation program (Module 3)
   - Direct SGES-compliant data files
   - Database query results
   - API responses

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

3. **Use MCP tools for code generation:** Call `generate_scaffold` with workflow `add_records` and the bootcamper's chosen language to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

4. **Test with sample data:** Run the loading program on a small subset first:
   - Start with 10-100 records
   - Verify the program connects to the engine
   - Check that records are being added successfully
   - Observe any errors or warnings

5. **Observe entity resolution in real time:** As records load, Senzing resolves entities automatically:
   - Watch the console output for resolution activity
   - Note how entities are being formed
   - See how new records match or create entities
   - This gives immediate feedback on data quality and matching behavior

6. **Load the full dataset:** Once testing is successful, run the program on the complete data source:
   - Monitor progress and performance
   - Watch for any errors or issues
   - Note loading statistics (time, throughput, error rate)

7. **Save the loading program:** Document and save the program:
   - Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]`)
   - All loading programs must be in the `src/load/` directory
   - Document how to run it (command line, configuration)
   - Note any prerequisites or dependencies
   - Keep it for future reloads or updates

8. **Process redo records:** After loading completes, drain the redo queue. Redo records are deferred re-evaluations that refine the entity resolution graph — without processing them, results are incomplete.

   Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` to get the redo processing pattern. The loading program (or a separate script) should sequentially process all pending redos until the queue is empty.

   **CRITICAL:** If the generated redo scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db`.

   Include a comment in the code explaining that in production, redos are typically handled by an always-running redo processor that wakes up, checks for pending redos, processes them, and sleeps when the queue is empty.

9. **Mark data source as loaded:** Once loading and redo processing are complete, mark this data source as loaded and move to the next data source.

10. **Repeat for remaining data sources:** If there are more data sources to load, repeat this entire workflow for each one. Each data source should have its own loading program.

11. **Transition to Module 7:** Once all data sources have been loaded, proceed to Module 7 (Multi-Source Orchestration) to orchestrate loading of multiple sources with dependencies. If you only have one data source, skip to Module 8 (Query and Validate Results).

## Recovery from Failed Load

If loading fails partway through (crash, error, disk full, etc.):

1. **Check what loaded** — query a few known RECORD_IDs using `get_entity_by_record_id` to see if they exist. The loading program's progress counter tells you approximately how far it got.
2. **Decide — wipe and restart vs. resume:**
   - **Wipe and restart** (simpler): Restore the database from the backup created before loading (use `python scripts/restore_project.py`), fix the issue, and re-run the loading program from the beginning.
   - **Resume from where it stopped** (faster for large loads): Modify the loading program to skip records that are already loaded. The simplest approach is to track the last successfully loaded RECORD_ID and start from the next one.
3. **If the database is corrupted** — restore from backup. This is why the `backup-before-load` hook exists. If no backup exists, delete `database/G2C.db` and re-run Module 0's database configuration step, then reload.
4. **Common causes of mid-load failure:**
   - Disk full → free space or move database to a larger volume
   - Out of memory → reduce batch size or add RAM
   - Invalid records → check the error log, fix the transformation, and reload the bad records
   - Network timeout (remote database) → check connection and retry
