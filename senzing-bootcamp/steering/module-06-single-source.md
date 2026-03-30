---
inclusion: manual
---

# Module 6: Load Single Data Source

## Workflow: Quick SDK Test Load — Part B: Create Loading Programs (Module 6)

Use this workflow for each data source that needs to be loaded into Senzing. Create a separate loading program for each data source.

**Before starting**: Identify which data sources are ready to load:

- Data sources that were mapped in Module 5 (have transformation program output)
- Data sources that were SGES-compliant from Module 4 (can load directly)

**For each data source**:

1. **Identify the input data**: Determine where the Senzing-formatted JSON records are:
   - Output from a transformation program (Module 3)
   - Direct SGES-compliant data files
   - Database query results
   - API responses

2. **Create the loading program**: Help the user build a complete program that loads this specific data source. The program should:

   **IMPORTANT**: All generated Python code must be PEP-8 compliant (max 100 chars/line, no trailing whitespace, proper docstrings, 4-space indentation).

   **Connection handling**:
   - Initialize the Senzing engine
   - Connect to the configured database (SQLite or PostgreSQL)
   - Handle connection errors gracefully

   **Record loading**:
   - Read Senzing JSON records from the input source
   - Call the SDK's add record method for each record
   - Use the correct `DATA_SOURCE` identifier for this source
   - Process records in batches for efficiency

   **Error handling**:
   - Catch and log errors for individual records
   - Continue processing even if some records fail
   - Track which records succeeded and which failed

   **Progress tracking**:
   - Report loading progress (records processed, success rate)
   - Show timing information
   - Display entity resolution statistics if available

   **Example loading program** (Python):

   ```python
   import json
   from senzing import G2Engine, G2Exception

   def load_records(input_file, data_source_code):
       """Load Senzing JSON records into the engine"""

       # Initialize engine
       engine = G2Engine()
       config = {
           "PIPELINE": {
               "CONFIGPATH": "/etc/opt/senzing",
               "RESOURCEPATH": "/opt/senzing/g2/resources",
               "SUPPORTPATH": "/opt/senzing/data"
           },
           "SQL": {
               "CONNECTION": "sqlite3://na:na@database/G2C.db"
           }
       }
       engine.init("LoaderApp", json.dumps(config), False)

       # Load records
       success_count = 0
       error_count = 0

       with open(input_file, 'r') as f:
           for line_num, line in enumerate(f, 1):
               try:
                   record = json.loads(line)
                   engine.addRecord(
                       data_source_code,
                       record.get("RECORD_ID"),
                       json.dumps(record)
                   )
                   success_count += 1

                   if success_count % 100 == 0:
                       print(f"Loaded {success_count} records...")

               except G2Exception as e:
                   error_count += 1
                   print(f"Error on line {line_num}: {e}")
               except json.JSONDecodeError as e:
                   error_count += 1
                   print(f"Invalid JSON on line {line_num}: {e}")

       # Cleanup
       engine.destroy()

       print(f"\nLoading complete:")
       print(f"  Success: {success_count}")
       print(f"  Errors: {error_count}")

   if __name__ == "__main__":
       load_records("customer_data_senzing.jsonl", "CUSTOMER_DB")
   ```

   **Customize the program** based on:
   - User's preferred programming language (Python, Java, C#, Rust)
   - Data source location (file, database, stream)
   - Data volume (small dataset vs. millions of records)
   - Environment (local script, cloud function, production pipeline)

3. **Use MCP tools for code generation**: Call `generate_scaffold` with workflow `add_records` to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

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
   - Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.py`)
   - All loading programs must be in the `src/load/` directory
   - Document how to run it (command line, configuration)
   - Note any prerequisites or dependencies
   - Keep it for future reloads or updates

8. **Mark data source as loaded**: Once loading is complete, mark this data source as loaded and move to the next data source.

9. **Repeat for remaining data sources**: If there are more data sources to load, repeat this entire workflow for each one. Each data source should have its own loading program.

10. **Transition to Module 7**: Once all data sources have been loaded, proceed to Module 7 (Multi-Source Orchestration) to orchestrate loading of multiple sources with dependencies. If you only have one data source, skip to Module 8 (Query and Validate Results).
