---
inclusion: manual
---
## Phase B: Load First Source

4. **Test with sample data (if Phase 3 was skipped):** If the bootcamper did not complete Phase 3 in Module 5, run the loading program on a small subset first:
   - Start with 10–100 records
   - Verify the program connects to the engine
   - Check that records are being added successfully
   - Observe any errors or warnings

   If Phase 3 was completed, skip this step — the test load already verified basic loading works. Proceed directly to production loading.

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Observe entity resolution in real time:** As records load, Senzing resolves entities automatically:
   - Watch the console output for resolution activity
   - Note how entities are being formed
   - See how new records match or create entities
   - This gives immediate feedback on data quality and matching behavior

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Load the full dataset:** Run the program on the complete data source with production-quality monitoring:
   - Monitor progress and throughput performance
   - Watch for error rate trends (increasing errors may indicate data issues)
   - Note loading statistics (time, throughput, error rate)
   - If errors exceed 5%, pause and investigate before continuing

   > **Agent instruction — License capacity before loading:** Before warning that the load will stop at the built-in evaluation limit (a SENZ9000 error at the licensed cap), **read `license_record_limit` from `config/bootcamp_progress.json`** (Module 2 Step 5e persists it via `detect_license_limit.py` after a custom license is configured) and drive the decision from that effective limit, never a remembered or hardcoded figure:
   >
   > - **`0` (no cap), or ≥ the dataset size** — the active license permits the full load: **omit** the SENZ9000/evaluation-capacity warning and proceed.
   > - **Positive and below the dataset size** — the dataset genuinely exceeds the cap: present the Module 1 licensing paths (apply an existing license, the external request, or the in-flow MCP request when available) as choices, not a wall; do not force downsizing.
   > - **Absent or null** (no custom license detected) — keep the existing behavior: warn that the evaluation license halts the load at its cap with a SENZ9000 error, confirming the current capacity figure and SENZ9000 behavior from the Senzing MCP server at request time. If no figure is returned, say it is currently unavailable rather than restating a remembered one.

   > **Agent instruction — Data Source Registry:** On success, update `load_status` to `loaded` and `record_count` to the actual loaded count in `config/data_sources.yaml`. On failure, set `load_status` to `failed` and add an `issues` entry describing the error. Update `updated_at` in either case.

   **⚠️ SQLite performance note:** On SQLite with single-threaded loading, entity resolution gets progressively slower as the database grows. For the bootcamp learning experience, recommend loading ≤1,000 records initially. This is enough to see meaningful entity resolution results without long waits. If the user has more data, suggest: "Let's start with the first 1,000 records so we can see results quickly. Once we validate the results here, we can load the full dataset — or switch to PostgreSQL for better performance with larger volumes (Module 8 covers this)."

   **Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

7. **Save and document the loading program:** Document and save the program:
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

   Tell the bootcamper: "Processing the redo queue now. This refines entity resolution — without it, some matches would be incomplete."

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

9. **Incremental loading strategy:** Discuss incremental loading as a production concern distinct from the initial bulk load:
   - **Full reload** (what we just did): Load all records every time. Simple but slow for large datasets.
   - **Incremental load** (production pattern): Track which records are new or changed since the last load. Only load deltas. Requires a change detection mechanism (timestamps, sequence numbers, change data capture).
   - **Upsert pattern**: Use `add_record` with the same `RECORD_ID` to update existing records. Senzing re-evaluates entity resolution automatically.
   - Help the bootcamper understand when each strategy applies and document the choice in `docs/loading_strategy.md`.

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

10. **Mark first data source as loaded:** Once loading and redo processing are complete, mark this data source as loaded.

    **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

---
