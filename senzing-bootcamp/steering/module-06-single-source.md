---
inclusion: manual
---

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md`.

# Module 6: Load Single Data Source

## Workflow: Quick SDK Test Load — Part B: Create Loading Programs (Module 6)

Use this workflow for each data source that needs to be loaded into Senzing. Create a separate loading program for each data source.

**Before starting**: Identify which data sources are ready to load:

> **Agent instruction:** Before starting any loading, check for anti-patterns:
> `search_docs(query="loading", category="anti_patterns", version="current")`.
> This catches known pitfalls like bulk loading issues, threading problems, and
> PostgreSQL schema DDL requirements.

- Data sources that were mapped in Module 5 (have transformation program output)
- Data sources that were SGES-compliant from Module 4 (can load directly)

**For each data source**:

1. **Identify the input data**: Determine where the Senzing-formatted JSON records are:
   - Output from a transformation program (Module 3)
   - Direct SGES-compliant data files
   - Database query results
   - API responses

2. **Create the loading program**: Help the user build a complete program that loads this specific data source.

   **IMPORTANT**: All generated code must follow the coding standards for the bootcamper's chosen language. For Python: PEP-8 compliant. For other languages, follow their standard conventions.

   > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`
   > to get the current loading pattern. Do not use the inline example below — it uses V3 patterns
   > (G2Engine, init/destroy) that are incorrect for V4. Customize the scaffold with the user's
   > file path, data source name, and progress reporting.

   The program should handle: SDK initialization, record loading loop, error handling per record, progress tracking, and statistics reporting.

   **Save the program**: Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]` using the appropriate file extension for the chosen language).

3. **Use MCP tools for code generation**: Call `generate_scaffold` with workflow `add_records` and the bootcamper's chosen language to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

4. **Test with sample data**: Run the loading program on a small subset first:
   - Start with 10-100 records
   - Verify the program connects to the engine
   - Check that records are being added successfully
   - Observe any errors or warnings

5. **Observe entity resolution in real time**: As records load, Senzing resolves entities automatically:
   - Watch the console output for resolution activity
   - Note how entities are being formed
   - See how new records match or create entities
   - This gives immediate feedback on data quality and matching behavior

6. **Load the full dataset**: Once testing is successful, run the program on the complete data source:
   - Monitor progress and performance
   - Watch for any errors or issues
   - Note loading statistics (time, throughput, error rate)

7. **Save the loading program**: Document and save the program:
   - Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]`)
   - All loading programs must be in the `src/load/` directory
   - Document how to run it (command line, configuration)
   - Note any prerequisites or dependencies
   - Keep it for future reloads or updates

8. **Mark data source as loaded**: Once loading is complete, mark this data source as loaded and move to the next data source.

9. **Repeat for remaining data sources**: If there are more data sources to load, repeat this entire workflow for each one. Each data source should have its own loading program.

10. **Transition to Module 7**: Once all data sources have been loaded, proceed to Module 7 (Multi-Source Orchestration) to orchestrate loading of multiple sources with dependencies. If you only have one data source, skip to Module 8 (Query and Validate Results).
