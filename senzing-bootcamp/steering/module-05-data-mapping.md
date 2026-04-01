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

4. **Step 3 — Map**: Map each source field to Senzing features and attributes.

   > **Agent instruction:** Do not list specific attribute names here. The `mapping_workflow`
   > tool handles field mapping interactively and provides the correct, current attribute names.
   > Use `download_resource(filename="senzing_entity_specification.md")` if the user needs
   > the full attribute reference.

   Map fields for: names, addresses, contact info, identifiers, and dates.
   Assign confidence scores (0-100) based on data quality.

   **CRITICAL**: Never guess attribute names. Use the mapping workflow to ensure correct names.

   > **Agent instruction:** If the user's data contains non-Latin characters (Cyrillic, CJK,
   > Arabic, etc.), use `search_docs(query="globalization", category="globalization", version="current")`
   > for character set and transliteration guidance before mapping.

   Advance with `mapping_workflow` using `action='schema_mappings'` and your field mappings.

5. **Step 4 — Generate Starter Code**: The workflow generates:
   - Sample Senzing JSON output showing the target format
   - Starter mapper code (Python, JavaScript, or other languages)
   - Transformation logic for complex fields

   This provides the foundation for the transformation program.

   Advance with `mapping_workflow` using `action='paths'` and the output file paths.

6. **Step 5 — Build the Transformation Program**: Help the user create a complete, runnable program for this data source.

   **IMPORTANT**: All generated code must follow the coding standards for the bootcamper's chosen language. For Python: PEP-8 compliant (max 100 chars/line, no trailing whitespace, proper docstrings, 4-space indentation). For other languages, follow their standard conventions.

   > **Agent instruction:** The `mapping_workflow` generates starter code in Step 4. Use that
   > as the foundation. Do not use the inline example below — use `generate_scaffold` or the
   > mapping_workflow output for current SDK patterns. Customize based on the user's chosen
   > language, data source type, and volume.

   The program should handle:

   **Input**: Read from the original data source format (CSV, JSON, database, API)
   **Transformation**: Apply field mappings from Step 3, handle type conversions, combine/split fields, apply cleansing, set required `DATA_SOURCE` and `RECORD_ID` fields
   **Output**: Write Senzing JSON records to JSONL file in `data/transformed/`
   **Errors**: Handle malformed input records gracefully

   **Save the program**: Save to `src/transform/transform_[datasource_name].[ext]` where `[ext]` is the appropriate file extension for the chosen language. All transformation programs must be in the `src/transform/` directory.

7. **Step 6 — Test the Program**: Run the transformation program on sample data from `data/samples/`:
   - Start with a small subset (10-100 records) for initial testing
   - Verify the program runs without errors
   - Check that output files are created in `data/transformed/`
   - Inspect a few output records manually

   Call `analyze_record` with sample output records to validate they conform to the Senzing Entity Specification and check data quality.

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

1. **Step 10 — Save and Document**: Ensure the transformation program is properly saved and documented:

    - Program saved in `src/transform/transform_[datasource_name].[ext]` (all source code must be in `src/`)
    - Create `docs/mapping_[datasource_name].md` with:
      - Field mappings
      - Transformation logic
      - Data quality results
      - How to run the program
      - Dependencies and prerequisites
    - Save sample output in `data/transformed/[datasource_name]_sample.jsonl`

2. **Mark data source as complete**: Once the user is satisfied with the transformation program for this data source, mark it as complete and move to the next data source that needs mapping.

3. **Repeat for remaining data sources**: If there are more data sources that need mapping (from Module 3), repeat this entire workflow for each one. Each data source should have its own transformation program in `src/transform/`.

4. **Transition to Module 0**: Once all data sources have been either mapped (with working transformation programs) or confirmed as SGES-compliant, proceed to Module 0 (SDK Setup).

### Important Rules for Data Mapping

- NEVER hand-code Senzing JSON attribute names — use `mapping_workflow` to get the correct names. Use `search_docs` or `download_resource` for the current entity specification if needed.
- NEVER guess method signatures — use `generate_scaffold` or `get_sdk_reference` for correct API calls.
- Always validate output with `analyze_record` before proceeding to loading.
