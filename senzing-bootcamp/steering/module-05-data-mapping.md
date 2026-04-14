---
inclusion: manual
---

# Module 5: Data Mapping

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_5_DATA_MAPPING.md`.

## Workflow: Data Mapping End-to-End (Module 5)

Use this workflow for each data source that needs mapping (identified in Module 4). Complete the entire mapping process for one data source before moving to the next.

**Before/After:** You have raw data that Senzing can't read yet. After this module, you'll have transformation programs that convert your data into Senzing JSON format, validated and ready to load.

**Important:** While these steps are numbered sequentially, mapping is an iterative and exploratory process. Users can:

- Jump back to earlier steps when they discover new information
- Skip ahead to test ideas before completing all prior steps
- Revisit the profiling or planning stages after seeing quality analysis results
- Refine field mappings multiple times based on testing

Be flexible and supportive of non-linear exploration. The goal is a working transformation program, not strict adherence to the sequence.

**Before starting:** Confirm which data source you're currently mapping. If multiple sources need mapping, keep track of progress:

- Data Source 1: Customer Database → In Progress / Complete
- Data Source 2: Transaction Logs → Pending
- Data Source 3: Vendor Data → Pending

**Prerequisites:** ✅ Module 3 complete (sources evaluated, non-compliant sources identified)

**For the current data source:**

1. **Start the mapping workflow:** Call `mapping_workflow` with `action='start'` and the user's source file path from `data/raw/` or `data/samples/` for this specific data source. The workflow will return a unique session ID for tracking this mapping.

   **IMPORTANT:** If the mapping workflow returns any file paths pointing to `/tmp/` or other system temporary directories, override them with project-local paths. Downloaded resources go in `data/temp/` or `data/raw/`, profiler output goes in `data/temp/`, and generated scripts go in `src/transform/`. See `docs/policies/FILE_STORAGE_POLICY.md`.

   **Tell the user:** "I'm starting the mapping workflow for [data source name]. Mapping is the process of translating your data fields into Senzing's format so the entity resolution engine can understand them. I'll walk you through each step and explain what I find along the way."

2. **Step 1 — Profile:** Run the profiler script returned by the workflow, or read the data directly. Summarize:
   - Column names and their meanings
   - Data types (string, integer, date, etc.)
   - Sample values from each column
   - Null rates and data completeness
   - Any data quality issues observed

   Advance with `mapping_workflow` using `action='profile_summary'` and your analysis.

   **Tell the user what was discovered:** Present the profiling results in a clear table and explain what they mean for mapping. For example:

   ```text
   Here's what I found in your data:

   | Column | Type | Sample Values | Completeness | Notes |
   |--------|------|---------------|-------------|-------|
   | full_name | string | "John Smith", "Jane Doe" | 98% | Good — maps directly to a Senzing name attribute |
   | address | string | "123 Main St, NY 10001" | 87% | Full address string — Senzing can parse this |
   | phone | string | "(555) 123-4567", "555.123.4567" | 72% | Mixed formats, but Senzing handles this |
   | internal_id | integer | 1001, 1002 | 100% | Will use as RECORD_ID (required by Senzing) |
   | status | string | "active", "inactive" | 100% | Not an entity feature — won't map to Senzing |

   Key takeaway: Your data has strong name coverage (98%) which is great for matching. Address coverage at 87% is solid. Phone at 72% means some records will rely more on name+address for matching. The "status" column doesn't describe the entity itself, so we'll skip it in the mapping.
   ```

3. **Step 2 — Plan:** Identify the entity structure for this data source:
   - **Master entities:** Are these person records, organization records, or both?
   - **Child records:** Are there related records (e.g., multiple addresses per person)?
   - **Relationships:** Does this data describe relationships between entities?
   - **Lookup tables:** Are there reference data or code tables?

   Advance with `mapping_workflow` using `action='entity_plan'` and your plan.

   **Tell the user what was decided and why:** Explain the entity structure decision clearly:

   ```text
   Based on the profiling, here's the plan:

   Entity type: PERSON — your records describe individual people (I can tell from the name and address fields).

   Structure: Flat records — each row is one person with one set of attributes. No child records or relationships to handle.

   What this means: Each row in your CSV will become one Senzing JSON record. Senzing will then figure out which records refer to the same real-world person.

   Fields we'll map:
   - full_name → Senzing name feature (this is the primary matching field)
   - address → Senzing address feature (strong secondary matching)
   - phone → Senzing phone feature (helps confirm matches)
   - email → Senzing email feature (helps confirm matches)
   - internal_id → RECORD_ID (required identifier, not used for matching)

   Fields we'll skip:
   - status, created_date — these describe the record, not the person

   Does this plan look right, or would you like to adjust anything?
   ```

   **WAIT for user confirmation before proceeding.**

4. **Step 3 — Map:** Map each source field to Senzing features and attributes.

   > **Agent instruction:** Do not list specific attribute names here. The `mapping_workflow`
   > tool handles field mapping interactively and provides the correct, current attribute names.
   > Use `download_resource(filename="senzing_entity_specification.md")` if the user needs
   > the full attribute reference.

   Map fields for: names, addresses, contact info, identifiers, and dates.
   Assign confidence scores (0-100) based on data quality.

   **CRITICAL:** Never guess attribute names. Use the mapping workflow to ensure correct names.

   > **Agent instruction:** If the user's data contains non-Latin characters (Cyrillic, CJK,
   > Arabic, etc.), use `search_docs(query="globalization", category="globalization", version="current")`
   > for character set and transliteration guidance before mapping.

   Advance with `mapping_workflow` using `action='schema_mappings'` and your field mappings.

   **Tell the user what each mapping decision means:** Don't just show a mapping table — explain the reasoning:

   ```text
   Here are the field mappings I'm recommending, and why:

   | Your Field | → Senzing Attribute | Why This Mapping |
   |-----------|-------------------|-----------------|
   | full_name | NAME_FULL | Your data has complete names in one field. Senzing will parse first/last/middle automatically. |
   | address | ADDR_FULL | Full address string. Senzing parses street/city/state/zip internally. |
   | phone | PHONE_NUMBER | Senzing normalizes phone formats, so the mixed formatting in your data is fine. |
   | email | EMAIL_ADDRESS | Direct mapping. Senzing uses email as a confirming feature. |
   | internal_id | RECORD_ID | Every Senzing record needs a unique ID. Your internal_id is perfect for this. |

   Confidence: I'm fairly confident in these mappings (85/100). The main uncertainty is whether "address" always contains a full address or sometimes just a city/state — we'll find out when we test.

   Any of these look wrong, or should I adjust anything?
   ```

   **WAIT for user confirmation before proceeding.**

5. **Step 4 — Generate Starter Code:** The workflow generates:
   - Sample Senzing JSON output showing the target format
   - Starter mapper code in the bootcamper's chosen language
   - Transformation logic for complex fields

   This provides the foundation for the transformation program.

   Advance with `mapping_workflow` using `action='paths'` and the output file paths.

   **Tell the user what was generated:** Show a sample of the target JSON format so the user can see what their data will look like after transformation:

   ```text
   Here's what your data will look like after transformation (sample record):

   {
     "DATA_SOURCE": "CUSTOMERS",
     "RECORD_ID": "1001",
     "NAME_FULL": "John Smith",
     "ADDR_FULL": "123 Main St, New York, NY 10001",
     "PHONE_NUMBER": "5551234567",
     "EMAIL_ADDRESS": "john.smith@email.com"
   }

   The mapping workflow also generated starter code that I'll use as the foundation for your transformation program. Next, I'll build the complete program.
   ```

6. **Step 5 — Build the Transformation Program:** Help the user create a complete, runnable program for this data source.

   **IMPORTANT:** All generated code must follow the coding standards for the bootcamper's chosen language (see `docs/policies/CODE_QUALITY_STANDARDS.md`).

   > **Agent instruction:** The `mapping_workflow` generates starter code in Step 4. Use that
   > as the foundation. Do not use the inline example below — use `generate_scaffold` or the
   > mapping_workflow output for current SDK patterns. Customize based on the user's chosen
   > language, data source type, and volume.

   The program should handle:

   **Input:** Read from the original data source format (CSV, JSON, database, API)
   **Transformation:** Apply field mappings from Step 3, handle type conversions, combine/split fields, apply cleansing, set required `DATA_SOURCE` and `RECORD_ID` fields
   **Output:** Write Senzing JSON records to JSONL file in `data/transformed/`
   **Errors:** Handle malformed input records gracefully

   **Save the program:** Save to `src/transform/transform_[datasource_name].[ext]` where `[ext]` is the appropriate file extension for the chosen language. All transformation programs must be in the `src/transform/` directory.

   **Tell the user what was built and where:**

   ```text
   Done. I've created the transformation program:

   File: src/transform/transform_customers.py
   - Reads: data/raw/customers.csv
   - Writes: data/transformed/customers.jsonl
   - Handles: name normalization, phone format cleanup, missing field defaults
   - Error handling: Logs malformed rows to data/transformed/customers_errors.log

   Next: Let's test it on a small sample to make sure everything works before running the full dataset.
   ```

7. **Step 6 — Test the Program:** Run the transformation program on sample data from `data/samples/`:
   - Start with a small subset (10-100 records) for initial testing
   - Verify the program runs without errors
   - Check that output files are created in `data/transformed/`
   - Inspect a few output records manually

   Call `analyze_record` with sample output records to validate they conform to the Senzing Entity Specification and check data quality.

   **Tell the user the test results clearly:**

   ```text
   Test results (ran on 10 sample records):

   ✅ Program ran without errors
   ✅ Output file created: data/transformed/customers.jsonl
   ✅ All 10 records transformed successfully
   ✅ Senzing validation passed — records conform to the Entity Specification

   Sample output (first record):
   {"DATA_SOURCE": "CUSTOMERS", "RECORD_ID": "1001", "NAME_FULL": "John Smith", ...}

   One thing I noticed: 2 of 10 records had empty phone numbers. That's expected given the 72% completeness we saw in profiling — those records will still match on name and address.
   ```

8. **Step 7 — Quality Analysis:** Run the program on a larger sample (1000+ records if available). Call `analyze_record` with several mapped records to evaluate:
   - Feature distribution (are all important features populated?)
   - Attribute coverage (what percentage of records have each attribute?)
   - Data quality scores (completeness, consistency, validity)
   - Potential issues (missing critical data, malformed values)

   Advance with `mapping_workflow` using `action='verdict'` and your quality assessment.

   **Tell the user the quality analysis results with context:**

   ```text
   Quality analysis on 1,000 records:

   Overall quality score: 84/100 — Good

   Feature coverage:
   - Names: 98% of records have names → excellent for matching
   - Addresses: 87% → solid, most records will match on address too
   - Phones: 72% → decent, serves as confirming evidence
   - Emails: 65% → lower, but email is a bonus feature, not required

   What this means for entity resolution:
   - Records with names + addresses (87% of your data) will have strong matching potential
   - The 13% missing addresses will rely on name + phone/email, which may produce fewer matches
   - No critical issues found — this data is ready to load

   Potential improvements (optional):
   - 23 records have phone numbers in an unusual format (e.g., "ext. 123") — these were kept as-is
   - 5 records have names that look like company names — if these are organizations, we might want to map them differently
   ```

9. **Step 8 — Review Results:** Review the transformation program and results with the user:
   - Confirm the program successfully reads the input data
   - Verify the output format is correct Senzing JSON
   - Review data quality metrics
   - Discuss any data quality concerns
   - Confirm the program is ready for production use or needs adjustments

10. **Step 9 — Iterate if needed:** If quality issues were found or the program needs refinement, make adjustments. This is where the iterative nature of mapping becomes clear:

- Go back to Step 3 to adjust field mappings
- Return to Step 2 to reconsider entity structure
- Revisit Step 1 if you need to understand the data better
- Fix bugs in the transformation logic
- Adjust confidence scores
- Handle edge cases better
- Improve data cleansing
- Add validation or error handling

   Retest the program after changes. You may cycle through steps multiple times before achieving the desired quality.

1. **Step 10 — Save and Document:** Ensure the transformation program is properly saved and documented:

    - Program saved in `src/transform/transform_[datasource_name].[ext]` (all source code must be in `src/`)
    - Create `docs/mapping_[datasource_name].md` with:
      - Field mappings
      - Transformation logic
      - Data quality results
      - How to run the program
      - Dependencies and prerequisites
    - Save sample output in `data/transformed/[datasource_name]_sample.jsonl`

2. **Mark data source as complete:** Once the user is satisfied with the transformation program for this data source, mark it as complete and move to the next data source that needs mapping.

3. **Repeat for remaining data sources:** If there are more data sources that need mapping (from Module 4), repeat this entire workflow for each one. Each data source should have its own transformation program in `src/transform/`.

4. **Transition to Module 0:** Once all data sources have been either mapped (with working transformation programs) or confirmed as SGES-compliant, proceed to Module 0 (SDK Setup).

### Mapping State Checkpointing

The `mapping_workflow` MCP tool's state does not persist across Kiro sessions. To avoid losing progress during long mapping sessions, save a local checkpoint after each completed step.

**After each mapping step completes**, save the current state to `config/mapping_state_[datasource_name].json`:

```json
{
  "data_source": "CUSTOMERS",
  "source_file": "data/raw/customers.csv",
  "current_step": 3,
  "step_name": "Map fields",
  "completed_steps": ["profile", "plan", "map"],
  "decisions": {
    "entity_type": "PERSON",
    "structure": "flat",
    "field_mappings": {
      "full_name": "NAME_FULL",
      "address": "ADDR_FULL",
      "phone": "PHONE_NUMBER",
      "email": "EMAIL_ADDRESS",
      "internal_id": "RECORD_ID"
    },
    "skipped_fields": ["status", "created_date"],
    "confidence_score": 85
  },
  "last_updated": "2026-04-14T10:30:00Z"
}
```

**On session resume**, if `config/mapping_state_[datasource].json` exists:

1. Read the checkpoint and present it to the user: "Last time we were mapping [data source]. We completed steps 1-3 (profile, plan, map). Here's where we left off: [show decisions made so far]."
2. Restart `mapping_workflow` with `action='start'` and the same source file.
3. Fast-track through already-decided steps by reusing the saved decisions — don't re-ask the user questions they already answered.
4. Resume interactive work from the first incomplete step.

**Delete the checkpoint** when the data source mapping is fully complete (Step 10 done).

### Important Rules for Data Mapping

- NEVER hand-code Senzing JSON attribute names — use `mapping_workflow` to get the correct names. Use `search_docs` or `download_resource` for the current entity specification if needed.
- NEVER guess method signatures — use `generate_scaffold` or `get_sdk_reference` for correct API calls.
- NEVER save files to `/tmp/` or any system temporary directory — all resources, profiler output, scripts, and generated files must stay in the project directory. Downloaded resources go in `data/temp/` or `data/raw/`, profiler scripts go in `scripts/` or `src/transform/`, and generated output goes in `data/transformed/`. See `docs/policies/FILE_STORAGE_POLICY.md`.
- Always validate output with `analyze_record` before proceeding to loading.

### Handling Encoding and Special Characters

Source data may have encoding issues that cause silent data corruption during transformation. Check for these before mapping:

- **Detect encoding:** If the source file isn't UTF-8, the profiler step (Step 1) may show garbled characters. Common encodings: Latin-1 (ISO-8859-1), Windows-1252, Shift-JIS, GB2312.
- **Convert to UTF-8:** The transformation program should read the source file in its original encoding and write UTF-8 output. Most languages have built-in encoding support (e.g., Python's `open(file, encoding='latin-1')`, Java's `InputStreamReader` with charset).
- **Non-Latin characters:** If the data contains Cyrillic, CJK, Arabic, or other non-Latin scripts, use `search_docs(query="globalization", category="globalization", version="current")` for Senzing's transliteration and character handling guidance.
- **Special characters in field values:** Ensure JSON output properly escapes special characters (quotes, backslashes, control characters). Most JSON serialization libraries handle this automatically.
- **BOM (Byte Order Mark):** Some Windows-generated CSV files start with a UTF-8 BOM (`\xEF\xBB\xBF`). Strip it during reading or it will corrupt the first field name.
