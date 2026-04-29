---
inclusion: manual
---
## Phase A: Build Loading Program

1. **Identify the input data:** Determine where the Senzing-formatted JSON records are for the first data source:
   - Output from a transformation program (Module 5)
   - Direct Entity Specification-compliant data files
   - Database query results or API responses

   > **Agent instruction — Data Source Registry:** Update the source's `load_status` to `loading` in `config/data_sources.yaml` and set `updated_at`.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Create the production loading program:** Help the user build a complete, production-quality loading program for this data source.

   **IMPORTANT:** All generated code must follow the coding standards for the bootcamper's chosen language (see `docs/policies/CODE_QUALITY_STANDARDS.md`).

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

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Use MCP tools for code generation:** Call `generate_scaffold` with workflow `add_records` and the bootcamper's chosen language to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

---

