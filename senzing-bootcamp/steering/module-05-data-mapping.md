---
inclusion: manual
---

# Module 5: Data Mapping

## Workflow: Data Mapping End-to-End (Module 5)

Use this workflow for each data source that needs mapping (identified in Module 3). Complete the entire mapping process for one data source before moving to the next.

**Important**: While these steps are numbered sequentially, mapping is an iterative and exploratory process. Users can:

- Jump back to earlier steps when they discover new information
- Skip ahead to test ideas before completing all prior steps
- Revisit the profiling or planning stages after seeing quality analysis results
- Refine field mappings multiple times based on testing

Be flexible and supportive of non-linear exploration. The goal is a working transformation program, not strict adherence to the sequence.

**Before starting**: Confirm which data source you're currently mapping. If multiple sources need mapping, keep track of progress:

- Data Source 1: Customer Database → In Progress / Complete
- Data Source 2: Transaction Logs → Pending
- Data Source 3: Vendor Data → Pending

**Prerequisites**: ✅ Module 3 complete (sources evaluated, non-compliant sources identified)

**For the current data source**:

1. **Start the mapping workflow**: Call `mapping_workflow` with `action='start'` and the user's source file path from `data/raw/` or `data/samples/` for this specific data source. The workflow will return a unique session ID for tracking this mapping.

2. **Step 1 — Profile**: Run the profiler script returned by the workflow, or read the data directly. Summarize:
   - Column names and their meanings
   - Data types (string, integer, date, etc.)
   - Sample values from each column
   - Null rates and data completeness
   - Any data quality issues observed

   Advance with `mapping_workflow` using `action='profile_summary'` and your analysis.

3. **Step 2 — Plan**: Identify the entity structure for this data source:
   - **Master entities**: Are these person records, organization records, or both?
   - **Child records**: Are there related records (e.g., multiple addresses per person)?
   - **Relationships**: Does this data describe relationships between entities?
   - **Lookup tables**: Are there reference data or code tables?

   Advance with `mapping_workflow` using `action='entity_plan'` and your plan.

4. **Step 3 — Map**: Map each source field to Senzing features and attributes:
   - Name fields → `NAME_FULL`, `NAME_FIRST`, `NAME_LAST`, `NAME_ORG`
   - Address fields → `ADDR_FULL`, `ADDR_LINE1`, `ADDR_CITY`, `ADDR_STATE`, `ADDR_POSTAL_CODE`, `ADDR_COUNTRY`
   - Contact fields → `PHONE_NUMBER`, `EMAIL_ADDRESS`, `WEBSITE_ADDRESS`
   - Identifier fields → `SSN_NUMBER`, `PASSPORT_NUMBER`, `DRIVERS_LICENSE_NUMBER`, `NATIONAL_ID_NUMBER`
   - Date fields → `DATE_OF_BIRTH`, `REGISTRATION_DATE`
   - Assign confidence scores (0-100) based on data quality

   **CRITICAL**: Never guess attribute names. Use the mapping workflow to ensure correct names.

   Advance with `mapping_workflow` using `action='schema_mappings'` and your field mappings.

5. **Step 4 — Generate Starter Code**: The workflow generates:
   - Sample Senzing JSON output showing the target format
   - Starter mapper code (Python, JavaScript, or other languages)
   - Transformation logic for complex fields

   This provides the foundation for the transformation program.

   Advance with `mapping_workflow` using `action='paths'` and the output file paths.

6. **Step 5 — Build the Transformation Program**: Help the user create a complete, runnable program for this data source. The program should:

   **IMPORTANT**: All generated Python code must be PEP-8 compliant (max 100 chars/line, no trailing whitespace, proper docstrings, 4-space indentation).

   **Input handling**:
   - Read from the original data source format (CSV file, JSON file, database query, API endpoint, etc.)
   - Handle file paths, connection strings, or API credentials
   - Process records in batches for large datasets

   **Transformation logic**:
   - Apply the field mappings from Step 3
   - Handle data type conversions (dates, numbers, booleans)
   - Combine fields when needed (e.g., first_name + last_name → NAME_FULL)
   - Split fields when needed (e.g., full address → ADDR_LINE1, ADDR_CITY, ADDR_STATE)
   - Apply data cleansing (trim whitespace, normalize formats)
   - Set required fields: `DATA_SOURCE` (unique identifier for this source) and `RECORD_ID` (unique within the source)

   **Output handling**:
   - Write Senzing JSON records to output file (one JSON object per line, JSONL format)
   - Or prepare records for direct loading via SDK
   - Include error handling for malformed input records

   **Example program structure** (Python):

   ```python
   import csv
   import json

   def transform_record(source_record):
       """Transform a single source record to Senzing format"""
       senzing_record = {
           "DATA_SOURCE": "CUSTOMER_DB",
           "RECORD_ID": source_record["customer_id"],
       }

       # Map name fields
       if source_record.get("full_name"):
           senzing_record["NAME_FULL"] = source_record["full_name"]

       # Map address fields
       if source_record.get("address"):
           senzing_record["ADDR_FULL"] = source_record["address"]

       # Map contact fields
       if source_record.get("phone"):
           senzing_record["PHONE_NUMBER"] = source_record["phone"]

       return senzing_record

   def main():
       with open("input_data.csv", "r") as infile:
           reader = csv.DictReader(infile)

           with open("output_senzing.jsonl", "w") as outfile:
               for row in reader:
                   try:
                       senzing_record = transform_record(row)
                       outfile.write(json.dumps(senzing_record) + "\n")
                   except Exception as e:
                       print(f"Error processing record {row.get('customer_id')}: {e}")

   if __name__ == "__main__":
       main()
   ```

   **Customize the program** based on:
   - User's preferred programming language (Python, JavaScript, Java, etc.)
   - Data source type (file, database, API)
   - Data volume (single file vs. batch processing)
   - Environment (local script, cloud function, ETL pipeline)

   **Save the program**: Save to `src/transform/transform_[datasource_name].py` (or appropriate extension for the language). All transformation programs must be in the `src/transform/` directory.

7. **Step 6 — Test the Program**: Run the transformation program on sample data from `data/samples/`:
   - Start with a small subset (10-100 records) for initial testing
   - Verify the program runs without errors
   - Check that output files are created in `data/transformed/`
   - Inspect a few output records manually

   Call `lint_record` with sample output records to validate they're syntactically correct Senzing JSON.

8. **Step 7 — Quality Analysis**: Run the program on a larger sample (1000+ records if available). Call `analyze_record` with several mapped records to evaluate:
   - Feature distribution (are all important features populated?)
   - Attribute coverage (what percentage of records have each attribute?)
   - Data quality scores (completeness, consistency, validity)
   - Potential issues (missing critical data, malformed values)

   Advance with `mapping_workflow` using `action='verdict'` and your quality assessment.

9. **Step 8 — Review Results**: Review the transformation program and results with the user:
   - Confirm the program successfully reads the input data
   - Verify the output format is correct Senzing JSON
   - Review data quality metrics
   - Discuss any data quality concerns
   - Confirm the program is ready for production use or needs adjustments

10. **Step 9 — Iterate if needed**: If quality issues were found or the program needs refinement, make adjustments. This is where the iterative nature of mapping becomes clear:

- Go back to Step 3 to adjust field mappings
- Return to Step 2 to reconsider entity structure
- Revisit Step 1 if you need to understand the data better
- Fix bugs in the transformation logic
- Adjust confidence scores
- Handle edge cases better
- Improve data cleansing
- Add validation or error handling

   Retest the program after changes. You may cycle through steps multiple times before achieving the desired quality.

11. **Step 10 — Save and Document**: Ensure the transformation program is properly saved and documented:

    - Program saved in `src/transform/transform_[datasource_name].py` (all source code must be in `src/`)
    - Create `docs/mapping_[datasource_name].md` with:
      - Field mappings
      - Transformation logic
      - Data quality results
      - How to run the program
      - Dependencies and prerequisites
    - Save sample output in `data/transformed/[datasource_name]_sample.jsonl`

11. **Mark data source as complete**: Once the user is satisfied with the transformation program for this data source, mark it as complete and move to the next data source that needs mapping.

12. **Repeat for remaining data sources**: If there are more data sources that need mapping (from Module 3), repeat this entire workflow for each one. Each data source should have its own transformation program in `src/transform/`.

13. **Transition to Module 0**: Once all data sources have been either mapped (with working transformation programs) or confirmed as SGES-compliant, proceed to Module 0 (SDK Setup).

### Important Rules for Data Mapping

- NEVER hand-code Senzing JSON attribute names — common mistakes include using `BUSINESS_NAME_ORG` instead of the correct `NAME_ORG`, or `EMPLOYER_NAME` instead of `NAME_ORG`.
- NEVER guess method signatures — use `generate_scaffold` or `get_sdk_reference` for correct API calls.
- Always validate output with `lint_record` before proceeding to loading.
